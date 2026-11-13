# The mini bar is the source of truth (no <audio>, Web Audio pipeline). The 歌曲 tab number is the song
# count; the badge on the playlist cover is the play count.


def cloudmusic_read_player_state(driver):
    js = r"""
    const footer = document.querySelector('footer');
    const icon = footer ? footer.querySelector('span[aria-label=pause], span[aria-label=play]') : null;
    const state = icon ? (icon.getAttribute('aria-label') === 'pause' ? 'PLAYING' : 'PAUSED') : 'NO_CONTROL';
    const times = footer ? [...footer.querySelectorAll('[class*=miniBarTimeTextStyle]')].map(e => e.innerText.trim()) : [];
    const mq = footer ? footer.querySelector('[class*=marquee-item]') : null;
    let title = mq ? (mq.innerText || '').replace(/\s+/g, ' ').trim() : '';
    // long titles: marquee duplicates the whole "Title - Artist" text; dedupe an exact two-half repeat
    const mid = Math.floor(title.length / 2);
    if (title.length > 8 && title[mid] === ' ' && title.slice(0, mid) === title.slice(mid + 1)) title = title.slice(0, mid);
    return {state: state, title: title, times: times};
    """
    print(driver.execute_script(js))
