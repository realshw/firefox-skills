# Either /video/ or /bangumi/play/ (covers PGC movies/series) counts; if paused, resume and verify.
import json

exec(open("snippets/common/wait_js.py").read())


def resume_playback(driver):
    state_js = r"""
    const v = document.querySelector('video');
    if (!v) return null;
    return {paused: v.paused, t: v.currentTime, d: v.duration, muted: v.muted, vol: v.volume};
    """

    orig = driver.current_window_handle
    try:
        found = False
        for h in driver.window_handles:
            driver.switch_to.window(h)
            try:
                url = driver.current_url or ''
            except Exception:
                continue  # privileged tabs (about:*) reject the query — don't let them break the scan before the target
            if '/video/' in url or '/bangumi/play/' in url:
                found = True
                break
        if not found:
            print('NO_VIDEO_TAB')
            return
        print('TAB:', driver.title[:60])
        s0 = driver.execute_script(state_js)
        if not s0:
            print('NO_VIDEO_EL')
        else:
            if s0['paused']:
                # a real WebDriver click doubles as the user gesture (a JS click may not count)
                driver.find_element('css selector',
                                    '.bpx-player-ctrl-play').click()
            # Wait for the media clock, not for a duration: read currentTime within the same media-clock tick
            # and you get the value you started with, so the click alone proves nothing.
            wait_js(driver,
                    "!document.querySelector('video').paused"
                    " && document.querySelector('video').currentTime > %r" %
                    s0['t'],
                    10,
                    tick=0.5)
            s1 = driver.execute_script(state_js)
            print('BEFORE:', json.dumps(s0))
            print('AFTER:', json.dumps(s1))
            print('RESUME_OK' if (
                not s1['paused'] and s1['t'] > s0['t']) else 'RESUME_FAILED')
    finally:
        # the video tab is the user's: leave the session where it was, or its next navigation replaces
        # the page the user is watching.
        try:
            driver.switch_to.window(orig)
        except Exception:
            pass
