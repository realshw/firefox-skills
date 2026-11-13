# The timeline is virtualized, so x_collect_tweets(driver) reads after every scroll and dedupes on the status id.
# Engagement comes from the stats group's aria-label — the number group must start with a digit, or a
# liked row's ", Reposted" poisons the count. Quoted tweets carry a second tweetText inside the article:
# count only outside that box. /notifications has no articles; promoted rows need a handle filter.
import time

X_EXTRACT_JS = r"""
const clean = s => (s || '').replace(/\s+/g, ' ').trim();
const KEY = {reply: 'replies', replies: 'replies', repost: 'reposts', reposts: 'reposts',
             quote: 'quotes', quotes: 'quotes', like: 'likes', likes: 'likes',
             bookmark: 'bookmarks', bookmarks: 'bookmarks', view: 'views', views: 'views'};
const out = [];
document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
  const quoteBox = a.querySelector('div[role="link"]');
  const inQuote = el => !!(quoteBox && quoteBox.contains(el));
  const texts = [...a.querySelectorAll('[data-testid="tweetText"]')];
  const nameBlock = a.querySelector('[data-testid="User-Name"]');
  const handleA = nameBlock && nameBlock.querySelector('a[href^="/"]');
  const handle = handleA ? (handleA.getAttribute('href') || '').replace(/^\//, '') : '';
  let name = clean(nameBlock ? nameBlock.innerText : '');
  if (handle && name.indexOf('@') > 0) name = clean(name.slice(0, name.indexOf('@')));
  const statusA = a.querySelector('a[href*="/status/"]');
  const m = statusA ? (statusA.getAttribute('href') || '').match(/^\/([^/]+)\/status\/(\d+)/) : null;
  const timeEl = a.querySelector('time');
  const statsDiv = [...a.querySelectorAll('div[aria-label]')]
      .find(d => /(likes?|views?|reposts?)/i.test(d.getAttribute('aria-label') || ''));
  const label = statsDiv ? (statsDiv.getAttribute('aria-label') || '') : '';
  const stats = {replies: 0, reposts: 0, quotes: 0, likes: 0, bookmarks: 0, views: 0};
  if (label) {
    const re = /(\d[\d,]*)\s+(replies?|reposts?|quotes?|likes?|bookmarks?|views?)/gi;
    let mm;
    while ((mm = re.exec(label))) {
      const k = KEY[mm[2].toLowerCase()];
      if (k) stats[k] = parseInt(mm[1].replace(/,/g, ''), 10);
    }
  }
  const body = clean(a.innerText);
  out.push({
    id: m ? m[2] : null,
    handle: handle,
    name: name,
    url: m ? '/' + m[1] + '/status/' + m[2] : null,
    datetime: timeEl ? timeEl.getAttribute('datetime') : null,
    text: texts.filter(t => !inQuote(t)).map(t => clean(t.innerText)).join('\n'),
    quoted_text: texts.filter(t => inQuote(t)).map(t => clean(t.innerText)).join('\n'),
    media: [...a.querySelectorAll('[data-testid="tweetPhoto"] img')]
        .filter(img => !inQuote(img)).map(img => img.src),
    pinned: /^Pinned\b/.test(body),
    is_reply: /Replying to/.test(body),
    liked: /\bLiked\b/.test(label),
    reposted: /\bReposted\b/.test(label),
    stats: stats,
  });
});
return out;
"""


def x_read_tweets(driver, limit=100):
    """Every tweet currently mounted on the page (no scrolling) as dicts:

    {"id": "1234567890123456789", "handle": "example", "name": "Example User",
     "url": "/example/status/1234567890123456789", "datetime": "2026-01-01T00:00:00.000Z",
     "text": "...", "quoted_text": "", "media": ["https://pbs.twimg.com/media/...?name=small"],
     "pinned": False, "is_reply": False, "liked": True, "reposted": False,
     "stats": {"replies": 1, "reposts": 2, "quotes": 0, "likes": 3,
               "bookmarks": 0, "views": 0}}

    `url` is site-relative (prefix https://x.com). `stats` holds the exact aria-label numbers, not
    the rounded "1.4K" on screen; 0 means the field was missing, which on X means "none yet".
    """
    return (driver.execute_script(X_EXTRACT_JS) or [])[:limit]


def x_collect_tweets(driver, n=30, max_scrolls=20, pause=2.5):
    """Read-and-scroll until n tweets are gathered, the feed ends, or two scrolls add nothing."""
    seen, out, dry = set(), [], 0
    for _ in range(max_scrolls + 1):
        fresh = 0
        for r in x_read_tweets(driver, limit=500):
            if r["id"] and r["id"] not in seen:
                seen.add(r["id"])
                out.append(r)
                fresh += 1
        if len(out) >= n:
            break
        body = driver.execute_script("return document.body.innerText") or ""
        if "You've reached the end" in body or "到底了" in body:
            break
        dry = 0 if fresh else dry + 1
        if dry >= 2:
            break
        driver.execute_script("window.scrollBy(0, window.innerHeight * 2)")
        time.sleep(pause)
    return out[:n]


def x_print_tweets(rows, n=10, text_len=200):
    """Print author / time / text / quote / stats / link for the first n rows."""
    for r in rows[:n]:
        st = r["stats"]
        flags = ("  [pinned]" if r["pinned"] else "") + ("  [liked]" if r["liked"] else "") + \
                ("  [reposted]" if r["reposted"] else "")
        print("%s @%s  %s%s" % (r["name"], r["handle"], r["datetime"] or "", flags))
        text = (r["text"] or "").replace("\n", " ")
        if not text:
            text = "(no text: %d photo(s))" % len(r["media"]) if r["media"] else "(no text)"
        print("  " + text[:text_len])
        if r["quoted_text"]:
            print("  quote: " + r["quoted_text"][:120].replace("\n", " "))
        print("  replies %d  reposts %d  quotes %d  likes %d  bookmarks %d  views %d" %
              (st["replies"], st["reposts"], st["quotes"], st["likes"], st["bookmarks"], st["views"]))
        if r["url"]:
            print("  https://x.com" + r["url"])
    print("SHOWN: %d of %d" % (min(n, len(rows)), len(rows)))
