"""Search a game's Steam Workshop and read the item cards and one item's stats."""

from urllib.parse import quote_plus

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/goto.py").read())
exec(open("snippets/common/wait_js.py").read())

STEAM_WORKSHOP_BROWSE = "https://steamcommunity.com/workshop/browse/"
STEAM_APPID_GARRYSMOD = 4000

# Steam rewrote the browse page with hashed class names (SxMdVrGe9aY-, tK5agp5sRy8-, …), so the card is found
# by its link and its title read off the cover image's alt — .workshopItemTitle is gone and returns 0 matches.
_STEAM_CARD_JS = r"""
const clean = s => (s || '').replace(/\s+/g, ' ').trim();
const cards = new Map();
document.querySelectorAll('a[href*="sharedfiles/filedetails/?id="]').forEach(a => {
  const card = a.closest('[class*="Panel"]') && a.parentElement.parentElement;
  if (!card || cards.has(a.href)) return;
  const img = a.querySelector('img');
  // innerText must be split before clean(): collapsing whitespace first glues title and author into one line.
  const txt = card.innerText.split('\n').map(clean).filter(Boolean);
  cards.set(a.href, {title: clean(img && img.alt) || txt[0] || '', url: a.href,
                     author: (txt.find(t => t.startsWith('By ')) || '').slice(3),
                     thumb: img ? img.src : null});
});
return [...cards.values()].filter(c => c.title);
"""

_STEAM_CARD_READY_JS = "document.querySelectorAll('a[href*=\"sharedfiles/filedetails/?id=\"]').length > 0"

_STEAM_TOTAL_JS = r"""
const m = document.body.innerText.match(/([\d,]+)\s+entr(?:y|ies)\s+matching/);
return m ? m[1] : '';
"""

_STEAM_DETAIL_JS = r"""
const clean = s => (s || '').replace(/[\u00a0\s]+/g, ' ').trim();
// The right-hand stat table flattens into innerText as labels-then-values: "Content Type:\u00a0Addon" keeps its
// value on the same line, while "File Size / Posted / Updated" sit on three lines above their three values.
// So the sizes are read as one fixed group, never by asking each label for the next line.
const txt = document.body.innerText.replace(/\u00a0/g, ' ');
const one = re => { const m = txt.match(re); return m ? clean(m[1]) : ''; };
const sizes = txt.match(/File Size\nPosted\nUpdated\n([^\n]+)\n([^\n]+)\n([^\n]+)/);
return {
  title: clean((document.querySelector('.workshopItemTitle') || {}).innerText || document.title),
  content_type: one(/Content Type:\s*([^\n]+)/),
  addon_type: one(/Addon Type:\s*([^\n]+)/),
  tags: one(/Addon Tags:\s*([^\n]+)/),
  size: sizes ? clean(sizes[1]) : '', posted: sizes ? clean(sizes[2]) : '',
  updated: sizes ? clean(sizes[3]) : '',
  ratings: one(/([\d,]+) ratings/),
  visitors: one(/([\d,]+)\s+Unique Visitors/), subscribers: one(/([\d,]+)\s+Current Subscribers/),
  favorites: one(/([\d,]+)\s+Current Favorites/), collections: one(/See all ([\d,]+) collections/),
  // friendBlockContent carries the online status under the name, so the name is the first raw line, not a cleaned one.
  author: (((document.querySelector('.friendBlockContent') || {}).innerText || '').split('\n')[0] || '').trim(),
  url: location.href
};
"""


def steam_workshop_url(appid, query, page=1, sort="textsearch", section="readytouseitems"):
    """Build a browse url: appid, query text, page (1-based) and the sort/section Steam itself uses."""
    url = (STEAM_WORKSHOP_BROWSE + "?appid=%d&searchtext=%s&browsesort=%s&section=%s" %
           (appid, quote_plus(query), sort, section))
    if page > 1:
        url += "&p=%d" % page
    return url


def steam_goto_workshop(driver, appid, query, page=1, sort="textsearch", section="readytouseitems", timeout=30):
    """Load one Workshop browse page and wait for the item cards; returns the "N entries matching" count.

    The cards mount after the shell, so the poll is on the image-based card JS rather than on body text —
    reading straight after goto() hands back 0 cards on an otherwise loaded page.
    """
    site_tab(driver, "steamcommunity.com")
    url = steam_workshop_url(appid, query, page, sort, section)
    goto(driver, url, timeout)
    if not wait_js(driver, _STEAM_CARD_READY_JS, timeout):
        print("WORKSHOP: no cards on %s" % url)
    total = driver.execute_script("return (function(){%s})();" % _STEAM_TOTAL_JS) or "?"
    print("WORKSHOP: %s | %s | entries matching %s | %s" % (driver.title, query, total, driver.current_url))
    return total


def steam_read_workshop_items(driver):
    """The cards on the current browse page as [{title, url, author, extra, thumb}].

    Cards are found by their filedetails link because every layout class is a hash; the title is the cover
    image's alt, which survives a layout rename better than any heading selector.
    """
    return driver.execute_script("return (function(){%s})();" % _STEAM_CARD_JS) or []


def steam_read_item(driver, url=None, timeout=30):
    """Load one item page (or read the one already open) and return its stats dict, or None if it has no title.

    The stat block is scraped out of innerText keyed by Steam's own labels ("Current Subscribers" and
    friends): the markup has no stable ids, and the numbers carry thousands separators as text.
    """
    if url:
        site_tab(driver, "steamcommunity.com")
        goto(driver, url, timeout)
        wait_js(
            driver, "(document.querySelector('.workshopItemTitle')||{}).innerText && "
            "document.body.innerText.indexOf('Subscribers') > 0", timeout)
    info = driver.execute_script("return (function(){%s})();" % _STEAM_DETAIL_JS)
    if not info or not info.get("title"):
        print("ITEM: no title on %s" % driver.current_url)
        return None
    return info


def steam_read_description(driver, url=None, timeout=30):
    """The item's DESCRIPTION block as text, blank when the page has none.

    Read from .workshopItemDescription rather than innerText: the page keeps the author's own line breaks, and
    the surrounding chrome (comments, required items) would otherwise swamp the description.
    """
    if url:
        site_tab(driver, "steamcommunity.com")
        goto(driver, url, timeout)
    return driver.execute_script("return (function(){const e=document.querySelector('.workshopItemDescription');"
                                 "return e ? e.innerText : '';})()") or ""


def steam_print_items(rows, n=20):
    """Print title / author / url for the first n cards."""
    for i, r in enumerate(rows[:n], 1):
        print("%d. %s  [by %s]  %s" % (i, r["title"], r["author"], r["url"]))
    print("SHOWN: %d of %d" % (min(n, len(rows)), len(rows)))
