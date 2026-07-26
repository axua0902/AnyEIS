# -*- coding: utf-8 -*-
# ui_main.py
# 描述: AnyEIS应用程序的主界面设置和配置

"""
应用程序布局结构说明
----------------
1. 主窗口层次结构（从外到内）：
   MainWindow (主窗口)
   └── central_widget (中央部件)
       └── window (PyWindow窗口)
           ├── left_menu_frame (左侧菜单框架)
           ├── left_column_frame (左侧栏框架)
           └── right_panel_frame (右侧应用框架)

2. 详细布局说明：
   A. 左侧菜单区域 (left_menu_frame)：
      left_menu_frame (左侧菜单区)
      ├── QHBoxLayout (水平布局)
      └── PyLeftMenu (自定义菜单组件)
          ├── icon_buttons (图标按钮)
          └── app_color (应用主题色)

   B. 左侧栏区域 (left_column_frame)：
      left_column_frame (左侧栏区)
      ├── QVBoxLayout (垂直布局)
      └── PyLeftColumn (自定义左栏组件)
          ├── text_title (标题文本)
          └── content_area (内容区域)

   C. 右侧应用区域 (right_panel_frame)：
      right_panel_frame (右侧主应用区)
      ├── title_bar_frame (顶部标题栏，固定高度40像素)
      ├── content_area_frame (内容显示区)
      │   ├── content_area_left_frame (左侧内容区)
      │   └── right_column_frame (右侧内容栏)
      └── credits_frame (底部版权栏，固定高度26像素)
"""

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

# Custom widgets imports
from widgets.py_window.py_window import PyWindow
from widgets.py_left_menu.py_left_menu import PyLeftMenu
from widgets.py_left_column.py_left_column import PyLeftColumn
from widgets.py_title_bar.py_title_bar import PyTitleBar
from widgets.py_credits_bar.py_credits import PyCredits

# UI components imports
from GUI.pages.ui_main_page import Ui_Pages
from GUI.columns.ui_right_column import Ui_RightColumn
from GUI.functions.functions import Functions

from .menu_config import add_left_menus_top, add_left_menus_bottom, add_title_bar_menus


