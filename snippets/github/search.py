# Every result kind is rows under [data-testid="results-list"], whose first child can be a banner — filter
# rows by name. Code hits carry [data-testid="link-to-search-result"]; other rows hold ordinary links.
# Code search needs the signed-in account; q rides in one percent-encoded string — free text and
# qualifiers together: "webdriver.Firefox language:Python".
import re
from urllib.parse import quote

from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js

_KINDS = ('repositories', 'code', 'issues', 'pullrequests', 'users',
          'discussions')

_ROWS_JS = """
const list = document.querySelector('[data-testid="results-list"]');
if (!list) return [];
const rows = [...list.children].filter(el => !/InfoBar/i.test(typeof el.className === 'string' ? el.className : ''));
return rows.map(r => {
  const a = r.querySelector('a[data-testid="link-to-search-result"]');
  return {text: r.innerText.trim(),
          href: a ? a.getAttribute('href') : '',
          hrefs: [...r.querySelectorAll('a[href]')].map(x => x.getAttribute('href')),
          anchors: [...r.querySelectorAll('a[href]')].map(x => ({href: x.getAttribute('href'), text: x.innerText.trim()}))};
});
"""


def github_goto_search(driver, query, kind='repositories', timeout=45):
    """Load a search results page and wait for the result list to mount. Returns the url."""
    if kind not in _KINDS:
        raise ValueError("kind must be one of " + ", ".join(_KINDS))
    url = "https://github.com/search?q=" + quote(query) + "&type=" + kind
    site_tab(driver, "github.com")
    driver.get(url)
    wait_js(driver,
            "!!document.querySelector('[data-testid=\"results-list\"]')",
            timeout)
    print("SEARCH:", kind, "|", (driver.title or '')[:70])
    return url


def _abs(href):
    if not href:
        return ''
    return href if href.startswith('http') else "https://github.com" + href


def github_search(driver, query, kind='repositories', limit=10, timeout=45):
    """Print and return [{title, url, extra}] for a GitHub search; kind see _KINDS."""
    github_goto_search(driver, query, kind, timeout=timeout)
    rows = driver.execute_script(_ROWS_JS)
    out, seen = [], set()
    for r in rows or []:
        text, href = r['text'], r['href']
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            continue
        if kind == 'code':
            m = re.match(r"([\w.-]+/[\w.-]+)\s*·\s*(.+)$", lines[0])
            repo, path = (m.group(1), m.group(2)) if m else ('', lines[0])
            url = _abs(href)
            title, extra = repo + "/" + path, " ".join(lines[1:])[:300]
        elif kind in ('issues', 'pullrequests'):
            hit = next((a for a in r['anchors']
                        if re.search(r"/(issues|pull)/\d+", a['href'] or '')),
                       None)
            url = _abs(hit['href']) if hit else ''
            # an issue row's first line is the repo name; the title is the anchor's own text
            title = (hit['text'] if hit and hit['text'] else
                     (lines[1] if len(lines) > 1 else lines[0]))
            extra = " ".join(lines[1:])[:200]
            if extra.startswith(title):
                extra = extra[len(title):].strip(
                )  # the row repeats the title before the snippet
        else:
            name = lines[0]
            if not re.match(r"^[\w.-]+/[\w.-]+$", name):
                name = next((h.strip('/') for h in r['hrefs']
                             if re.match(r"^/[\w.-]+/[\w.-]+$", h or '')),
                            lines[0])
            url = _abs("/" + name.strip('/'))
            title, extra = name, " ".join(lines[1:])[:200]
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({'title': title, 'url': url, 'extra': extra})
    for r in out[:limit]:
        print("-", r['title'], "|", r['extra'][:120] if r['extra'] else '',
              "|", r['url'])
    print("RESULTS", len(out))
    return out
