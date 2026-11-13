# Load the web player and wait for the mini-bar <footer> — that bar is the only playback state (no <audio>
# on the page, Web Audio pipeline). "Already on the player" means the player tab, and playback snippets
# need that tab to stay theirs rather than the page the user is reading. Two player tabs mean two audio
# pipelines that cloudmusic_toggle_play cannot reach, so an existing one is adopted, not opened next to.
from selenium.webdriver.support.ui import WebDriverWait

exec(open("snippets/common/site_tab.py").read())

CLOUDMUSIC_PLAYER_URL = "https://music.163.com/st/webplayer"


def _cloudmusic_find_player(driver):
    """Handle of an open player tab (focus ends there), or None with focus put back."""
    orig = driver.current_window_handle
    for h in driver.window_handles:
        if h == orig:
            continue
        try:
            driver.switch_to.window(h)
            if (driver.current_url or "").startswith(CLOUDMUSIC_PLAYER_URL):
                print("ADOPTED:", h[:12])
                return h
        except Exception:
            continue  # privileged, or discarded since the scan started
    try:
        driver.switch_to.window(orig)
    except Exception:
        pass
    return None


def cloudmusic_goto_player(driver):
    if not driver.current_url.startswith(CLOUDMUSIC_PLAYER_URL):
        if not _cloudmusic_find_player(driver):
            site_tab(driver, "music.163.com")
            driver.get(CLOUDMUSIC_PLAYER_URL)
    WebDriverWait(driver, 25).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, 25).until(lambda d: d.find_elements("css selector", "footer"))
    print("TITLE:", driver.title)
    print("URL:", driver.current_url)
