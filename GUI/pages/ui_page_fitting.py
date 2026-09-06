from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# IMPORT SETTINGS
from setting import Settings
# IMPORT THEME COLORS
from  themes import Themes


from EIS.InputFile.Input import inputWidget
from EIS.FigureFile.Figure import FigWidget
from EIS.FittingFile.Fitting import Fitting
from EIS.FittingFile.FittingSetRes import settingWidget, resultWidget

class Ui_FittingPage(object):
    def __init__(self):
        settings = Settings()# LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()# LOAD THEME COLOR
        self.themes = themes.items

        # 设置页面 Fitting
        self.Fitting = QWidget()
        self.Fitting.setObjectName(u"Fitting")
        self.Fitting_layout = QHBoxLayout(self.Fitting)
        self.Fitting_layout.setSpacing(2)
        self.Fitting_layout.setObjectName(u"Fitting_layout")
        self.Fitting_layout.setContentsMargins(1, 1, 1, 1)

        # 初始化各个组件
        self.inputWg = inputWidget()# 数据输入区
        self.FittingWg = Fitting()# 拟合处理区

        self.settingWg = settingWidget()# 设置区
        self.resultsWg = resultWidget()# 结果区
        self.figureWg = FigWidget()# 绘图区
        
        # 建立连接引用
        self.FittingWg.set_setting_widget(self.settingWg)


        # 左侧区域 - 数据输入和拟合处理
        self.left_widget = QWidget(self.Fitting)
        self.left_widget.setObjectName("LeftWidget")
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.addWidget(self.inputWg)# 左侧上部数据输入区
        self.Fitting_layout.addWidget(self.left_widget, 2)

        self.left_widget.setStyleSheet(f"""
            QWidget#LeftWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 左侧背景 */
                border-radius: 6px;
            }}
        """)

        # 中间区域-设置和结果
        self.middle_widget = QWidget(self.Fitting)
        self.middle_widget.setObjectName("MiddleWidget")
        self.middle_layout = QVBoxLayout(self.middle_widget)
        self.middle_layout.setSpacing(1)
        self.middle_layout.setContentsMargins(0, 0, 0, 0)
        
        self.middle_layout.addWidget(self.FittingWg)# 上部拟合处理区域
        self.middle_layout.addWidget(self.settingWg)# 中部设置区
        self.middle_layout.addWidget(self.resultsWg)# 下部结果区

        # 设置各区域高度
        self.settingWg.setFixedHeight(100)   # 压缩设置区
        self.resultsWg.setFixedHeight(170)   # 压缩结果区
        self.middle_layout.setStretch(0, 0)  # FittingWg 固定
        self.middle_layout.setStretch(1, 0)  # settingWg 固定高度
        self.middle_layout.setStretch(2, 0)  # resultsWg 固定

        self.Fitting_layout.addWidget(self.middle_widget, 4)
        self.FittingWg.setMinimumHeight(550)  # 设置更大的最小高度
        self.middle_widget.setStyleSheet(f"""
            QWidget#MiddleWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 中间背景 */
                border-radius: 6px;
            }}
        """)







        # 右侧区域 -绘图 
        self.right_widget = QWidget(self.Fitting)
        self.right_widget.setObjectName("RightWidget")
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.addWidget(self.figureWg)
        self.Fitting_layout.addWidget(self.right_widget, 4)

        self.right_widget.setStyleSheet(f"""
            QWidget#RightWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 右侧背景 */
                border-radius: 6px;
            }}
        """)

        # 信号连接
        self.inputWg.datasignal.connect(self.FittingWg.getsignal)# 从输入类向拟合类发送数据
        self.settingWg.Settingsignal.connect(self.FittingWg.getsignal)# 设置类向拟合类发送数据
        self.FittingWg.Fittingdatasignal.connect(self.figureWg.getsignal)# 从拟合类向绘制图表类发送数据
        self.FittingWg.Fittingdatasignal.connect(self.resultsWg.getsingal)# 从拟合类向结果类发送数据

        # Tab 切换时同步 figure 数据类型下拉框
        self.FittingWg.currentChanged.connect(self.on_fitting_tab_changed)

    def on_fitting_tab_changed(self, index):
        if index == 0:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Z,Phase,Re(Z),Im(Z)')
        elif index == 1:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Epsilon,Sigma')
















