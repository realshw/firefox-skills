# move_videos(driver, plan, out_path=None) -> [{'target','mid','count','ok','code','missing','resp'}]
# plan: {"src_media_id": 0, "targets": [{"mid": 0, "name": "folder", "avids": [123, "456:24", (789, 24)]}]}
# API: POST /x/v3/fav/resource/move (src_media_id, tar_media_id, mid, resources="<avid>:<type>,...", csrf).
# Trap: the type must be the list entry's own `type` — PGC film / 番剧 are 24 — and a wrong one is accepted
# with exactly the {"code": 0, "data": 0} a real move returns, so the reply proves nothing either way.
# That is why ok comes from re-pulling the target folder and finding the avids, never from code 0.
import json
import time

from snippets.bilibili.api import fav_post, folder_medias, uid


def _entry(item):
    """One resources entry: an int means type 2, a "id:type" string or an (id, type) pair says its own."""
    if isinstance(item, (tuple, list)):
        return '%d:%d' % (int(item[0]), int(item[1]))
    if isinstance(item, str):
        return item
    return '%d:2' % int(item)


def _avid(item):
    if isinstance(item, (tuple, list)):
        return int(item[0])
    return int(str(item).split(':')[0])


def move_videos(driver, plan, out_path=None, verify=True):
    if isinstance(plan, str):
        plan = json.load(open(plan))
    account, src = uid(driver), plan['src_media_id']
    results = []
    for t in plan['targets']:
        resources = ','.join(_entry(a) for a in t['avids'])
        j = fav_post(
            driver, '/x/v3/fav/resource/move', {
                'src_media_id': src,
                'tar_media_id': t['mid'],
                'mid': account,
                'resources': resources,
                'platform': 'web'
            })
        code_ok = j.get('code') == 0
        missing = []
        if code_ok and verify:
            present = {m['id'] for m in folder_medias(driver, t['mid'])}
            missing = [a for a in map(_avid, t['avids']) if a not in present]
        ok = code_ok and not missing
        results.append({
            'target': t['name'],
            'mid': t['mid'],
            'count': len(t['avids']),
            'ok': ok,
            'code': j.get('code'),
            'missing': missing,
            'resp': j
        })
        if ok:
            print('OK  ', t['name'], len(t['avids']), 'items landed')
        else:
            print('FAIL', t['name'], len(t['avids']), 'items |', 'message:',
                  j.get('message'), '| not in target:', missing
                  or '(code rejected)')
        time.sleep(2)
    ok_n = sum(1 for r in results if r['ok'])
    print('DONE %d/%d batches ok' % (ok_n, len(results)))
    if out_path:
        json.dump(results, open(out_path, 'w'), ensure_ascii=False, indent=1)
    return results
