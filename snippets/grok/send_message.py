"""Send what is typed in the Grok composer."""

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def grok_send_message(driver):
    """Click the button whose aria-label says send/submit — no wait, no confirmation.

    Enter is the fallback when no such button is on the page.
    """
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
