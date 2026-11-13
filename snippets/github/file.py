# File contents cannot be fetch()ed (/raw/ 302s to raw.githubusercontent.com without CORS; a credentialed
# api.github.com call loses the login and hits 60 req/h), so _github_read_in_tab(driver) *navigates* a tab of its
# own, reads document.body — Firefox renders text/plain in a <pre> — then switches back, leaving the fetched
# page open like any other. Firefox discards an unloaded background tab, handle and all, so the way back is
# not guaranteed: stay on whatever is left rather than raising after a read that already succeeded.
import os
import tempfile
import time

exec(open("snippets/common/wait_js.py").read())


def _github_read_in_tab(driver, url, settle=1.2, timeout=30):
    """Load url in a tab of its own, return (body_text, content_type), then switch back."""
    orig = driver.current_window_handle
    driver.switch_to.new_window('tab')
    try:
        driver.get(url)
        wait_js(driver,
                "document.readyState === 'complete'",
                timeout,
                tick=0.4)
        time.sleep(settle)  # the <pre> body mounts a beat after readyState
        text = driver.find_element("tag name", "body").text
        ctype = driver.execute_script("return document.contentType || ''")
        return text, ctype
    finally:
        try:
            if orig in driver.window_handles:
                driver.switch_to.window(orig)
            else:
                print(
                    "READ_TAB: the tab we came from is gone - staying on the fetched page"
                )
        except Exception:
            pass  # the session itself is gone; nothing left to switch to


def github_raw_url(slug, path, ref='HEAD'):
    """https://github.com/<slug>/raw/<ref>/<path> — the redirecting form is the one that works."""
    return "https://github.com/" + slug.strip(
        "/") + "/raw/" + ref + "/" + path.lstrip("/")


def _github_fetch(driver, slug, path, ref):
    """(text, content_type) for one file; GitHub answers a wrong path with an html 404 page, which is a
    successful read of the wrong thing — say so instead of handing back the page as the file."""
    text, ctype = _github_read_in_tab(driver, github_raw_url(slug, path, ref))
    if ctype and not ctype.startswith('text/plain'):
        print("NO_FILE:",
              slug.strip('/') + "/" + path + " @" + ref, "->", ctype,
              "not text/plain (wrong path or ref?)")
        return '', ctype
    return text, ctype


def github_save_file(driver, slug, path, ref='HEAD', out_path=None):
    """Download one file's text to out_path (default: the system temp dir); return the text."""
    text, ctype = _github_fetch(driver, slug, path, ref)
    if not text:
        print("SAVE_FAILED: nothing to write")
        return ''
    out_path = out_path or os.path.join(
        tempfile.gettempdir(),
        os.path.basename(path.rstrip('/')) or 'github_file')
    with open(out_path, "w") as f:
        f.write(text)
    print("SAVED:", out_path,
          "(" + str(len(text)) + " chars, " + (ctype or '?') + ")")
    return text


def github_read_file(driver, slug, path, ref='HEAD', preview=0):
    """Return a file's text and print its exact length; preview > 0 prints that many chars."""
    text, ctype = _github_fetch(driver, slug, path, ref)
    print("FILE:",
          slug.strip('/') + "/" + path + " @" + ref, "->", len(text), "chars",
          "(" + (ctype or '?') + ")")
    if preview:
        print(text[:preview])
    return text
