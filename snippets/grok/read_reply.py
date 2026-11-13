# Completion: a visible button[aria-label~="Stop"] while generating, gone once done — pass that as js_done
# or a mid-stream pause passes as stable (the bubble is created empty on send). The reply text is
# div.response-content-markdown, not the outer "Worked for Xs" line.
import os
import tempfile

exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/common/wait_stable.py").read())

GROK_JS_COUNT = "return document.querySelectorAll('[data-testid=assistant-message]').length"
GROK_JS_TEXT = """
const ns = [...document.querySelectorAll('[data-testid=assistant-message] div.response-content-markdown')];
return ns.length ? ns[ns.length - 1].innerText : '';
"""
GROK_JS_DONE = """
const generating = [...document.querySelectorAll('button')].some(b => b.offsetParent && /stop/i.test(b.getAttribute('aria-label') || ''));
return !generating;
"""

GROK_REPLY_PATH = os.path.join(tempfile.gettempdir(), 'grok_reply.txt')


def grok_read_reply(driver):
    print("NUM_RESPONSES:", driver.execute_script(GROK_JS_COUNT))
    if not driver.execute_script(GROK_JS_DONE):
        print("GENERATING - waiting for the Stop button to clear")

    # Early exit: don't pay the stability wait on an empty chat — a real reply shows a container, some text or
    # a working Stop button within seconds.
    grace = 15
    pending = wait_js(driver,
                      "%s || %s || !%s" % (as_expr(GROK_JS_COUNT), as_expr(GROK_JS_TEXT), as_expr(GROK_JS_DONE)),
                      grace,
                      tick=1.5)

    if pending:
        text = wait_text_stable(driver,
                                GROK_JS_TEXT,
                                timeout=240,
                                tick=1.0,
                                stable_ticks=3,
                                label="REPLY",
                                js_done=GROK_JS_DONE)
    else:
        print("REPLY nothing to read (no reply appeared in %ds) - skipping stability wait" % grace)
        text = ""
    if text:
        open(GROK_REPLY_PATH, 'w', encoding='utf-8').write(text)
        print("SAVED: %s (%d chars)" % (GROK_REPLY_PATH, len(text)))
    else:
        print("NOTHING SAVED: no reply text")
