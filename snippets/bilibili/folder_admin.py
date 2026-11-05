# create_folder(driver, title, intro, privacy); rename_folder(driver, media_id, title/intro/privacy/cover=None);
# folder_list(driver); folder_info(driver, media_id); first_cover(driver, media_id); delete_folders(driver, ids).
# Traps: attr bit 0 is the only reliable privacy flag (never compare the whole number — add returns an
# unsettled 6/7); edit overwrites every field it is given, cover='' wipes it, so unset args come from
# folder_info(driver) (list-all lacks intro). 默认收藏夹 (attr=1) can be neither renamed nor deleted.
import json
import time


def _fav_post(driver, path, params):
    csrf = driver.get_cookie('bili_jct')['value']
    res = driver.execute_async_script(
        """
    var path = arguments[0], params = arguments[1], csrf = arguments[2];
    var cb = arguments[arguments.length - 1];
    var fd = new URLSearchParams(params);
    fd.append('csrf', csrf);
    fetch('https://api.bilibili.com' + path, {method: 'POST', credentials: 'include',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: fd.toString()})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, path, params, csrf)
    try:
        return json.loads(res) if isinstance(
            res, str) and res.startswith('{') else {
                'raw': res
            }
    except Exception:
        return {'raw': res}


def folder_list(driver):
    """The account's own folders as list-all reports them — the settled attr, not the add response."""
    uid = driver.get_cookie('DedeUserID')['value']
    res = driver.execute_async_script(
        """
    var uid = arguments[0], cb = arguments[arguments.length - 1];
    fetch('https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=' + uid,
          {credentials: 'include'})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, uid)
    try:
        return (json.loads(res).get('data') or {}).get('list') or []
    except Exception:
        return []


def delete_folders(driver, media_ids):
    """POST /x/v3/fav/folder/del — a single int, a comma-separated string, or an iterable of ints."""
    if isinstance(media_ids, int):
        media_ids = str(media_ids)
    elif not isinstance(media_ids, str):
        media_ids = ','.join(str(m) for m in media_ids)
    return _fav_post(driver, '/x/v3/fav/folder/del', {'media_ids': media_ids})


def create_folder(driver, title, intro='', privacy=1):
    j = _fav_post(driver, '/x/v3/fav/folder/add', {
        'title': title,
        'intro': intro,
        'privacy': str(privacy),
        'cover': ''
    })
    if j.get('code') != 0:
        print('CREATE_FAILED:', j.get('code'), j.get('message'))
        return None
    time.sleep(1.5)
    created = (j.get('data') or {})
    settled = next(
        (f for f in folder_list(driver) if f['id'] == created.get('id')), None)
    print('CREATED: %s id=%s attr=%s (privacy=%d)' %
          (title, created.get('id'), (settled or {}).get('attr'), privacy))
    return settled or created


def folder_info(driver, media_id):
    """data.info for one folder."""
    res = driver.execute_async_script(
        """
    var mid = arguments[0], cb = arguments[arguments.length - 1];
    fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid +
          '&pn=1&ps=1&platform=web', {credentials: 'include'})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, media_id)
    try:
        return (json.loads(res).get('data') or {}).get('info') or {}
    except Exception:
        return {}


def first_cover(driver, media_id):
    """Cover URL of the folder's first video — the obvious thing to put on the folder itself."""
    res = driver.execute_async_script(
        """
    var mid = arguments[0], cb = arguments[arguments.length - 1];
    fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid +
          '&pn=1&ps=1&platform=web&order=mtime&type=0&tid=0', {credentials: 'include'})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, media_id)
    try:
        medias = (json.loads(res).get('data') or {}).get('medias') or []
        return (medias[0].get('cover') or '') if medias else ''
    except Exception:
        return ''


def rename_folder(driver,
                  media_id,
                  title=None,
                  intro=None,
                  privacy=None,
                  cover=None):
    """Edit a folder, keeping title / intro / privacy / cover unless told otherwise."""
    info = folder_info(driver, media_id)
    if not info:
        print('RENAME_FAILED: no such folder', media_id)
        return False
    if title is None:
        title = info.get('title')
    if intro is None:
        intro = info.get('intro') or ''
    if privacy is None:
        privacy = 1 if int(info.get('attr') or 0) & 1 else 0
    if cover is None:
        cover = info.get('cover') or ''
    j = _fav_post(
        driver, '/x/v3/fav/folder/edit', {
            'media_id': str(media_id),
            'title': title,
            'intro': intro,
            'privacy': str(privacy),
            'cover': cover
        })
    ok = j.get('code') == 0
    if ok:
        print('EDITED: %s | intro=%r | cover=%s' %
              (title, intro, 'set' if cover else 'empty'))
    else:
        print('RENAME_FAILED: %s (%s)' % (info.get('title'), j.get('message')))
    return ok
