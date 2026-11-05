# purge_dead(driver) -> [(folder, avid)]; a dead item stays behind under the exact title "已失效视频" — the only
# reliable handle. Needs remove_from_folder; safe to run when nothing is dead.
import json
import time
from snippets.bilibili.remove_from_folder import remove_from_folder


def purge_dead(driver):
    uid = driver.get_cookie('DedeUserID')['value']
    res = driver.execute_async_script(
        """
    var uid = arguments[0], cb = arguments[arguments.length - 1];
    fetch('https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=' + uid,
          {credentials: 'include'})
      .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
    """, uid)
    folders = (json.loads(res).get('data') or {}).get('list') or []
    dead = []
    for f in folders:
        pn = 1
        while True:
            r = driver.execute_async_script(
                """
            var mid = arguments[0], pn = arguments[1];
            var cb = arguments[arguments.length - 1];
            fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid +
                  '&pn=' + pn + '&ps=20&platform=web&order=mtime&type=0&tid=0',
                  {credentials: 'include'})
              .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
            """, f['id'], pn)
            d = json.loads(r).get('data') or {}
            for m in (d.get('medias') or []):
                if m['title'] == '已失效视频':
                    dead.append((f['title'], m['id']))
            if not d.get('has_more'):
                break
            pn += 1
            time.sleep(0.6)
        time.sleep(0.4)
    for title, avid in dead:
        print('DEAD', title, avid)
    by_folder = {}
    for title, avid in dead:
        by_folder.setdefault(title, []).append(avid)
    mid = {f['title']: f['id'] for f in folders}
    for title, aids in by_folder.items():
        remove_from_folder(driver, aids, mid[title], sleep_s=1.0)
    print('PURGED', len(dead))
    return dead
