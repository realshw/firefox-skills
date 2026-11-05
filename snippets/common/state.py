# Peek at the browser's current state


def state(driver):
    # about:* pages reject title/url, and a tab left after a close often is one: never abort the peek.
    for label, attr in (("TITLE", "title"), ("URL", "current_url")):
        try:
            print(label + ":", getattr(driver, attr))
        except Exception:
            print(label + ": (privileged)")
    print("WINDOWS:", len(driver.window_handles))
