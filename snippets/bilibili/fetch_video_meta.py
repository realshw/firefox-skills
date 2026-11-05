# fetch_video_meta(driver, vids, out_path=None) -> the same list with tname/desc/tags filled in (needs 'avid' and
# 'bvid'). Tags are the deciding signal when reshuffling — tname is empty these days.
# API: GET /x/web-interface/view?aid=, GET /x/tag/archive/tags?bvid=
import json, time


def fetch_video_meta(driver, vids, out_path=None):
    for i, m in enumerate(vids):
        aid, bvid = m['avid'], m.get('bvid')
        res = driver.execute_async_script(
            """
        var aid = arguments[0];
        var cb = arguments[arguments.length - 1];
        fetch('https://api.bilibili.com/x/web-interface/view?aid=' + aid, {credentials: 'include'})
          .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
        """, aid)
        if not res or (isinstance(res, str) and res.startswith('ERR')):
            raise RuntimeError('view %s: %s' % (aid, res))
        d = json.loads(res).get('data') or {}
        m['tname'] = d.get('tname')
        m['desc'] = (d.get('desc') or '')[:150]
        res2 = driver.execute_async_script(
            """
        var bv = arguments[0];
        var cb = arguments[arguments.length - 1];
        fetch('https://api.bilibili.com/x/tag/archive/tags?bvid=' + bv, {credentials: 'include'})
          .then(r => r.json()).then(j => cb(JSON.stringify(j))).catch(e => cb('ERR:' + e));
        """, bvid)
        j2 = json.loads(res2) if res2 and not (
            isinstance(res2, str) and res2.startswith('ERR')) else {}
        m['tags'] = [t['tag_name'] for t in (j2.get('data') or [])][:8]
        print('meta %d/%d' % (i + 1, len(vids)), bvid)
        time.sleep(0.8)
    if out_path:
        json.dump(vids, open(out_path, 'w'), ensure_ascii=False, indent=1)
    return vids
