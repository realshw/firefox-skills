# bilibili_list_folders(driver) -> the summary written to <tempdir>/bili_folders.json, one printed line each.
# API: GET /x/v3/fav/folder/created/list-all?up_mid=<uid> — 默认收藏夹 has attr=1, the rest 3/22/23,
# and attr bit 0 is the only reliable privacy flag.
import json
import os
import tempfile

exec(open("snippets/bilibili/api.py").read())

BILIBILI_OUT_PATH = os.path.join(tempfile.gettempdir(), 'bili_folders.json')


def bilibili_list_folders(driver):
    summary = [{
        'id': f['id'],
        'title': f['title'],
        'count': f['media_count'],
        'attr': f['attr']
    } for f in bilibili_read_fav_folders(driver)]
    json.dump({
        'uid': bilibili_get_uid(driver),
        'folders': summary
    },
              open(BILIBILI_OUT_PATH, 'w'),
              ensure_ascii=False,
              indent=1)
    print('SAVED', len(summary), 'folders ->', BILIBILI_OUT_PATH)
    for f in summary:
        print(f['id'], f['title'], f['count'], 'attr=%d' % f['attr'])
    return summary
