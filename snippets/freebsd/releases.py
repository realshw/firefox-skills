# The page states its own tiers ("Production Release: 15.1", …) then lists every release with a date —
# parse those two shapes, not the markup. Url trap the folder depends on: /releases/15.1R/relnotes/ works,
# /releases/15.1.0/relnotes/ is a 404.
import re

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

FREEBSD_RELEASES_URL = "https://www.freebsd.org/releases/"
_FREEBSD_TIER = re.compile(r"(Production|Legacy|Upcoming) Release:\s*([\d.]+)")
_FREEBSD_DATED = re.compile(r"Release (\d+\.\d+) \(([^)]+)\)")


def freebsd_open_releases(driver, timeout=30):
    """Load the releases page and wait for the tier summary to render."""
    site_tab(driver, "freebsd.org")
    driver.get(FREEBSD_RELEASES_URL)
    wait_js(
        driver,
        "!!document.body.innerText.match(/Production Release:\\s*[\\d.]+/)",
        timeout)
    t = driver.execute_script("return document.body.innerText")
    print("RELEASES:",
          re.search(r"Production Release:\s*([\d.]+)", t).group(1),
          "is the production release")
    return t


def freebsd_list_releases(driver):
    """{production: [...], legacy: [...], upcoming: [...], dated: [(version, date)]}"""
    t = driver.execute_script("return document.body.innerText")
    out = {'production': [], 'legacy': [], 'upcoming': []}
    for tier, ver in _FREEBSD_TIER.findall(t):
        out[tier.lower()].append(ver)
    out['dated'] = _FREEBSD_DATED.findall(t)
    for k in ('production', 'legacy', 'upcoming'):
        print("%-11s %s" % (k + ":", " ".join(out[k]) or "-"))
    for ver, date in out['dated'][:6]:
        print("  %-6s %s" % (ver, date))
    return out


def freebsd_read_latest_release(driver):
    """The current production version, as a string ('15.1')."""
    t = freebsd_open_releases(driver)
    return re.search(r"Production Release:\s*([\d.]+)", t).group(1)
