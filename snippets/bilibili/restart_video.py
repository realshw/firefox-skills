# Bilibili resumes from account history, so force it to 00:00 — but after a seek the stream re-buffers and
# paused is already false while currentTime sits at 0: wait for the playing state, never read it once.
import json

exec(open("snippets/common/wait_js.py").read())

PLAYING = "!document.querySelector('video').paused"
MOVING = "!document.querySelector('video').paused && document.querySelector('video').currentTime > 1.0"


def restart_video(driver):
    js = """const v = document.querySelector('video');
    if (!v) return null;
    return {paused: v.paused, t: v.currentTime, d: v.duration};"""

    if not driver.execute_script(js):
        raise RuntimeError('no <video> on this tab')
    driver.execute_script("document.querySelector('video').currentTime = 0;")
    if not wait_js(driver, PLAYING, 5, tick=0.3):
        # a real WebDriver click doubles as the user gesture (a JS click may not count)
        driver.find_element('css selector', '.bpx-player-ctrl-play').click()

    ok = wait_js(driver, MOVING, 30, tick=2.0)
    print('RESTARTED' if ok else 'FAILED',
          json.dumps(driver.execute_script(js)))
