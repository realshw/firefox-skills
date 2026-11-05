# DeepSeek's composer is a <textarea>, not a contenteditable, so the read-back is .value and the caret is a
# selection range — both of which common/type_verified.py picks by tag name once it is told the selector.
from snippets.common.type_verified import type_verified


def type_in_composer(driver, msg, **kwargs):
    """Type msg into DeepSeek's textarea, verifying the read-back. True only when it matches exactly."""
    return type_verified(driver, msg, selector="textarea", **kwargs)
