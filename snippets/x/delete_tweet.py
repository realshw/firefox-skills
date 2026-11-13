# The caret opens a [role="menu"] whose "Delete" item carries no testid — match the label exactly; the
# confirm sheet has no [role="dialog"] wrapper. The caret is one click from a real deletion, so every call
# takes `expect` and refuses unless the focal post's text contains it. /status/ pages only.
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

X_CARET = 'article[data-testid="tweet"] [data-testid="caret"]'


def x_delete_tweet(driver, url, expect=None, dry_run=False):
    """Delete the post at `url` (must be yours). `expect` guards the target; dry_run stops at the sheet."""
    if not url.startswith("http"):
        url = "https://x.com/" + url.lstrip("/")
    site_tab(driver, "//x.com/")
    driver.get(url)
    if not wait_js(driver, "!!document.querySelector('%s')" % X_CARET):
        print("DELETE_FAILED: no caret on the page (not on a /status/ page, or not your post)")
        return False
    text = driver.execute_script("const a = document.querySelector('article[data-testid=\"tweet\"]');"
                                 "const t = a && a.querySelector('[data-testid=\"tweetText\"]');"
                                 "return t ? t.innerText : '';") or ""
    if expect and expect not in text:
        print("DELETE_ABORTED: target text does not contain %r - saw: %s" % (expect, text[:80].replace("\n", " ")))
        return False
    print("TARGET:", text[:80].replace("\n", " "))
    driver.find_element("css selector", X_CARET).click()
    if not wait_js(driver, '!!document.querySelector(\'[role="menu"]\')'):
        print("DELETE_FAILED: caret menu never opened")
        return False
    item = None
    for e in driver.find_elements("css selector", '[role="menu"] [role="menuitem"]'):
        if (e.text or "").strip() == "Delete":
            item = e
            break
    if item is None:
        print("DELETE_FAILED: no 'Delete' item (someone else's post, or the menu changed)")
        driver.find_element("tag name", "body").send_keys("\ue00c")  # ESC: close the menu
        return False
    item.click()
    if not wait_js(driver, '!!document.querySelector(\'[data-testid="confirmationSheetConfirm"]\')'):
        print("DELETE_FAILED: confirmation sheet never appeared")
        return False
    if dry_run:
        driver.find_element("css selector", '[data-testid="confirmationSheetCancel"]').click()
        print("DRY_RUN: cancelled at the sheet - nothing deleted")
        return False
    driver.find_element("css selector", '[data-testid="confirmationSheetConfirm"]').click()
    gone = wait_js(driver, '!/\\S/.test((document.querySelector(\'article[data-testid="tweet"] '
                   '[data-testid="tweetText"]\') || {}).innerText || "")'
                   ' || /deleted/i.test(document.body.innerText)',
                   timeout=25)
    toast = ""
    try:
        toast = " ".join(driver.find_element("css selector", '[data-testid="toast"]').text.split())
    except Exception:
        pass
    print("DELETED:" if gone else "DELETE_UNCONFIRMED:", gone, "| toast:", toast or "(none)")
    return gone
