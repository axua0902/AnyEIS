from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import os
import sys
from PySide6.QtCore import QProcess

# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
from setting import Settings
# IMPORT THEME COLORS
# ///////////////////////////////////////////////////////////////
from  themes import Themes

from widgets.py_push_button.py_push_button2 import PyPushButton2
from GUI.functions.functions import Functions

# LEFT COLUMN
# ///////////////////////////////////////////////////////////////
class Ui_LeftSetting(object):
    def __init__(self):
        # LOAD SETTINGS
        # ///////////////////////////////////////////////////////////////
        settings = Settings()
        self.settings = settings.items

        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items


        self.settings_obj = Settings()  # 保存Settings实例
        self.settings = self.settings_obj.items


        # theme buttons
        # theme_dark
        self.theme_dark = PyPushButton2(
            text=" Dark",
            font_size=self.settings["font"]["text_size_large"],
            font_weight=700,
            radius=8,
            font_color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"],
            border_color=self.themes["app_color"]["dark_one"]
        )
        self.icon = QIcon(Functions.set_svg_icon("icon_settings.svg"))
        self.theme_dark.setIcon(self.icon)
        self.theme_dark.setMaximumHeight(80)
        self.theme_dark.setMinimumHeight(80)
        self.theme_dark.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


        # theme_light
        self.theme_light = PyPushButton2(
            text="light",
            font_size=self.settings["font"]["text_size_large"],
            font_weight=700,
            radius=8,
            font_color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["light_one"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["light_four"],
            border_color=self.themes["app_color"]["light_one"]
        )
        self.icon = QIcon(Functions.set_svg_icon("icon_settings.svg"))
        self.theme_light.setIcon(self.icon)
        self.theme_light.setMaximumHeight(80)
        self.theme_light.setMinimumHeight(80)
        self.theme_light.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.theme_dark.clicked.connect(lambda: self.on_theme_update_clicked("dark"))
        self.theme_light.clicked.connect(lambda: self.on_theme_update_clicked("light"))


        #SETTING BUTTON
        # BTN Working path
        self.left_btn_working_path = PyPushButton2(
            text="Working path",
            font_size=self.settings["font"]["text_size_large"],
            font_weight=700,
            radius=8,
            font_color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"],
            border_color=self.themes["app_color"]["dark_one"]
        )
        self.left_btn_working_path.setMaximumHeight(80)
        self.left_btn_working_path.setMinimumHeight(80)
        self.left_btn_working_path.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


        # BTN Language
        self.left_btn_language = PyPushButton2(
            text="Language",
            font_size=self.settings["font"]["text_size_large"],
            font_weight=700,
            radius=8,
            font_color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"],
            border_color=self.themes["app_color"]["dark_one"]
        )
        self.left_btn_language.setMaximumHeight(80)
        self.left_btn_language.setMinimumHeight(80)
        self.left_btn_language.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # BTN 2
        self.left_btn_2 = PyPushButton2(
            text="Help",
            font_size=self.settings["font"]["text_size_large"],
            font_weight=700,
            radius=8,
            font_color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"],
            border_color=self.themes["app_color"]["dark_one"]
        )
        self.icon = QIcon(Functions.set_svg_icon("icon_settings.svg"))
        self.left_btn_2.setIcon(self.icon)
        self.left_btn_2.setMaximumHeight(80)
        self.left_btn_2.setMinimumHeight(80)
        self.left_btn_2.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)



        # BTN 3 - Default QPushButton
        self.left_btn_3 = PyPushButton2(
            text="About",
            font_size=self.settings["font"]["text_size_large"],
            font_weight=700,
            radius=8,
            font_color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"],
            border_color=self.themes["app_color"]["dark_one"]
        )
        self.icon = QIcon(Functions.set_svg_icon("icon_settings.svg"))
        self.left_btn_3.setIcon(self.icon)
        self.left_btn_3.setMaximumHeight(80)
        self.left_btn_3.setMinimumHeight(80)
        self.left_btn_3.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)







    def on_theme_update_clicked(self, theme_name):
        settings = Settings()
        settings.update_theme(theme_name)
        print(f"Theme {theme_name} has been updated. Restarting...")
        self.restart_application()

    def restart_application(self):
        program = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        working_dir = os.getcwd()
        window = QApplication.activeWindow()
        if window:
            window.close()
        QApplication.processEvents()
        QProcess.startDetached(program, [script_path], working_dir)
        QApplication.quit()
        sys.exit(0)

    def on_working_path_clicked(self):
        settings = Settings()
        current_path = settings.get_working_path()
        msg = QMessageBox()
        msg.setWindowTitle("Working Path / 工作路径")
        msg.setText(f"Current working path:\n{current_path}")
        msg.setInformativeText("Select a new working directory:")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        dialog = QFileDialog(None, "Select Working Directory", current_path)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly)

        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            settings.update_working_path(selected_path)
            QMessageBox.information(None, "Success", f"Working path changed to:\n{selected_path}")
        else:
            pass

    def on_language_clicked(self):
        settings = Settings()
        current_lang = settings.items.get("language", "en")
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Language / 语言")
        msg_box.setText("Select Language / 选择语言")

        chinese_btn = msg_box.addButton("中文", QMessageBox.ButtonRole.AcceptRole)
        english_btn = msg_box.addButton("English", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel / 取消", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()

        if msg_box.clickedButton() == chinese_btn:
            settings.update_language("zh")
            QMessageBox.information(None, "Language / 语言", "Language changed to Chinese / 语言已切换到中文")
        elif msg_box.clickedButton() == english_btn:
            settings.update_language("en")
            QMessageBox.information(None, "Language / 语言", "Language changed to English / 语言已切换到英文")

    def on_help_clicked(self):
        pdf_path = os.path.join(os.getcwd(), "Manual_EN.pdf")
        if os.path.exists(pdf_path):
            os.startfile(pdf_path)
        else:
            QMessageBox.warning(None, "Help / 帮助", f"PDF file not found: {pdf_path}")

    def on_about_clicked(self):
        about_info = """
        <h3>AnyEIS</h3>
        <p>Version: v1.0.0</p>
        <p>© 2023-2025 AnyEIS Authors. All rights reserved.</p>
        <p><a href="https://opensource.org/licenses/MIT">License: MIT License</a></p>
        <hr>
        <p><b>Official Website:</b> <a href="https://anyeis.org">https://anyeis.org</a></p>
        <p><b>Support Email:</b> support@anyeis.org</p>
        <p><b>GitHub:</b> <a href="https://github.com/zhan9013/AnyEIS">github.com/zhan9013/AnyEIS</a></p>
        <hr>
        <p><b>Contributors:</b> Zhang San, Li Si, Wang Wu</p>
        <p><b>Developer:</b> AnyEIS Authors</p>
        <p><b>Release Date:</b> 2025-06-26</p>
        <hr>
        <p>Acknowledgements: Thanks to all testers and community supporters.</p>
        <hr>
        <p><b>Dependencies:</b><br>
        PySide6 >= 6.5, numpy >= 1.24, pandas >= 2.0,<br>
        matplotlib >= 3.7, xlsxwriter >= 3.1, lmfit >= 1.2,<br>
        schemdraw >= 0.18, scipy >= 1.10, mpmath >= 1.3</p>
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle("About AnyEIS")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(about_info)
        msg_box.exec()
