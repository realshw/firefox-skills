# type_verified(driver) verifies against the page, not against send_keys: an observer counts
# beforeinput/input/compositionend, a short chunk is retyped from the missing tail only, and the normalized
# read-back (never .value on a contenteditable, which has none; never .text on a textarea, which is empty) is
# the proof. Long text is pasted first — async, so confirm activeElement and poll the read-back — with chunked
# keys as the fallback. selector picks the field: contenteditable by default, "textarea" for DeepSeek; Grok's
# composer drops fast keystrokes, so chunk=1, delay=(0.08, 0.08) types there one character at a time.
import random
import shutil
import subprocess
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

_JS_ATTACH = r"""
const el = arguments[0];
if (!window.__inputObs || !window.__inputObs.alive) {
  window.__inputObs = {
    alive: true, received: 0, lastEvent: 0,
    attach(t) {
      if (!t || t === this._el) return;
      this.detach();
      this._el = t;
      this._h = () => { this.received++; this.lastEvent = Date.now(); };
      for (const ev of ['beforeinput', 'input', 'compositionend'])
        t.addEventListener(ev, this._h, true);
    },
    detach() {
      if (this._el && this._h)
        for (const ev of ['beforeinput', 'input', 'compositionend'])
          this._el.removeEventListener(ev, this._h, true);
      this._el = null;
    }
  };
}
window.__inputObs.attach(el);
return window.__inputObs.received;
"""

_JS_CARET_END = r"""
const el = arguments[0];
el.focus();
if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
  el.setSelectionRange(el.value.length, el.value.length);
  return true;
}
const r = document.createRange();
r.selectNodeContents(el);
r.collapse(false);
const s = window.getSelection();
s.removeAllRanges();
s.addRange(r);
return true;
"""

_JS_CLEAR = r"""
const el = arguments[0];
el.focus();
if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
  el.value = '';
  return 0;
}
const r = document.createRange();
r.selectNodeContents(el);
const s = window.getSelection();
s.removeAllRanges();
s.addRange(r);
document.execCommand('delete');
return (el.innerText || '').length;
"""

_JS_RECEIVED = "return window.__inputObs ? window.__inputObs.received : -1"


def composer(driver, selector=None, timeout=20):
    """The visible field to type into: contenteditable, or whatever selector the site needs.

    The field mounts a beat after readyState, so wait for it rather than failing a load in progress."""
    sel = selector or "[contenteditable='true']"
    end = time.time() + timeout
    while time.time() < end:
        els = [
            e for e in driver.find_elements("css selector", sel)
            if e.is_displayed()
        ]
        if els:
            return els[0]
        time.sleep(0.3)
    raise RuntimeError("no visible composer matching %s" % sel)


def _norm(s):
    return s.replace("\u00a0", " ").replace("\u200b", "").strip()


def _read(el):
    """Read a field back in the property that actually holds its text."""
    if el.tag_name in ("textarea", "input"):
        return _norm(el.get_attribute("value") or "")
    return _norm(el.text)


def _focus(driver, el):
    """Click the editor and prove it holds focus — a Ctrl+V into a lost focus lands nowhere."""
    for _ in range(2):
        el.click()
        time.sleep(0.3)
        if driver.execute_script(
                "return document.activeElement === arguments[0]", el):
            return True
    print("FOCUS: composer never took focus")
    return False


def _paste(driver, text):
    """Put text on the X clipboard and Ctrl+V it into the focused editor. False when there is no xclip, or no
    display for it to reach — the chunked-keys path is slower but always available."""
    if not shutil.which("xclip"):
        print("PASTE: no xclip - typing instead")
        return False
    try:
        subprocess.run(["xclip", "-selection", "clipboard"],
                       input=text.encode(),
                       check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        print("PASTE: xclip failed (%s) - typing instead" % type(e).__name__)
        return False
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("v").key_up(
        Keys.CONTROL).perform()
    print("PASTED: %d chars" % len(text))
    return True


def _VERIFIED_SETTLE(el, target, timeout=2.0, tick=0.1):
    """Pasting fires before the editor writes the text: poll instead of reading on the next line."""
    t0 = time.time()
    typed = _read(el)
    while time.time() - t0 < timeout and typed != target:
        time.sleep(tick)
        typed = _read(el)
    return typed


def type_verified(driver,
                  msg,
                  selector=None,
                  chunk=24,
                  delay=(0.06, 0.14),
                  tries=3,
                  paste_over=80):
    """Type msg (paste first when long), verifying the read-back; True only when it matches exactly."""
    el = composer(driver, selector)
    base = driver.execute_script(_JS_ATTACH, el)
    target = _norm(msg)
    if len(target) >= paste_over and _focus(driver, el) and _paste(
            driver, target):
        typed = _VERIFIED_SETTLE(el, target)
        print("SETTLE: read back %d/%d chars" % (len(typed), len(target)))
    for attempt in range(tries):
        typed = _read(el)
        if typed == target:
            break
        if typed and not target.startswith(typed):
            if attempt == 0:
                print("DRIFT: editor rewrote the paste (%r) - clearing it" %
                      typed[:40])
                print("CLEARED:", driver.execute_script(_JS_CLEAR, el))
                continue
            raise RuntimeError("composer drifted off the message: %r" %
                               typed[:60])
        driver.execute_script(_JS_CARET_END, el)
        rest = target[len(typed):]
        for i in range(0, len(rest), chunk):
            el.send_keys(rest[i:i + chunk])
            time.sleep(random.uniform(*delay))
    typed = _read(el)
    ok = typed == target
    print("VERIFIED_TYPED: %s | chars: %d/%d | input events: %d" %
          (ok, len(typed), len(target),
           driver.execute_script(_JS_RECEIVED) - base))
    return ok
