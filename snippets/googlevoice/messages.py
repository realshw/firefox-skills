"""Read and send Google Voice SMS threads, one numbered account tab at a time."""

import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

GOOGLE_VOICE_BASE = "https://voice.google.com"

MESSAGES_URL = GOOGLE_VOICE_BASE + "/u/%d/messages"

THREAD_ITEM = "gv-thread-list-item"

MESSAGE_ITEM = "gv-message-item"

RECIPIENT_INPUT = "input[placeholder='Type a name or phone number']"

MESSAGE_INPUT = "textarea.message-input"

SEND_BUTTON = "button.send-button"

COMPOSE_PANEL_X_LIMIT = 1000


def voice_account_tab(driver, account):
    """Switches to the Voice tab for /u/<account> and returns its handle.

    Each signed-in Voice account lives in its own tab; the account index is the
    only thing that tells two Messages tabs apart, so never match on title.
    """
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "/u/%d/" % account in driver.current_url:
            return handle
    raise RuntimeError("no Google Voice tab for account /u/%d" % account)


def voice_read_thread(driver, account, name=None):
    """Returns [(direction, text)] for the open thread, oldest first.

    Opens the thread named `name` from the message list when given; direction is
    'incoming' or 'outgoing' as set by Voice's own bubble classes, which live on
    the inner .full-container, not on gv-message-item itself.
    """
    voice_account_tab(driver, account)
    if name is not None:
        _open_thread(driver, name)
    WebDriverWait(driver, 20).until(lambda d: d.find_elements(By.CSS_SELECTOR, MESSAGE_ITEM))
    out = []
    for item in driver.find_elements(By.CSS_SELECTOR, MESSAGE_ITEM):
        inner = item.find_element(By.CSS_SELECTOR, ".full-container")
        direction = "outgoing" if "outgoing" in (inner.get_attribute("class") or "") else "incoming"
        text = driver.execute_script("return (arguments[0].querySelector('.content') || arguments[0]).innerText;", item)
        out.append((direction, text.strip()))
    return out


def voice_send_message(driver, account, text, name=None, number=None, dry_run=False):
    """Sends `text` and returns the thread URL once the bubble shows it.

    Types into the open thread when `name` or `number` are omitted; otherwise
    opens that conversation first. Refuses to guess a recipient: starting a new
    thread needs `number`, because clicking a suggestion row by accident dials a
    call instead of adding the recipient.
    """
    voice_account_tab(driver, account)
    if name is not None:
        _open_thread(driver, name)
    elif number is not None:
        _compose_to(driver, number)
    WebDriverWait(driver, 20).until(lambda d: d.find_element(By.CSS_SELECTOR, MESSAGE_INPUT))
    if dry_run:
        return "dry-run: would send %r" % text
    box = driver.find_element(By.CSS_SELECTOR, MESSAGE_INPUT)
    box.click()
    box.send_keys(text)
    driver.find_element(By.CSS_SELECTOR, SEND_BUTTON).click()
    WebDriverWait(
        driver,
        30).until(lambda d: text in d.execute_script("var e=document.querySelectorAll('%s');"
                                                     "return e.length ? e[e.length-1].innerText : '';" % MESSAGE_ITEM))
    time.sleep(1.5)
    return driver.current_url


def _open_thread(driver, name):
    item = WebDriverWait(driver, 20).until(lambda d: next(
        (e for e in d.find_elements(By.CSS_SELECTOR, THREAD_ITEM) if name.split()[0] in e.text), None))
    item.click()
    WebDriverWait(driver, 20).until(lambda d: "itemId=t." in d.current_url)


def _compose_to(driver, number):
    if "itemId=draft" not in driver.current_url:
        for b in driver.find_elements(By.TAG_NAME, "button"):
            if "Send new message" in (b.text or ""):
                b.click()
                break
        WebDriverWait(driver, 20).until(lambda d: d.find_elements(By.CSS_SELECTOR, RECIPIENT_INPUT))
    box = driver.find_element(By.CSS_SELECTOR, RECIPIENT_INPUT)
    box.click()
    box.send_keys(number)
    # Two contact lists can be on screen: the compose dropdown sits left of the
    # call keypad's, and the keypad rows dial when clicked.
    item = WebDriverWait(driver, 20).until(lambda d: next(
        (e for e in d.find_elements(By.CSS_SELECTOR, "gv-contact-item") if e.rect["x"] < COMPOSE_PANEL_X_LIMIT), None))
    ActionChains(driver).move_to_element_with_offset(item, -120, 0).click().perform()
    WebDriverWait(driver, 20).until(lambda d: "recipient added" in d.find_element(By.TAG_NAME, "body").text)
