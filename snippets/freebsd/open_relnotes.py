# One giant page with a TOC that repeats every heading — read it with common/page_sections.py (outline(driver)
# then section(driver)), never a text search. The url keeps its "R" (/releases/15.1R/relnotes/, 15.1.0 is a
# 404) and relnotes get edited after release, so check the last-modified date.
import os
import tempfile
exec(open("snippets/common/page_sections.py").read())
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())


def freebsd_open_relnotes(driver, version='15.1', timeout=30, cache=True):
    """Load one release's notes; returns the page text (cached to <tempdir>/relnotes_<v>.txt)."""
    v = version.strip().rstrip("Rr")
    url = "https://www.freebsd.org/releases/" + v + "R/relnotes/"
    site_tab(driver, "freebsd.org")
    driver.get(url)
    wait_js(driver, "document.querySelectorAll('h2').length > 3", timeout)
    if driver.execute_script("return document.title").startswith("404"):
        print("NO_RELNOTES:", v,
              "— check the version; the url needs the R suffix")
        return ''
    print("RELNOTES:", v, "|", driver.title.replace("\n", " ")[:70])
    return page_text(
        driver,
        os.path.join(tempfile.gettempdir(), 'relnotes_' + v +
                     '.txt') if cache else None)
