# download_covers(driver, aids, out_dir=None) -> [saved paths]; the cover URL comes from the view API, out_dir
# defaults to the system temp dir.
import json, tempfile, urllib.request


def download_covers(driver, aids, out_dir=None):
    out_dir = out_dir or tempfile.gettempdir()
    saved = []
    for aid in aids:
        res = driver.execute_async_script(
            """
        var aid = arguments[0];
        var cb = arguments[arguments.length - 1];
        fetch('https://api.bilibili.com/x/web-interface/view?aid=' + aid, {credentials: 'include'})
          .then(r => r.json()).then(j => cb((j.data || {}).pic || 'NOPIC')).catch(e => cb('ERR:' + e));
        """, aid)
        url = res.replace('http://', 'https://') if isinstance(res,
                                                               str) else None
        if not url or url == 'NOPIC' or url.startswith('ERR'):
            print('FAIL', aid, res)
            continue
        fn = '%s/bili_cover_%d.jpg' % (out_dir.rstrip('/'), aid)
        try:
            req = urllib.request.Request(url,
                                         headers={
                                             'User-Agent': 'Mozilla/5.0',
                                             'Referer':
                                             'https://www.bilibili.com/'
                                         })
            data = urllib.request.urlopen(req, timeout=20).read()
            open(fn, 'wb').write(data)
            saved.append(fn)
            print('SAVED', fn, len(data))
        except Exception as e:
            print('FAIL', aid, str(e)[:100])
    return saved
