"""Print a Wikipedia article's infobox."""


def wikipedia_read_infobox(driver):
    """Print table.infobox, or NO INFOBOX when the page has none."""
    try:
        print(driver.find_element("css selector", "table.infobox").text)
    except Exception as e:
        print("NO INFOBOX: %s" % type(e).__name__)
