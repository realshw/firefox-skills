# The favourite-API plumbing every bilibili snippet shares, so the traps live in one place.
# Auth: fetch(..., {credentials: 'include'}) from a bilibili.com tab; a write also needs csrf = bili_jct.
# That tab has to be a loaded bilibili page: a fresh about:blank one carries neither the cookies nor the
# origin, so uid() answers None ("'NoneType' object is not subscriptable") and the fetch reports
# NetworkError. site_tab only picks the tab, it does not navigate — load the page first.
# Reads: GET /x/v3/fav/folder/created/list-all?up_mid=<uid> — 默认收藏夹 has attr=1, the rest 3/22/23 —
# and GET /x/v3/fav/resource/list?media_id=&pn=&ps=20, where ps is capped at 20: page until has_more,
# never until a short page. Media type 2 = video, 24 = PGC 番剧/film; a move or delete needs the real type.
import json
import time

GET_JS = """
var url = arguments[0], cb = arguments[arguments.length - 1];
fetch(url, {credentials: 'include'})
  .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
"""

POST_JS = """
var url = arguments[0], params = arguments[1], cb = arguments[arguments.length - 1];
var fd = new URLSearchParams(params);
fetch(url, {method: 'POST', credentials: 'include',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: fd.toString()})
  .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
"""

BASE = 'https://api.bilibili.com'
PAGE_SLEEP = 0.6


def _reply(res, what):
    """The parsed reply, or RuntimeError — a fetch that never ran must not pass for an empty page."""
    if isinstance(res, str) and res.startswith('{'):
        return json.loads(res)
    raise RuntimeError('%s: %s' % (what, res))


def uid(driver):
    return driver.get_cookie('DedeUserID')['value']


def csrf(driver):
    return driver.get_cookie('bili_jct')['value']


def fav_get(driver, path, **params):
    """GET an api.bilibili.com path as the logged-in user; params go into the query string."""
    url = BASE + path
    if params:
        url += '?' + '&'.join('%s=%s' % (k, v) for k, v in params.items())
    return _reply(driver.execute_async_script(GET_JS, url), path)


def fav_post(driver, path, params):
    """POST a form body to api.bilibili.com, with csrf filled in from the cookie."""
    params = dict(params)
    params['csrf'] = csrf(driver)
    return _reply(driver.execute_async_script(POST_JS, BASE + path, params), path)


def fav_folders(driver):
    """The account's own folders, in list-all's shape (id, title, media_count, attr)."""
    data = fav_get(driver, '/x/v3/fav/folder/created/list-all', up_mid=uid(driver)).get('data') or {}
    return data.get('list') or []


def folder_medias(driver, media_id, sleep=PAGE_SLEEP, order='mtime'):
    """Every media entry of one folder, page by page — has_more is the stop condition, ps is 20."""
    out, pn = [], 1
    while True:
        data = fav_get(driver,
                       '/x/v3/fav/resource/list',
                       media_id=media_id,
                       pn=pn,
                       ps=20,
                       platform='web',
                       order=order,
                       type=0,
                       tid=0).get('data') or {}
        out.extend(data.get('medias') or [])
        if not data.get('has_more'):
            return out
        pn += 1
        time.sleep(sleep)
