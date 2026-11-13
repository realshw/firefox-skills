# Click 播放全部 and wait for the pause icon in the mini bar. Right after a cold load the track can park
# itself at PAUSED, so sample the mini-bar clock too and resume once if it has not moved.
import json
from selenium.webdriver.support.ui import WebDriverWait

exec(open("snippets/common/wait_js.py").read())

_CLOCK_JS = (
    "(function(){const f = document.querySelector('footer');"
    " if (!f) return null;"
    " const t = [...f.querySelectorAll('[class*=miniBarTimeTextStyle]')]"
    ".map(e => e.innerText.trim());"
    " return t.length ? t[0] : null;})()")


def _PLAY_ICON(driver):
    els = [
        e for e in driver.find_elements(
            "css selector",
            "footer span[aria-label=pause], footer span[aria-label=play]")
        if e.is_displayed()
    ]
    return els[0] if els else None


def _clock(driver):
    return driver.execute_script("return (%s);" % _CLOCK_JS)


def _clock_moves(driver, first):
    return wait_js(driver, "(%s) !== %s" % (_CLOCK_JS, json.dumps(first)), 8)


def play_all(driver):
    els = [
        e
        for e in driver.find_elements("xpath", '//*[contains(text(), "播放全部")]')
        if e.is_displayed()
    ]
    if not els:
        raise RuntimeError("播放全部 button not found")
    els[0].click()
    WebDriverWait(driver, 15).until(lambda d: d.find_elements(
        "css selector", "footer span[aria-label=pause]"))
    first = _clock(driver)
    if not _clock_moves(driver, first):
        icon = _PLAY_ICON(driver)
        if icon is not None and icon.get_attribute("aria-label") == "play":
            icon.click()
            _clock_moves(driver, first)
    print(
        "PLAY_ALL_CLICKED", "clock=" + str(first),
        "icon=" + (_PLAY_ICON(driver).get_attribute("aria-label")
                   if _PLAY_ICON(driver) else "MISSING"))
