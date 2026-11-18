"""Load a url, absorbing the load timeout, and wait until the page has text."""

from selenium.common.exceptions import TimeoutException

exec(open("snippets/common/wait_js.py").read())


def goto(driver, url, timeout=25, tick=0.5):
    """Navigate absorbing the load timeout, then wait until the page has text; True when it does.

    driver.get() raises TimeoutException whenever one subresource never settles, but by then the document is
    usually rendered — news sites leave an ad or analytics request hanging forever, and the article is
    readable, so the timeout is absorbed instead of re-navigating. The wait is on innerText because a page
    mid-load has no body at all (readyState "loading", find_element("body") raises NoSuchElement).
    """
    try:
        driver.get(url)
    except TimeoutException:
        print("GOTO: load timed out after the page-load ceiling - reading what rendered")
    ok = wait_js(driver, "!!(document.body && document.body.innerText.trim())", timeout, tick)
    if not ok:
        print("GOTO: no body text after %.0fs (%s)" % (timeout, driver.current_url))
    return ok
