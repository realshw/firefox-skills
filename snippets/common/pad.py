# '%-14s' counts characters; a terminal counts columns, and a CJK character is two of them, so every
# Chinese folder title in a printed table drifts one column right per character. Pad by display width.

import unicodedata


def width(text):
    """Display columns taken by text, CJK and fullwidth counted as two."""
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in str(text))


def pad(text, columns, align='<'):
    """text widened to `columns` display columns — trailing or leading spaces, never truncation."""
    fill = ' ' * max(0, columns - width(text))
    return (str(text) + fill) if align == '<' else (fill + str(text))
