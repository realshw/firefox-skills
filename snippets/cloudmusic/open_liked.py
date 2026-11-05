# "我喜欢的音乐" appears in 4 nodes — take the sidebar one (x < 240). Clicks right after a cold load are
# swallowed and handles go stale during hydration, so every check runs through JS and the click is retried.
import time
from selenium.common.exceptions import StaleElementReferenceException


def _toolbar_up(driver):
    return bool(
        driver.execute_script(
            "return document.body.innerText.includes('播放全部')"))


def _on_liked(driver):
    # the playlist page's header h2 — other pages have their own h2 (visible = non-zero rect)
    return bool(
        driver.execute_script(
            "return [...document.querySelectorAll('h2')].some(h => {"
            "const r = h.getBoundingClientRect();"
            "return r.width > 0 && r.height > 0 && (h.innerText || '').includes('我喜欢的音乐');})"
        ))


def open_liked(driver):
    deadline = time.time() + 30
    while not _toolbar_up(driver):
        if time.time() > deadline:
            raise RuntimeError("liked playlist toolbar did not appear")
        if not _on_liked(driver):
            try:
                els = [
                    e for e in driver.find_elements(
                        "xpath", '//*[contains(text(), "我喜欢的音乐")]')
                    if e.is_displayed() and e.location["x"] < 240
                ]
                if els:
                    driver.execute_script("arguments[0].click()", els[0])
            except StaleElementReferenceException:
                pass  # the DOM re-rendered mid-scan — try again next tick
        time.sleep(0.5)
    print("OPENED_LIKED")
