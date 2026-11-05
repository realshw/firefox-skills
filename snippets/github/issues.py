# Rows are React children (data-testid issue-listitem-title-link / issue-activity-timestamp); filtering
# needs ?q=is%3Aissue+is%3Aclosed (?state=closed just reloads the open list). thread(driver) reads both the React
# comment viewer and the classic timeline — a page picks either one. JS strings double their escapes.
import re

from snippets.common.wait_js import wait_js

_NUM = re.compile(r"/issues/(\d+)")

_THREAD_JS = """
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


def thread(driver, timeout=30):
    """Wait for the open issue/PR page, return {title, state, body, items} (body may be '')."""
    wait_js(
        driver, "!!(document.querySelector('[data-testid=\"issue-body\"]')"
        " || document.querySelector('div.timeline-comment-group')"
        " || document.querySelector('[data-testid=\"issue-title\"]'))",
        timeout)
    d = driver.execute_script(_THREAD_JS)
    if not d['body'] and d['items']:
        d['body'], d['comments'] = d['items'][0]['text'], d['items'][1:]
    else:
        d['comments'] = d['items']
    return d


def list_issues(driver, slug, state='open', limit=25, timeout=30):
    """Print and return [{num, title, url, time}] for one state of a repo's issues."""
    if "github.com" not in (driver.current_url or ""):
        driver.switch_to.new_window("tab")
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


def read_issue(driver,
               url_or_num,
               slug=None,
               body_limit=6000,
               comment_limit=1500):
    """Load an issue (full url, or a number when slug is given); print and return it as a dict."""
    url = url_or_num
    if not str(url_or_num).startswith('http'):
        m = _NUM.search(str(url_or_num))
        num = m.group(1) if m else str(url_or_num)
        if not slug:
            raise ValueError("read_issue(driver, num) needs slug='owner/repo'")
        url = "https://github.com/" + slug.strip("/") + "/issues/" + num
    if "github.com" not in (driver.current_url or ""):
        driver.switch_to.new_window("tab")
    driver.get(url)
    d = thread(driver)
    print("ISSUE:", d['title'][:90], "|", d['state'] or '-')
    print("BODY:", d['body'][:body_limit] or "(empty)")
    for c in d['comments']:
        print("---- @" + (c['author'] or '?') + ":",
              c['text'][:comment_limit].replace("\n", " "))
    print("COMMENTS", len(d['comments']), "|", url)
    d['url'] = url
    return d
