"""Read the official WeChat for Linux download page and its release notes."""

import re

from selenium.webdriver.common.by import By

WEIXIN_LINUX_URL = "https://linux.weixin.qq.com/"
WEIXIN_LINUX_NOTES_URL = "https://weixin.qq.com/updates/linux/%s"
WEIXIN_LINUX_CDN = "dldir1v6.qq.com/weixin/Universal/Linux/"


def _weixin_open(driver, url, timeout=25):
    """Load `url` with site_tab/goto when those snippets are loaded, else plain, and wait for text."""
    if "site_tab" in globals() and "goto" in globals():
        site_tab(driver, "weixin.qq.com")
        goto(driver, url)
    else:
        driver.get(url)
    if "wait_js" in globals():
        wait_js(driver, "document.body && document.body.innerText.length > 200", timeout=timeout)
    return driver.current_url


def weixin_open_linux_page(driver):
    """Load linux.weixin.qq.com and return the version the page advertises (e.g. "4.1.13").

    That string is the release series, not the build: the packages behind it carry a fourth field
    (4.1.13.29 in the deb's control), and the page never shows it. The page mounts before its links do, so
    the wait is on a[href*=WeChatLinux], not on body text — the version node lands first and would let a
    caller read a page that has no package urls yet.
    """
    _weixin_open(driver, WEIXIN_LINUX_URL)
    if "wait_js" in globals():
        wait_js(driver, "document.querySelectorAll('a[href*=\"WeChatLinux\"]').length >= 5", timeout=25)
    return driver.find_element(By.CSS_SELECTOR, ".main-section__bd-version").text.strip()


def weixin_download_packages(driver):
    """The official package links on the page as [{arch, format, url}], one per file.

    Architecture comes from the file name (x86_64 / arm64 / LoongArch), never from the section heading —
    the headings are localized ("X86 版" vs "X86") and their leaves are icon nodes. Format is the
    extension: deb, rpm, AppImage. LoongArch ships a .deb only, so no LoongArch rpm/AppImage row exists.
    The urls are versionless — the CDN path overwrites one file per arch+format, so an older build can only
    come from a third-party archive, not from this page.
    """
    rows = driver.execute_script("""
    return [...document.querySelectorAll('a[href*="WeChatLinux"]')].map(a => a.href);
    """)
    out = []
    for url in rows:
        name = url.rsplit("/", 1)[-1]
        arch = re.sub(r"^WeChatLinux_|\.(deb|rpm|AppImage)$", "", name)
        fmt = name.rsplit(".", 1)[-1]
        out.append({"arch": arch, "format": fmt, "url": url})
    return out


def weixin_release_notes(driver, version):
    """Read the official release-notes page for `version` as {version, date, notes}, or None when 404.

    The url drops the dots ("4.1.13" -> /updates/linux/4113), which is the only way in: the platform log at
    /updates?platform=linux lists each version as a link-less div, so the href has to be built here. Only the
    versions that log shows have a page — the Linux list stops at 4.1.0, 4.1.1 and 4.1.13 — and every other
    build number answers 404 with a redirect to the weixin.qq.com homepage, whose own news list also says
    "全新发布". So the None test is the url plus the version in the heading, never that phrase alone.
    """
    digits = version.replace(".", "")
    url = WEIXIN_LINUX_NOTES_URL % digits
    _weixin_open(driver, url)
    body = driver.find_element(By.TAG_NAME, "body").text
    if "/updates/linux/" not in driver.current_url:
        return None
    if not re.search(r"微信\s*%s\s*for Linux" % re.escape(version), body):
        return None
    date = None
    m = re.search(r"发布日期：\s*(\d{4}-\d{2}-\d{2})", body)
    if m:
        date = m.group(1)
    notes = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("- "):
            notes.append(line[2:])
    return {"version": version, "date": date, "notes": notes}
