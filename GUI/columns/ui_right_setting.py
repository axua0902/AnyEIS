from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
from setting import Settings
# IMPORT THEME COLORS
# ///////////////////////////////////////////////////////////////
from  themes import Themes

from widgets.py_push_button.py_push_button import PyPushButton
from GUI.functions.functions import Functions
from GUI.mainwindow.functions_main_window import MainFunctions


# RIGHT COLUMN
# ///////////////////////////////////////////////////////////////
class Ui_RightColumn(object):
    def __init__(self):
        # LOAD SETTINGS
        # ///////////////////////////////////////////////////////////////
        settings = Settings()
        self.settings = settings.items

        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items



        # BTN 1
        self.right_btn_1 = PyPushButton(
            text="Show Menu 2",
            radius=8,
            color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"]
        )
        self.icon_right = QIcon(Functions.set_svg_icon("icon_arrow_right.svg"))
        self.right_btn_1.setIcon(self.icon_right)
        self.right_btn_1.setMaximumHeight(40)
        self.right_btn_1.clicked.connect(lambda: MainFunctions.set_right_column_menu(self,
            # self.ui.right_column.menu_2
        ))
        # self.ui.right_column.btn_1_layout.addWidget(self.right_btn_1)

        # BTN 2
        self.right_btn_2 = PyPushButton(
            text="Show Menu 1",
            radius=8,
            color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_hover=self.themes["app_color"]["dark_three"],
            bg_color_pressed=self.themes["app_color"]["dark_four"]
        )
        self.icon_left = QIcon(Functions.set_svg_icon("icon_arrow_left.svg"))
        self.right_btn_2.setIcon(self.icon_left)
        self.right_btn_2.setMaximumHeight(40)
        self.right_btn_2.clicked.connect(lambda: MainFunctions.set_right_column_menu(self,
            # self.ui.right_column.menu_1
        ))
        # self.ui.right_column.btn_2_layout.addWidget(self.right_btn_2)