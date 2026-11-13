# ytInitialPlayerResponse is the *initial load* snapshot, so an SPA hop leaves a stale one — open_video(driver)
# always does a full driver.get() then waits until videoDetails.videoId matches (ytcfg is on the home page
# too, never use it as the check). The DOM lands later, so every read waits first; one regex covers all
# id forms. publishDate is absent on some uploads — .get() it and fall back to the DOM.
import json
import re

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

_ID = re.compile(
    r"(?:v=|/shorts/|/live/|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})")


def video_id(url_or_id):
    """11-char id from any YouTube url shape, or the bare id passed through."""
    m = _ID.search(url_or_id)
    return m.group(1) if m else url_or_id.strip()


def open_video(driver, url_or_id, timeout=30):
    """Load a watch page and return its metadata as a dict (see video_info)."""
    vid = video_id(url_or_id)
    site_tab(driver, "youtube.com")
    driver.get("https://www.youtube.com/watch?v=" + vid)
    wait_js(
        driver,
        "(window.ytInitialPlayerResponse"
        " && window.ytInitialPlayerResponse.videoDetails || {}).videoId === %s"
        % json.dumps(vid),
        timeout,
        tick=0.8)
    wait_js(driver, "!!document.querySelector('ytd-watch-metadata')", timeout)
    info = youtube_video_info(driver)
    print("YOUTUBE:", info["title"][:80], "|", info["author"], "|",
          info["length"], "s |", info["id"])
    return info


def youtube_video_info(driver):
    """Current watch page as a dict: id / title / author / length / views / publish / description."""
    js = """
    var r = window.ytInitialPlayerResponse; if (!r || !r.videoDetails) return null;
    var v = r.videoDetails, m = (r.microformat || {}).playerMicroformatRenderer || {};
    return {id: v.videoId, title: v.title, author: v.author, length: v.lengthSeconds,
            views: v.viewCount, publish: m.publishDate || '',
            description: v.shortDescription || ''};
    """
    d = driver.execute_script(js)
    if not d:
        raise RuntimeError(
            "no player response on this page — not a watch page?")
    return d


def description(driver, limit=4000, timeout=15):
    """Print the description (the page's collapsed text, not the truncated meta one)."""
    wait_js(
        driver,
        "!!document.querySelector('ytd-watch-metadata #description-inline-expander')",
        timeout)
    t = driver.execute_script(
        "var e = document.querySelector('ytd-watch-metadata #description-inline-expander');"
        "return e ? e.innerText : '';")
    print(t[:limit] or "NO DESCRIPTION")
    return len(t)
