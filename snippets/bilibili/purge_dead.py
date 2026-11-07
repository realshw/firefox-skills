# purge_dead(driver) -> [(folder, avid)]; a dead item stays behind under the exact title "已失效视频" — the only
# reliable handle. Needs remove_from_folder; safe to run when nothing is dead.
from snippets.bilibili.api import fav_folders, folder_medias
from snippets.bilibili.remove_from_folder import remove_from_folder


def purge_dead(driver):
    folders = fav_folders(driver)
    dead = []
    for f in folders:
        for m in folder_medias(driver, f['id']):
            if m['title'] == '已失效视频':
                dead.append((f['title'], m['id']))
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
