# Already open when h1.recommend-title .recommend shows 每日推荐. 30 songs per list; the "10 / 10" on the
# h1 is the date, not a count.
from selenium.webdriver.support.ui import WebDriverWait

exec(open("snippets/cloudmusic/open_rec.py").read())

_DAILY_JS = ('const t = document.querySelector("h1.recommend-title .recommend");'
       'return !!t && t.innerText.includes("每日推荐");')


def open_daily(driver):
    if not driver.execute_script(_DAILY_JS):
        open_rec(driver)
        spans = [
            e for e in driver.find_elements(
                "xpath",
                '//span[normalize-space(text())="每日推荐" and not(ancestor::h1)]')
            if e.is_displayed() and e.location["x"] > 240
        ]
        if not spans:
            raise RuntimeError("每日推荐 card not found on the rec home")
        card = min(spans, key=lambda e: e.location["y"])
        driver.execute_script(
            "arguments[0].click()", card
        )  # JS click: the cover <img> sits over the span and intercepts a real click
        WebDriverWait(driver, 15).until(lambda d: d.execute_script(_DAILY_JS))
    print("OPENED_DAILY")
