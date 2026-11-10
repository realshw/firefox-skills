# GitLab raw URLs on archlinux.org sit behind an Anubis proof-of-work interstitial ("Making sure you're
# not a bot!"). driver.get() can time out while the challenge is still being solved, and the bot page is
# text/html, so wait for the title to lose "bot" before trusting the body. The tab stays on the fetched
# file, the way github's file.py leaves it.
import os

from selenium.common.exceptions import TimeoutException
from snippets.common.site_tab import site_tab
from snippets.common.wait_js import wait_js

BOT = "not a bot"


def raw_url(project, path, ref="main", host="gitlab.archlinux.org"):
    """https://<host>/<group>/<project>/-/raw/<ref>/<path> — the only form that serves text/plain."""
    return "https://%s/%s/-/raw/%s/%s" % (host, project.strip("/"), ref,
                                          path.lstrip("/"))


def _settle(driver, timeout=90):
    """True once the Anubis interstitial is gone and the document has finished loading."""
    return wait_js(
        driver,
        "document.title.indexOf(%r) === -1 && document.readyState === "
        "'complete'" % BOT,
        timeout,
        tick=1)


def read_file(driver,
              project,
              path,
              ref="main",
              out_path=None,
              host="gitlab.archlinux.org",
              preview=0):
    """Load one repo file in a tab; return its text, optionally writing it to out_path."""
    url = raw_url(project, path, ref, host)
    site_tab(driver, host)
    try:
        driver.get(url)
    except TimeoutException:
        pass  # the challenge keeps the load open; _settle is what decides
    if not _settle(driver):
        print("NO_FILE:", url, "-> still on the challenge page")
        return ""
    body = driver.find_element("tag name", "body")
    text = body.text
    ctype = driver.execute_script("return document.contentType || ''")
    if ctype and not ctype.startswith("text/plain"):
        print("NO_FILE:", url, "->", ctype,
              "not text/plain (wrong path or ref?)")
        return ""
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            f.write(text + "\n")
        print("SAVED:", out_path)
    print("FILE:",
          project.strip("/") + "/" + path + " @" + ref, "->", len(text),
          "chars", "(" + (ctype or "?") + ")")
    if preview:
        print(text[:preview])
    return text
