# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import sys
import os

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtSvgWidgets import *



# MAIN FUNCTIONS
# ///////////////////////////////////////////////////////////////
from GUI.mainwindow.functions_main_window import MainFunctions
from GUI.functions.functions import Functions


class SetupMainWindow():

    def __init__(self, ui):
        self.ui = ui

    # SETUP MAIN WINDOW WITH CUSTOM PARAMETERS
    def config_gui(self):
        self.init_ui()
        self.setup_signals()        # 初始化信号与槽函数绑定


    # 初始化
    def init_ui(self):
        # 初始化页面配置
        MainFunctions.set_page(self,self.ui.load_pages.home_page.page_home)

        # 初始化左侧菜单
        MainFunctions.set_left_column_menu(
            self,
            menu = self.ui.left_column.menus.menu_info,
            title = "Information",
            icon_path = Functions.set_svg_icon("icon_info.svg")
        )
        # 初始化右侧菜单
        MainFunctions.set_right_column_menu(self,self.ui.right_column.menu_1)



    # 信号与槽函数绑定
    def setup_signals(self):
        self.ui.left_menu.clicked.connect(self.on_button_clicked)
        self.ui.left_menu.released.connect(self.on_button_released)

        self.ui.left_column.clicked.connect(self.on_button_clicked)
        self.ui.left_column.released.connect(self.on_button_released)

        self.ui.title_bar.clicked.connect(self.on_button_clicked)
        self.ui.title_bar.released.connect(self.on_button_released)



    # ON BUTTON CLICKED
    def on_button_clicked(self,btn):
        MainFunctions.btn_clicked(self,btn)

    # ON BUTTON RELEASED
    def on_button_released(self,btn):
        MainFunctions.btn_released(self,btn)





