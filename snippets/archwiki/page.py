# Titles are /title/With_Underscores (spaces normalize). Read .mw-parser-output through
# common/page_sections.py; MediaWiki wraps headings in div.mw-heading so [edit] never leaks into the h2.
# What the wiki adds: <pre> blocks with real commands (archwiki_read_code_blocks(driver))
# and warning/note templates (archwiki_read_notes(driver)).
from urllib.parse import quote

exec(open("snippets/common/page_sections.py").read())
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())


def archwiki_open_page(driver, title, timeout=30):
    """Load an article by title (spaces or underscores); returns the page text."""
    site_tab(driver, "//wiki.archlinux.org/")
    driver.get("https://wiki.archlinux.org/title/" + quote(title.strip().replace(" ", "_"), safe="_()/:.-"))
    wait_js(driver, "!!document.querySelector('.mw-parser-output')", timeout)
    print("ARCHWIKI:", driver.title.replace("\n", " ")[:80])
    return page_text(driver)


def archwiki_read_code_blocks(driver, limit=30, pattern=None, show=True):
    """Commands from the article's <pre> blocks; pattern filters with a JS regex string."""
    blocks = driver.execute_script(
        "return [...document.querySelectorAll('.mw-parser-output pre')].map(e => e.innerText.trim())")
    if pattern:
        blocks = [
            b for b in blocks if driver.execute_script("return new RegExp(arguments[0]).test(arguments[1])", pattern, b)
        ]
    if show:
        for b in blocks[:limit]:
            print("```")
            print(b)
            print("```")
    print("CODE_BLOCKS", len(blocks))
    return blocks


def archwiki_read_notes(driver, kind=None, show=True):
    """Warning / note / tip boxes (kind filters on the template class, e.g. 'warning')."""
    sel = '[class*="archwiki-template-box"]'
    boxes = driver.execute_script("""
    return [...document.querySelectorAll('%s')].map(e => ({cls: (typeof e.className === 'string' ? e.className : ''),
                                                          text: e.innerText.trim()}));
    """ % sel)
    if kind:
        boxes = [b for b in boxes if kind.lower() in b['cls'].lower()]
    if show:
        for b in boxes:
            print("[box]", b['text'][:400].replace("\n", " "))
    print("BOXES", len(boxes))
    return boxes
