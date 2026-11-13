# Toggle play/pause and verify by reading the label back — read it *before* the click, the toggle swaps
# the node out. The 0.3 s is not a condition: the mini bar slides in, and a click aimed at a moving element
# lands somewhere else.
import time

exec(open("snippets/common/wait_js.py").read())


def _TOGGLE_ICON(driver):
    els = [
        e for e in driver.find_elements(
            "css selector",
            "footer span[aria-label=pause], footer span[aria-label=play]")
        if e.is_displayed()
    ]
    return els[0] if els else None


def toggle_play(driver):
    before = _TOGGLE_ICON(driver)
    if before is None:
        raise RuntimeError("play/pause control not found in mini bar")
    before_label = before.get_attribute("aria-label")
    want = "play" if before_label == "pause" else "pause"
    time.sleep(0.3)
    before.click()
    wait_js(
        driver,
        "[...document.querySelectorAll('footer span[aria-label]')]"
        ".some(e => e.offsetParent && e.getAttribute('aria-label') === '%s')" %
        want,
        5,
        tick=0.3)
    after = _TOGGLE_ICON(driver)
    print("TOGGLED:", before_label, "->",
          after.get_attribute("aria-label") if after else "MISSING")
