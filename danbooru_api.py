import os
import time
import requests

def _create_settion():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "DanbooruDownloader/1.0 (by yosxpeee)"
    })
    return session

# アーティスト検索
def getArtistInfobyName(page, searchKey):
    username = page.settings["account"]["username"]
    api_key = page.settings["account"]["api_key"]
    session = _create_settion()
    r = session.get(
        f"https://danbooru.donmai.us/artists.json?search[name]={searchKey}",
        auth=(username, api_key),
        timeout=30
    )
    r.raise_for_status()
    posts = r.json()
    return posts

# ダウンロードする
def downloadItems(page, artistName, log_callback=None):
    username = page.settings["account"]["username"]
    api_key = page.settings["account"]["api_key"]
    session = _create_settion()
    os.makedirs("output/"+artistName, exist_ok=True)
    page_num = 1
    total_downloaded = 0
    
    if log_callback:
        log_callback(f"「{artistName}」のダウンロードを開始します")
    
    while True:
        params = {
            "tags": f"{artistName}",
            "limit": 100,
            "page": page_num
        }
        r = session.get(
            "https://danbooru.donmai.us/posts.json",
            params=params,
            auth=(username, api_key),
            timeout=30
        )
        r.raise_for_status()
        posts = r.json()
        if not posts:
            if log_callback:
                log_callback("これ以上の投稿はありません")
            break
        for post in posts:
            file_url = post.get("file_url")
            if not file_url:
                continue
            post_id = post["id"]
            ext = os.path.splitext(file_url)[1]
            img_path = os.path.join("output/"+artistName, f"{post_id}{ext}")
            tag_path = os.path.join("output/"+artistName, f"{post_id}.txt")
            
            # 画像ファイルが存在しない場合のみダウンロード
            if not os.path.exists(img_path):
                img = session.get(file_url, timeout=30)
                img.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(img.content)
            
            # タグファイル書き込み
            with open(tag_path, "w", encoding="utf-8") as f:
                tag_string = post.get("tag_string", "")
                tags = tag_string.split()
                tags_with_artist = [item for item in tags if item == artistName]
                tags_without_artist = [item for item in tags if item != artistName]
                corrected_tags = tags_with_artist + tags_without_artist
                corrected_tags = [s.replace("_", " ") for s in corrected_tags]
                f.write(", ".join(corrected_tags))
            
            total_downloaded += 1
            if log_callback:
                log_callback(f"Saved {post_id}")
            else:
                print(f"Saved {post_id}")
        
        page_num += 1
        time.sleep(1)
    
    if log_callback:
        log_callback(f"ダウンロード完了: {total_downloaded}枚")
    
    return total_downloaded