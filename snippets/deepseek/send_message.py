# Click the composer's send button (the first enabled one) — no wait, no confirmation. Returns the send
# time so read_reply(since=...) can tell the new answer from the previous one during the submit spinner.
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def send_message(driver):
    btns = []
    for b in driver.find_elements("css selector",
                                  "div.ds-button--circle, button"):
        try:
            cls = b.get_attribute("class") or ""
            if b.is_displayed() and "disabled" not in cls:
                btns.append(b)
        except Exception:
            pass
    if btns:
        btns[-1].click()
        print("SENT_BUTTON")
    else:
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        print("SENT_ENTER")
    return time.time()
