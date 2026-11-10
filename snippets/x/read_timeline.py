# Reads the home timeline (For You), first 30 posts, printed. For the
# Following feed use https://x.com/home?filter=following.
from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js
from snippets.x.extract_tweets import collect_tweets, print_tweets


def read_timeline(driver):
    site_tab(driver, "//x.com/")
    driver.get("https://x.com/home")
    wait_js(
        driver,
        'document.querySelectorAll(\'article[data-testid="tweet"]\').length',
        25)
    rows = collect_tweets(driver, n=30)
    print("TIMELINE:", driver.title, "| collected:", len(rows))
    print_tweets(rows, n=30)
