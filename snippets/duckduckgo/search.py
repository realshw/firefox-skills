# Class names are hashed per deploy but the hooks survive: article[data-testid=result],
# a[data-testid=result-title-a] (the real target), [data-result=snippet]. ?s= is ignored and scrolling
# loads nothing — paging is the "More Results" button, so search(driver, rounds=N) clicks it. Captcha pages
# swap the cards for a bot check and have no articles at all. Searching navigates this session's own tab,
# so the page the user is reading keeps its url.
import time
from urllib.parse import quote_plus

from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js
from snippets.common.wait_stable import wait_js_stable

DDG_BASE = "https://duckduckgo.com/?q="

_DDG_COUNT_JS = "document.querySelectorAll('article[data-testid=result]').length"

DDG_EXTRACT_JS = r"""
const clean = s => (s || '').replace(/\s+/g, ' ').trim();
const DATE = /^(Today|Yesterday|\d+\s+(?:min|hour|day|week|month|year)s?\s+ago|[A-Z][a-z]{2} \d{1,2}, \d{4})$/;
const out = [];
document.querySelectorAll('article[data-testid=result]').forEach(a => {
  const title = a.querySelector('a[data-testid=result-title-a]');
  const body = a.querySelector('[data-result=snippet]');
  const site = a.querySelector('[data-testid=result-extras-url-link]');
  let snippet = clean(body && body.innerText);
  let time = '';
  if (body) {
    const d = [...body.querySelectorAll('span')].find(e => !e.children.length && DATE.test(clean(e.textContent)));
    if (d) {
      time = clean(d.textContent);
      if (snippet.startsWith(time)) snippet = snippet.slice(time.length).trim();
    }
  }
  out.push({title: clean(title && title.innerText), snippet: snippet, time: time,
            site: clean(site && site.innerText), url: title ? title.href : null});
});
return out;
"""


def ddg_goto_search(driver, query):
    """Navigate the DDG tab to the results page (opening it when the current tab is elsewhere)."""
    site_tab(driver, "duckduckgo.com")
    driver.get(DDG_BASE + quote_plus(query) + "&ia=web")
    # Cards mount in batches: trust the count only once it has stopped growing. Bot-check pages never have
    # one, so they settle nowhere and the caller's retry is what handles it.
    wait_js_stable(driver, _DDG_COUNT_JS, 10, tick=0.4, stable_ticks=2)
    print("SEARCH:", driver.title)


def _organic(rows):
    return [
        r for r in rows if r["title"] and (r["url"] or "").startswith("http")
        and "duckduckgo.com" not in r["url"]
    ]


def _grow(driver):
    """Click "More Results" and wait for the appended batch of cards."""
    before = len(
        driver.find_elements("css selector", "article[data-testid=result]"))
    if not driver.execute_script(
            "const b = [...document.querySelectorAll('button')].find(b => /more results/i.test(b.innerText));"
            "if (!b) return false;"
            "b.scrollIntoView(); b.click();"
            "return true;"):
        return False
    return wait_js(driver, "%s > %d" % (_DDG_COUNT_JS, before), 10, tick=0.4)


def ddg_search(driver, query, rounds=1, tries=3):
    """Run query, return [{title, snippet, time, site, url}] (retries on bot-check pages)."""
    rows = []
    for attempt in range(tries):
        ddg_goto_search(driver, query)
        rows = _organic(driver.execute_script(DDG_EXTRACT_JS) or [])
        if rows:
            for _ in range(max(rounds - 1, 0)):
                if not _grow(driver):
                    break
            rows = _organic(driver.execute_script(DDG_EXTRACT_JS) or [])
            return rows
        print("NO RESULTS attempt %d (url=%s)" %
              (attempt + 1, driver.current_url))
        time.sleep(3)
    return rows


def ddg_print_results(rows, n=10):
    """Print title / date / site / snippet / url for the first n rows."""
    for i, r in enumerate(rows[:n], 1):
        print("%d. %s" % (i, r["title"]))
        meta = " / ".join(x for x in (r["time"], r["site"]) if x)
        if meta:
            print("   [%s]" % meta)
        if r["snippet"]:
            print("   %s" % r["snippet"])
        if r["url"]:
            print("   -> %s" % r["url"])
    print("SHOWN: %d of %d" % (min(n, len(rows)), len(rows)))
