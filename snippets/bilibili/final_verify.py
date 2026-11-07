# final_verify(driver, plan, require_src_empty=True) -> bool; plan is move_videos.py's plan dict or its JSON path.
# True iff every target folder holds all its avids and, when require_src_empty, the source is empty —
# pass require_src_empty=False for a partial rebalance or it reports CHECK NEEDED with everything landed.
# It only speaks for the folders the plan names; verify_reorg is the one that watches the whole account.
import json

from snippets.bilibili.api import folder_medias
from snippets.common.pad import pad


def final_verify(driver, plan, require_src_empty=True):
    if isinstance(plan, str):
        plan = json.load(open(plan))

    def folder_ids(mid):
        return {m['id'] for m in folder_medias(driver, mid)}

    all_ok = True
    for t in plan['targets']:
        wanted = [
            a if isinstance(a, int) else int(str(a).split(':')[0])
            for a in t['avids']
        ]
        ids = folder_ids(t['mid'])
        missing = [a for a in wanted if a not in ids]
        if missing:
            all_ok = False
        print(
            pad(t['name'], 14), 'expected+%d -> now %d items; %s' %
            (len(wanted), len(ids),
             'OK' if not missing else 'MISSING:' + str(missing)))
    src_ids = folder_ids(plan['src_media_id'])
    print('source folder now:', len(src_ids), 'items')
    ok = all_ok and (not require_src_empty or not src_ids)
    print('FINAL:', 'ALL GOOD' if ok else 'CHECK NEEDED')
    return ok
