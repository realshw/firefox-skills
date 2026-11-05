# The one and only connection incantation — reattach.py calls this too, so args and timeout ceilings drift
# in one place only. Precondition: Firefox up with -marionette and no stray geckodriver (reattach.py).
import shutil

from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service

# The tab nobody is reading: what a fresh attach lands on when the previous session ended on its own.
BLANK = ("", "about:blank", "about:newtab", "about:home")


def connect():
    """Attach to the running Firefox and return the driver. Every attach is a fresh session."""
    service = Service(
        executable_path=shutil.which("geckodriver"),
        service_args=["--connect-existing", "--marionette-port", "2828"])
    driver = Firefox(service=service)
    # No page-load ceiling: if a single resource never loads, driver.get() and every command after it
    # get stuck; every attach is a fresh session, so set it again here.
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    print("SELENIUM: driver connects to Marionette")
    # Fresh attaches land on the tab used last — the user's page, often. Stay on it when it is blank, and
    # open one otherwise: from here on the session drives the tab it is on, and no snippet switches away.
    try:
        landed_blank = (driver.current_url or "") in BLANK
    except Exception:
        landed_blank = False  # privileged pages reject the query, and are not ours to navigate
    if not landed_blank:
        try:
            driver.switch_to.new_window("tab")
        except NoSuchWindowException:
            print(
                "TAB: no window to open a tab in - open one, then driver = reattach()"
            )
            raise
    # about:* tabs yield no title/url, so the state line must not be able to kill the attach.
    try:
        print("TAB: %r  %s" % (driver.title, driver.current_url))
    except Exception as e:
        print("TAB: (privileged) %s" % type(e).__name__)
    return driver
