# Two composers share the testids: scope everything to [role="dialog"] or an unscoped querySelector types
# into the inline box while you watch the modal's button. Post state lives in aria-disabled (never the
# `disabled` property) and X counts CJK as 2 chars. The composer emptying is the signal, not the click.
from selenium.webdriver.common.keys import Keys
exec(open("snippets/common/wait_js.py").read())

X_DIALOG_BOX = '[role="dialog"] [data-testid="tweetTextarea_0"]'
X_POST = '[role="dialog"] [data-testid="tweetButton"]'
X_CLOSE = '[role="dialog"] [data-testid="app-bar-close"]'
X_NEW_TWEET = '[data-testid="SideNav_NewTweet_Button"]'


def _x_check_enabled(driver, sel):
    return wait_js(
        driver,
        "!!document.querySelector('%s') && document.querySelector('%s')"
        ".getAttribute('aria-disabled') !== 'true'" % (sel, sel),
        timeout=15)


def _x_clear_box(driver):
    """Empty the DraftJS contenteditable (no .clear() on a div): select-all then DELETE. Re-clicking
    the box can hit ElementClickInterceptedException — X floats hints/tooltips over the composer the
    moment there is text in it — so keep the existing focus instead of insisting on a click."""
    box = driver.find_element("css selector", X_DIALOG_BOX)
    try:
        box.click()
    except Exception:
        box = driver.switch_to.active_element
    box.send_keys(Keys.CONTROL, "a")
    box.send_keys(Keys.DELETE)
    return wait_js(driver,
                   "!document.querySelector('%s').innerText.trim()" % X_DIALOG_BOX,
                   timeout=5)


def _x_close_composer(driver):
    if not driver.find_elements("css selector", X_DIALOG_BOX):
        return True
    driver.find_element("css selector", X_CLOSE).click()
    if wait_js(driver, "!document.querySelector('%s')" % X_DIALOG_BOX, timeout=4):
        return True
    if driver.find_elements("css selector",
                            '[data-testid="confirmationSheetCancel"]'):
        driver.find_element("css selector",
                            '[data-testid="confirmationSheetCancel"]').click()
    return wait_js(driver, "!document.querySelector('%s')" % X_DIALOG_BOX, timeout=6)


def x_post_tweet(driver, text, dry_run=False):
    """Compose `text` and post it. dry_run=True types, checks the button, then discards — nothing sent."""
    if not driver.find_elements("css selector", X_DIALOG_BOX):
        driver.find_element("css selector", X_NEW_TWEET).click()
    if not wait_js(driver, "!!document.querySelector('%s')" % X_DIALOG_BOX):
        print(
            "POST_FAILED: modal composer never mounted (logged in? overlay stuck?)"
        )
        return False
    box = driver.find_element("css selector", X_DIALOG_BOX)
    box.click()
    box.send_keys(text)
    ready = _x_check_enabled(driver, X_POST)
    print("TYPED: %d chars | READY: %s" % (len(box.text), ready))
    if dry_run or not ready:
        cleared = _x_clear_box(driver)
        closed = _x_close_composer(driver)
        print(
            "DRY_RUN: cleared=%s closed=%s - nothing was sent" %
            (cleared, closed) if dry_run else
            "NOT_SENT: Post button never enabled (too long? CJK counts double)"
        )
        return False
    driver.find_element("css selector", X_POST).click()
    closed = wait_js(driver, "!document.querySelector('%s')" % X_DIALOG_BOX, timeout=30)
    toast = ""
    try:
        toast = " ".join(
            driver.find_element("css selector",
                                '[data-testid="toast"]').text.split())
    except Exception:
        pass
    print("POSTED:" if closed else "POST_UNCONFIRMED:", closed, "| toast:",
          toast or "(none)")
    return closed
