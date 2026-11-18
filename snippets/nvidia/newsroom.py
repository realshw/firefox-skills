"""Read NVIDIA's press-release newsroom — the index pages and a single release."""

import re

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/goto.py").read())
exec(open("snippets/common/wait_stable.py").read())

NVIDIA_NEWSROOM = "https://nvidianews.nvidia.com/news"

_NVIDIA_COUNT_JS = "document.querySelectorAll('.index-item').length"

# Each card is article.index-item: .index-item-text-info-date holds the date, h3 a the title, and the
# .index-item-text-description the summary — the card holds no <p>. 10 cards per index page.
NVIDIA_INDEX_JS = r"""
const clean = s => (s || '').replace(/\s+/g, ' ').trim();
const out = [];
document.querySelectorAll('.index-item').forEach(li => {
  const a = li.querySelector('.index-item-text-title a') || li.querySelector('a[href*="/news/"]');
  const date = li.querySelector('.index-item-text-info-date');
  const body = li.querySelector('.index-item-text-description');
  out.push({date: clean(date && date.textContent), title: clean(a && a.textContent),
            summary: clean(body && body.textContent), url: a ? a.href : null});
});
return out;
"""


def nvidia_list_releases(driver, pages=1, timeout=20):
    """The newsroom index as [{date, title, summary, url}], pages 1..pages, newest first.

    Paging is ?page=N on /news and each page holds 10 cards, so the walk stops as soon as a page's first
    url repeats the previous page's — the newsroom answers a page past its end with the last page again.
    The date is the card's own "November 17, 2026" string, not a "days ago" relative.
    """
    site_tab(driver, "nvidianews.nvidia.com")
    rows, seen = [], set()
    for page in range(1, pages + 1):
        url = NVIDIA_NEWSROOM if page == 1 else NVIDIA_NEWSROOM + "?page=%d" % page
        goto(driver, url, timeout)
        wait_js_stable(driver, _NVIDIA_COUNT_JS, timeout, tick=0.5, stable_ticks=2)
        more = driver.execute_script(NVIDIA_INDEX_JS) or []
        more = [r for r in more if r["title"] and (r["url"] or "").startswith("http")]
        if not more:
            print("PAGE: index page %d came back empty - stopping" % page)
            break
        if rows and more[0]["url"] == rows[0]["url"]:
            print("PAGE: index page %d repeated page 1 - stopping" % page)
            break
        for r in more:
            if r["url"] not in seen:
                seen.add(r["url"])
                rows.append(r)
    print("NEWSROOM: %d releases over %d index page(s)" % (len(rows), min(pages, max(1, page))))
    return rows


def nvidia_find_releases(driver, pattern, pages=5, flags=re.I):
    """Releases whose title or summary matches `pattern` (a regex), searched over the newest `pages` pages.

    An empty list means the index says nothing about it — read the release itself before concluding that
    a topic was never announced, because a summary can omit what the document states.
    """
    rx = re.compile(pattern, flags)
    hits = [r for r in nvidia_list_releases(driver, pages) if rx.search(r["title"] + " " + r["summary"])]
    print("MATCH: %d release(s) for %r over %d page(s)" % (len(hits), pattern, pages))
    return hits


def nvidia_read_release(driver, url, timeout=20):
    """A press release as {title, date, text}: the page's own headline, dateline and body text.

    The body is innerText of the document, not a single container — the newsroom nests the release in
    wrappers that change per layout, and the template's nav/footer sit around it. Use the returned text
    for regex reading ("said … Interim CEO"), since quotes carry the title someone is actually serving.
    """
    site_tab(driver, "nvidianews.nvidia.com")
    goto(driver, url, timeout)
    text = driver.execute_script("return document.body.innerText") or ""
    date = driver.execute_script("const e=document.querySelector('.article-date, .release-date, time');"
                                 "return e ? e.textContent.replace(/\\s+/g,' ').trim() : '';")
    title = driver.execute_script(
        "const h=document.querySelector('h1');return h ? h.textContent.replace(/\\s+/g,' ').trim() : '';")
    if not date:
        m = re.search(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|"
            r"December)\s+\d{1,2},\s+\d{4}\b", text)
        date = m.group(0) if m else ""
    print("RELEASE: %s | %s" % (title or driver.title, date or "no date found"))
    return {"title": title, "date": date, "text": text}


def nvidia_print_releases(rows, n=10):
    """Print date / title / summary / url for the first n rows, newest first as the newsroom lists them."""
    for i, r in enumerate(rows[:n], 1):
        print("%d. %s — %s" % (i, r["date"], r["title"]))
        if r["summary"]:
            print("   %s" % r["summary"][:220])
        if r["url"]:
            print("   -> %s" % r["url"])
    print("SHOWN: %d of %d" % (min(n, len(rows)), len(rows)))
