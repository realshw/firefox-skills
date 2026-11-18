"""Send what is typed in the DeepSeek composer."""

import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def deepseek_send_message(driver):
    """Click the composer's send button (the last enabled one) — no wait, no confirmation.

    Returns time.time() of the send, the `since` deepseek_read_reply wants so it can tell the new answer from
    the previous one during the submit spinner. Falls back to Enter when no button is enabled.
    """
    btns = []
    for b in driver.find_elements("css selector", "div.ds-button--circle, button"):
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
