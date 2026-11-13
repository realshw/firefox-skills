# Click the button whose aria-label says send/submit — no wait, no confirmation.
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def grok_send_message(driver):
    btns = []
    for b in driver.find_elements("css selector", "button"):
        try:
            al = (b.get_attribute("aria-label") or "").lower()
            if b.is_displayed() and ("send" in al or "submit" in al):
                btns.append(b)
        except Exception:
            pass
    if btns:
        btns[0].click()
        print("SENT_BUTTON")
    else:
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        print("SENT_ENTER")
