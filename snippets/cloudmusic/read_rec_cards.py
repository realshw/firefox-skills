# Lazily-scrolled card grid: playlists, per-genre 每日推荐 and 私人漫游 look alike and cards nest
# duplicates — collect by text, dedupe, keep only cards >150px right of the 240px sidebar. The document
# doesn't grow: scroll [class*=AppScrollContainer] by 0.8*clientHeight and restore scrollTop. The row of
# brand-new cards under the top edge is what says the grid has re-rendered.
import json

exec(open("snippets/common/wait_js.py").read())

_CLOUDMUSIC_FIRST_CARD_JS = ("(function(){const e = document.querySelector('[class*=CardWrapper], [class*=cmd-card]');"
                             "return e ? (e.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 80) : '';})()")


def _cloudmusic_find_first_card(driver):
    """The topmost mounted card's text — the handle on how far the grid has slid."""
    return driver.execute_script("return %s;" % _CLOUDMUSIC_FIRST_CARD_JS)


def _cloudmusic_count_grid_slides(driver, before, timeout=2.5):
    """True once a different card has mounted on top; False when the grid did not move at all."""
    return wait_js(driver, "%s !== %s" % (_CLOUDMUSIC_FIRST_CARD_JS, json.dumps(before)), timeout, tick=0.2)


_CLOUDMUSIC_CARDS_JS = r"""
const out = [];
for (const e of document.querySelectorAll('[class*=CardWrapper], [class*=cmd-card]')) {
  const r = e.getBoundingClientRect();
  if (r.width < 150 || r.left < 240) continue;
  const t = (e.innerText || '').replace(/\s+/g, ' ').trim().replace(/^[\d.]+万?\s+/, '');  // drop the play-count badge
  if (!t || /^[\d.]+万?$/.test(t)) continue;  // bare play-count badge with no title
  out.push(t.slice(0, 80));
}
return out;
"""


def cloudmusic_read_rec_cards(driver):
    orig = driver.execute_script(
        "const c = document.querySelector('[class*=AppScrollContainer]'); return c ? c.scrollTop : 0;")
    seen = []
    top = None
    for _ in range(15):
        for line in driver.execute_script(_CLOUDMUSIC_CARDS_JS):
            if line not in seen:
                seen.append(line)
        before = _cloudmusic_find_first_card(driver)
        s = driver.execute_script(
            "const c = document.querySelector('[class*=AppScrollContainer]'); if (!c) return null;"
            "c.scrollTop += c.clientHeight * 0.8;"
            "return [c.scrollTop, c.scrollHeight, c.clientHeight];")
        if s is None:
            break  # no scroll container — every card is already mounted
        if s[0] == top:
            break  # scrollTop did not move: shorter than the viewport
        top = s[0]
        _cloudmusic_count_grid_slides(driver, before)
        if s[0] + s[2] >= s[1] - 2:
            break
    driver.execute_script(
        "const c = document.querySelector('[class*=AppScrollContainer]'); if (c) c.scrollTop = arguments[0];", orig)
    cards = [c for c in seen if not any(c != o and c in o for o in seen)]  # nested cards repeat the same title
    print(f"CARDS: {len(cards)}")
    for c in cards:
        print(" ", c)
