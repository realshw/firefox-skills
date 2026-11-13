# Completion: while generating the composer's round button is a stop control, done flips it back to
# disabled + the send paper-plane — but the ~0.3 s submit spinner also reads disabled. Counting clean
# ticks to outlast that spinner cost ~3 s per read; instead the previous reply's exact text is vetoed for
# 5 s after the send stamp, so 2 ticks suffice. done + text growth were measured to coincide (max 1.3 s).
import json
import os
import tempfile
import time

exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/common/wait_stable.py").read())

DEEPSEEK_JS_COUNT = "return document.querySelectorAll('div.ds-assistant-message-main-content').length"
DEEPSEEK_JS_TEXT = """
const nodes = [...document.querySelectorAll('div.ds-assistant-message-main-content')];
const denylist = ['thinking', 'typing', 'cursor', 'toolbar', 'timestamp'];
const ok = nodes.filter(n =>
  !denylist.some(d => (n.className || '').toLowerCase().includes(d)) &&
  n.innerText && n.innerText.trim().length > 0
);
if (ok.length === 0) return '';
return ok[ok.length - 1].innerText;
"""

# The veto has to expire on its own: a read that starts while the answer is already complete would
# otherwise wait out the whole timeout for a text it is told to ignore.

DEEPSEEK_JS_DONE = """
const c = document.querySelector('div.ds-button--circle');
if (!c) return false;
const disabled = (c.className || '').toString().includes('ds-button--disabled');
return disabled && !c.querySelector('.ds-loading');
"""

DEEPSEEK_REPLY_PATH = os.path.join(tempfile.gettempdir(), 'deepseek_reply.txt')


def deepseek_read_reply(driver, since=0.0):
    """Read the last reply; `since` is the return value of deepseek_send_message() when one was just sent."""
    if time.time() - since < 5:
        prev = driver.execute_script(DEEPSEEK_JS_TEXT)
        if prev:
            DEEPSEEK_JS_TEXT = DEEPSEEK_JS_TEXT.replace(
                "if (ok.length === 0) return '';", "if (ok.length === 0) return '';\n"
                "if (Date.now() < %d && ok[ok.length - 1].innerText === %s) return '';" % (int(
                    (since + 5) * 1000), json.dumps(prev)))
            print("VETO: previous reply ignored for %ds after send" % max(0, round(since + 5 - time.time())))
    print("NUM_RESPONSES:", driver.execute_script(DEEPSEEK_JS_COUNT))

    if not driver.execute_script(DEEPSEEK_JS_DONE):
        print("GENERATING - waiting for the stop control to clear")

    # Early exit: don't pay the stability wait on an empty chat — a real reply shows a container, some text or
    # a control that is still working, the thinking phase included, within seconds.
    grace = 15
    pending = wait_js(driver,
                      "%s || %s || !%s" %
                      (as_expr(DEEPSEEK_JS_COUNT), as_expr(DEEPSEEK_JS_TEXT), as_expr(DEEPSEEK_JS_DONE)),
                      grace,
                      tick=1.5)

    if pending:
        text = wait_text_stable(driver,
                                DEEPSEEK_JS_TEXT,
                                timeout=240,
                                tick=0.3,
                                stable_ticks=2,
                                label="REPLY",
                                js_done=DEEPSEEK_JS_DONE)
    else:
        print("REPLY nothing to read (no reply appeared in %ds) - skipping stability wait" % grace)
        text = ""
    if text:
        open(DEEPSEEK_REPLY_PATH, 'w', encoding='utf-8').write(text)
        print("SAVED: %s (%d chars)" % (DEEPSEEK_REPLY_PATH, len(text)))
    else:
        print("NOTHING SAVED: no reply text")
