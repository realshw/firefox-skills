# /news is a plain table (Published / Title / Author) linking to /news/<slug>/, where manual-intervention
# notices land and fail silently on upgrade. Item pages are div.article-content inside div.news-article —
# not an <article>; narrow to it or the nav/footer makes a body dump useless.
from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js


def news(driver, limit=8, timeout=30):
    """Print and return [{date, title, author, url}] for the newest news entries."""
    site_tab(driver, "//archlinux.org/")
    driver.get("https://archlinux.org/news/")
    wait_js(driver, '!!document.querySelector(\'a[href^="/news/"]\')', timeout)
    rows = driver.execute_script("""
    return [...document.querySelectorAll('table tbody tr')].map(r => {
      const tds = [...r.querySelectorAll('td')];
      const a = r.querySelector('a[href^="/news/"]');
      return {date: tds[0] ? tds[0].innerText.trim() : '',
              title: a ? a.innerText.trim() : '',
              url: a ? 'https://archlinux.org' + a.getAttribute('href') : '',
              author: tds[2] ? tds[2].innerText.trim() : ''};
    }).filter(r => r.url);
    """)
    for r in rows[:limit]:
        print(r['date'], "|", r['title'][:88], "|", r['author'])
    print("NEWS", len(rows))
    return rows


def read_item(driver, url_or_slug, limit=5000):
    """Open one news item (full url or bare slug) and print its article text."""
    url = url_or_slug if url_or_slug.startswith("http") else \
        "https://archlinux.org/news/" + url_or_slug.strip("/") + "/"
    site_tab(driver, "//archlinux.org/")
    driver.get(url)
    wait_js(driver,
            "!!document.querySelector('.article-content, .news-article')", 30)
    text = driver.execute_script(
        "const e = document.querySelector('.article-content') || document.querySelector('.news-article');"
        "return e ? e.innerText.trim() : ''")
    print("NEWS_ITEM:", driver.title.replace("\n", " ")[:80])
    print(text[:limit] or "NO_ARTICLE")
    return text
