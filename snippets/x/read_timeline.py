# Reads the home timeline (For You), first 30 posts, printed. For the
# Following feed use https://x.com/home?filter=following.
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/x/extract_tweets.py").read())


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
