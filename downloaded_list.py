import os
import json

DOWNLOADED_LIST_PATH = "output/downloaded_list.json"

####################
# ダウンロード済みリストの管理クラス
####################
class DownloadedListManager:
    @staticmethod
    # downloaded_list.jsonを読み込む
    def load():
        if not os.path.exists(DOWNLOADED_LIST_PATH):
            return {}
        try:
            with open(DOWNLOADED_LIST_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    @staticmethod
    # downloaded_list.jsonを保存する
    def save(data):
        os.makedirs("output", exist_ok=True)
        with open(DOWNLOADED_LIST_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    @staticmethod
    # 特定のアーティストの更新日を保存
    def update_artist(artist_name, updated_date):
        data = DownloadedListManager.load()
        data[artist_name] = updated_date
        DownloadedListManager.save(data)
    @staticmethod
    # 特定のアーティストの更新日を取得
    def get_artist_date(artist_name):
        data = DownloadedListManager.load()
        return data.get(artist_name, "")
    @staticmethod
    # 特定のアーティストを削除
    def remove_artist(artist_name):
        data = DownloadedListManager.load()
        if artist_name in data:
            del data[artist_name]
            DownloadedListManager.save(data)
            return True
        return False
