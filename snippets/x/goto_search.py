# f=live is the "Latest" tab; operators go straight into q — quote() the whole query once, never
# hand-build the url. Queries can legitimately have no hits, so return 0 rather than spinning out the
# timeout. Past a few dozen navigations X serves a rate-limit wall and tweets: 0 — back off, don't read
# that as "no hits".
from urllib.parse import quote

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())


def x_goto_search(driver, query, latest=True, timeout=25):
    """Navigate the x.com tab to the search results; return the number of tweets mounted."""
    site_tab(driver, "//x.com/")
    driver.get("https://x.com/search?q=" + quote(query) +
               ("&f=live" if latest else ""))
    wait_js(driver,
            'document.querySelectorAll(\'article[data-testid="tweet"]\')'
            '.length || /No results|没有结果/.test(document.body.innerText)',
            timeout,
            tick=1.0)
    n = driver.execute_script(
        'return document.querySelectorAll(\'article[data-testid="tweet"]\').length'
    )
    print("SEARCH:", driver.title, "| tweets:", n)
    return n
