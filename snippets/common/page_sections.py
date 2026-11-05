# outline(driver) / section(driver) / find(driver) / count(driver) for long official documents. Headings are walked as *elements*,
# never by text offset (the TOC repeats every heading verbatim), the walk climbs out of heading-only
# wrappers (MediaWiki div.mw-heading), and a section includes its subsections.
import re


def page_text(driver, out_path=None):
    """innerText of the current page, optionally cached to out_path."""
    t = driver.execute_script("return document.body.innerText")
    if out_path:
        with open(out_path, "w") as f:
            f.write(t)
        print("SAVED:", out_path, "(" + str(len(t)) + " chars)")
    return t


def headings(driver, tags=("h1", "h2", "h3", "h4")):
    """Every heading on the page as [(tag, text)] in document order."""
    js = ("return [...document.querySelectorAll('" + ",".join(tags) + "')]"
          ".map(h => [h.tagName, h.innerText.trim()]).filter(x => x[1])")
    return driver.execute_script(js)


def outline(driver, tags=("h2", "h3")):
    """Print the heading skeleton — cheap way to decide what to pull before pulling it."""
    hs = headings(driver, tags)
    for tag, text in hs:
        print(tag.lower(), text)
    print("HEADINGS", len(hs))
    return hs


_SECTION_JS = """
const name = arguments[0].trim().toLowerCase();
const hs = [...document.querySelectorAll('h1,h2,h3,h4')];
const t = h => h.innerText.trim();
const target = hs.find(h => t(h) === arguments[0].trim())
            || hs.find(h => t(h).toLowerCase() === name)
            || hs.find(h => t(h).toLowerCase().includes(name));
if (!target) return null;
const isH = e => /^H[1-4]$/.test(e.tagName);
const isEdit = e => /mw-editsection/.test(typeof e.className === 'string' ? e.className : '');
let start = target;   // climb out of a heading-only wrapper (MediaWiki's div.mw-heading)
while (start.parentElement && start.parentElement !== document.body) {
  const p = start.parentElement;
  if ([...p.children].every(c => c === start || isEdit(c))) start = p; else break;
}
const lvl = parseInt(target.tagName[1], 10);
let out = [], cur = start.nextElementSibling;
while (cur) {
  const h = isH(cur) ? cur : cur.querySelector('h1,h2,h3,h4');
  if (h && parseInt(h.tagName[1], 10) <= lvl) break;   // next same-or-higher heading
  out.push(cur.innerText.trim());
  cur = cur.nextElementSibling;
}
return out.join('\\n').trim();
"""


def section(driver, name, limit=2000, show=True):
    """Text of one section by heading text; falls back to text slicing (last hit — TOC comes first)."""
    body = driver.execute_script(_SECTION_JS, name)
    if body is None:
        t = page_text(driver)
        i = t.rfind("\n" + name + "\n")
        if i < 0:
            print("NO_SECTION:", name)
            return ''
        body = t[i:i + limit].strip()
    if show:
        print("## " + name)
        print(body[:limit])
    return body


def find(driver, term, context=200, limit=12, pattern=None, text=None):
    """Print the snippets around each hit of term; pattern, if given, replaces term as the regex, and
    text, if given, replaces the page read (callers that already hold the settled text pass it)."""
    t = page_text(driver) if text is None else text
    hits = [m.start() for m in re.finditer(pattern or re.escape(term), t)]
    for h in hits[:limit]:
        print(">>", t[max(0, h - context):h + context].replace("\n", " "))
    return len(hits)


def count(driver, *terms):
    """How many times each term occurs on the page — a crude but handy emphasis gauge."""
    t = page_text(driver).lower()
    for term in terms:
        print("%-14s x%d" % (term, t.count(term.lower())))
