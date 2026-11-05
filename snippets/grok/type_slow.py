# Grok drops fast keystrokes, so this is type_verified one character at a time: same read-back proof, the
# verify-and-retype loop still catches whatever the page swallowed.
from snippets.common.type_verified import type_verified


def type_slow(driver, msg, delay=0.08):
    """Type msg char by char into Grok's composer, verifying the read-back. True when it matches."""
    return type_verified(driver, msg, chunk=1, delay=(delay, delay))
