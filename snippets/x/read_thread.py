"""Print the thread under the /status/ page that is open."""

exec(open("snippets/x/extract_tweets.py").read())


def x_read_thread(driver):
    """Print the focal tweet and then every reply, in order, with its stats.

    The focal tweet is the *first* article, everything after it is a reply. Replies lazy-load, so a long
    chain needs a bigger max_scrolls than the 6 here.
    """
    rows = x_collect_tweets(driver, n=200, max_scrolls=6)
    if not rows:
        print("NO_THREAD: not on a /status/ page? url =", driver.current_url)
    else:
        focal, replies = rows[0], rows[1:]
        print("FOCAL:", "%s @%s" % (focal["name"], focal["handle"]))
        print("  " + (focal["text"] or "(no text)")[:400].replace("\n", " "))
        print("  https://x.com" + (focal["url"] or ""))
        print("  replies %d  reposts %d  likes %d  views %d" %
              (focal["stats"]["replies"], focal["stats"]["reposts"], focal["stats"]["likes"], focal["stats"]["views"]))
        print("REPLIES: %d" % len(replies))
        for i, r in enumerate(replies, 1):
            print("%d. %s @%s  ♥%d" % (i, r["name"], r["handle"], r["stats"]["likes"]))
            print("   " + (r["text"] or "(no text)")[:200].replace("\n", " "))
