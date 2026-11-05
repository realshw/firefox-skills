# Sends whatever sits in the inline composer (the half set_reply_draft.py does not do). tweetButtonInline's
# aria-disabled only clears once there is content and an early click is a silent no-op, so check it first.
# Confirmation is "the editor emptied"; the toast is reported, never required.
from snippets.common.wait_js import wait_js

BOX = '[data-testid="tweetTextarea_0"]'
SEND = '[data-testid="tweetButtonInline"]'

_INLINE = ("[...document.querySelectorAll('" + BOX + "')]"
           ".find(e => !e.closest('[role=\"dialog\"]')) || null")


def send_reply_draft(driver, timeout=30):
    """Click Reply on the current inline draft; True once the composer is empty again."""
    box = driver.execute_script("return (" + _INLINE + ")")
    if not box:
        print("NO_COMPOSER: no inline reply box on this page")
        return False
    before = driver.execute_script("return (" + _INLINE +
                                   ").innerText").strip()
    if not before:
        print("EMPTY: nothing typed, not clicking Reply")
        return False
    if not wait_js(
            driver, "!!document.querySelector('" + SEND + "')"
            " && document.querySelector('" + SEND +
            "').getAttribute('aria-disabled') !== 'true'", 15):
        print("NOT_SENT: Reply button never enabled")
        return False
    driver.find_element("css selector", SEND).click()
    ok = wait_js(
        driver, "!(function(){var e=" + _INLINE +
        "; return e && e.innerText.trim()})()", timeout)
    toast = driver.execute_script(
        "const t = document.querySelector('[data-testid=\"toast\"]'); return t ? t.innerText.trim() : ''"
    )
    print("SENT: %s | %d chars | toast: %s | %s" %
          (ok, len(before), toast or '-', driver.current_url))
    return ok
