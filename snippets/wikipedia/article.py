# body innerText puts the TOC headings before the body, so a text search lands in the TOC —
# common/page_sections.py walks heading *elements*; section() here is Wikipedia's older signature over it.
from snippets.common.page_sections import section as _section


def section(driver, name, limit=3500):
    """Text of the named section, TOC-proof: the shared walker, cut at limit, no echo."""
    return _section(driver, name, limit=limit, show=False)[:limit]
