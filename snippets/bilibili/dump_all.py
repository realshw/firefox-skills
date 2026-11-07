# dump_all(driver, out_path=None) -> {folder: {id, count, medias:[{id,type,bvid,title,upper}]}} written to
# <tempdir>/bili_all_media.json — the whole account in one call, which is what every reshuffle starts from.
# type 2 = video, 24 = PGC 番剧/film (move/delete need it); a type-2 entry with an empty upper.name is
# dead, and type 24 never reports an upper.
import json
import os
import tempfile
from collections import defaultdict

from snippets.bilibili.api import fav_folders, folder_medias
from snippets.common.pad import pad

DEFAULT_OUT = os.path.join(tempfile.gettempdir(), 'bili_all_media.json')


def dump_all(driver, out_path=None):
    out_path = out_path or DEFAULT_OUT
    out, dead, seen = {}, [], defaultdict(list)
    for f in fav_folders(driver):
        medias = []
        for m in folder_medias(driver, f['id']):
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
                dead.append((f['title'], m['id'], m.get('type'), m['title']))
        out[f['title']] = {
            'id': f['id'],
            'count': f['media_count'],
            'medias': medias
        }
        print(pad(f['title'], 14), '%3d' % len(medias))
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
