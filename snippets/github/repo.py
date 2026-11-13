# data-testid is stable, class names are CSS modules with a per-build hash — match the module prefix with
# [class*=...]. The description is p[class*="SidebarAbout-module"]; the tree is plain /tree/ and /blob/ links.
import os
import tempfile

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())


def github_open_repo(driver, slug, timeout=45):
    """Load a repo home page; return {name, desc, stars, forks, branch}."""
    site_tab(driver, "github.com")
    driver.get("https://github.com/" + slug.strip("/"))
    wait_js(driver,
            "!!document.querySelector('[data-testid=\"repo-name-link\"]')",
            timeout)
    info = github_read_repo_info(driver)
    print("REPO:", info["name"], "|", info["stars"], "stars |", info["forks"],
          "forks |", info["desc"][:80])
    return info


def github_read_repo_info(driver):
    """Current repo page as a dict."""
    js = """
    const t = s => { const e = document.querySelector(s); return e ? e.innerText.trim() : ''; };
    const num = s => { const m = t(s).match(/\\(([^)]+)\\)/); return m ? m[1] : t(s).replace(/^\\w+/, '').trim(); };
    const link = document.querySelector('[data-testid="repo-name-link"]');
    const d = document.querySelector('p[class*="SidebarAbout-module"]');
    return {name: link ? link.innerText.trim() : '',
            desc: d ? d.innerText.trim() : '',
            stars: num('[data-testid="star-button"]'),
            forks: num('[data-testid="fork-button"]')};
    """
    return driver.execute_script(js)


def github_read_readme(driver, out_path=None, limit=6000):
    """Save the rendered README (article.markdown-body) to out_path (default: the system temp dir)
    and print its head."""
    if not driver.execute_script(
            "return !!document.querySelector('article.markdown-body')"):
        print("NO README on this page")
        return ''
    text = driver.execute_script(
        "return document.querySelector('article.markdown-body').innerText")
    out_path = out_path or os.path.join(tempfile.gettempdir(),
                                        'github_readme.md')
    with open(out_path, "w") as f:
        f.write(text + "\n")
    print("README saved:", out_path, "(" + str(len(text)) + " chars)")
    print(text[:limit])
    return text


def github_list_tree(driver, limit=80):
    """Print the entry names in the root listing (dirs and files, deduped, order kept)."""
    seen = driver.execute_script("""
    const out = [], seen = new Set();
    document.querySelectorAll('a[href*="/tree/"], a[href*="/blob/"]').forEach(a => {
      const href = a.getAttribute('href');
      const name = href.split('/').slice(5).join('/');
      if (!name || seen.has(name)) return;
      seen.add(name);
      out.push((href.includes('/tree/') ? 'd ' : 'f ') + name);
    });
    return out;
    """)
    for s in seen[:limit]:
        print(s)
    return seen
