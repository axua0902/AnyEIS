from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# IMPORT SETTINGS
from setting import Settings
# IMPORT THEME COLORS
from  themes import Themes


from EIS.InputFile.Input import inputWidget
from EIS.FigureFile.Figure import FigWidget

#PLOTTING
class Ui_PlottingPage(object):
    def __init__(self):
        settings = Settings()# LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()# LOAD THEME COLOR
        self.themes = themes.items


        # 设置页面 Plotting
        self.Plotting = QWidget()
        self.Plotting.setObjectName(u"Plotting")
        self.Plotting_layout = QHBoxLayout(self.Plotting)# 1.left_widget 2.right_widget
        self.Plotting_layout.setSpacing(2)
        self.Plotting_layout.setObjectName(u"Plotting_layout")
        self.Plotting_layout.setContentsMargins(1, 1, 1, 1)
        

        # 初始化inputWidget和FigWidget
        self.inputWg = inputWidget()#左侧数据输入区
        self.figureWg= FigWidget()#右侧绘图区



        # 左侧区域 - inputWg 内容
        self.left_widget = QWidget(self.Plotting)
        self.left_widget.setObjectName("LeftWidget")
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.addWidget(self.inputWg)##插入inputWg 内容
        self.Plotting_layout.addWidget(self.left_widget,4)# 左侧占4成

        self.left_widget.setStyleSheet(f"""
            QWidget#LeftWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 左侧背景 */
                border-radius: 6px;
            }}
        """)


        # 右侧区域 - figureWg 内容
        self.right_widget = QWidget(self.Plotting)
        self.right_widget.setObjectName("RightWidget")
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.addWidget(self.figureWg)####插入figureWg
        self.Plotting_layout.addWidget(self.right_widget,6)# 右侧占6成

        self.right_widget.setStyleSheet(f"""
            QWidget#RightWidget {{
            background-color: {self.themes["app_color"]["bg_two"]};      /* 右侧背景 */
            border-radius: 6px;
        }}
        """)

        self.inputWg.datasignal.connect(self.figureWg.getsignal)###从输入类向绘制图表类发送数据

















