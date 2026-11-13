# The DOM exposes only a poster jpg and a blob: src (MSE), so the mp4 url comes from the syndication API —
# its token must be computed *in the browser* (Python's base36 rounds differently, a wrong token 404s).
# Working door: a tab of its own on the viewer, click "Raw Data", read pre#rawdata.textContent; the bytes
# come back in ~4 MB Range slices. The m3u8 fallback is partial (video track only).
import base64
import json
import os
import re
import tempfile
import time
from urllib.parse import urljoin

CHUNK = 4 * 1024 * 1024  # per-fetch slice; base64 of this is ~5.5 MB on the wire
SYND = "https://cdn.syndication.twimg.com/tweet-result?id=%s&token=%s"

FETCH_RANGE_JS = r"""
const url = arguments[0], start = arguments[1], end = arguments[2];
const done = arguments[arguments.length - 1];
let finished = false;
const fin = o => { if (!finished) { finished = true; done(o); } };
setTimeout(() => fin({ok: false, err: 'timeout'}), 120000);
fetch(url, {headers: {'Range': 'bytes=' + start + '-' + end}}).then(r => r.blob().then(b => {
    const fr = new FileReader();
    fr.onload = () => fin({ok: r.ok, status: r.status,
                           total: r.headers.get('content-range'), data: fr.result});
    fr.onerror = () => fin({ok: false, err: 'filereader'});
    fr.readAsDataURL(b);
})).catch(e => fin({ok: false, err: String(e)}));
"""

FETCH_TEXT_JS = r"""
const url = arguments[0], done = arguments[arguments.length - 1];
let finished = false;
const fin = o => { if (!finished) { finished = true; done(o); } };
setTimeout(() => fin({ok: false, err: 'timeout'}), 20000);
fetch(url).then(r => r.text().then(t => fin({ok: r.ok, status: r.status, body: t})))
           .catch(e => fin({ok: false, err: String(e)}));
"""

RAW_JS = r"""
const b = [...document.querySelectorAll('button, a')]
    .find(el => /raw data/i.test(el.textContent || ''));
if (b) b.click();
const p = document.querySelector('pre#rawdata') || document.querySelector('pre');
return p ? p.textContent : null;
"""


