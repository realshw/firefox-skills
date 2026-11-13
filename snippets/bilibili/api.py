# The favourite-API plumbing every bilibili snippet shares, so the traps live in one place.
# Auth: fetch(..., {credentials: 'include'}) from a bilibili.com tab; a write also needs csrf = bili_jct.
# That tab has to be a loaded bilibili page: a fresh about:blank one carries neither the cookies nor the
# origin, so bilibili_get_uid() answers None ("'NoneType' object is not subscriptable") and the fetch reports
# NetworkError. site_tab only picks the tab, it does not navigate — load the page first.
# Reads: GET /x/v3/fav/folder/created/list-all?up_mid=<uid> — 默认收藏夹 has attr=1, the rest 3/22/23 —
# and GET /x/v3/fav/resource/list?media_id=&pn=&ps=20, where ps is capped at 20: page until has_more,
# never until a short page. Media type 2 = video, 24 = PGC 番剧/film; a move or delete needs the real type.
import json
import time

BILIBILI_GET_JS = """
var url = arguments[0], cb = arguments[arguments.length - 1];
fetch(url, {credentials: 'include'})
  .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
"""

BILIBILI_POST_JS = """
var url = arguments[0], params = arguments[1], cb = arguments[arguments.length - 1];
var fd = new URLSearchParams(params);
fetch(url, {method: 'POST', credentials: 'include',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: fd.toString()})
  .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
"""

BILIBILI_BASE = 'https://api.bilibili.com'
BILIBILI_PAGE_SLEEP = 0.6


def _bilibili_parse_reply(res, what):
    """The parsed reply, or RuntimeError — a fetch that never ran must not pass for an empty page."""
    if isinstance(res, str) and res.startswith('{'):
        return json.loads(res)
    raise RuntimeError('%s: %s' % (what, res))


def bilibili_get_uid(driver):
    return driver.get_cookie('DedeUserID')['value']


def bilibili_get_csrf(driver):
    return driver.get_cookie('bili_jct')['value']


def bilibili_get_api(driver, path, **params):
    """GET an api.bilibili.com path as the logged-in user; params go into the query string."""
    url = BILIBILI_BASE + path
    if params:
        url += '?' + '&'.join('%s=%s' % (k, v) for k, v in params.items())
    return _bilibili_parse_reply(driver.execute_async_script(BILIBILI_GET_JS, url), path)


def bilibili_post_api(driver, path, params):
    """POST a form body to api.bilibili.com, with csrf filled in from the cookie."""
    params = dict(params)
    params['csrf'] = bilibili_get_csrf(driver)
    return _bilibili_parse_reply(driver.execute_async_script(BILIBILI_POST_JS, BILIBILI_BASE + path, params), path)


def bilibili_read_fav_folders(driver):
    """The account's own folders, in list-all's shape (id, title, media_count, attr)."""
    data = bilibili_get_api(driver, '/x/v3/fav/folder/created/list-all',
                            up_mid=bilibili_get_uid(driver)).get('data') or {}
    return data.get('list') or []


def bilibili_read_folder_ids(driver, media_id):
    """One folder's entries as [{id, type}] from /x/v3/fav/resource/ids — no paging, cheap enough to re-pull
    the whole account for a verify. Two traps: a PGC type-24 entry is never in this list (影视·剧集 answers
    media_count 10 and 9 ids), and it shows an entry resource/list hides — a favourite whose video is gone
    (view answers 62012) still counts in media_count yet is on no page of the list, so a folder can read 20
    there and 19 here with nothing lost. Its real use is a 412: risk control blocks resource/list alone
    after a full-account dump, while list-all, view and ids keep answering 200, so a verify need not wait."""
    return bilibili_get_api(driver, '/x/v3/fav/resource/ids', media_id=media_id).get('data') or []


def bilibili_read_folder_medias(driver, media_id, sleep=BILIBILI_PAGE_SLEEP, order='mtime'):
    """Every media entry of one folder, page by page — has_more is the stop condition, ps is 20."""
    out, pn = [], 1
    while True:
        data = bilibili_get_api(driver,
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
