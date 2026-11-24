"""Unsubscribe an address from a lists.debian.org mailing list through the list's web form."""

import time

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())

DEBIAN_LIST_URL = "https://lists.debian.org/%s/"

# The list page's one form: user_email + list + action=Subscribe|Unsubscribe, posted to /cgi-bin/subscribe.pl
DEBIAN_FORM_JS = """
const form = document.querySelector('form[action*="subscribe.pl"]');
return form ? form.outerHTML : '';
"""


def debian_unsubscribe(driver, list_name, address, dry_run=True):
    """Submit the unsubscribe form for `list_name`, and return the page Debian answers with.

    Debian takes the request as a *request* only: it mails a "CONFIRM <token>" message to `address`, and the
    subscription stands until that message is answered with the token in the subject — see
    https://www.debian.org/MailingLists/#subunsub. The site sits behind a proof-of-work cookie
    (pow_challenge/pow_nonce), so the form must be posted from this browser, not with a bare request.
    dry_run fills the address in and leaves the button alone.
    """
    site_tab(driver, "lists.debian.org")
    driver.get(DEBIAN_LIST_URL % list_name)
    wait_js(driver, "document.querySelector('input[name=user_email]') !== null")
    time.sleep(1)
    print("DEBIAN: form = %s" % (driver.execute_script(DEBIAN_FORM_JS)[:160].replace("\n", " ")))
    field = driver.find_element("css selector", "input[name=user_email]")
    field.clear()
    field.send_keys(address)
    if dry_run:
        print("DEBIAN: dry_run - would unsubscribe %s from %s" % (address, list_name))
        return ""
    button = driver.execute_script("""
    return [...document.querySelectorAll('input[type=submit]')].find(b => b.value === 'Unsubscribe');
    """)
    driver.execute_script("arguments[0].click()", button)
    wait_js(driver,
            "document.body.innerText.length>0 && !document.querySelector('form[action*=\"subscribe.pl\"]')",
            timeout=30)
    time.sleep(1)
    answer = driver.execute_script("return document.body.innerText.trim()")
    print("DEBIAN: %s | %s" % (driver.current_url, answer.splitlines()[0] if answer else ""))
    return answer
