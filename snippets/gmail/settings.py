"""Read, compare and change one Gmail account's settings panels, so two accounts can be made alike."""

import time

exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/common/site_tab.py").read())

GMAIL_PANELS = [
    "general", "labels", "inbox", "accounts", "filters", "fwdandpop", "addons", "chat", "advanced", "offline"
]

# The phrase only the named panel carries, to wait on after the reload. Waiting for "a control" is not enough:
# the inbox behind the panel has selects and checkboxes of its own, so that wait passed while the panel was
# still empty and the save button missing.
GMAIL_PANEL_MARKERS = {
    "general": "Undo Send",
    "labels": "System labels",
    "inbox": "Inbox type",
    "accounts": "Send mail as",
    "filters": "Filters",
    "fwdandpop": "POP download",
    "addons": "Add-ons",
    "chat": "Chat and Meet",
    "advanced": "Advanced",
    "offline": "Offline",
}

# Every value each panel's controls hold, keyed for a diff. The row text is the only stable name: Gmail names
# its inputs after a base64 id that differs per account and per session, and leaves the notification-sound
# <select> with no name at all.
_CONTROLS_JS = r"""
var out = [];
document.querySelectorAll('input[type=checkbox],input[type=radio],select').forEach(function(el){
  var tr = el.closest('tr');
  var lab = tr ? tr.innerText.replace(/\s+/g,' ').trim().slice(0,95) : '';
  if (el.type === 'select-one') {
    out.push('SELECT | '+lab+' | '+(el.options[el.selectedIndex]?el.options[el.selectedIndex].text:'?'));
  } else if (el.type === 'checkbox') {
    out.push('CHECK | '+lab+' | '+el.checked);
  } else if (el.checked) {
    out.push('RADIO | '+lab);
  }
});
return out.join('\n');
"""


def gmail_settings_panel(driver, index, panel, timeout=40):
    """Open one settings panel of account `index` (u/0, u/1, ...) and wait until its controls render.

    The panel only changes when the document is reloaded: Gmail's router keeps the old panel on a bare
    #settings/<panel> hash change, so the page is refreshed after the goto, and the wait is on a phrase only
    that panel carries rather than on "a control" — the inbox behind the panel already has controls while the
    panel is still empty. It navigates whichever Gmail tab the session is on, so switch to a tab set aside
    for the job first: on a browser holding two accounts, that tab decides which account is being read.
    """
    site_tab(driver, "mail.google.com")
    driver.get("https://mail.google.com/mail/u/%d/#settings/%s" % (index, panel))
    driver.refresh()
    ok = gmail_settings_marker_wait(driver, panel, timeout)
    time.sleep(1.5)  # the rows below the marker paint with it, the bottom of the panel last
    return ok


def gmail_settings_dump(driver):
    """Every control's state on the open panel, one line each: kind, its row's text, and the value set.

    Radios report only the one that is checked, so the lines of a radio group collapse to a single line and
    two accounts on the same option diff clean.
    """
    return driver.execute_script(_CONTROLS_JS).splitlines()


def gmail_settings_marker_wait(driver, panel, timeout=40):
    """Wait for the open panel's marker phrase alone; True once it is on the page.

    Split out of gmail_settings_panel for the caller that re-reads a panel it has already navigated to: it
    must not re-navigate, but it still cannot read the rows before they paint.
    """
    marker = GMAIL_PANEL_MARKERS.get(panel, "Save Changes")
    return wait_js(driver, "document.body.innerText.indexOf(%r) >= 0" % marker, timeout)


def gmail_settings_compare(driver, indices, panels=None):
    """Diff the settings of accounts `indices` panel by panel; {(reference, other, panel): [lines differing]}.

    The first index is the reference. Lines are diffed as written by gmail_settings_dump(), so an account
    address inside a label ("Show this address only (someone@gmail.com)") shows up as a difference even
    when both accounts hold the same option — read those by their option, not by their address. Panels with
    nothing to compare stay out of the result, so an empty dict is the answer for two accounts that match.
    """
    import difflib
    panels = panels or GMAIL_PANELS
    dumps = {}
    for i in indices:
        for panel in panels:
            gmail_settings_panel(driver, i, panel)
            dumps[(i, panel)] = gmail_settings_dump(driver)
    out = {}
    ref = indices[0]
    for panel in panels:
        for i in indices[1:]:
            diff = difflib.unified_diff(dumps[(ref, panel)], dumps[(i, panel)], lineterm="", n=0)
            lines = [l for l in diff if l[0] in "+-" and not l.startswith(("---", "+++"))]
            if lines:
                out[(ref, i, panel)] = lines
    return out


def gmail_pick_radio(driver, name, label_text):
    """Tick the radio named `name` whose visible label reads `label_text`; True once it is the checked one.

    Gmail hides the input and paints its own, but every option ships a real <label for=...>, and clicking
    that label is what the browser's radio selection listens to — setting .checked from JS leaves Gmail's
    own state untouched, so the save button posts the old value.
    """
    js = r"""
    var want = arguments[0], name = arguments[1], done = false;
    document.querySelectorAll('input[type=radio][name="'+name+'"]').forEach(function(el){
      var lab = el.id ? document.querySelector('label[for="'+el.id+'"]') : null;
      if (!lab && el.parentElement) lab = el.parentElement.querySelector('label');
      if (lab && lab.innerText.replace(/\s+/g,' ').trim() === want) { lab.click(); done = true; }
    });
    return done;
    """
    if not driver.execute_script(js, label_text, name):
        print("SETTINGS: no radio %r under %r" % (label_text, name))
        return False
    return wait_js(driver, "!!document.querySelector('input[name=\"%s\"]:checked')" % name, 10)


def gmail_pick_sound(driver, option_text):
    """Set the desktop-notification sound by its option text; True once the select shows it.

    That select carries neither name nor id, so it is found by the one option only it has ("Nudge") — and it
    is the change event, not the value, that tells Gmail the setting was touched.
    """
    js = r"""
    var want = arguments[0];
    var sel = null;
    document.querySelectorAll('select').forEach(function(s){
      if (s.textContent.indexOf('Nudge') >= 0) sel = s;
    });
    if (!sel) return false;
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].text === want) {
        sel.selectedIndex = i;
        sel.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
      }
    }
    return false;
    """
    if not driver.execute_script(js, option_text):
        print("SETTINGS: cannot select sound %r" % option_text)
        return False
    return wait_js(driver, ("(function(){var s=null;document.querySelectorAll('select').forEach(function(x){"
                            "if(x.textContent.indexOf('Nudge')>=0)s=x;});"
                            "return s && s.options[s.selectedIndex].text === %r;})()") % option_text, 10)


def gmail_save_settings(driver, timeout=30):
    """Click the panel's Save Changes and wait for Gmail to finish; True when the button is no longer busy.

    The button reads "Save Changes" until pressed, then the panel re-renders and a snackbar reports the save,
    so the wait is for the snackbar rather than for a fixed pause - a slow save that is read back too early
    looks like the change never landed.
    """
    btn = None
    for b in driver.find_elements("xpath", "//button[contains(., 'Save Changes')]"):
        if b.is_displayed():
            btn = b
            break
    if btn is None:
        print("SETTINGS: no Save Changes button on this panel")
        return False
    btn.click()
    return wait_js(driver, "!!document.querySelector('.bAq, .J-M.aT5, [role=alert], .vh')", timeout)
