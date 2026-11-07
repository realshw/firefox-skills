# fetch_video_meta(driver, vids, out_path=None) -> the same list with tname/desc/tags filled in; each entry
# needs 'avid' and gets its 'bvid' resolved when it is missing or empty. Tags are the deciding signal when
# reshuffling — tname is empty these days, and a title alone routinely points at the wrong folder.
# API: GET /x/web-interface/view?aid=, GET /x/tag/archive/tags?bvid=
import json
import time

from snippets.bilibili.api import fav_get


def fetch_video_meta(driver, vids, out_path=None):
    for i, m in enumerate(vids):
        aid = m['avid']
        if not m.get('bvid'):
            m['bvid'] = (fav_get(driver, '/x/web-interface/view',
                                 aid=aid).get('data') or {}).get('bvid') or ''
            time.sleep(0.4)
        d = fav_get(driver, '/x/web-interface/view', aid=aid).get('data') or {}
        m['tname'] = d.get('tname')
        m['desc'] = (d.get('desc') or '')[:150]
        tags = []
        if m['bvid']:
            tags = (fav_get(driver, '/x/tag/archive/tags',
                            bvid=m['bvid']).get('data') or [])
        m['tags'] = [t['tag_name'] for t in tags][:8]
        print('meta %d/%d' % (i + 1, len(vids)), m['bvid'], '|',
              ','.join(m['tags'][:6]))
        time.sleep(0.5)
    if out_path:
        json.dump(vids, open(out_path, 'w'), ensure_ascii=False, indent=1)
    return vids