# Status/timeline pages mount their articles a beat after driver.get() returns: reading index 0 too
# early reports NO_TWEET while the DOM is still empty, which looks exactly like "this post has no
# video". Poll for the article instead of sleeping a guessed 3 s.
def _wait_articles(driver, index, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        n = driver.execute_script(
            "return document.querySelectorAll('article[data-testid=\"tweet\"]').length"
        )
        if n and n > index:
            return True
        time.sleep(0.5)
    return False


def tweet_id(driver, index=0):
    _wait_articles(driver, index)
    try:
        return driver.execute_script(
            "const a = document.querySelectorAll('article[data-testid=\"tweet\"]')[arguments[0]];"
            "if (!a) return null;"
            "const l = a.querySelector('a[href*=\"/status/\"]');"
            "const m = l && (l.getAttribute('href') || '').match(/status\\/(\\d+)/);"
            "return m ? m[1] : null;", index)
    except Exception:
        return None


def _syndication(driver, tid, timeout=25):
    """The syndication JSON for tid, read out of its own tab's raw pane."""
    token = driver.execute_script(
        "return ((%s/1e15)*Math.PI).toString(36).replace(/(0+|\\.)/g,'')" %
        tid)
    current = driver.current_window_handle
    driver.switch_to.new_window('tab')
    # the new tab has focus, so driver.get() navigates it and leaves the tweet tab alone
    try:
        driver.get(SYND % (tid, token))
        end = time.time() + timeout
        raw = None
        while time.time() < end:
            raw = driver.execute_script(RAW_JS)
            if raw and raw.lstrip().startswith("{"):
                break
            time.sleep(0.5)
        return json.loads(raw) if raw else None
    except Exception as e:
        print("SYNDICATION_FAILED:", type(e).__name__, e)
        return None
    finally:
        if current in driver.window_handles:
            driver.switch_to.window(current)


def x_video_info(driver, index=0, tid=None):
    """{tid, duration_ms, poster, variants: [{type, bitrate, url}]} or None if the post has no video.

    `tid` skips the DOM read entirely — a timeline/search result row's status id is enough.
    """
    tid = tid or tweet_id(driver, index)
    if not tid:
        print(
            "NO_TWEET: no article at index %d — not an x.com timeline/status, or still loading?"
            % index)
        return None
    j = _syndication(driver, tid) or {}
    media = (j.get("mediaDetails") or [{}])[0]
    vi = media.get("video_info") or {}
    out = {
        "tid":
        tid,
        "duration_ms":
        media.get("video_info", {}).get("duration_millis")
        or media.get("video", {}).get("durationMs"),
        "poster":
        (media.get("media_url_https") or "") + "?name=orig" if media else "",
        "variants": []
    }
    for v in vi.get("variants") or []:
        out["variants"].append({
            "type": v.get("content_type"),
            "bitrate": v.get("bitrate") or 0,
            "url": v.get("url")
        })
    if not out["variants"]:
        alt = ((media.get("video") or {}).get("variants")) or []
        for v in alt:
            out["variants"].append({
                "type": v.get("type"),
                "bitrate": 0,
                "url": v.get("src")
            })
    return out if out["variants"] else None


def _slice(driver, url, start, end):
    """(bytes, status) for one Range request — status is the http code, or None on failure."""
    info = driver.execute_async_script(FETCH_RANGE_JS, url, start, end) or {}
    if not info.get("ok") or not (info.get("data") or "").startswith("data:"):
        print("FETCH_FAILED:", info.get("err") or info.get("status"), url[:90])
        return None, None
    head, b64 = info["data"].split(",", 1)
    return base64.b64decode(b64), info.get("status")


def _download(driver, url, path, chunk=CHUNK, verbose=True):
    """Chunked Range download through the page fetch; returns bytes written or None.

    The total size *cannot* be read from Content-Range: it is not a CORS-safelisted response
    header, so r.headers.get('content-range') is null cross-origin and a "stop at total" loop
    silently keeps only the first 4 MB slice (a 1072x1080 GIF came back as exactly 4194304 bytes).
    So probe by short read instead: a slice shorter than asked for is the last one, an empty slice
    is past EOF, and a 200 means Range was ignored and that one slice is the whole file.
    """
    parts, got, guard = [], 0, 0
    while True:
        part, status = _slice(driver, url, got, got + chunk - 1)
        if part is None:
            if not parts:
                return None
            print("FETCH_ABORTED at %d KB" % (got // 1024))
            break
        if not part:
            break
        parts.append(part)
        got += len(part)
        if status == 200 or len(part) < chunk:
            break
        guard += 1
        if guard > 256:  # ~1 GB sanity stop, never a real X video
            print("CHUNK_LIMIT_REACHED at %d KB" % (got // 1024))
            break
        if verbose:
            print("  %d KB" % (got // 1024))
    blob = b"".join(parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    return len(blob)


def _hls(driver, url, path_base, verbose=True):
    """Fallback: pull a media playlist's segments and concatenate them into a .ts."""
    info = driver.execute_async_script(FETCH_TEXT_JS, url) or {}
    if not info.get("ok"):
        print("HLS_PLAYLIST_FAILED:", info.get("err") or info.get("status"))
        return None
    lines = [l.strip() for l in (info.get("body") or "").splitlines()]
    if any("#EXT-X-STREAM-INF" in l for l in lines):
        # master playlist — take the highest BANDWIDTH variant, not the first line (the smallest).
        # Its audio lives in a separate #EXT-X-MEDIA group, so this yields a video-only stream.
        best, level = None, -1
        for i, l in enumerate(lines):
            if l.startswith("#EXT-X-STREAM-INF"):
                bw = re.search(r"BANDWIDTH=(\d+)", l)
                nxt = next(
                    (x for x in lines[i + 1:] if x and not x.startswith("#")),
                    None)
                if nxt and bw and int(bw.group(1)) > level:
                    best, level = nxt, int(bw.group(1))
        return _hls(driver, urljoin(url, best), path_base,
                    verbose) if best else None
    segs = [urljoin(url, l) for l in lines if l and not l.startswith("#")]
    for l in lines:
        if l.startswith("#EXT-X-MAP"):
            m = re.search(r'URI="([^"]+)"', l)
            if m:
                segs.insert(0, urljoin(url, m.group(1)))
    if not segs:
        print("HLS_NO_SEGMENTS")
        return None
    blob = b""
    for i, s in enumerate(segs, 1):
        part, _st = _slice(driver, s, 0, CHUNK * 8 - 1)
        if not part:
            print("HLS_SEGMENT_FAILED", i)
            return None
        blob += part
        if verbose:
            print("  segment %d/%d  %d KB" % (i, len(segs), len(part) // 1024))
    path = path_base + ".ts"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    return len(blob), path


def save_video(driver,
               index=0,
               out_dir=None,
               max_height=720,
               dry_run=False,
               verbose=True):
    """Save the video attached to article `index` (current page must be x.com) to out_dir (default:
    the system temp dir). Returns path(s)."""
    # Marionette kills execute_async_script at the *driver's* script timeout (20-30 s by default) long
    # before our in-page 120 s guard fires — a slow 4 MB slice then surfaces as a TimeoutException that
    # looks like a hang. Raise it once, here, rather than per call.
    try:
        driver.set_script_timeout(180)
    except Exception:
        pass
    out_dir = out_dir or os.path.join(tempfile.gettempdir(), "x_video")
    vi = x_video_info(driver, index)
    if not vi:
        print(
            "NO_VIDEO: article %d carries no video (photo-only, or the media is in a quoted post)"
            % index)
        return []
    tid = vi["tid"]
    mp4s = [
        v for v in vi["variants"]
        if (v["type"] or "").endswith("mp4") and v["url"]
    ]
    hls = [v for v in vi["variants"] if "mpegURL" in (v["type"] or "")]

    def _h(u):
        m = re.search(r"/(\d+)x(\d+)/", u)
        return int(m.group(2)) if m else 0

    mp4s = [v for v in mp4s if _h(v["url"]) <= max_height] or mp4s
    mp4s.sort(key=lambda v: v["bitrate"] or _h(v["url"]))
    pick = mp4s[-1] if mp4s else None
    base = os.path.join(out_dir, "x_%s" % tid)

    if dry_run:
        print("DURATION: %.1fs" % ((vi["duration_ms"] or 0) / 1000.0))
        for v in vi["variants"]:
            print("  DRY: %-22s %8s  %s" % (v["type"], v["bitrate"], v["url"]))
        print("DRY_PICK:", (pick or {}).get("url")
              or (hls[0]["url"] if hls else "none"))
        return []

    print("DURATION: %.1fs  (%d variant(s))" %
          ((vi["duration_ms"] or 0) / 1000.0, len(vi["variants"])))
    if pick:
        path = base + ".mp4"
        dims = re.search(r"/(\d+)x(\d+)/", pick["url"])
        if verbose:
            print("PICK: %s  bitrate=%s  %s" %
                  (pick["type"], pick["bitrate"],
                   (dims.group(1) + "x" + dims.group(2)) if dims else "?"))
        size = _download(driver, pick["url"], path, verbose=verbose)
        if size:
            print("SAVED: %s (%.1f MB)" % (path, size / 1048576.0))
            return [path]
        return []
    if hls:
        got = _hls(driver, hls[0]["url"], base, verbose=verbose)
        if got:
            size, path = got
            print("SAVED: %s (%.1f MB, HLS fallback — .ts container)" %
                  (path, size / 1048576.0))
            return [path]
    print("NO_DOWNLOADABLE_VARIANT")
    return []
