# Reads the mounted cells of /notifications (navigate there first) — they are
# [data-testid="notification"], not articles. links[0] is the actor; the second link may be a quoted excerpt.


def x_read_notifications(driver):
    cells = driver.find_elements("css selector",
                                 '[data-testid="notification"]')
    print("NOTIFICATIONS:", len(cells), "|", driver.title)
    for i, c in enumerate(cells, 1):
        txt = " ".join((c.text or "").split())
        links = []
        for a in c.find_elements("css selector", "a[href^='/']"):
            h = a.get_attribute("href")
            if h and h not in links:
                links.append(h)
        print("%d. %s" % (i, txt[:300]))
        if links:
            print("   links:", " ".join(links[:3]))
    if not cells:
        print(
            "(none mounted — /notifications not open, or the list hasn't loaded yet)"
        )
