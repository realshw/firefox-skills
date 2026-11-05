# final_verify(driver, plan, require_src_empty=True) -> bool; plan is move_videos.py's plan dict or its JSON path.
# True iff every target folder holds all its avids and, when require_src_empty, the source is empty —
# pass require_src_empty=False for a partial rebalance or it reports CHECK NEEDED with everything landed.
import json, time


def final_verify(driver, plan, require_src_empty=True):
    if isinstance(plan, str):
        plan = json.load(open(plan))

    def folder_ids(mid):
        ids, pn = set(), 1
        while True:
            res = driver.execute_async_script(
                """
            var mid = arguments[0], pn = arguments[1];
            var cb = arguments[arguments.length - 1];
            fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid + '&pn=' + pn + '&ps=20&platform=web&order=mtime&type=0&tid=0', {credentials: 'include'})
              .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
            """, mid, pn)
            if not res or (isinstance(res, str) and res.startswith('ERR')):
                raise RuntimeError(res)
            d = json.loads(res).get('data') or {}
            ids.update(m['id'] for m in (d.get('medias') or []))
            if not d.get('has_more'):
                return ids
            pn += 1
            time.sleep(0.6)

    all_ok = True
    for t in plan['targets']:
        ids = folder_ids(t['mid'])
        missing = [a for a in t['avids'] if a not in ids]
        if missing:
            all_ok = False
        print('%-14s expected+%d -> now %d items; %s' %
              (t['name'], len(t['avids']), len(ids),
               'OK' if not missing else 'MISSING:' + str(missing)))
        time.sleep(0.6)
    src_ids = folder_ids(plan['src_media_id'])
    print('source folder now:', len(src_ids), 'items')
    ok = all_ok and (not require_src_empty or not src_ids)
    print('FINAL:', 'ALL GOOD' if ok else 'CHECK NEEDED')
    return ok
