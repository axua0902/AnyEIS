# -*- coding: utf-8 -*-
# main.py
# Author: Zhang An
# Description: Main entry point for the AnyEIS application

import sys
import os
import ctypes

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt


# Import custom modules
from setting import Settings
from themes import Themes
from GUI.mainwindow.ui_main import UI_MainWindow
from GUI.mainwindow.setup_main_window import SetupMainWindow
from widgets.py_grips.py_grips import PyGrips



# 自动检测高分屏并设置缩放因子
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
if screen_width >= 3840:  # 4K分辨率
    os.environ["QT_SCALE_FACTOR"] = "2"
else:
    os.environ["QT_FONT_DPI"] = "110"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        settings = Settings()# Initialize application settings
        self.settings = settings.items

        themes = Themes()# Initialize theme settings
        self.themes = themes.items

        # settings.update_theme("default")  # Update the theme to "light" mode
        # settings.update_theme("dark")  # Update the theme to "light" mode
        settings.update_theme("light6")  # Update the theme to "light" mode

        self.ui = UI_MainWindow(self, self.settings, self.themes)   # Initialize main window GUI
        self.ui.setup_ui(self) # Setup UI components

        self.ui_config = SetupMainWindow(self.ui) # Initialize UI configuration
        self.ui_config.config_gui()# Configure UI

        self.dragPos = None

        # Add Grips 初始化窗口拖拽手柄
        self.hide_grips = True # Show/Hide resize grips
        if self.ui.settings["custom_title_bar"]:
            self.left_grip = PyGrips(self, "left", self.hide_grips)
            self.right_grip = PyGrips(self, "right", self.hide_grips)
            self.top_grip = PyGrips(self, "top", self.hide_grips)
            self.bottom_grip = PyGrips(self, "bottom", self.hide_grips)
            self.top_left_grip = PyGrips(self, "top_left", self.hide_grips)
            self.top_right_grip = PyGrips(self, "top_right", self.hide_grips)
            self.bottom_left_grip = PyGrips(self, "bottom_left", self.hide_grips)
            self.bottom_right_grip = PyGrips(self, "bottom_right", self.hide_grips)


        self.show() # Display window


    def mousePressEvent(self, event):# Override mouse press event to handle moving
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()
        super().mousePressEvent(event)


    def resizeEvent(self, event):# Override resize event to handle resizing
        if self.ui.settings["custom_title_bar"]:
            self.resize_grips()
        super().resizeEvent(event)

    # resize grips
    def resize_grips(self):
        if self.ui.settings["custom_title_bar"]:
            self.left_grip.setGeometry(5, 10, 10, self.height())
            self.right_grip.setGeometry(self.width() - 15, 10, 10, self.height())
            self.top_grip.setGeometry(5, 5, self.width() - 10, 10)
            self.bottom_grip.setGeometry(5, self.height() - 15, self.width() - 10, 10)
            self.top_right_grip.setGeometry(self.width() - 20, 5, 15, 15)
            self.bottom_left_grip.setGeometry(5, self.height() - 20, 15, 15)
            self.bottom_right_grip.setGeometry(self.width() - 20, self.height() - 20, 15, 15)


# Set the initial class and also additional parameters of the "QApplication" class
if __name__ == "__main__":

    app = QApplication(sys.argv) # APPLICATION
    app.setWindowIcon(QIcon("logo.png"))
    window = MainWindow()


    sys.exit(app.exec())# EXEC APP
