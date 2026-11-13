# Rows are React children (data-testid issue-listitem-title-link / issue-activity-timestamp); filtering
# needs ?q=is%3Aissue+is%3Aclosed (?state=closed just reloads the open list).
# github_read_thread(driver) reads both the React
# comment viewer and the classic timeline — a page picks either one. JS strings double their escapes.
import re
import time

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/type_verified.py").read())
exec(open("snippets/common/wait_js.py").read())

# Editing the issue body: the body's first icon button is the kebab holding "Edit", the editor is the same
# textarea the new-issue form uses, and "Save" carries no testid (the comment box's own buttons sit too).
# Commenting: the page's Markdown textarea is the comment box, and its submit is the last enabled "Comment"
# button — "Close with comment" keeps its own pair just above.
_GITHUB_BODY_SEL = 'textarea[placeholder^="Type your description"]'
_GITHUB_COMMENT_SEL = 'textarea[placeholder*="Markdown"]'
_GITHUB_SAVE_BODY_JS = """
const b = [...document.querySelectorAll('button')]
  .filter(x => (x.innerText || '').trim() === 'Save' && (x.offsetParent || x.getClientRects().length));
if (b.length) b[b.length - 1].click();
return b.length;
"""
_GITHUB_SUBMIT_COMMENT_JS = """
const b = [...document.querySelectorAll('button')]
  .filter(x => (x.innerText || '').trim() === 'Comment' && !x.disabled
               && (x.offsetParent || x.getClientRects().length));
if (b.length) b[b.length - 1].click();
return b.length;
"""


def _github_wait_editor(driver, sel, timeout=60):
    """Wait for a body editor or comment box to mount and return the text it holds now."""
    end = time.time() + timeout
    while time.time() < end:
        for el in driver.find_elements("css selector", sel):
            if el.is_displayed():
                return el.get_attribute('value') or ''
        time.sleep(0.2)
    raise RuntimeError("editor never opened: %s" % sel)


def _github_build_issue_url(url_or_num, slug=None):
    """Full issue URL: a URL passes through as given, a bare number needs slug='owner/repo'."""
    if str(url_or_num).startswith('http'):
        return url_or_num
    m = _GITHUB_ISSUE_NUM.search(str(url_or_num))
    num = m.group(1) if m else str(url_or_num)
    if not slug:
        raise ValueError("an issue number needs slug='owner/repo'")
    return "https://github.com/" + slug.strip("/") + "/issues/" + num


_GITHUB_ISSUE_NUM = re.compile(r"/issues/(\d+)")

_GITHUB_THREAD_JS = """
const txt = s => { const e = document.querySelector(s); return e ? e.innerText.trim() : ''; };
const items = [];
document.querySelectorAll('[data-testid^="comment-viewer-outer-box"]').forEach(c => {
  const a = c.querySelector('a[data-testid="avatar-link"]') || c.querySelector('a[data-hovercard-type="user"]');
  const b = c.querySelector('.markdown-body');
  items.push({author: a ? a.innerText.trim() : '', text: b ? b.innerText.trim() : ''});
});
if (!items.length) {
  document.querySelectorAll('div.timeline-comment-group').forEach(c => {
    const a = c.querySelector('a.author');
    const b = c.querySelector('.comment-body');
    items.push({author: a ? a.innerText.trim() : '', text: b ? b.innerText.trim() : ''});
  });
}
// The React body box also contains its own "Description / <author> / opened" header, so read the
// .markdown-body inside it — innerText of the box carries that header into the body text.
const box = document.querySelector('[data-testid="issue-body"]');
const md = box && box.querySelector('.markdown-body');
// The classic h1 keeps "- #5918" on a second line; the React title does not.
const rawTitle = txt('[data-testid="issue-title"]') || txt('h1[class*="PageHeader-Title"]');
const stateLabel = document.querySelector('span[class*="StateLabel"]');
return {title: rawTitle.split('\\n')[0].trim(),
        state: txt('[data-testid="header-state"]') || (stateLabel ? stateLabel.innerText.trim() : ''),
        body: md ? md.innerText.trim() : txt('[data-testid="issue-body"]'),
        items: items};
"""


def github_read_thread(driver, timeout=30):
    """Wait for the open issue/PR page, return {title, state, body, items} (body may be '')."""
    wait_js(
        driver, "!!(document.querySelector('[data-testid=\"issue-body\"]')"
        " || document.querySelector('div.timeline-comment-group')"
        " || document.querySelector('[data-testid=\"issue-title\"]'))",
        timeout)
    d = driver.execute_script(_GITHUB_THREAD_JS)
    if not d['body'] and d['items']:
        d['body'], d['comments'] = d['items'][0]['text'], d['items'][1:]
    else:
        d['comments'] = d['items']
    return d


