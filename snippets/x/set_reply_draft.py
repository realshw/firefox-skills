# Replaces the inline reply draft without sending (send_reply_draft.py sends). Take the box NOT inside
# [role="dialog"]; never click it to focus (a floating hint eats the click) — send_keys focuses fine.
# Draft.js needs real keys: clear with Control+A + DELETE, then read innerText back.
from selenium.webdriver.common.keys import Keys

exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/x/reply_tweet.py").read())


def x_set_reply_draft(driver, text, timeout=25):
    """Replace the inline reply draft with text. Returns the draft read back from the editor."""
    wait_js(driver, "!!(" + _X_INLINE + ")", timeout)
    box = driver.execute_script("return (" + _X_INLINE + ")")
    if not box:
        print("NO_COMPOSER: inline reply box never mounted on this page")
        return ''
    driver.execute_script("arguments[0].focus()", box)
    box.send_keys(Keys.CONTROL, "a")
    box.send_keys(Keys.DELETE)
    if text:
        box.send_keys(text)
    draft = driver.execute_script("return (" + _X_INLINE + ").innerText")
    ready = driver.execute_script("const b = document.querySelector('" + X_SEND + "');"
                                  "return !!(b && b.getAttribute('aria-disabled') !== 'true');")
    print("DRAFT:", repr(draft.strip()))
    print("LEN %d | REPLY_BUTTON_READY %s | NOT SENT" % (len(draft.strip()), ready))
    return draft.strip()
