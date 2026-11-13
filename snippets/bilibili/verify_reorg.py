# verify_reorg(driver, baseline, out_path=None) -> {'ok','lost','new','dup','folders'}; baseline is a previous
# dump_all dict or its JSON path. Re-dumps the account and compares by folder id — ids survive renames, so a
# renamed folder is not reported as one folder emptied and another filled. lost = an avid that is now in no
# folder at all (the only real failure); new = favourited since the baseline, not a failure; dup = the same
# avid twice in one folder. It speaks for the whole account, so a plan's targets need no separate check.
import json
import os
import tempfile
from collections import Counter

exec(open("snippets/bilibili/dump_all.py").read())
exec(open("snippets/common/pad.py").read())


def verify_reorg(driver, baseline, out_path=None):
    if isinstance(baseline, str):
        baseline = json.load(open(baseline))
    after = dump_all(
        driver, out_path
        or os.path.join(tempfile.gettempdir(), 'bili_reorg_after.json'))
    before = {
        v['id']: (k, [m['id'] for m in v['medias']])
        for k, v in baseline.items()
    }
    now = {
        v['id']: (k, [m['id'] for m in v['medias']])
        for k, v in after.items()
    }

    before_ids = {a for _, ids in before.values() for a in ids}
    now_flat = [a for _, ids in now.values() for a in ids]
    now_ids = set(now_flat)
    lost = sorted(before_ids - now_ids)
    new = sorted(now_ids - before_ids)
    dup = [a for a, n in Counter(now_flat).items() if n > 1]
    before_dup = {
        a
        for a, n in Counter(
            a for _, ids in before.values() for a in ids).items() if n > 1
    }

    print('---')
    print('%-16s %6s %6s %5s %5s' %
          ('folder', 'before', 'after', '+in', '-out'))
    for mid in sorted(set(before) | set(now),
                      key=lambda m: (now.get(m) or before.get(m))[0]):
        title = (now.get(mid) or before.get(mid))[0]
        b = set((before.get(mid) or (None, []))[1])
        a = set((now.get(mid) or (None, []))[1])
        print(pad(title, 16),
              '%6d %6d %5d %5d' % (len(b), len(a), len(a - b), len(b - a)))
    for mid, (title, _) in before.items():
        if mid not in now:
            print('GONE: folder %s (%s) no longer exists' % (title, mid))
    for mid, (title, ids) in now.items():
        if mid not in before:
            print('NEW FOLDER: %s (%s) with %d items' % (title, mid, len(ids)))
    if lost:
        titles = {
            m['id']: m['title']
            for v in baseline.values()
            for m in v['medias']
        }
        for a in lost:
            print('LOST', a, '|', titles.get(a, '?'))
    if new:
        print('NEW ITEMS', len(new), '- favourited after the baseline')
    if dup:
        print('DUP', dup)
    ok = not lost and all(a in before_dup for a in dup)
    print('TOTAL', len(now_flat), '| unique', len(now_ids), '| lost',
          len(lost), '| new', len(new), '| dup', len(dup))
    print('REORG:', 'ALL GOOD' if ok else 'CHECK NEEDED')
    return {
        'ok': ok,
        'lost': lost,
        'new': new,
        'dup': dup,
        'folders': {
            (now.get(m) or before.get(m))[0]: {
                'before': len(set((before.get(m) or (None, []))[1])),
                'after': len(set((now.get(m) or (None, []))[1]))
            }
            for m in set(before) | set(now)
        }
    }
