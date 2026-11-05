# fetch_folder_videos(driver, media_id, out_path=None) -> [{avid, bvid, title, upper, intro, fav_time, duration,
# ctime}], 20 per page, JSON when out_path is given.
# API: GET /x/v3/fav/resource/list?media_id=&pn=&ps=20&platform=web&order=mtime&type=0&tid=0
import json, time


def fetch_folder_videos(driver, media_id, out_path=None):
    all_medias, pn = [], 1
    while True:
        res = driver.execute_async_script(
            """
        var mid = arguments[0], pn = arguments[1];
        var cb = arguments[arguments.length - 1];
        fetch('https://api.bilibili.com/x/v3/fav/resource/list?media_id=' + mid + '&pn=' + pn + '&ps=20&platform=web&order=mtime&type=0&tid=0', {credentials: 'include'})
          .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
        """, media_id, pn)
        if not res or (isinstance(res, str) and res.startswith('ERR')):
            raise RuntimeError(res)
        data = json.loads(res).get('data') or {}
        for m in (data.get('medias') or []):
            all_medias.append({
                'avid': m['id'],
                'bvid': m.get('bvid'),
                'title': m['title'],
                'upper': (m.get('upper') or {}).get('name'),
                'intro': (m.get('intro') or '')[:200],
                'fav_time': m.get('fav_time'),
                'duration': m.get('duration'),
                'ctime': m.get('ctime'),
            })
        if not data.get('has_more'):
            break
        pn += 1
        time.sleep(1)
    if out_path:
        json.dump(all_medias,
                  open(out_path, 'w'),
                  ensure_ascii=False,
                  indent=1)
    return all_medias
