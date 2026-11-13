# The list is virtualized (~20 rows mounted, the page itself does not scroll) — yank
# [class*=AppScrollContainer] to the top and step down 0.75*clientHeight collecting div.tr rows, restoring
# scrollTop after. The playing row hides its number but div.play.playing marks it; skip the '#' header.
# Virtualized means the DOM is ready when the number under the first mounted row changes, not after a sleep.
import json

from selenium.webdriver.common.by import By

exec(open("snippets/common/wait_js.py").read())

_FIRST_NUM_JS = (
    "(function(){const s = document.querySelector('div.tr div.td-num span');"
    "return s ? (s.textContent || '').trim() : '';})()")


def _first_num(driver):
    """The number of the topmost mounted row — the handle on how far the window has slid."""
    return driver.execute_script("return %s;" % _FIRST_NUM_JS)


def _window_slides(driver, before, timeout=2.5):
    """True once a different row has mounted on top; False when the list did not move at all."""
    return wait_js(driver,
                   "%s !== %s" % (_FIRST_NUM_JS, json.dumps(before)),
                   timeout,
                   tick=0.2)


def _collect(driver, rows):
    for r in driver.find_elements(By.CSS_SELECTOR, "div.tr"):
        num_els = r.find_elements(By.CSS_SELECTOR, "div.td-num span")
        title_els = r.find_elements(By.CSS_SELECTOR, "h4.title")
        if not num_els or not title_els:
            continue  # header row / non-song row
        num = (num_els[0].get_attribute("textContent") or "").strip()
        if not num.isdigit():
            continue
        album = r.find_elements(By.CSS_SELECTOR, "div.td-album")
        dur = r.find_elements(By.CSS_SELECTOR, "div.td-duration")
        artists = r.find_elements(By.CSS_SELECTOR, "h5.artists")
        rows[int(num)] = {
            "num":
            int(num),
            "title":
            title_els[0].text,
            "artists":
            artists[0].text if artists else "",
            "album":
            album[0].text if album else "",
            "duration":
            dur[0].text if dur else "",
            "playing":
            bool(
                r.find_elements(By.CSS_SELECTOR,
                                "div.td-num div.play.playing")),
        }


def _scroll_by(driver, frac):
    return driver.execute_script(
        "const c = document.querySelector('[class*=AppScrollContainer]'); if (!c) return null;"
        "c.scrollTop = c.scrollTop + c.clientHeight * arguments[0];"
        "return [c.scrollTop, c.scrollHeight, c.clientHeight];", frac)


def _scroll_to(driver, top):
    return driver.execute_script(
        "const c = document.querySelector('[class*=AppScrollContainer]'); if (!c) return null;"
        "c.scrollTop = arguments[0];"
        "return [c.scrollTop, c.scrollHeight, c.clientHeight];", top)


def read_songlist(driver):
    rows = {}

    container = driver.execute_script(
        "const c = document.querySelector('[class*=AppScrollContainer]'); return c ? [c.scrollTop, c.scrollHeight, c.clientHeight] : null;"
    )
    if container and container[0] > 0:
        before = _first_num(driver)
        _scroll_to(driver, 0)
        _window_slides(driver, before)
    _collect(driver, rows)
    top = None
    for _ in range(60):
        before = _first_num(driver)
        s = _scroll_by(driver, 0.75)
        if s is None:
            break  # no scroll container — every row is already in the DOM
        if s[0] == top:
            break  # scrollTop did not move: the list is shorter than the viewport
        top = s[0]
        _window_slides(driver, before)
        _collect(driver, rows)
        if s[0] + s[2] >= s[1] - 2:
            break
    _collect(driver, rows)
    if container:
        driver.execute_script(
            "const c = document.querySelector('[class*=AppScrollContainer]'); c.scrollTop = arguments[0];",
            container[0])
    rows = [rows[k] for k in sorted(rows)]
    print(f"SONGLIST: {len(rows)} songs")
    for r in rows:
        mark = "▶" if r["playing"] else " "
        print(
            f"{mark} {r['num']:02d}. {r['title']} — {r['artists']}  [{r['duration']}]"
        )
