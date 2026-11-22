"""Leave cloudmusic's 每日推荐 list open."""

exec(open("snippets/cloudmusic/open_rec.py").read())
exec(open("snippets/common/wait_js.py").read())

_CLOUDMUSIC_DAILY_JS = ('const t = document.querySelector("h1.recommend-title .recommend");'
                        'return !!t && t.innerText.includes("每日推荐");')


def cloudmusic_open_daily(driver):
    """Open the 每日推荐 list; it counts as open when h1.recommend-title .recommend says so.

    30 songs per list, and the "10 / 10" on that h1 is the date, not a count.
    """
    if not driver.execute_script(_CLOUDMUSIC_DAILY_JS):
        cloudmusic_open_rec(driver)
        spans = [
            e for e in driver.find_elements("xpath", '//span[normalize-space(text())="每日推荐" and not(ancestor::h1)]')
            if e.is_displayed() and e.location["x"] > 240
        ]
        if not spans:
            raise RuntimeError("每日推荐 card not found on the rec home")
        card = min(spans, key=lambda e: e.location["y"])
        driver.execute_script("arguments[0].click()",
                              card)  # JS click: the cover <img> sits over the span and intercepts a real click
        if not wait_js(driver, as_expr(_CLOUDMUSIC_DAILY_JS), 15):
            raise RuntimeError("每日推荐 never opened")
    print("OPENED_DAILY")
