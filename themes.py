# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import json
import os

# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
from setting import Settings

# APP THEMES
# ///////////////////////////////////////////////////////////////
class Themes(object):
    # 保留类级别的默认设置，作为后备方案
    # ///////////////////////////////////////////////////////////////
    _default_settings = Settings()
    _default_theme_name = _default_settings.items.get('theme_name', 'default')
    _theme_name = _default_theme_name

    # INIT SETTINGS
    # ///////////////////////////////////////////////////////////////
    def __init__(self):
        super(Themes, self).__init__()

        # LOAD SETTINGS
        # ///////////////////////////////////////////////////////////////
        setup_settings = Settings()
        _settings = setup_settings.items

        # APP PATH
        # ///////////////////////////////////////////////////////////////
        json_file = f"themes/{_settings['theme_name']}.json"
        app_path = os.path.abspath(os.getcwd())
        self.settings_path = os.path.normpath(os.path.join(app_path, json_file))

        if not os.path.isfile(self.settings_path):
            print(f"WARNING: \"themes/{_settings['theme_name']}.json\" not found! check in the folder {self.settings_path}")
            # DICTIONARY WITH SETTINGS
            # 尝试使用默认主题作为后备
            if self._theme_name != self._default_theme_name:
                print(f"Falling back to default theme: {self._default_theme_name}")
                self._theme_name = self._default_theme_name
                json_file = f"themes/{self._theme_name}.json"
                self.settings_path = os.path.normpath(os.path.join(app_path, json_file))
            else:
                raise FileNotFoundError(f"Default theme file not found: {self.settings_path}")


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
        try:
            # READ JSON FILE
            with open(self.settings_path, "r", encoding='utf-8') as reader:
                settings = json.loads(reader.read())
                self.items = settings
        except Exception as e:
            print(f"Error loading theme file: {e}")
            self.items = self._get_default_colors()     # 可以在这里设置一些默认的颜色值作为后备




    def _get_default_colors(self):
        """提供默认的颜色配置作为后备方案"""
        return {
            "theme_name": self._theme_name,
            "app_color":
            {
                "light_one": "#ffffff",
                "light_two": "#F5F5F5",
                "light_three": "#F0F2F5",
                "light_four": "#DCDFE6",

                "dark_one": "#FFFFFF",
                "dark_two": "#F5F5F5",
                "dark_three": "#F5F5F5",
                "dark_four": "#FFFFFF",

                "bg_one": "#F5F5F5",
                "bg_two": "#FFFFFF",
                "bg_three": "#ECF5FF",

                "icon_color": "#606266",
                "icon_hover": "#303133",
                "icon_pressed": "#409EFF",
                "icon_active": "#409EFF",

                "context_color": "#409EFF",
                "context_hover": "#79BBFF",
                "context_pressed": "#337ECC",

                "text_title": "#303133",
                "text_foreground": "#303133",
                "text_description": "#606266",
                "text_active": "#409EFF",

                "black": "#000000",
                "white": "#ffffff",
                "pink": "#F89898",
                "green": "#67C23A",
                "red": "#F56C6C",
                "yellow": "#E6A23C"
            }
        }