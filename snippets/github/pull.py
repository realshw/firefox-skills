# Reuses issues.py's github_read_thread(driver): PR pages still render the classic timeline while issues render React.
# /pull/N.diff 302s to a host without CORS, so the diff is read in a tab of its own (file.py).
import os
import re
import tempfile
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/github/file.py").read())
exec(open("snippets/github/issues.py").read())

_GITHUB_PULL_NUM = re.compile(r"/pull/(\d+)")


def _github_build_pull_url(url_or_num, slug):
    if str(url_or_num).startswith('http'):
        return url_or_num
    m = _GITHUB_PULL_NUM.search(str(url_or_num))
    num = m.group(1) if m else str(url_or_num)
    if not slug:
        raise ValueError("read_pull(driver, num) needs slug='owner/repo'")
    return "https://github.com/" + slug.strip("/") + "/pull/" + num


def github_read_pull(driver,
              url_or_num,
              slug=None,
              body_limit=6000,
              comment_limit=1200):
    """Print and return {title, state, body, comments, url} for a PR."""
    url = _github_build_pull_url(url_or_num, slug)
    site_tab(driver, "github.com")
    driver.get(url)
    d = github_read_thread(driver)
    print("PR:", d['title'][:90], "|", d['state'] or '-')
    print("BODY:", d['body'][:body_limit] or "(empty)")
    for c in d['comments']:
        print("---- @" + (c['author'] or '?') + ":",
              c['text'][:comment_limit].replace("\n", " "))
    print("COMMENTS", len(d['comments']), "|", url)
    d['url'] = url
    return d


def github_read_pull_diff(driver, url_or_num, slug=None, out_path=None):
    """Save the PR's unified diff to out_path (default: the system temp dir); print size + file count.
    Returns the text."""
    url = _github_build_pull_url(url_or_num, slug)
    text, ctype = _github_read_in_tab(driver, url.rstrip('/') + '.diff', settle=1.5)
    files = text.count("\ndiff --git ") + (1 if text.startswith("diff --git ")
                                           else 0)
    out_path = out_path or os.path.join(tempfile.gettempdir(), 'pr.diff')
    with open(out_path, "w") as f:
        f.write(text)
    print("DIFF:", out_path, "(" + str(len(text)) + " chars,", files, "files)")
    return text
