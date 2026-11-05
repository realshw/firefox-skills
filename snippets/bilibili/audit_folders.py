# Writes every folder's avids into <tempdir>/bili_all_folders.json plus a cross-folder duplicate
# map. Fix one bad item with remove_from_folder(driver, [avid], mid); a wholesale split is a move_videos.py plan.
import json, os, tempfile, time
from collections import defaultdict

OUT_PATH = os.path.join(tempfile.gettempdir(), 'bili_all_folders.json')


def audit_folders(driver):
    uid = driver.get_cookie('DedeUserID')['value']
    res = driver.execute_async_script(
        """
    var uid = arguments[0];
    var cb = arguments[arguments.length - 1];
    fetch('https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=' + uid, {credentials: 'include'})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, uid)
    if not res or (isinstance(res, str) and res.startswith('ERR')):
        raise RuntimeError(res)
    folder_list = (json.loads(res).get('data') or {}).get('list') or []
    out, avid_title = {}, {}
    for f in folder_list:
        avids, pn = [], 1
        while True:
            r2 = driver.execute_async_script(
                """
            var mid = arguments[0], pn = arguments[1];
            var cb = arguments[arguments.length - 1];
            fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid + '&pn=' + pn + '&ps=20&platform=web&order=mtime&type=0&tid=0', {credentials: 'include'})
              .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
            """, f['id'], pn)
            if not r2 or (isinstance(r2, str) and r2.startswith('ERR')):
                raise RuntimeError(r2)
            d = json.loads(r2).get('data') or {}
            for m in (d.get('medias') or []):
                avids.append(m['id'])
                avid_title.setdefault(m['id'], m['title'])
            if not d.get('has_more'):
                break
            pn += 1
            time.sleep(0.6)
        out[f['title']] = {
            'id': f['id'],
            'count': f['media_count'],
            'fetched': len(avids),
            'avids': avids
        }
        print('%-12s %3d videos' % (f['title'], len(avids)))
        time.sleep(0.6)
    seen = defaultdict(list)
    for name, d in out.items():
        for a in d['avids']:
            seen[a].append(name)
    dups = {a: ns for a, ns in seen.items() if len(ns) > 1}
    json.dump(
        {
            'folders': out,
            'avid_title': {
                str(k): v
                for k, v in avid_title.items()
            }
        },
        open(OUT_PATH, 'w'),
        ensure_ascii=False)
    total = sum(len(d['avids']) for d in out.values())
    print('---')
    print('TOTAL videos across folders:', total, '| unique:', len(seen),
          '| in >1 folder:', len(dups))
    for a, ns in dups.items():
        print('DUP', a, '|', avid_title.get(a, '?')[:50], '|', ' + '.join(ns))
