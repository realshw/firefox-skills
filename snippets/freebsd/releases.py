# The page states its own tiers ("Production Release: 15.1", …) then lists every release with a date —
# parse those two shapes, not the markup. Url trap the folder depends on: /releases/15.1R/relnotes/ works,
# /releases/15.1.0/relnotes/ is a 404.
import re

from snippets.common.wait_js import wait_js

PAGE = "https://www.freebsd.org/releases/"
_TIER = re.compile(r"(Production|Legacy|Upcoming) Release:\s*([\d.]+)")
_DATED = re.compile(r"Release (\d+\.\d+) \(([^)]+)\)")


def open_releases(driver, timeout=30):
    """Load the releases page and wait for the tier summary to render."""
    if "freebsd.org" not in (driver.current_url or ""):
        driver.switch_to.new_window("tab")
    driver.get(PAGE)
    wait_js(
        driver,
        "!!document.body.innerText.match(/Production Release:\\s*[\\d.]+/)",
        timeout)
    t = driver.execute_script("return document.body.innerText")
    print("RELEASES:",
          re.search(r"Production Release:\s*([\d.]+)", t).group(1),
          "is the production release")
    return t


def releases(driver):
    """{production: [...], legacy: [...], upcoming: [...], dated: [(version, date)]}"""
    t = driver.execute_script("return document.body.innerText")
    out = {'production': [], 'legacy': [], 'upcoming': []}
    for tier, ver in _TIER.findall(t):
        out[tier.lower()].append(ver)
    out['dated'] = _DATED.findall(t)
    for k in ('production', 'legacy', 'upcoming'):
        print("%-11s %s" % (k + ":", " ".join(out[k]) or "-"))
    for ver, date in out['dated'][:6]:
        print("  %-6s %s" % (ver, date))
    return out


def latest(driver):
    """The current production version, as a string ('15.1')."""
    t = open_releases(driver)
    return re.search(r"Production Release:\s*([\d.]+)", t).group(1)
