# Same outline(driver) / section(driver) pair as everywhere else. Traps: the links are relative slugs shaped
# report-2026-04-2026-06/ (start + end month), and the newest quarter is often announced but unpublished.
import os
import re
import tempfile
from snippets.common.page_sections import page_text
from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js

BASE = "https://www.freebsd.org/status/"
_SLUG = re.compile(r"report-\d{4}-\d{2}-\d{4}-\d{2}")
_QUARTERS = None  # cached: open_status(driver) would otherwise reload /status/ and print the list twice


def quarters(driver, force=False):
    """Published report slugs, newest first. Drives the tab to /status/ (cached after the first call)."""
    global _QUARTERS
    if _QUARTERS is not None and not force:
        return _QUARTERS
    site_tab(driver, "freebsd.org")
    driver.get(BASE)
    wait_js(driver, "document.body.innerText.length > 1500", 30)
    hrefs = driver.execute_script(
        "return [...document.querySelectorAll('a')].map(a => a.getAttribute('href') || '')"
    )
    slugs = []
    for h in hrefs:
        m = _SLUG.search(h or '')
        if m and m.group(0) not in slugs:
            slugs.append(m.group(0))
    for s in slugs[:6]:
        print(s)
    print("REPORTS", len(slugs))
    _QUARTERS = slugs
    return slugs


def open_status(driver, report=None, timeout=30, cache=True):
    """Load one quarterly report (slug or None = newest); returns the page text."""
    slug = report or (quarters(driver) or [''])[0]
    if not slug:
        print("NO_REPORTS")
        return ''
    site_tab(driver, "freebsd.org")
    driver.get(BASE + slug + "/")
    wait_js(driver, "document.querySelectorAll('h2').length > 3", timeout)
    print("STATUS:", slug, "|", driver.title.replace("\n", " ")[:70])
    return page_text(
        driver,
        os.path.join(tempfile.gettempdir(), 'fbsd_status_' + slug +
                     '.txt') if cache else None)
