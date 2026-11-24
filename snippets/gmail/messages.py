"""Read a Gmail search result, open one conversation, and reply to it."""

import time
from urllib.parse import quote

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

GMAIL_BASE = "https://mail.google.com/mail/u/0/"

# A row carries its subject in .y6; rows of the list Gmail navigated away from stay in the DOM, hidden.
_GMAIL_ROWS_JS = """
const out = [];
document.querySelectorAll('tr.zA').forEach((tr, i) => {
  if (tr.getBoundingClientRect().height === 0) return;  // the previous list stays in the DOM, hidden
  const subject = (tr.querySelector('.y6 span') || {}).innerText || '';
  if (!subject.trim()) return;
  const sender = (tr.querySelector('.yX.xY .yW span, .bog') || {}).innerText || '';
  out.push({index: i, sender: sender.trim(), subject: subject.trim(),
            snippet: ((tr.querySelector('.y2') || {}).innerText || '').trim()});
});
return out;
"""

_GMAIL_COMPOSE_JS = """
const input = document.querySelector('div[aria-label="Message Body"]');
if (!input) return null;
const to = [...document.querySelectorAll('span[email]')].map(e => e.getAttribute('email'));
const subj = [...document.querySelectorAll('input[name=subjectbox]')].map(e => e.value);
return {to: to, subject: subj, visible: [...document.querySelectorAll('span[email]')].length};
"""


def gmail_search(driver, query, timeout=25):
    """Rows of a Gmail search as {index, sender, subject, snippet}, index counting every tr.zA on the page.

    Gmail keeps the list it navigated away from in the DOM at zero height, so a bare `tr.zA` query answers
    with the inbox while the search result is one row among nineteen: rows are filtered by their rect here,
    and the index stays a position in driver.find_elements("tr.zA") for gmail_open(). Confirmed on
    "newer_than:2h subject:CONFIRM": 20 rows in the DOM, 1 of them displayed.
    """
    site_tab(driver, "mail.google.com")
    driver.get(GMAIL_BASE + "#search/" + quote(query))
    shown = "[...document.querySelectorAll('tr.zA')].some(t => t.getBoundingClientRect().height > 0)"
    wait_js(driver, shown, timeout=timeout)
    for _ in range(3):  # the result set can be swapped in after the first rows appear
        rows = driver.execute_script(_GMAIL_ROWS_JS)
        if rows:
            return rows
        time.sleep(1)
    return []


def gmail_open(driver, index=None, subject_contains=None, timeout=25):
    """Body text of the newest message in the opened conversation; picks the row by index or by subject.

    Rows are located on the results page already loaded, then clicked through JS: WebDriver's click throws
    ElementNotInteractable on Gmail's synthetic rows. A conversation opens as #<search>/<thread id>, which
    is the receipt that the right one opened.
    """
    rows = driver.execute_script(_GMAIL_ROWS_JS)
    pick = next((r for r in rows if subject_contains and subject_contains in r["subject"]), None)
    if pick is None and index is not None:
        pick = next((r for r in rows if r["index"] == index), None)
    if pick is None and rows:
        pick = rows[0]
    if pick is None:
        raise RuntimeError("gmail_open: no rows on the page — run gmail_search() first")
    trs = driver.find_elements("css selector", "tr.zA")
    driver.execute_script("arguments[0].click()", trs[pick["index"]])
    wait_js(driver, "document.querySelectorAll('div.a3s').length>0", timeout=timeout)
    time.sleep(1)
    bodies = driver.find_elements("css selector", "div.a3s")
    print("GMAIL_OPEN: %s | %s | %s" % (pick["subject"][:60], driver.current_url[-40:], len(bodies)))
    return bodies[-1].text if bodies else ""


def gmail_reply(driver, body="", dry_run=True, timeout=20):
    """Compose a reply to the open conversation; sends it unless dry_run, which discards the draft.

    The reply goes to the From address of the message, so open a message whose sender is the address that
    must receive it (a SmartList confirmation, for one, is from the -request address). This account's split
    button is set to "Send and archive": the send also archives the thread, and the call says so.
    """
    reply = """const el = [...document.querySelectorAll('span.ams.bkH')]
      .find(e => e.innerText.trim() === 'Reply' && e.getBoundingClientRect().width > 0);
    if (el) el.click();
    return !!el;"""
    if not driver.execute_script(reply):
        raise RuntimeError("gmail_reply: no Reply button — is a conversation open?")
    wait_js(driver, "document.querySelectorAll('div[aria-label=\"Message Body\"]').length>0", timeout=timeout)
    time.sleep(1)
    fields = driver.execute_script(_GMAIL_COMPOSE_JS)
    print("GMAIL_REPLY: to=%s subject=%r" % (fields["to"][-1:], fields["subject"][:1]))
    box = driver.find_element("css selector", "div[aria-label='Message Body']")
    box.click()
    if body:
        box.send_keys(body)
    if dry_run:
        driver.execute_script("""
        const d = [...document.querySelectorAll('div[role=button]')]
          .filter(e => /Discard draft/.test(e.getAttribute('aria-label') || '')
                       && e.getBoundingClientRect().width > 0).pop();
        if (d) d.click();
        """)
        time.sleep(1)
        print("GMAIL_REPLY: dry_run - draft discarded, nothing sent")
        return False
    button = driver.execute_script("""
    return [...document.querySelectorAll('div[role=button]')]
      .find(e => /^Send/.test((e.getAttribute('aria-label') || '').trim())
                 && e.getBoundingClientRect().width > 0) || null;
    """)
    print("GMAIL_REPLY: sending via %r" % button.get_attribute("aria-label"))
    button.click()
    time.sleep(3)
    snack = driver.execute_script("const a=document.querySelector('div[role=alert],span.bAq');"
                                  "return a ? a.innerText.trim() : '';")
    print("GMAIL_REPLY: %s" % (snack or "compose closed"))
    return True
