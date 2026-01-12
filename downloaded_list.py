import os
import json

DOWNLOADED_LIST_PATH = "output/downloaded_list.json"

class DownloadedListManager:
    @staticmethod
    def load():
        """downloaded_list.jsonを読み込む"""
        if not os.path.exists(DOWNLOADED_LIST_PATH):
            return {}
        try:
            with open(DOWNLOADED_LIST_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    @staticmethod
    def save(data):
        """downloaded_list.jsonを保存する"""
        os.makedirs("output", exist_ok=True)
        with open(DOWNLOADED_LIST_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    @staticmethod
    def update_artist(artist_name, updated_date):
        """特定のアーティストの更新日を保存"""
        data = DownloadedListManager.load()
        data[artist_name] = updated_date
        DownloadedListManager.save(data)
    
    @staticmethod
    def get_artist_date(artist_name):
        """特定のアーティストの更新日を取得"""
        data = DownloadedListManager.load()
        return data.get(artist_name, "")