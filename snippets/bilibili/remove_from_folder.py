# remove_from_folder(driver, avids, media_id, sleep_s=1.5) -> [{'avid','ok','resp'}]; avids are ints (type 2) or
# "<id>:<type>" strings — PGC entries are 24 and a type-2 delete reports code 0 with success_num 0.
# API: POST /x/v3/fav/resource/deal (rid, type, del_media_ids, csrf). success_num counts additions only —
# confirm by re-pulling the list.
import time

from snippets.bilibili.api import fav_post


def remove_from_folder(driver, avids, media_id, sleep_s=1.5):
    out = []
    for item in avids:
        if isinstance(item, (tuple, list)):
            avid, rtype = int(item[0]), str(item[1])
        elif isinstance(item, str):
            avid, rtype = item.split(':')[:2]
            avid = int(avid)
        else:
            avid, rtype = int(item), '2'
        j = fav_post(
            driver, '/x/v3/fav/resource/deal', {
                'rid': avid,
                'type': rtype,
                'add_media_ids': '',
                'del_media_ids': media_id,
                'platform': 'web'
            })
        ok = j.get('code') == 0 and (j.get('data')
                                     or {}).get('success_num') != 0
        out.append({'avid': avid, 'ok': ok, 'resp': j})
        print(('OK  ' if ok else 'FAIL'), 'del', avid, 'type', rtype, 'from',
              media_id, '|', j.get('message', j.get('raw')))
        time.sleep(sleep_s)
    return out
