# remove_from_folder(driver, avids, media_id, sleep_s=1.5) -> [{'avid', 'ok', 'resp'}]; avids are ints (type 2) or
# "<id>:<type>" strings — PGC entries are 24 and a type-2 delete reports code 0 with success_num 0.
# API: POST /x/v3/fav/resource/deal (rid, type, del_media_ids, csrf). success_num counts additions only —
# confirm by re-pulling the list.
import json, time


def remove_from_folder(driver, avids, media_id, sleep_s=1.5):
    csrf = driver.get_cookie('bili_jct')['value']
    out = []
    for item in avids:
        if isinstance(item, str):
            avid, rtype = item.split(':')[:2]
        else:
            avid, rtype = item, '2'
        avid = int(avid)
        res = driver.execute_async_script(
            """
        var avid = arguments[0], mid = arguments[1], csrf = arguments[2], rtype = arguments[3];
        var cb = arguments[arguments.length - 1];
        var fd = new URLSearchParams();
        fd.append('rid', avid); fd.append('type', rtype);
        fd.append('add_media_ids', ''); fd.append('del_media_ids', mid);
        fd.append('platform', 'web'); fd.append('csrf', csrf);
        fetch('https://api.bilibili.com/x/v3/fav/resource/deal', {
          method: 'POST', credentials: 'include',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: fd.toString()
        }).then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
        """, avid, media_id, csrf, rtype)
        j = json.loads(res) if isinstance(res,
                                          str) and res.startswith('{') else {
                                              'raw': res
                                          }
        ok = j.get('code') == 0 and (j.get('data')
                                     or {}).get('success_num') != 0
        out.append({'avid': avid, 'ok': ok, 'resp': j})
        print(('OK  ' if ok else 'FAIL'), 'del', avid, 'type', rtype, 'from',
              media_id, '|', j.get('message', res))
        time.sleep(sleep_s)
    return out
