"""Read the lines of a loaded page that match a pattern, without dumping the whole article."""

import re
import textwrap

from selenium.webdriver.common.by import By


def grep_page(driver, pattern, min_len=0, width=160, flags=re.I):
    """Print the body-text lines matching `pattern` (a regex), each wrapped to `width`; returns them.

    The line-level read for a question the page answers in a sentence or two — "said … Interim CEO", an
    earnings figure, a dateline. Skips lines shorter than `min_len`, which is how nav labels, "SHARE" and
    section headings stay out of the way when only prose is wanted (60 is a good prose floor). Lines are
    printed as they are found, so the caller need not print them again to read the answer.
    """
    body = driver.find_element(By.TAG_NAME, "body").text
    hits = []
    for line in body.splitlines():
        s = line.strip()
        if len(s) < min_len or not re.search(pattern, s, flags):
            continue
        hits.append(s)
        print(textwrap.fill(s, width))
    if not hits:
        print("GREP: no line matched %r (%s)" % (pattern, driver.current_url))
    return hits
