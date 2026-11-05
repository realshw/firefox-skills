# dump_all(driver, out_path=None) -> {folder: {id, count, medias:[{id,type,bvid,title,upper}]}} written to
# <tempdir>/bili_all_media.json. type 2 = video,
# 24 = PGC film·番剧 (move/delete need it); a type-2 entry with an empty upper.name is dead, and type 24
# never reports an upper. API: GET /x/v3/fav/folder/created/list-all, /x/v3/fav/resource/list (ps=20).
import json, os, tempfile, time
from collections import defaultdict

DEFAULT_OUT = os.path.join(tempfile.gettempdir(), 'bili_all_media.json')


def dump_all(driver, out_path=None):
    out_path = out_path or DEFAULT_OUT
    uid = driver.get_cookie('DedeUserID')['value']
    res = driver.execute_async_script(
        """
    var uid = arguments[0], cb = arguments[arguments.length - 1];
    fetch('https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=' + uid,
          {credentials: 'include'})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, uid)
    if not res or (isinstance(res, str) and res.startswith('ERR')):
        raise RuntimeError(res)
    folders = (json.loads(res).get('data') or {}).get('list') or []
    out, dead, seen = {}, [], defaultdict(list)
    for f in folders:
        medias, pn = [], 1
        while True:
            r = driver.execute_async_script(
                """
            var mid = arguments[0], pn = arguments[1];
            var cb = arguments[arguments.length - 1];
            fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid + '&pn=' + pn +
                  '&ps=20&platform=web&order=mtime&type=0&tid=0', {credentials: 'include'})
              .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
            """, f['id'], pn)
            if not r or (isinstance(r, str) and r.startswith('ERR')):
                raise RuntimeError(r)
            d = json.loads(r).get('data') or {}
            for m in (d.get('medias') or []):
                upper = (m.get('upper') or {}).get('name') or ''
                medias.append({
                    'id': m['id'],
                    'type': m.get('type'),
                    'bvid': m.get('bvid'),
                    'title': m['title'],
                    'upper': upper
                })
                seen[m['id']].append(f['title'])
                if m.get('type') == 2 and not upper:
                    dead.append(
                        (f['title'], m['id'], m.get('type'), m['title']))
            if not d.get('has_more'):
                break
            pn += 1
            time.sleep(0.6)
        out[f['title']] = {
            'id': f['id'],
            'count': f['media_count'],
            'medias': medias
        }
        print('%-14s %3d' % (f['title'], len(medias)))
        time.sleep(0.5)
    json.dump(out, open(out_path, 'w'), ensure_ascii=False, indent=1)
    total = sum(len(v['medias']) for v in out.values())
    dups = {a: ns for a, ns in seen.items() if len(ns) > 1}
    print('---')
    print('TOTAL', total, '| unique', len(seen), '| dup', len(dups), '->',
          out_path)
    for a, ns in dups.items():
        print('DUP', a, '|', ' + '.join(ns))
    for row in dead:
        print('DEAD', row)
    return out
