# Already open when that description line shows (the visible title is a plain span, the only h1 is a 0×0
# hidden copy). 35 songs, mixing repeats with fresh recommendations.
from selenium.webdriver.support.ui import WebDriverWait

exec(open("snippets/cloudmusic/open_rec.py").read())

_CLOUDMUSIC_RADAR_JS = 'return document.body.innerText.includes("反复聆听你最爱的歌");'


def cloudmusic_open_radar(driver):
    if not driver.execute_script(_CLOUDMUSIC_RADAR_JS):
        cloudmusic_open_rec(driver)
        spans = [
            e for e in driver.find_elements("xpath", '//span[normalize-space(text())="私人雷达" and not(ancestor::h1)]')
            if e.is_displayed() and e.location["x"] > 240
        ]
        if not spans:
            raise RuntimeError("私人雷达 card not found on the rec home")
        card = min(spans, key=lambda e: e.location["y"])
        driver.execute_script("arguments[0].click()",
                              card)  # JS click: the cover <img> sits over the span and intercepts a real click
        WebDriverWait(driver, 15).until(lambda d: d.execute_script(_CLOUDMUSIC_RADAR_JS))
    print("OPENED_RADAR")
