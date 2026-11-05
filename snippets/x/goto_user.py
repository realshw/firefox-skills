# Tab urls are plain (/handle, /handle/replies, /handle/media): don't click the role="tab" buttons. Wait
# for the tweets, not [data-testid="UserName"] — a count taken when the header mounts is still 0. The
# empty-profile wording differs by tab and owner, so match the fragments.
from snippets.common.wait_js import wait_js

TABS = {
    "posts": "",
    "replies": "/with_replies",
    "media": "/media",
    "likes": "/likes"
}


def goto_user(driver, handle, tab="posts", timeout=25):
    """Navigate the x.com tab to a profile page (handle with or without @); returns tweets mounted."""
    h = handle.strip().lstrip("@").split("/")[0]
    if tab not in TABS:
        print("BAD_TAB:", tab, "expected one of", list(TABS))
        return -1
    if "//x.com/" not in (driver.current_url or ""):
        driver.switch_to.new_window("tab")
    driver.get("https://x.com/" + h + TABS[tab])
    wait_js(driver,
            'document.querySelectorAll(\'article[data-testid="tweet"]\')'
            '.length || (document.body.innerText.includes("post")'
            ' && /hasn|haven|还没/.test(document.body.innerText))',
            timeout,
            tick=1.0)
    n = driver.execute_script(
        'return document.querySelectorAll(\'article[data-testid="tweet"]\').length'
    )
    body = driver.execute_script("return document.body.innerText") or ""
    empty = not n and "post" in body and any(m in body
                                             for m in ("hasn", "haven", "还没"))
    print("PROFILE:", driver.title, "| tweets:", n, "| empty:", empty)
    return n
