# The one and only connection incantation — reattach.py calls this too, so args and timeout ceilings drift
# in one place only. Precondition: Firefox up with -marionette and no stray geckodriver (reattach.py).
# Calling it again hands back the driver the session already holds, so two attaches never fight over one
# Marionette; reattach() asks for a fresh one instead, which is how a dead session gets replaced.
import __main__
import shutil

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver


def connect(reuse=True, port=2828):
    """Attach to the running Firefox and return the driver, or the one the session already holds."""
    driver = getattr(__main__, "driver", None) if reuse else None
    if isinstance(driver, WebDriver):
        print("SELENIUM: reusing the driver already attached")
    else:
        service_args = ["--connect-existing", "--marionette-port", str(port)]
        service = Service(executable_path=shutil.which("geckodriver"),
                          service_args=service_args)
        driver = Firefox(service=service)
        print("SELENIUM: driver attaches to Marionette")
    # The session keeps whichever tab it landed on - a fresh attach may be on the page the user is reading,
    # and a reused driver was left wherever the last block put it. Neither opens a blank tab for nobody: a
    # snippet that loads a page asks common/site_tab.py for a tab of its own. The line below names the tab.
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
