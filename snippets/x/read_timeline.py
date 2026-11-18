"""Print the first 30 posts of the x.com home timeline."""

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/x/extract_tweets.py").read())


def x_read_timeline(driver):
    """Print the first 30 posts of the For You feed (the Following feed is /home?filter=following)."""
    site_tab(driver, "//x.com/")
    driver.get("https://x.com/home")
    wait_js(driver, 'document.querySelectorAll(\'article[data-testid="tweet"]\').length', 25)
    rows = x_collect_tweets(driver, n=30)
    print("TIMELINE:", driver.title, "| collected:", len(rows))
    x_print_tweets(rows, n=30)
