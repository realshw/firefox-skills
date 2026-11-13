# The like button's data-testid flips like → unlike, and that is the confirmation, not the count (which
# lags). Index is DOM order on the page (0 = first mounted article). Re-query the articles after every
# click — the element goes stale on re-render. undo=True un-likes.
import json

exec(open("snippets/common/wait_js.py").read())

LIKE = '[data-testid="like"], [data-testid="unlike"]'

_LABEL_JS = ("(function(){const a = "
             "document.querySelectorAll('article[data-testid=\"tweet\"]')[%d];"
             "if (!a) return '';"
             "const b = a.querySelector('%s');"
             "return b ? b.getAttribute('data-testid') : '';})()")


def _label(driver, index):
    """data-testid of the like button in that article, '' while it is not mounted."""
    return driver.execute_script("return " + _LABEL_JS % (index, LIKE) + ";")


def like_tweet(driver, index=0, undo=False):
    """Like (or un-like with undo=True) the article at `index`."""
    arts = driver.find_elements("css selector", 'article[data-testid="tweet"]')
    if index >= len(arts):
        print("LIKE_FAILED: only %d articles mounted (index %d)" %
              (len(arts), index))
        return False
    btns = arts[index].find_elements("css selector", LIKE)
    if not btns:
        print("LIKE_FAILED: no like button in article %d" % index)
        return False
    before = btns[0].get_attribute("data-testid")
    if (before == "unlike") == (not undo):
        print("NOOP:", "already liked" if before == "unlike" else "not liked")
        return True
    btns[0].click()
    want = "like" if undo else "unlike"
    ok = wait_js(driver,
                 "%s === %s" % (_LABEL_JS % (index, LIKE), json.dumps(want)),
                 10)
    got = _label(driver, index) or before
    print(("UNLIKED" if undo else "LIKED") if ok else "LIKE_FAILED",
          "| article %d: %s -> %s" % (index, before, got))
    return ok