def github_list_issues(driver, slug, state='open', limit=25, timeout=30):
    """Print and return [{num, title, url, time}] for one state of a repo's issues."""
    site_tab(driver, "github.com")
    driver.get("https://github.com/" + slug.strip("/") +
               "/issues?q=is%3Aissue+is%3A" + state)
    wait_js(
        driver,
        "!!document.querySelector('[data-testid=\"issue-listitem-title-link\"]')",
        timeout)
    rows = driver.execute_script("""
    const out = [];
    document.querySelectorAll('[data-testid="issue-listitem-title-link"]').forEach(a => {
      let href = a.getAttribute('href') || '';
      const m = href.match(/\\/issues\\/(\\d+)/);
      if (!m) return;
      if (!/^https?:/.test(href)) href = 'https://github.com' + href;
      out.push({num: m[1], title: a.innerText.trim(), url: href, time: ''});
    });
    return out;
    """)
    stamps = driver.execute_script(
        "return [...document.querySelectorAll('[data-testid=\"issue-activity-timestamp\"]')].map(e => e.innerText.trim())"
    )
    for i, r in enumerate(rows):
        r['time'] = stamps[i] if i < len(stamps) else ''
    for r in rows[:limit]:
        print("#" + r['num'], "|", r['title'][:70], "|", r['time'])
    print("ISSUES", state, len(rows))
    return rows


def github_read_issue(driver,
               url_or_num,
               slug=None,
               body_limit=6000,
               comment_limit=1500):
    """Load an issue (full url, or a number when slug is given); print and return it as a dict."""
    url = url_or_num
    if not str(url_or_num).startswith('http'):
        m = _GITHUB_ISSUE_NUM.search(str(url_or_num))
        num = m.group(1) if m else str(url_or_num)
        if not slug:
            raise ValueError("read_issue(driver, num) needs slug='owner/repo'")
        url = "https://github.com/" + slug.strip("/") + "/issues/" + num
    site_tab(driver, "github.com")
    driver.get(url)
    d = github_read_thread(driver)
    print("ISSUE:", d['title'][:90], "|", d['state'] or '-')
    print("BODY:", d['body'][:body_limit] or "(empty)")
    for c in d['comments']:
        print("---- @" + (c['author'] or '?') + ":",
              c['text'][:comment_limit].replace("\n", " "))
    print("COMMENTS", len(d['comments']), "|", url)
    d['url'] = url
    return d


def github_append_body(driver, url_or_num, text, slug=None, timeout=60):
    """Append text to an issue body (kebab -> Edit), verify the saved tail, return the new body.

    Only the tail is typed: type_verified reads the editor, sees the old body as a prefix of the wanted
    text and sends the remainder after moving the caret to the end. Safe to re-run - appending twice is a
    visible duplicate, not a silent one."""
    url = _github_build_issue_url(url_or_num, slug)
    site_tab(driver, "github.com")
    driver.get(url)
    github_read_thread(driver, timeout)

    driver.find_elements("css selector",
                         '[data-testid="issue-body"] button')[0].click()
    for item in driver.find_elements("css selector", '[role="menuitem"]'):
        if (item.text or '').strip() == 'Edit':
            item.click()
            break
    else:
        raise RuntimeError(
            "no Edit menu item - the issue body is not editable")

    old = _github_wait_editor(driver, _GITHUB_BODY_SEL, timeout)
    want = old.rstrip() + "\n\n" + text.strip()
    if not type_verified(driver, want, selector=_GITHUB_BODY_SEL, paste_over=10**9):
        raise RuntimeError("appended body did not type back exactly")
    print("SAVE_BUTTONS:", driver.execute_script(_GITHUB_SAVE_BODY_JS))
    wait_js(driver, "!document.querySelector('%s')" % _GITHUB_BODY_SEL, timeout)

    d = github_read_thread(driver, timeout)
    saved = d['body'].rstrip().endswith(text.strip())
    print("BODY_APPENDED:", saved, "| chars:", len(d['body']))
    if not saved:
        raise RuntimeError(
            "the saved body does not end with the appended text")
    return d['body']


def github_post_comment(driver, url_or_num, text, slug=None, timeout=60, dry_run=False):
    """Post text as a new comment on an issue, then reload and prove it is in the thread.

    dry_run=True only checks the box is there - nothing is typed and nothing is sent, so it is safe on
    an issue the caller is not ready to post to. Returns the comment dict when it lands."""
    url = _github_build_issue_url(url_or_num, slug)
    site_tab(driver, "github.com")
    driver.get(url)
    github_read_thread(driver, timeout)

    if _github_wait_editor(driver, _GITHUB_COMMENT_SEL, timeout) is None:
        raise RuntimeError("no comment box: locked or read-only issue?")
    if dry_run:
        print("DRY_RUN: comment box found, nothing typed |", url)
        return {"url": url, "dry_run": True}

    if not type_verified(driver, text, selector=_GITHUB_COMMENT_SEL):
        raise RuntimeError("comment did not type back exactly")
    print("SUBMIT_BUTTONS:", driver.execute_script(_GITHUB_SUBMIT_COMMENT_JS))
    wait_js(
        driver,
        "!document.querySelector('%s') || !document.querySelector('%s').value"
        % (_GITHUB_COMMENT_SEL, _GITHUB_COMMENT_SEL), timeout)

    driver.get(url)
    d = github_read_thread(driver, timeout)
    head = text.strip().splitlines()[0][:40]
    hit = [c for c in d['comments'] if head in (c['text'] or '')]
    print("COMMENT_POSTED:", bool(hit), "| comments:", len(d['comments']))
    if not hit:
        raise RuntimeError("the comment is not in the thread after submitting")
    return hit[-1]
