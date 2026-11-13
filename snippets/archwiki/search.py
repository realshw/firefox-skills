# index.php?search=<q>&fulltext=1 — fulltext=1 is not optional or you get the "go to title" page. Pair
# .mw-search-result-heading with the .searchresult div by index. The top hit is often a #REDIRECT stub and
# matching is loose — don't dedupe, the redirect is frequently the canonical name.
from urllib.parse import quote
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())


def archwiki_search(driver, query, limit=10, timeout=30):
    """Print and return [{title, url, snippet}] for an ArchWiki full-text search."""
    site_tab(driver, "//wiki.archlinux.org/")
    driver.get("https://wiki.archlinux.org/index.php?search=" + quote(query) +
               "&fulltext=1")
    wait_js(driver, "!!document.querySelector('.mw-search-result-heading')",
            timeout)
    rows = driver.execute_script("""
    const heads = [...document.querySelectorAll('.mw-search-result-heading')];
    const snips = [...document.querySelectorAll('.searchresult')];
    return heads.map((h, i) => {
      const a = h.querySelector('a');
      return {title: h.innerText.trim(),
              url: a ? 'https://wiki.archlinux.org' + a.getAttribute('href') : '',
              snippet: snips[i] ? snips[i].innerText.trim().slice(0, 200) : ''};
    });
    """)
    for r in rows[:limit]:
        print("-", r['title'], "|", r['snippet'][:110].replace("\n", " "), "|",
              r['url'])
    print("RESULTS", len(rows))
    return rows
