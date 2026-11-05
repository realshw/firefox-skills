# SPA — the url stays /st/webplayer, so poll for "推荐歌单" instead. The 推荐 item wraps an icon, so match
# innerText in JS (text() is direct nodes only). Cold loads paint a logged-out skeleton first, so the item
# is missing for a while: poll, never fail on the first look, and click through JS.
import time
from selenium.webdriver.support.ui import WebDriverWait

_FIND_SIDEBAR = r"""
const t = arguments[0];
return [...document.querySelectorAll('body *')].find(e => {
  const r = e.getBoundingClientRect();
  return r.width > 0 && r.left < 240 && e.children.length === 0 && (e.innerText || '').trim() === t;
}) || null;
"""


def _click_sidebar(driver, label):
    el = driver.execute_script(_FIND_SIDEBAR, label)
    if el is None:
        return False
    driver.execute_script("arguments[0].click()", el)
    return True


def open_rec(driver):
    if "推荐歌单" not in driver.find_element("tag name", "body").text:
        deadline = time.time() + 30
        while not _click_sidebar(driver, "推荐"):
            if time.time() > deadline:
                raise RuntimeError("sidebar item 推荐 not found")
            time.sleep(0.5)
        WebDriverWait(driver, 15).until(
            lambda d: "推荐歌单" in d.find_element("tag name", "body").text)
    print("OPENED_REC")
