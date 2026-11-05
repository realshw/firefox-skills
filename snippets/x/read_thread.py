# Reads the thread of the open /status/ page — the focal tweet is the *first* article, everything after
# it is a reply. Needs extract_tweets.py; replies lazy-load, so a long chain needs a bigger max_scrolls.
from snippets.x.extract_tweets import collect_tweets


def read_thread(driver):
    rows = collect_tweets(driver, n=200, max_scrolls=6)
    if not rows:
        print("NO_THREAD: not on a /status/ page? url =", driver.current_url)
    else:
        focal, replies = rows[0], rows[1:]
        print("FOCAL:", "%s @%s" % (focal["name"], focal["handle"]))
        print("  " + (focal["text"] or "(no text)")[:400].replace("\n", " "))
        print("  https://x.com" + (focal["url"] or ""))
        print("  replies %d  reposts %d  likes %d  views %d" %
              (focal["stats"]["replies"], focal["stats"]["reposts"],
               focal["stats"]["likes"], focal["stats"]["views"]))
        print("REPLIES: %d" % len(replies))
        for i, r in enumerate(replies, 1):
            print("%d. %s @%s  ♥%d" %
                  (i, r["name"], r["handle"], r["stats"]["likes"]))
            print("   " + (r["text"] or "(no text)")[:200].replace("\n", " "))
