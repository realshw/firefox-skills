# The gear is button[aria-label="Edit repository metadata"]; once open the backdrop covers it, so check for
# the backdrop before clicking. The description is an input with a random React id — identify it by its
# placeholder and set it through the native value setter + an input event; checkboxes flip via their label.
# Save only closes the dialog on a server ack — the backdrop vanishing is the confirmation.
import time
from selenium.webdriver.common.by import By

exec(open("snippets/common/wait_js.py").read())

_GITHUB_BACKDROP = "[class*=Dialog-Backdrop]"
_GITHUB_DESC = 'input[placeholder="Short description of this repository"], input[maxlength="350"]'

_GITHUB_STATE_JS = """
const out = {desc: null, sections: {}};
const d = document.querySelector('p[class*=SidebarAbout-module]');
out.desc = d ? d.innerText.trim() : null;
for (const c of document.querySelectorAll('[class*=Dialog] input[type=checkbox]')) {
  const l = c.closest('label') || document.querySelector('label[for="' + c.id + '"]');
  const name = l ? l.innerText.trim() : c.id;
  out.sections[name] = c.checked;
}
return out;
"""


def _github_open_dialog(driver, timeout=15):
    if driver.execute_script("return !!document.querySelector(%r)" %
                             _GITHUB_BACKDROP):
        return
    gear = [
        b for b in driver.find_elements(By.CSS_SELECTOR, "button")
        if (b.get_attribute("aria-label") or "") == "Edit repository metadata"
        and b.is_displayed()
    ]
    if not gear:
        raise RuntimeError("no About gear — logged out?")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})",
                          gear[0])
    time.sleep(0.5)
    gear[0].click()
    if not wait_js(driver, "!!document.querySelector(%r)" % _GITHUB_BACKDROP,
                   timeout):
        raise RuntimeError("about dialog did not open")


def _github_set_desc(driver, text):
    got = driver.execute_script(
        """
    const box = document.querySelector(arguments[1]);
    if (!box) return null;
    const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
    box.focus();
    set.call(box, arguments[0]);
    for (const t of ["input", "change"]) box.dispatchEvent(new Event(t, {bubbles: true}));
    return box.value;
    """, text, _GITHUB_DESC)
    if got != text:
        raise RuntimeError("description field did not take the text: %r" %
                           (got))


def _github_set_sections(driver, wanted):
    """wanted: {'Releases': False, ...} — click only the labels whose state differs."""
    for name, want in wanted.items():
        state = driver.execute_script(
            """
        const l = [...document.querySelectorAll('[class*=Dialog] label')]
                    .find(e => e.innerText.trim() === arguments[0]);
        if (!l) return null;
        const c = l.querySelector('input[type=checkbox]') || document.getElementById(l.htmlFor);
        if (c.checked === arguments[1]) return c.checked;
        l.click();
        return c.checked;
        """, name, bool(want))
        if state is None:
            raise RuntimeError("no checkbox labelled %r" % (name))
        if state != bool(want):
            raise RuntimeError("checkbox %r did not flip, still %r" %
                               (name, state))


def github_edit_about(driver, new_desc=None, sections=None, timeout=20):
    """Rewrite the About description and/or home-page sections; return (before, after)."""
    _github_open_dialog(driver)
    before = driver.execute_script(_GITHUB_STATE_JS)
    if new_desc is not None:
        _github_set_desc(driver, new_desc)
    if sections:
        _github_set_sections(driver, sections)
    time.sleep(0.5)
    save = [
        b for b in driver.find_elements(By.CSS_SELECTOR, "button")
        if b.is_displayed() and b.text.strip() == "Save changes"
    ]
    if not save:
        raise RuntimeError("Save changes button not found")
    save[-1].click()
    if not wait_js(driver, "!document.querySelector(%r)" % _GITHUB_BACKDROP, timeout):
        raise RuntimeError(
            "dialog stayed open after Save — check the console for a failed request"
        )
    time.sleep(1)
    after = driver.execute_script(_GITHUB_STATE_JS)
    print("ABOUT:", repr(before), "->", repr(after))
    return before, after
