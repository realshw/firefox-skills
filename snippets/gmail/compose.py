"""Write and send a new Gmail message, or fill it in and throw the draft away."""

import time

from selenium.webdriver.common.keys import Keys

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

GMAIL_BASE = "https://mail.google.com/mail/u/0/"

_GMAIL_COMPOSE_JS = """
const box = document.querySelector('div[aria-label="Message Body"]');
if (!box) return null;
const send = [...document.querySelectorAll('div[role=button]')]
  .filter(e => e.getBoundingClientRect().width > 0)
  .map(e => (e.getAttribute('aria-label') || '').trim())
  .find(l => /^Send/.test(l)) || '';
return {send: send,
        body: box.innerText,
        subject: [...document.querySelectorAll('input[name=subjectbox]')].map(e => e.value)};
"""


def _discard(driver):
    """Throw the open compose away, answering Gmail's "Discard draft?" prompt when it appears."""
    driver.execute_script("""
    const d = [...document.querySelectorAll('div[role=button]')]
      .filter(e => /Discard draft/.test(e.getAttribute('aria-label') || '')
                   && e.getBoundingClientRect().width > 0).pop();
    if (d) d.click();
    """)
    time.sleep(1)
    driver.execute_script("""
    const ok = [...document.querySelectorAll('div[role=dialog] div[role=button]')]
      .find(e => /^(Discard|OK|Yes)/i.test(e.innerText.trim()));
    if (ok) ok.click();
    """)
    time.sleep(1)


def gmail_compose(driver, to, subject, body, dry_run=True, timeout=20):
    """Fill a fresh compose with (to, subject, body); send it, or discard it when dry_run.

    Gmail's compose button and fields are addressed by aria-label, which survives the class-name churn. The
    recipient needs Enter after send_keys or Gmail leaves the text uncommitted and refuses to send. A fresh
    compose's primary button reads "Send (Ctrl-Enter)"; a reply made from inside an open conversation may
    read "Send and archive" instead, so the label is printed before it is clicked.
    """
    site_tab(driver, "mail.google.com")
    if not driver.execute_script("""
    const b = [...document.querySelectorAll('div[role=button]')]
      .find(e => /Compose/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
    if (b) b.click();
    return !!b;
    """):
        raise RuntimeError("gmail_compose: no Compose button on the page")
    wait_js(driver, "document.querySelector('input[aria-label=\"To recipients\"]') !== null", timeout=timeout)
    time.sleep(1)
    field = driver.find_element("css selector", "input[aria-label='To recipients']")
    field.click()
    field.send_keys(to)
    field.send_keys(Keys.ENTER)
    time.sleep(0.5)
    driver.find_element("css selector", "input[name=subjectbox]").send_keys(subject)
    box = driver.find_element("css selector", "div[aria-label='Message Body']")
    box.click()
    box.send_keys(body)
    time.sleep(0.5)
    state = driver.execute_script(_GMAIL_COMPOSE_JS)
    print("GMAIL_COMPOSE: to=%r subject=%r send=%r" % (to, subject, state["send"]))
    if dry_run:
        _discard(driver)
        print("GMAIL_COMPOSE: dry_run - draft discarded, nothing sent")
        return False
    button = driver.execute_script("""
    return [...document.querySelectorAll('div[role=button]')]
      .find(e => /^Send/.test((e.getAttribute('aria-label') || '').trim())
                 && e.getBoundingClientRect().width > 0) || null;
    """)
    button.click()
    time.sleep(3)
    print("GMAIL_COMPOSE: %s" % (driver.execute_script("const a=document.querySelector('div[role=alert],span.bAq');"
                                                       "return a ? a.innerText.trim() : 'compose closed';")))
    return True
