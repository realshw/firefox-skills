"""Delete entries out of a bilibili favourite folder."""

import time

exec(open("snippets/bilibili/api.py").read())


def bilibili_remove_from_folder(driver, avids, media_id, sleep_s=1.5):
    """[{'avid','ok','resp'}] with OK/FAIL printed per entry; avids are ints (type 2) or "<id>:<type>".

    PGC entries are 24. API: POST /x/v3/fav/resource/deal (rid, type, del_media_ids, csrf). success_num
    counts additions only — a delete that worked answers data {"success_num": 0} — so ok comes from code alone,
    and the real proof is a re-pull of the list (a dead entry lingers there for a moment after the call).
    """
    out = []
    for item in avids:
        if isinstance(item, (tuple, list)):
            avid, rtype = int(item[0]), str(item[1])
        elif isinstance(item, str):
            avid, rtype = item.split(':')[:2]
            avid = int(avid)
        else:
            avid, rtype = int(item), '2'
        j = bilibili_post_api(driver, '/x/v3/fav/resource/deal', {
            'rid': avid,
            'type': rtype,
            'add_media_ids': '',
            'del_media_ids': media_id,
            'platform': 'web'
        })
        ok = j.get('code') == 0
        out.append({'avid': avid, 'ok': ok, 'resp': j})
        print(('OK  ' if ok else 'FAIL'), 'del', avid, 'type', rtype, 'from', media_id, '|',
              j.get('message', j.get('raw')))
        time.sleep(sleep_s)
    return out
