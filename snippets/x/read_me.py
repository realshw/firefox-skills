"""Print which handle the open x.com session is logged in as."""


def x_read_me(driver):
    """Print the handle from the profile tab, and what the account switcher spells out.

    get_attribute("href") returns the *resolved* url, so take the last path segment. .text may include the
    avatar's alt text — squash newlines.
    """
    try:
        handle = (driver.find_element("css selector", '[data-testid="AppTabBar_Profile_Link"]').get_attribute("href")
                  or "").rstrip("/").rsplit("/", 1)[-1]
    except Exception:
        handle = "(no profile tab - not logged in?)"
    try:
        who = driver.find_element("css selector", '[data-testid="SideNav_AccountSwitcher_Button"]').text
        who = " ".join(who.split())
    except Exception as e:
        who = "(switcher not mounted: %s)" % type(e).__name__
    print("HANDLE:", handle)
    print("ACCOUNT:", who)
