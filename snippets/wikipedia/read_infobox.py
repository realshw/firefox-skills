# Print the article's table.infobox, or NO INFOBOX when the page has none.


def wikipedia_read_infobox(driver):
    try:
        print(driver.find_element("css selector", "table.infobox").text)
    except Exception as e:
        print("NO INFOBOX: %s" % type(e).__name__)
