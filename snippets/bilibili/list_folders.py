# API: GET /x/v3/fav/folder/created/list-all?up_mid=<uid> — 默认收藏夹 has attr=1, the rest 3/22/23.
# Always fetch(..., {credentials:'include'}) from a bilibili.com page (cookie auth); POST bodies are
# URLSearchParams-encoded with csrf from bili_jct.
import json
import os
import tempfile

OUT_PATH = os.path.join(tempfile.gettempdir(), 'bili_folders.json')


def list_folders(driver):
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
    data = json.loads(res).get('data') or {}
    folders = data.get('list') or []
    summary = [{
        'id': f['id'],
        'title': f['title'],
        'count': f['media_count'],
        'attr': f['attr']
    } for f in folders]
    json.dump({
        'uid': uid,
        'folders': summary
    },
              open(OUT_PATH, 'w'),
              ensure_ascii=False,
              indent=1)
    print('SAVED', len(summary), 'folders ->', OUT_PATH)
    for f in summary:
        print(f['id'], f['title'], f['count'], 'attr=%d' % f['attr'])
