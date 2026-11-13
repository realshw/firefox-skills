# verify_ids(driver, baseline) -> {'ok','lost','new','dup','folders'} — verify_reorg's cheap sibling: same
# comparison by folder id, but from folder_ids instead of a page-by-page dump, so it costs 22 requests
# instead of 40+ and keeps answering when resource/list is 412 (risk control blocks that one endpoint alone;
# list-all, view and ids still answer 200). Trade-off: ids carry no titles, so a lost entry is reported by
# avid alone, and a PGC type-24 entry is invisible here — so the baseline side is filtered to type 2 as
# well, and 影视·剧集 does not read one short. Use it
# after a move batch; use verify_reorg (titles, dead-entry report) when the answer has to name the video.
from collections import Counter

exec(open("snippets/bilibili/api.py").read())
exec(open("snippets/common/pad.py").read())


def verify_ids(driver, baseline):
    before = {v['id']: (k, [m['id'] for m in v['medias'] if m.get('type') == 2]) for k, v in baseline.items()}
    now = {}
    for f in fav_folders(driver):
        now[f['id']] = (f['title'], [m['id'] for m in folder_ids(driver, f['id'])])
    before_ids = {a for _, ids in before.values() for a in ids}
    now_flat = [a for _, ids in now.values() for a in ids]
    now_ids = set(now_flat)
    lost = sorted(before_ids - now_ids)
    new = sorted(now_ids - before_ids)
    dup = [a for a, n in Counter(now_flat).items() if n > 1]
    print('%-14s %6s %6s %5s %5s' % ('folder', 'before', 'after', '+in', '-out'))
    for mid in sorted(set(before) | set(now), key=lambda m: -len((now.get(m) or before.get(m))[1])):
        title = (now.get(mid) or before.get(mid))[0]
        b = set((before.get(mid) or (None, []))[1])
        a = set((now.get(mid) or (None, []))[1])
        mark = '' if mid in before and mid in now else ('  NEW' if mid not in before else '  GONE')
        print(pad(title, 14), '%6d %6d %5d %5d%s' % (len(b), len(a), len(a - b), len(b - a), mark))
    for a in lost:
        print('LOST', a)
    if new:
        print('NEW ITEMS', len(new), new[:10])
    if dup:
        print('DUP', dup)
    ok = not lost and not dup
    print('TOTAL', len(now_flat), '| unique', len(now_ids), '| lost', len(lost), '| dup', len(dup))
    print('VERIFY:', 'ALL GOOD' if ok else 'CHECK NEEDED')
    return {'ok': ok, 'lost': lost, 'new': new, 'dup': dup}
