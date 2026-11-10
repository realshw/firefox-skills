# search(driver, term) returns /packages/<repo>/<arch>/<name>/ urls — the handle the rest of the file takes. The
# detail page is a Key:\tValue definition list (name/version are the h2, not lines) and dependencies sit
# under an h3 "Dependencies (58)" — section(driver, 'Dependencies') matches it by prefix.
import re

from snippets.common.page_sections import section
from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js


def search(driver, query, limit=10, timeout=30):
    """Print and return [{repo, arch, name, version, desc, updated, url}]."""
    site_tab(driver, "//archlinux.org/")
    driver.get("https://archlinux.org/packages/?q=" + query.replace(" ", "+"))
    wait_js(
        driver,
        '!!document.querySelector(\'a[href*="/x86_64/"], a[href*="/any/"]\')',
        timeout)
    rows = driver.execute_script("""
    return [...document.querySelectorAll('#pkglist-results tbody tr, table.results tbody tr')].map(r => {
      const tds = [...r.querySelectorAll('td')].map(td => td.innerText.trim());
      const a = r.querySelector('a[href*="/packages/"]');
      return {arch: tds[0] || '', repo: tds[1] || '', name: tds[2] || '', version: tds[3] || '',
              desc: tds[4] || '', updated: tds[5] || '', url: a ? 'https://archlinux.org' + a.getAttribute('href') : ''};
    }).filter(r => r.url);
    """)
    for r in rows[:limit]:
        print("%-9s %-8s %-28s %-12s %s" %
              (r['repo'], r['arch'], r['name'], r['version'], r['desc'][:60]))
    print("PACKAGES", len(rows))
    return rows


def info(driver,
         url_or_name,
         repo='extra',
         arch='x86_64',
         timeout=30,
         quiet=False):
    """Open a package page (full url, or name + repo/arch) and return its fields as a dict."""
    url = url_or_name if url_or_name.startswith("http") else \
        "https://archlinux.org/packages/%s/%s/%s/" % (repo, arch, url_or_name)
    site_tab(driver, "//archlinux.org/")
    driver.get(url)
    wait_js(driver, "document.body.innerText.indexOf('Architecture:') > 0",
            timeout)
    text = driver.execute_script("return document.body.innerText")
    title = driver.execute_script(
        "const h = document.querySelector('h2'); return h ? h.innerText.trim() : ''"
    )
    d = {'url': url}
    if " " in title:
        d['name'], _, d['version'] = title.partition(" ")
    for line in text.splitlines():
        if "\t" not in line:
            continue
        k, v = line.split("\t", 1)
        key = k.strip().rstrip(":").lower().replace(" ", "_").replace(
            "(", "").replace(")", "")
        if v.strip():
            d[key] = v.strip()
    if not quiet:
        print("%s %s | %s | %s" %
              (d.get('name', url_or_name), d.get('version', '?'),
               d.get('repository', ''), d.get('description', '')[:70]))
        print("sizes:", d.get('package_size', '?'), "/",
              d.get('installed_size', '?'), "| built",
              d.get('build_date', '?'), "| by", d.get('maintainers', '?'))
    return d


def depends(driver, url_or_name, repo='extra', arch='x86_64', limit=60):
    """Print the package's dependencies."""
    d = info(driver, url_or_name, repo, arch, quiet=True)
    print("DEPS for", d.get('name', url_or_name), d.get('version', ''))
    body = section(driver, 'Dependencies', limit=6000, show=False)
    deps = [
        l.strip() for l in body.splitlines()
        if l.strip() and not l.strip().startswith('Show More')
    ]  # the section's own expander
    for x in deps[:limit]:
        print("-", x)
    print("DEPENDS", len(deps))
    return deps
