# Every snippet that loads a page calls site_tab(driver, "<site>") before its driver.get(), so the page the
# user is reading keeps its url: the tab already on that site is reused (a second call in the same snippet
# costs nothing), anything else gets a tab of its own. `site` is a fragment of the url, as the guards want
# it — "github.com" takes any github tab, "//archlinux.org/" leaves wiki.archlinux.org alone.
from selenium.common.exceptions import NoSuchWindowException, WebDriverException


def site_tab(driver, site):
    """Leave the session on a tab already on `site`, and open a tab when the current one is elsewhere."""
    try:
        here = driver.current_url or ""
    except WebDriverException:
        here = ""  # a privileged tab (about:newtab) refuses the question, and is not ours to navigate
    if site in here:
        return
    try:
        driver.switch_to.new_window("tab")
    except NoSuchWindowException:
        print("TAB: the session lost its window - ask the user to open a Firefox "
              "window, then driver = reattach()")
        raise
