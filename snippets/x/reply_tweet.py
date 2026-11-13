# The inline and modal composers share tweetTextarea_0 — take the box NOT inside [role="dialog"], and it
# mounts a moment after navigation. Same aria-disabled rule as post_tweet; clear with select-all+DELETE,
# never a click on the box (a floating hint intercepts it).
from selenium.webdriver.common.keys import Keys
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

X_BOX = '[data-testid="tweetTextarea_0"]'
X_SEND = '[data-testid="tweetButtonInline"]'
# The two draft files exec this file for the same composer, so these three live here once.
_X_INLINE = ("[...document.querySelectorAll('" + X_BOX + "')]"
             ".find(e => !e.closest('[role=\"dialog\"]')) || null")


def _x_find_inline_box(driver):
    """The composer outside any modal (None if only a modal one exists)."""
    return driver.execute_script(
        "return [...document.querySelectorAll('" + X_BOX + "')]"
        ".find(e => !e.closest('[role=\"dialog\"]')) || null")


def x_reply_tweet(driver, url, text, dry_run=False):
    """Open `url` (a /status/ link or handle/status/id) and reply with the inline composer."""
    if not url.startswith("http"):
        url = "https://x.com/" + url.lstrip("/")
    site_tab(driver, "//x.com/")
    driver.get(url)
    if not wait_js(
            driver, "!!(function(){return [...document.querySelectorAll('" +
            X_BOX + "')]"
            ".find(e => !e.closest('[role=\"dialog\"]'))})()"):
        print(
            "REPLY_FAILED: inline composer never mounted (deleted post? replies limited?)"
        )
        return False
    box = _x_find_inline_box(driver)
    box.click()
    box.send_keys(text)
    ready = wait_js(driver,
                    "!!document.querySelector('" + X_SEND +
                    "') && document.querySelector('" + X_SEND +
                    "').getAttribute('aria-disabled') !== 'true'",
                    timeout=15)
    print("TYPED: %d chars | READY: %s" % (len(box.text), ready))
    if dry_run or not ready:
        box.send_keys(Keys.CONTROL, "a")
        box.send_keys(Keys.DELETE)
        cleared = wait_js(
            driver,
            "!(function(){var e=[...document.querySelectorAll('" + X_BOX + "')]"
            ".find(x => !x.closest('[role=\"dialog\"]'));return e && e.innerText.trim()})()",
            timeout=5)
        print("DRY_RUN: cleared=%s - no reply sent" %
              cleared if dry_run else "NOT_SENT: Reply button never enabled")
        return False
    driver.find_element("css selector", X_SEND).click()
    ok = wait_js(
        driver,
        "!(function(){var e=[...document.querySelectorAll('" + X_BOX + "')]"
        ".find(x => !x.closest('[role=\"dialog\"]'));return e && e.innerText.trim()})()",
        timeout=30)
    print("REPLIED:" if ok else "REPLY_UNCONFIRMED:", ok, "|",
          driver.current_url)
    return ok
