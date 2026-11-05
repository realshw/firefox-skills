# One poll loop for the whole skill: send JS, stop at the first truthy answer; a raised exception means
# "not yet", never a failure — the deadline decides. Pass a timeout when the site is slower than 25 s.
import time


def wait_js(driver, expr, timeout=25, tick=0.5):
    """True as soon as the JS expression evaluates truthy, False once timeout seconds pass."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if driver.execute_script("return (%s);" % expr):
                return True
        except Exception:
            pass
        time.sleep(tick)
    return False


def as_expr(js):
    """Wrap a JS block that ends in `return` so wait_js can take it as the expression it wants."""
    return "(function(){%s})()" % js
