# move_videos(driver, plan, out_path=None) -> [{'target', 'mid', 'count', 'ok', 'resp'}]
# plan: {"src_media_id": 0, "targets": [{"mid": 0, "name": "folder", "avids": [123, "456:24"]}]}
# API: POST /x/v3/fav/resource/move (src_media_id, tar_media_id, mid, resources="<avid>:2,...", csrf).
# Trap: the type is the list entry's own `type` — PGC film / 番剧 are 24, and "<avid>:2" is silently
# accepted (code 0, data 0) without moving anything.
import json, time


def move_videos(driver, plan, out_path=None):
    if isinstance(plan, str):
        plan = json.load(open(plan))
    uid, src = driver.get_cookie('DedeUserID')['value'], plan['src_media_id']
    csrf = driver.get_cookie('bili_jct')['value']
    results = []
    for t in plan['targets']:
        resources = ','.join(a if isinstance(a, str) else '%d:2' % a
                             for a in t['avids'])
        res = driver.execute_async_script(
            """
        var uid = arguments[0], src = arguments[1], tar = arguments[2], resources = arguments[3], csrf = arguments[4];
        var cb = arguments[arguments.length - 1];
        var fd = new URLSearchParams();
        fd.append('src_media_id', src); fd.append('tar_media_id', tar);
        fd.append('mid', uid); fd.append('resources', resources);
        fd.append('platform', 'web'); fd.append('csrf', csrf);
        fetch('https://api.bilibili.com/x/v3/fav/resource/move', {
          method: 'POST', credentials: 'include',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: fd.toString()
        }).then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
        """, uid, src, t['mid'], resources, csrf)
        j = json.loads(res) if isinstance(res,
                                          str) and res.startswith('{') else {
                                              'raw': res
                                          }
        ok = j.get('code') == 0
        results.append({
            'target': t['name'],
            'mid': t['mid'],
            'count': len(t['avids']),
            'ok': ok,
            'resp': j
        })
        print(('OK  ' if ok else 'FAIL'), t['name'], len(t['avids']),
              'message:', j.get('message', res))
        time.sleep(2)
    ok_n = sum(1 for r in results if r['ok'])
    print('DONE %d/%d batches ok' % (ok_n, len(results)))
    if out_path:
        json.dump(results, open(out_path, 'w'), ensure_ascii=False, indent=1)
    return results
