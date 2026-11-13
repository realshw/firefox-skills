# bilibili_create_folder(driver, title, intro, privacy);
# bilibili_rename_folder(driver, media_id, title/intro/privacy/cover=None);
# bilibili_read_folder_list(driver); bilibili_read_folder_info(driver, media_id);
# bilibili_read_first_cover(driver, media_id); bilibili_delete_folders(driver, ids).
# Traps: attr bit 0 is the only reliable privacy flag (never compare the whole number — add returns an
# unsettled 6/7); edit overwrites every field it is given, cover='' wipes it, so unset args come from
# bilibili_read_folder_info(driver) (list-all lacks intro). 默认收藏夹 (attr=1) can be neither renamed nor deleted.
import time

exec(open("snippets/bilibili/api.py").read())


def bilibili_read_folder_list(driver):
    """The account's own folders as list-all reports them — the settled attr, not the add response."""
    return bilibili_read_fav_folders(driver)


def bilibili_delete_folders(driver, media_ids):
    """POST /x/v3/fav/folder/del — a single int, a comma-separated string, or an iterable of ints."""
    if isinstance(media_ids, int):
        media_ids = str(media_ids)
    elif not isinstance(media_ids, str):
        media_ids = ','.join(str(m) for m in media_ids)
    return bilibili_post_api(driver, '/x/v3/fav/folder/del', {'media_ids': media_ids})


def bilibili_create_folder(driver, title, intro='', privacy=1):
    j = bilibili_post_api(driver, '/x/v3/fav/folder/add', {
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
    settled = next((f for f in bilibili_read_folder_list(driver) if f['id'] == created.get('id')), None)
    print('CREATED: %s id=%s attr=%s (privacy=%d)' % (title, created.get('id'), (settled or {}).get('attr'), privacy))
    return settled or created


def bilibili_read_folder_info(driver, media_id):
    """data.info for one folder."""
    return (bilibili_get_api(driver, '/x/v3/fav/resource/list', media_id=media_id, pn=1, ps=1,
                             platform='web').get('data') or {}).get('info') or {}


def bilibili_read_first_cover(driver, media_id):
    """Cover URL of the folder's first video — the obvious thing to put on the folder itself."""
    medias = (bilibili_get_api(
        driver, '/x/v3/fav/resource/list', media_id=media_id, pn=1, ps=1, platform='web', order='mtime', type=0,
        tid=0).get('data') or {}).get('medias') or []
    return (medias[0].get('cover') or '') if medias else ''


def bilibili_rename_folder(driver, media_id, title=None, intro=None, privacy=None, cover=None):
    """Edit a folder, keeping title / intro / privacy / cover unless told otherwise."""
    info = bilibili_read_folder_info(driver, media_id)
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
    j = bilibili_post_api(driver, '/x/v3/fav/folder/edit', {
        'media_id': str(media_id),
        'title': title,
        'intro': intro,
        'privacy': str(privacy),
        'cover': cover
    })
    ok = j.get('code') == 0
    if ok:
        print('EDITED: %s | intro=%r | cover=%s' % (title, intro, 'set' if cover else 'empty'))
    else:
        print('RENAME_FAILED: %s (%s)' % (info.get('title'), j.get('message')))
    return ok
