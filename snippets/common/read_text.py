# Read any page as text: navigate the site's tab — opening one when the current tab is on another site — then
# wait for readyState + a short settle (innerText is empty until layout, so the return of driver.get() proves
# nothing), and take body.innerText. Trimming is the caller's job.
import time
from urllib.parse import urlparse

from snippets.common.wait_js import wait_js


def read_text(driver, url, max_chars=7000, settle=2.0):
    """Navigate to url (in its own site's tab) and return its visible text, cut to max_chars."""
    if urlparse(url).netloc not in (driver.current_url or ""):
        driver.switch_to.new_window("tab")
    driver.get(url)
    wait_js(driver, "document.readyState === 'complete'", 20, tick=0.3)
    time.sleep(settle)
    text = driver.execute_script(
        "return document.body ? document.body.innerText : ''") or ""
    print("READ: %s | %d chars" % (url, len(text)))
    return text[:max_chars]
