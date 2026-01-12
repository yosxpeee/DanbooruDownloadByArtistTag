import os
import json

SETTING_JSON_FILE = "settings.json"

class SettingsManager:
    @staticmethod
    def load():
        settings = {}
        if os.path.exists(SETTING_JSON_FILE):
            with open(SETTING_JSON_FILE, 'r') as f:
                settings = json.load(f)
        # Danbooruアカウント情報
        if "account" not in settings:
            settings["account"] = {}
        if "username" not in settings["account"]:
            settings["account"]["username"] = "Input username"
        if "api_key" not in settings["account"]:
            settings["account"]["api_key"] = "Input api key"
        return settings
    @staticmethod
    def save(settings):
        with open(SETTING_JSON_FILE, 'w') as f:
            json.dump(settings, f, indent=4)