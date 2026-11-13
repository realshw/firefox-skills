# Waiting for a value to settle rather than for a condition to turn true: a streamed reply, a results grid the
# SPA keeps appending to. Poll and trust a value only once it has been unchanged for stable_ticks ticks —
# js_done is an optional JS predicate, and only ticks it passes count, so a pause mid-stream is not "stable".
# One poller underneath, so the text form (a JS statement with its own return) and the value form (an
# expression, like wait_js) cannot drift apart.
import time


def _poll_stable(read, timeout, tick, stable_ticks, done=None, label=None):
    """(value, settled): the last value read, and whether it had been unchanged long enough."""
    last = None
    stable = 0
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            value = read()
        except Exception as e:
            if label:
                print("WAIT_ERR:", type(e).__name__, str(e)[:120])
            value = None
        ok = True
        if done is not None:
            try:
                ok = bool(done())
            except Exception as e:
                if label:
                    print("WAIT_ERR(done):", type(e).__name__, str(e)[:120])
                ok = False
        if ok and value and value == last:
            stable += 1
            if stable >= stable_ticks:
                return value, True
        else:
            stable = 0
        last = value
        time.sleep(tick)
    return last, False


def wait_js_stable(driver, expr, timeout=30, tick=1.0, stable_ticks=2, js_done=None):
    """Return the expression's value once unchanged for stable_ticks ticks, else the last value seen."""
    done = None if js_done is None else (lambda: driver.execute_script("return (%s);" % js_done))
    value, _ = _poll_stable(lambda: driver.execute_script("return (%s);" % expr), timeout, tick, stable_ticks, done)
    return value


def wait_text_stable(driver, js_text, timeout=90, tick=1.5, stable_ticks=2, label="text", js_done=None):
    """wait_js_stable for a statement that returns the text; prints the settle line or the timeout."""
    t0 = time.time()
    done = None if js_done is None else (lambda: driver.execute_script(js_done))
    text, settled = _poll_stable(lambda: driver.execute_script(js_text), timeout, tick, stable_ticks, done, label)
    if settled:
        print("%s STABLE after %.1fs" % (label, time.time() - t0))
        return text
    print("%s TIMEOUT after %.1fs - returning last seen" % (label, timeout))
    return text or ""