class UI_MainWindow(object):
    #Main window UI configuration class.

    def __init__(self, MainWindow, settings, themes):
        """Initialize UI configuration.
        Args:
            MainWindow: Main window instance to configure
            settings: Settings instance
            themes: Themes instance
        """
        self.settings = settings
        self.themes = themes
        # Initialize Main Window
        self.MainWindow = MainWindow

    def setup_ui(self, MainWindow):
        """Set up the user interface components.
        Args:
            MainWindow: Main window instance to set up
        """

        # Set window name if not already set
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")

        # Configure initial window parameters
        MainWindow.setWindowTitle(self.settings["app_name"])
        MainWindow.resize(self.settings["startup_size"][0], self.settings["startup_size"][1])# 设置窗口初始大小
        MainWindow.setMinimumSize(self.settings["minimum_size"][0], self.settings["minimum_size"][1])# 设置窗口最小尺寸

        # Set up central widget，Add central widget to app
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f'''
            font: {self.settings["font"]["text_size"]}pt "{self.settings["font"]["family"]}";
            color: {self.themes["app_color"]["text_foreground"]};
        ''')
        self.central_widget_layout = QVBoxLayout(self.central_widget)

        if self.settings["custom_title_bar"]:
            self.central_widget_layout.setContentsMargins(2,2,2,2)# 设置中央部件的外边距
        else:
            self.central_widget_layout.setContentsMargins(0,0,0,0)#


        # Initialize custom window widget，Add inside PyWindow "layout" all Widgets
        self.main_window_frame = PyWindow(
            MainWindow,
            bg_color=self.themes["app_color"]["bg_one"],
            border_color=self.themes["app_color"]["bg_two"],
            text_color=self.themes["app_color"]["text_foreground"]
        )

        # Configure window style for non-custom title bar
        if not self.settings["custom_title_bar"]:
            self.main_window_frame.set_stylesheet(border_radius=0, border_size=0)

        # Add window to central widget
        self.central_widget_layout.addWidget(self.main_window_frame)

        # Configure left menu frame，Add here the custom left menu bar
        self.left_menu_frame = QFrame()
        left_menu_margin = self.settings["left_menu_content_margins"]
        left_menu_minimum = self.settings["left_menu_size"]["minimum"]
        self.left_menu_frame.setMaximumSize(left_menu_minimum + (left_menu_margin * 2), 17280)
        self.left_menu_frame.setMinimumSize(left_menu_minimum + (left_menu_margin * 2), 0)

        #############################################################################################
        # Set up left menu layout
        self.left_menu_layout = QHBoxLayout(self.left_menu_frame)
        self.left_menu_layout.setContentsMargins(
            left_menu_margin,
            left_menu_margin+1,
            left_menu_margin,
            left_menu_margin,
        )

        # Initialize left menu with theme colors， Add custom left menu here
        self.left_menu = PyLeftMenu(
            parent = self.left_menu_frame,
            app_parent = self.central_widget,  # For tooltip parent
            dark_one = self.themes["app_color"]["bg_one"],
            dark_three = self.themes["app_color"]["bg_three"],
            dark_four = self.themes["app_color"]["bg_four"],
            bg_one = self.themes["app_color"]["bg_one"],
            icon_color = self.themes["app_color"]["icon_color"],
            icon_color_hover = self.themes["app_color"]["icon_hover"],
            icon_color_pressed = self.themes["app_color"]["icon_pressed"],
            icon_color_active = self.themes["app_color"]["icon_active"],
            context_color = self.themes["app_color"]["context_color"],
            text_foreground = self.themes["app_color"]["text_foreground"],
            text_active = self.themes["app_color"]["text_active"]
        )

        ########添加页面####################
        self.left_menu.add_menus(add_left_menus_top)# from menu_config
        self.left_menu.add_menus(add_left_menus_bottom)# from menu_config


        self.left_menu_layout.addWidget(self.left_menu)


        #############################################################################################
        # Configure left column frame，Add here the left column with Stacked Widgets
        self.left_column_frame = QFrame()
        self.left_column_frame.setMaximumWidth(self.settings["left_column_size"]["minimum"])
        self.left_column_frame.setMinimumWidth(self.settings["left_column_size"]["minimum"])
        self.left_column_frame.setStyleSheet(f"background: {self.themes['app_color']['bg_two']}")

        # Set up left column layout
        self.left_column_layout = QVBoxLayout(self.left_column_frame)
        self.left_column_layout.setContentsMargins(0, 0, 0, 0)

        # Initialize left column with theme colors
        self.left_column = PyLeftColumn(
            MainWindow,
            app_parent=self.central_widget,
            text_title="Settings Left Frame",
            text_title_size=self.settings["font"]["title_size"],
            text_title_color=self.themes['app_color']['text_foreground'],
            icon_path=Functions.set_svg_icon("icon_settings.svg"),
            dark_one=self.themes['app_color']['dark_one'],
            bg_color=self.themes['app_color']['bg_three'],
            btn_color=self.themes['app_color']['bg_three'],
            btn_color_hover=self.themes['app_color']['bg_two'],
            btn_color_pressed=self.themes['app_color']['bg_one'],
            icon_color=self.themes['app_color']['icon_color'],
            icon_color_hover=self.themes['app_color']['icon_hover'],
            context_color=self.themes['app_color']['context_color'],
            icon_color_pressed=self.themes['app_color']['icon_pressed'],
            icon_close_path=Functions.set_svg_icon("icon_close.svg")
        )
        self.left_column_layout.addWidget(self.left_column)

        #############################################################################################
        # Configure right widgets frame， Add here the right widgets
        self.right_panel_frame = QFrame()

        # Set up right app layout
        self.right_panel_layout = QVBoxLayout(self.right_panel_frame)
        self.right_panel_layout.setContentsMargins(3,3,3,3)
        self.right_panel_layout.setSpacing(1)

        # Configure title bar frame
        self.title_bar_frame = QFrame()
        self.title_bar_frame.setMinimumHeight(40)
        self.title_bar_frame.setMaximumHeight(40)

        # Set up title bar layout
        self.title_bar_layout = QVBoxLayout(self.title_bar_frame)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Initialize title bar with theme colors
        self.title_bar = PyTitleBar(
            MainWindow,
            logo_width=100,
            app_parent=self.central_widget,
            logo_image="logo_top2_100x22.svg",
            bg_color=self.themes["app_color"]["bg_two"],
            div_color=self.themes["app_color"]["bg_three"],
            btn_bg_color=self.themes["app_color"]["bg_two"],
            btn_bg_color_hover=self.themes["app_color"]["bg_three"],
            btn_bg_color_pressed=self.themes["app_color"]["bg_one"],
            icon_color=self.themes["app_color"]["icon_color"],
            icon_color_hover=self.themes["app_color"]["icon_hover"],
            icon_color_pressed=self.themes["app_color"]["icon_pressed"],
            icon_color_active=self.themes["app_color"]["icon_active"],
            context_color=self.themes["app_color"]["context_color"],
            dark_one=self.themes["app_color"]["dark_one"],
            text_foreground=self.themes["app_color"]["text_foreground"],
            radius=2,
            font_family=self.settings["font"]["family"],
            title_size=self.settings["font"]["title_size"],
            is_custom_title_bar=self.settings["custom_title_bar"]
        )
        description = "AnyEIS - An EIS Research App based on Python"
        self.title_bar.title_label.setText(description)


        self.title_bar.add_menus(add_title_bar_menus)        # from menu_config


        self.title_bar_layout.addWidget(self.title_bar)

        #############################################################################################
        # Configure content area frame
        self.content_area_frame = QFrame()
        # Set up content area layout
        self.content_area_layout = QHBoxLayout(self.content_area_frame)
        self.content_area_layout.setContentsMargins(0,0,0,0)
        self.content_area_layout.setSpacing(0)


        # Configure left content frame
        self.content_area_left_frame = QFrame()

        ########################### Initialize main pages###############################################
        self.load_pages = Ui_Pages()
        self.load_pages.setupPages(self.content_area_left_frame)
        ########################### Initialize main pages###############################################


        # Configure right column frame
        # Note: minimum (0) is used for collapsed/closed state width
        #       maximum (240) is used for expanded/open state width
        #       The toggle animation in functions_main_window.py animates between these values
        self.right_column_frame = QFrame()
        self.right_column_frame.setMinimumWidth(self.settings["right_column_size"]["minimum"])
        self.right_column_frame.setMaximumWidth(self.settings["right_column_size"]["minimum"])

        # Set up right column layout
        self.content_area_right_layout = QVBoxLayout(self.right_column_frame)
        self.content_area_right_layout.setContentsMargins(5,5,5,5)
        self.content_area_right_layout.setSpacing(0)


        # Configure right column background frame
        self.content_area_right_bg_frame = QFrame()
        self.content_area_right_bg_frame.setObjectName("content_area_right_bg_frame")
        self.content_area_right_bg_frame.setStyleSheet(f'''
        #content_area_right_bg_frame {{
            border-radius: 8px;
            background-color: {self.themes["app_color"]["bg_two"]};
        }}
        ''')

        # Add right column background to layout
        self.content_area_right_layout.addWidget(self.content_area_right_bg_frame)

        # Initialize right column
        self.right_column = Ui_RightColumn()
        self.right_column.setupUi(self.content_area_right_bg_frame)

        # Add content to layout
        self.content_area_layout.addWidget(self.content_area_left_frame)
        self.content_area_layout.addWidget(self.right_column_frame)


        #############################################################################################
        # Configure credits frame
        self.credits_frame = QFrame()
        self.credits_frame.setMinimumHeight(26)
        self.credits_frame.setMaximumHeight(26)

        # Set up credits layout
        self.credits_layout = QVBoxLayout(self.credits_frame)
        self.credits_layout.setContentsMargins(0,0,0,0)

        # Initialize credits
        self.credits = PyCredits(
            bg_two = self.themes["app_color"]["bg_two"],
            copyright = self.settings["copyright"],
            version = self.settings["version"],
            font_family = self.settings["font"]["family"],
            text_size = self.settings["font"]["text_size_utralsmall"],
            text_description_color = self.themes["app_color"]["text_description"]
        )
        self.credits_layout.addWidget(self.credits)
        #############################################################################################


        # Add widgets to right layout
        self.right_panel_layout.addWidget(self.title_bar_frame)
        self.right_panel_layout.addWidget(self.content_area_frame)
        self.right_panel_layout.addWidget(self.credits_frame)


        # Add widgets to window
        self.main_window_frame.layout.addWidget(self.left_menu_frame)
        self.main_window_frame.layout.addWidget(self.left_column_frame)
        self.main_window_frame.layout.addWidget(self.right_panel_frame)

        # Set central widget and content margins
        MainWindow.setCentralWidget(self.central_widget)

        MainWindow.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        MainWindow.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


