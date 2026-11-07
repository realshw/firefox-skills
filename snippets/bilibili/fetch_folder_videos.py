# fetch_folder_videos(driver, media_id, out_path=None) -> [{avid, bvid, title, upper, intro, fav_time,
# duration, ctime}], JSON when out_path is given. The one-folder slice of dump_all, with the fields worth
# reading when deciding what a video is; dump_all covers the whole account.
import json

from snippets.bilibili.api import folder_medias


def fetch_folder_videos(driver, media_id, out_path=None):
    all_medias = [{
        'avid': m['id'],
        'bvid': m.get('bvid'),
        'title': m['title'],
        'upper': (m.get('upper') or {}).get('name'),
        'intro': (m.get('intro') or '')[:200],
        'fav_time': m.get('fav_time'),
        'duration': m.get('duration'),
        'ctime': m.get('ctime'),
    } for m in folder_medias(driver, media_id)]
    if out_path:
        json.dump(all_medias,
                  open(out_path, 'w'),
                  ensure_ascii=False,
                  indent=1)
    return all_medias
