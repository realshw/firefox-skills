# audit_folders(driver) -> {folder: {id, count, fetched, avids}} written to <tempdir>/bili_all_folders.json,
# plus a printed cross-folder duplicate map. The avid-only projection of dump_all, kept because the
# avids are what a move or delete plan is built from; reach for dump_all when titles matter.
# Fix one bad item with remove_from_folder(driver, [avid], mid); a wholesale split is a move_videos.py plan.
import json
import os
import tempfile
from collections import defaultdict

from snippets.bilibili.dump_all import dump_all

OUT_PATH = os.path.join(tempfile.gettempdir(), 'bili_all_folders.json')


def audit_folders(driver):
    dumped = dump_all(driver)
    out, seen = {}, defaultdict(list)
    for title, d in dumped.items():
        avids = [m['id'] for m in d['medias']]
        out[title] = {
            'id': d['id'],
            'count': d['count'],
            'fetched': len(avids),
            'avids': avids
        }
        for a in avids:
            seen[a].append(title)
    json.dump(
        {
            'folders': out,
            'avid_title': {
                str(m['id']): m['title']
                for d in dumped.values()
                for m in d['medias']
            }
        },
        open(OUT_PATH, 'w'),
        ensure_ascii=False)
    dups = {a: ns for a, ns in seen.items() if len(ns) > 1}
    total = sum(len(d['avids']) for d in out.values())
    print('---')
    print('TOTAL videos across folders:', total, '| unique:', len(seen),
          '| in >1 folder:', len(dups))
    print('SAVED ->', OUT_PATH)
    for a, ns in dups.items():
        print('DUP', a, '|', ' + '.join(ns))
    return out
