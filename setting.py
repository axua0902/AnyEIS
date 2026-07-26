# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import json
import os


# APP SETTINGS
# ///////////////////////////////////////////////////////////////
class Settings(object):
    # APP PATH
    # ///////////////////////////////////////////////////////////////
    json_file = "base_settings.json"
    app_path = os.path.abspath(os.getcwd())
    # print(app_path)
    settings_path = os.path.normpath(os.path.join(app_path, json_file))
    # print(settings_path)
    if not os.path.isfile(settings_path):
        print(f"WARNING: \"settings.json\" not found! check in the folder {settings_path}")

    # INIT SETTINGS
    # ///////////////////////////////////////////////////////////////
    def __init__(self):
        super(Settings, self).__init__()

        # DICTIONARY WITH SETTINGS
        # Just to have objects references
        self.items = {}

        # DESERIALIZE
        self.deserialize()

    # SERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def serialize(self):
        # WRITE JSON FILE
        with open(self.settings_path, "w", encoding='utf-8') as write:
            json.dump(self.items, write, indent=4)

    # DESERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def deserialize(self):
        # READ JSON FILE
        with open(self.settings_path, "r", encoding='utf-8') as reader:
            settings = json.loads(reader.read())
            self.items = settings


    # CHANGE THEME
    # ///////////////////////////////////////////////////////////////
    def update_theme(self, theme_name):
        self.items["theme_name"] = theme_name
        self.serialize()

    # CHANGE LANGUAGE
    # ///////////////////////////////////////////////////////////////
    def update_language(self, language):
        self.items["language"] = language
        self.serialize()

    # GET WORKING PATH
    # ///////////////////////////////////////////////////////////////
    def get_working_path(self):
        return self.items.get("working_path")

    # CHANGE WORKING PATH
    # ///////////////////////////////////////////////////////////////
    def update_working_path(self, working_path):
        self.items["working_path"] = working_path
        self.serialize()

    # GET TOP SETTINGS
    # ///////////////////////////////////////////////////////////////
    def get_top_settings(self):
        return self.items.get("top_settings", {})

    # UPDATE PENDING DATA PATH
    # ///////////////////////////////////////////////////////////////
    def update_pending_data_path(self, path):
        if "top_settings" not in self.items:
            self.items["top_settings"] = {}
        if "paths" not in self.items["top_settings"]:
            self.items["top_settings"]["paths"] = {}
        self.items["top_settings"]["paths"]["pending_data"] = path
        self.serialize()

    # UPDATE REFERENCE DATA PATH
    # ///////////////////////////////////////////////////////////////
    def update_reference_data_path(self, path):
        if "top_settings" not in self.items:
            self.items["top_settings"] = {}
        if "paths" not in self.items["top_settings"]:
            self.items["top_settings"]["paths"] = {}
        self.items["top_settings"]["paths"]["reference_data"] = path
        self.serialize()

    # UPDATE RESULTS DATA PATH
    # ///////////////////////////////////////////////////////////////
    def update_results_data_path(self, path):
        if "top_settings" not in self.items:
            self.items["top_settings"] = {}
        if "paths" not in self.items["top_settings"]:
            self.items["top_settings"]["paths"] = {}
        self.items["top_settings"]["paths"]["results_data"] = path
        self.serialize()

    # UPDATE EXPORT IMAGE FORMAT
    # ///////////////////////////////////////////////////////////////
    def update_export_image_format(self, format):
        if "top_settings" not in self.items:
            self.items["top_settings"] = {}
        if "export_image" not in self.items["top_settings"]:
            self.items["top_settings"]["export_image"] = {}
        self.items["top_settings"]["export_image"]["format"] = format
        self.serialize()

    # UPDATE EXPORT IMAGE RESOLUTION
    # ///////////////////////////////////////////////////////////////
    def update_export_image_resolution(self, resolution):
        if "top_settings" not in self.items:
            self.items["top_settings"] = {}
        if "export_image" not in self.items["top_settings"]:
            self.items["top_settings"]["export_image"] = {}
        self.items["top_settings"]["export_image"]["resolution"] = resolution
        self.serialize()

    # EXPORT USER PREFERENCES
    # ///////////////////////////////////////////////////////////////
    def export_user_preferences(self, file_path):
        preferences = {
            "app_name": self.items.get("app_name"),
            "version": self.items.get("version"),
            "theme_name": self.items.get("theme_name"),
            "language": self.items.get("language"),
            "working_path": self.items.get("working_path"),
            "top_settings": self.items.get("top_settings", {})
        }
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(preferences, f, indent=4, ensure_ascii=False)
        return True

    # IMPORT USER PREFERENCES
    # ///////////////////////////////////////////////////////////////
    def import_user_preferences(self, file_path):
        if not os.path.exists(file_path):
            return False
        with open(file_path, "r", encoding='utf-8') as f:
            preferences = json.load(f)
        if "theme_name" in preferences:
            self.items["theme_name"] = preferences["theme_name"]
        if "language" in preferences:
            self.items["language"] = preferences["language"]
        if "working_path" in preferences:
            self.items["working_path"] = preferences["working_path"]
        if "top_settings" in preferences:
            if "top_settings" not in self.items:
                self.items["top_settings"] = {}
            self.items["top_settings"].update(preferences["top_settings"])
        self.serialize()
        return True