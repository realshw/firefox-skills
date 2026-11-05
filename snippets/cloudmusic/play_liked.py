# Composition: player tab in place, liked playlist open, playback started, then the mini bar state.
from snippets.cloudmusic.goto_player import goto_player
from snippets.cloudmusic.open_liked import open_liked
from snippets.cloudmusic.play_all import play_all
from snippets.cloudmusic.player_state import player_state


def play_liked(driver):
    goto_player(driver)
    open_liked(driver)
    play_all(driver)
    player_state(driver)
