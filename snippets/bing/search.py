# Bing's two editions share one endpoint: cn.bing.com serves 国内版 by default and 国际版 once the ENSEARCH
# cookie is BENVER=1. The &ensearch=0/1 param is what writes that cookie, so it goes on every request — a
# bare url keeps whichever edition the jar already holds — and #est_switch says which one won: est_cn/est_en,
# the live one carrying est_selected. When that disagrees, write the cookie and load once more.
# www.bing.com answers with an empty shell from this machine (no #b_results at all), so 国际版 is
# cn.bing.com + ensearch=1, not www.
# Results are #b_results > li.b_algo: h2 > a is the target, div.b_caption p the snippet and its leading
# "date ·" segment is a date rather than text, .tptt the site name, cite the display url. Paging is
# &first=11, 21, … and nothing else, and a jar that has been through Bing's rdr=1 redirect flow answers
# every first= with page 1 again — so read the .sb_pagS marker and report it rather than trusting first=.
import time
from urllib.parse import quote_plus

from snippets.common.wait_stable import wait_js_stable

BASE = "https://cn.bing.com/search?q="
EDITIONS = {"cn": 0, "int": 1}

_COUNT_JS = "document.querySelectorAll('#b_results > li.b_algo').length"

# est_cn/est_en carry est_selected on the edition that is live; empty when the SERP has no switch (bot page).
_EDITION_JS = (
    "(function(){const c=document.querySelector('#est_cn'),e=document.querySelector('#est_en');"
    "if(!c||!e||!document.querySelector('#b_results'))return '';"
    "return /est_selected/.test(e.className)?'int':"
    "/est_selected/.test(c.className)?'cn':'';})()")

_PAGE_JS = "(document.querySelector('.sb_pagS')||{}).textContent || ''"

EXTRACT_JS = r"""
const clean = s => (s || '').replace(/\s+/g, ' ').trim();
const DATE = new RegExp('^(?:\\d+\\s+(?:min|hour|day|week|month|year)s?\\s+ago'
  + '|[A-Z][a-z]{2}\\s+\\d{1,2},\\s+\\d{4}|\\d{4}年\\d{1,2}月\\d{1,2}日'
  + '|\\d{1,2}\\s*(?:分钟|小时|天|周|个月|年)前)$');
const out = [];
document.querySelectorAll('#b_results > li.b_algo').forEach(li => {
  const title = li.querySelector('h2 a');
  const body = li.querySelector('.b_caption p, p.b_lineclamp2, .b_algoSlug, .b_snippet');
  const site = li.querySelector('.tptt');
  const cite = li.querySelector('cite');
  let snippet = clean(body && body.textContent);
  let date = '';
  const cut = snippet.indexOf(' · ');
  if (cut > 0 && DATE.test(snippet.slice(0, cut))) {
    date = snippet.slice(0, cut);
    snippet = snippet.slice(cut + 3).trim();
  }
  out.push({title: clean(title && title.textContent), snippet: snippet, date: date,
            site: clean(site && site.textContent), cite: clean(cite && cite.textContent),
            url: title ? title.href : null});
});
return out;
"""


def _url(query, edition, page):
    # The param on every request, not only for 国际版: a bare url leaves whatever the cookie already says,
    # so asking for 国内版 after a 国际版 call would come back 国际版 again.
    url = BASE + quote_plus(query) + "&ensearch=%d" % EDITIONS[edition]
    if page > 1:
        url += "&first=%d" % ((page - 1) * 10 + 1)
    return url


def _set_edition(driver, edition):
    """Pin the edition with the cookie the toggle itself writes; the page must already be on bing.com."""
    driver.add_cookie({
        "name": "ENSEARCH",
        "value": "BENVER=%d" % EDITIONS[edition],
        "domain": ".bing.com",
        "path": "/"
    })


def goto_search(driver, query, edition="cn", page=1, timeout=20):
    """Load one results page in the requested edition, and say which edition and page Bing actually served."""
    if edition not in EDITIONS:
        raise ValueError("edition is 'cn' or 'int', not %r" % (edition, ))
    if "bing.com" not in (driver.current_url or ""):
        driver.switch_to.new_window("tab")
    driver.get(_url(query, edition, page))
    # Cards mount in batches and page 2 holds fewer of them, so trust the count only once it stops moving.
    wait_js_stable(driver, _COUNT_JS, timeout, tick=0.5, stable_ticks=2)
    served = driver.execute_script("return %s;" % _EDITION_JS)
    if served and served != edition:
        print("EDITION: asked for %s, page says %s - re-pinning the cookie" %
              (edition, served))
        _set_edition(driver, edition)
        driver.get(_url(query, edition, page))
        wait_js_stable(driver, _COUNT_JS, timeout, tick=0.5, stable_ticks=2)
        served = driver.execute_script("return %s;" % _EDITION_JS) or served
    mark = driver.execute_script("return %s;" % _PAGE_JS) or "?"
    print("SEARCH: %s | edition=%s | page=%s of %d results" %
          (driver.title, served
           or "?", mark, driver.execute_script("return %s;" % _COUNT_JS)))
    return mark


def read_results(driver):
    """The organic cards on the current SERP as [{title, snippet, date, site, cite, url}]."""
    rows = driver.execute_script(EXTRACT_JS) or []
    return [
        r for r in rows if r["title"] and (r["url"] or "").startswith("http")
    ]


def search(driver, query, edition="cn", pages=1, tries=3):
    """Run query on 国内版 ("cn") or 国际版 ("int"), return the rows of pages 1..pages, deduped by url."""
    rows = []
    for attempt in range(tries):
        mark = goto_search(driver, query, edition)
        rows = read_results(driver)
        if not rows:
            print("NO RESULTS attempt %d (url=%s)" %
                  (attempt + 1, driver.current_url))
            time.sleep(3)
            continue
        last = pages
        if pages > 1 and mark not in ("", "?", "1"):
            # Paging is only worth walking while the marker moves: a page-1 answer to a bare request
            # means every first= will hand the same page back.
            print("PAGE: bing served page %s for page 1 - paging skipped" %
                  mark)
            last = 1
        for page in range(2, last + 1):
            served = goto_search(driver, query, edition, page)
            if served != str(page) and served != "?":
                print(
                    "PAGE: asked for page %d, bing served page %s - stopping" %
                    (page, served))
                break
            more = read_results(driver)
            if not more:
                print("PAGE: page %d came back empty" % page)
                break
            rows.extend(more)
        seen, out = set(), []
        for r in rows:
            if r["url"] not in seen:
                seen.add(r["url"])
                out.append(r)
        return out
    return rows


def print_results(rows, n=10):
    """Print title / date / site / snippet / url for the first n rows."""
    for i, r in enumerate(rows[:n], 1):
        print("%d. %s" % (i, r["title"]))
        meta = " / ".join(x for x in (r["date"], r["site"]) if x)
        if meta:
            print("   [%s]" % meta)
        if r["snippet"]:
            print("   %s" % r["snippet"])
        if r["url"]:
            print("   -> %s" % r["url"])
    print("SHOWN: %d of %d" % (min(n, len(rows)), len(rows)))
