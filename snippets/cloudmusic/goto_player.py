# Load the web player and wait for the mini-bar <footer> — that bar is the only playback state (no <audio>
# on the page, Web Audio pipeline). "Already on the player" means the player tab, and playback snippets
# need that tab to stay theirs rather than the page the user is reading. Two player tabs mean two audio
# pipelines that toggle_play cannot reach, so an existing one is adopted, not opened next to.
from selenium.webdriver.support.ui import WebDriverWait

PLAYER = "https://music.163.com/st/webplayer"


def _existing_player(driver):
    """Handle of an open player tab (focus ends there), or None with focus put back."""
    orig = driver.current_window_handle
    for h in driver.window_handles:
        if h == orig:
            continue
        try:
            driver.switch_to.window(h)
            if (driver.current_url or "").startswith(PLAYER):
                print("ADOPTED:", h[:12])
                return h
        except Exception:
            continue  # privileged, or discarded since the scan started
    try:
        driver.switch_to.window(orig)
    except Exception:
        pass
    return None


def goto_player(driver):
    if not driver.current_url.startswith(PLAYER):
        if not _existing_player(driver):
            if "music.163.com" not in driver.current_url:
                driver.switch_to.new_window("tab")
            driver.get(PLAYER)
    WebDriverWait(driver, 25).until(
        lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(
        driver, 25).until(lambda d: d.find_elements("css selector", "footer"))
    print("TITLE:", driver.title)
    print("URL:", driver.current_url)
