# Tab urls are plain (/handle, /handle/replies, /handle/media): don't click the role="tab" buttons. Wait
# for the tweets, not [data-testid="UserName"] — a count taken when the header mounts is still 0. The
# empty-profile wording differs by tab and owner, so match the fragments.
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

X_USER_TABS = {
    "posts": "",
    "replies": "/with_replies",
    "media": "/media",
    "likes": "/likes"
}


def x_goto_user(driver, handle, tab="posts", timeout=25):
    """Navigate the x.com tab to a profile page (handle with or without @); returns tweets mounted."""
    h = handle.strip().lstrip("@").split("/")[0]
    if tab not in X_USER_TABS:
        print("BAD_TAB:", tab, "expected one of", list(X_USER_TABS))
        return -1
    site_tab(driver, "//x.com/")
    driver.get("https://x.com/" + h + X_USER_TABS[tab])
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
