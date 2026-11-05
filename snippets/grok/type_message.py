# Grok's composer is the visible div[contenteditable='true'], which common/type_verified.py already drives and
# verifies; the site file stays only so every chat site answers to the same verb.
from snippets.common.type_verified import type_verified


def type_in_composer(driver, msg, **kwargs):
    """Type msg into Grok's composer, verifying the read-back. True only when it matches exactly."""
    return type_verified(driver, msg, **kwargs)
