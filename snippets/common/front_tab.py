# "Which page is the user on?" — WebDriver cannot answer this. window_handles carries no order,
# switch_to.window does NOT move the tab the human sees (proved: sessionstore's `selected` survives a
# 25 s switch), every tab answers visible + hasFocus, and a chrome-privileged context (about:newtab)
# raises UnsupportedOperationError on every command, titles included. Two signals outside WebDriver do
# work: the session store's `selected` index for the front tab, and the X11 window title
# "<front tab title> — Mozilla Firefox". Both are passive — reading them moves nothing.
import glob
import json
import os
import subprocess

SUFFIXES = (" — Mozilla Firefox", " - Mozilla Firefox")
LAYOUTS = (".config/mozilla/firefox", ".mozilla/firefox")


def _firefox_envs():
    """Environ of every running firefox, as dicts: HOME locates the profile, DISPLAY/XAUTHORITY reach X."""
    envs = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if open("/proc/%s/comm" % pid).read().strip() != "firefox":
                continue
            raw = open("/proc/%s/environ" % pid, "rb").read().split(b"\0")
        except OSError:
            continue
        envs.append(
            dict(
                item.decode(errors="replace").split("=", 1) for item in raw
                if b"=" in item))
    return envs or [{"HOME": os.path.expanduser("~")}]


def _firefox_homes():
    """$HOME of every running firefox: the profile sits under its user's home, not ours."""
    return [
        env.get("HOME", os.path.expanduser("~")) for env in _firefox_envs()
    ]


def store(limit=2):
    """Newest session store this user can read, parsed; None when lz4 or the profile is missing."""
    try:
        import lz4.block
    except ImportError:
        return None
    paths = [
        p for home in _firefox_homes() for layout in LAYOUTS
        for p in glob.glob(
            os.path.join(home, layout, "*", "sessionstore-backups",
                         "recovery.jsonlz4"))
    ]
    for path in sorted(paths, key=os.path.getmtime, reverse=True)[:limit]:
        try:
            with open(path, "rb") as f:
                return json.loads(lz4.block.decompress(f.read()[8:]))
        except (OSError, ValueError):
            continue
    return None


def front_index():
    """Index of the selected tab in the front window, or None — the cheapest truth about the front tab."""
    session = store()
    if not session or not session.get("windows"):
        return None
    return session["windows"][0].get("selected")


def _xprop(args):
    """xprop output, or "" — our env carries neither DISPLAY nor XAUTHORITY, firefox's carries both."""
    env = dict(os.environ)
    for key in ("DISPLAY", "XAUTHORITY"):
        if not env.get(key):
            borrowed = next((e[key] for e in _firefox_envs() if e.get(key)),
                            "")
            if borrowed:
                env[key] = borrowed
    env["DISPLAY"] = env.get("DISPLAY") or ":0"
    try:
        done = subprocess.run(["xprop"] + args,
                              capture_output=True,
                              text=True,
                              timeout=10,
                              env=env)
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout


def wm_title():
    """Title of the front tab, read off the Firefox window's X11 title; None when xprop is absent."""
    listing = _xprop(["-root", "_NET_CLIENT_LIST_STACKING"])
    for wid in listing.split("#")[-1].replace(",", " ").split():
        info = _xprop(["-id", wid, "WM_CLASS", "_NET_WM_NAME"])
        if not info:
            continue
        if '"Navigator"' not in info or "_NET_WM_NAME" not in info:
            continue
        title = info.split("_NET_WM_NAME",
                           1)[1].split("=", 1)[-1].strip().strip('"')
        for suffix in SUFFIXES:
            if title.endswith(suffix):
                return title[:-len(suffix)].strip()
        return title
    return None


def tabs(driver):
    """Every tab as {handle, index, title, url, error}; the session is left on the handle it arrived on."""
    start = driver.current_window_handle
    out = []
    for index, handle in enumerate(driver.window_handles):
        row = {
            "handle": handle,
            "index": index,
            "title": "",
            "url": "",
            "error": ""
        }
        try:
            driver.switch_to.window(handle)
            row["url"] = driver.current_url
            row["title"] = driver.title
        except Exception as e:  # privileged context, closed mid-scan: a row, not a crash
            row["error"] = type(e).__name__ + ": " + str(
                e).splitlines()[0][:80]
        out.append(row)
    try:
        driver.switch_to.window(start)
    except Exception:
        pass
    return out


def front_tab(driver, switch=False, rows=None):
    """The row the user is looking at: session-store index first, window title as the cross-check."""
    rows = tabs(driver) if rows is None else rows
    index, title = front_index(), wm_title()
    picked, source = None, ""
    if index is not None and index < len(rows) and not rows[index]["error"]:
        picked, source = rows[index], "sessionstore index %d" % index
    if picked and title and picked["title"] and picked["title"] not in title:
        source += " (window title disagrees: %r)" % title
    if picked is None and title:
        for row in rows:
            if row["title"] and row["title"] in title:
                picked, source = row, "window title %r" % title
                break
    if picked is None:
        print("FRONT_TAB: no signal — %d tabs, index=%r, title=%r" %
              (len(rows), index, title))
        return None
    if switch:
        driver.switch_to.window(picked["handle"])
    print("FRONT_TAB: #%d %s | %s | via %s" %
          (picked["index"], picked["title"][:60], picked["url"][:80], source))
    return picked
