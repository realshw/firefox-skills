# The one and only connection incantation — reattach.py calls this too, so args and timeout ceilings drift
# in one place only. Precondition: Firefox up with -marionette and no stray geckodriver (reattach.py).
# Calling it again hands back the driver the session already holds, so two attaches never fight over one
# Marionette; reattach() asks for a fresh one instead, which is how a dead session gets replaced.
import __main__
import shutil

from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver

# The tab nobody is reading: what a fresh attach lands on when the previous session ended on its own.
BLANK = ("", "about:blank", "about:newtab", "about:home")


def connect(reuse=True):
    """Attach to the running Firefox and return the driver, or the one the session already holds."""
    driver = getattr(__main__, "driver", None) if reuse else None
    if isinstance(driver, WebDriver):
        print("SELENIUM: reusing the driver already attached")
    else:
        service = Service(
            executable_path=shutil.which("geckodriver"),
            service_args=["--connect-existing", "--marionette-port", "2828"])
        driver = Firefox(service=service)
        print("SELENIUM: driver attaches to Marionette")
    # Either way the session starts on a blank tab: a fresh attach may have landed on the page the user is
    # reading, and a reused driver may have been left mid-page. Whatever it was on stays open for them.
    try:
        landed_blank = (driver.current_url or "") in BLANK
    except Exception:
        landed_blank = False  # privileged pages reject the query, and are not ours to navigate
    if not landed_blank:
        try:
            driver.switch_to.new_window("tab")
        except NoSuchWindowException:
            print("TAB: the session lost its window - ask the user to open a "
                  "Firefox window, then driver = reattach()")
            raise
    # No page-load ceiling: if a single resource never loads, driver.get() and every command after it
    # get stuck. Reused drivers may carry a timeout a snippet raised, so both are set either way.
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    # about:* tabs yield no title/url, so the state line must not be able to kill the attach.
    try:
        print("TAB: %r  %s" % (driver.title, driver.current_url))
    except Exception as e:
        print("TAB: (privileged) %s" % type(e).__name__)
    return driver
