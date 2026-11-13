# Downloads ride the browser: pbs.twimg.com answers CORS, so a fetch() inside the page reads the bytes and
# returns base64 — never shell out to curl/requests, the machine only reaches the net through the browser.
# ?name=orig 404s on some media, so fall back large -> as-is; and the fetch must start the FileReader or
# execute_async_script hangs into a 20 s TimeoutException. Video posts yield only their poster.
import base64
import os
import re
import tempfile

X_FETCH_JS = r"""
const url = arguments[0], done = arguments[arguments.length - 1];
let finished = false;
const fin = o => { if (!finished) { finished = true; done(o); } };
setTimeout(() => fin({ok: false, status: 0, err: 'timeout'}), 15000);
fetch(url).then(r => r.blob().then(b => {
    const fr = new FileReader();
    fr.onload = () => fin({ok: r.ok, status: r.status, type: b.type, data: fr.result});
    fr.onerror = () => fin({ok: false, status: r.status, err: 'filereader'});
    fr.readAsDataURL(b);
})).catch(e => fin({ok: false, status: 0, err: String(e)}));
"""

X_MEDIA_JS = r"""
const i = arguments[0];
const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
const a = arts[i];
if (!a) return null;
const quoteBox = a.querySelector('div[role="link"]');
const imgs = [...a.querySelectorAll('[data-testid="tweetPhoto"] img')]
    .filter(img => !(quoteBox && quoteBox.contains(img)));
return imgs.map(img => ({url: img.src, alt: img.getAttribute('alt') || ''}));
"""


def _x_read_tweet_id(driver, index):
    try:
        return driver.execute_script(
            "const a = document.querySelectorAll('article[data-testid=\"tweet\"]')[arguments[0]];"
            "if (!a) return null;"
            "const l = a.querySelector('a[href*=\"/status/\"]');"
            "const m = l && (l.getAttribute('href') || '').match(/status\\/(\\d+)/);"
            "return m ? m[1] : null;", index)
    except Exception:
        return None


def x_list_media(driver, index=0):
    """[{url, alt}] — the tweet's own photos / video posters (quoted media excluded)."""
    return driver.execute_script(X_MEDIA_JS, index) or []


def _x_fetch_data(driver, url):
    info = driver.execute_async_script(X_FETCH_JS, url) or {}
    if not info.get("ok") or not (info.get("data") or "").startswith("data:"):
        return None
    head, b64 = info["data"].split(",", 1)
    return base64.b64decode(b64), (info.get("type") or head.split(";")[0][5:] or ""), info["data"]


def _x_find_best_bytes(driver, url, want_orig=True):
    """Try name=orig, then name=large, then the URL as given — orig 404s on some media."""
    tries = []
    if want_orig:
        tries.append(re.sub(r"name=\w+", "name=orig", url))
        tries.append(re.sub(r"name=\w+", "name=large", url))
    tries.append(url)
    for u in dict.fromkeys(tries):
        got = _x_fetch_data(driver, u)
        if got and got[0]:
            return got[0], got[1], u
    return None, "", url


def x_save_media(driver, index=0, out_dir=None, want_orig=True, dry_run=False):
    """Save one tweet's photos/video posters to out_dir (default: the system temp dir); returns the
    saved paths (alt text printed)."""
    out_dir = out_dir or os.path.join(tempfile.gettempdir(), "x_media")
    items = x_list_media(driver, index)
    if not items:
        print("NO_MEDIA: article %d has no photo (text-only, or its media is in a quoted tweet)" % index)
        return []
    tid = _x_read_tweet_id(driver, index) or "notweet"
    if dry_run:
        for i, it in enumerate(items, 1):
            print("DRY: %s | alt: %s" % (it["url"], it["alt"] or "(none)"))
        return []
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, it in enumerate(items, 1):
        data, ctype, used = _x_find_best_bytes(driver, it["url"], want_orig)
        if not data:
            print("FAILED:", it["url"])
            continue
        ext = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif"
        }.get(ctype.split(";")[0], "jpg")
        path = os.path.join(out_dir, "x_%s_%d.%s" % (tid, i, ext))
        with open(path, "wb") as f:
            f.write(data)
        paths.append(path)
        print("SAVED: %s (%d KB) alt: %s" % (path, len(data) // 1024, it["alt"] or "(none)"))
        if used != it["url"]:
            print("  via", used)
    print("SAVED_COUNT:", len(paths), "-> read each path to actually look at it")
    return paths
