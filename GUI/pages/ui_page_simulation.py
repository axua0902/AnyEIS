from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# IMPORT SETTINGS
from setting import Settings
# IMPORT THEME COLORS
from  themes import Themes


from EIS.FigureFile.Figure import FigWidget
from EIS.SimulationFile.simulation import Simu
# from EIS.SimulationFile.referencedata import topRWidget

class Ui_SimulationPage(object):
    def __init__(self):
        settings = Settings()# LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()# LOAD THEME COLOR
        self.themes = themes.items

        # 设置页面 Simulation
        self.Simulation = QWidget()
        self.Simulation.setObjectName(u"Simulation")
        self.Simulation_layout = QHBoxLayout(self.Simulation)
        self.Simulation_layout.setSpacing(5)
        self.Simulation_layout.setObjectName(u"Simulation_layout")
        self.Simulation_layout.setContentsMargins(1, 1, 1, 1)

        # 初始化组件
        self.simWg = Simu()# 仿真组件
        self.figureWg = FigWidget()# 绘图组件

        # Simulation 页面(纯仿真模式)不区分原始/处理数据,关闭这两个无意义复选框
        self.figureWg.set_processing_state_enabled(False)

        # 左侧区域 - 仿真和参考数据
        self.left_widget = QWidget(self.Simulation)
        self.left_widget.setObjectName("LeftWidget")
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.addWidget(self.simWg)# 仿真区

        self.Simulation_layout.addWidget(self.left_widget, 6)

        self.left_widget.setStyleSheet(f"""
            QWidget#LeftWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 左侧背景 */
                border-radius: 6px;
            }}
        """)

        # 右侧区域 - figureWg 内容
        self.right_widget = QWidget(self.Simulation)
        self.right_widget.setObjectName("RightWidget")
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.addWidget(self.figureWg)
        self.Simulation_layout.addWidget(self.right_widget, 4)

        self.right_widget.setStyleSheet(f"""
            QWidget#RightWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 右侧背景 */
                border-radius: 6px;
            }}
        """)

        # 信号连接
        self.simWg.datasignal.connect(self.figureWg.getsignal)
        self.simWg.currentChanged.connect(self.on_simulation_tab_changed)

    def on_simulation_tab_changed(self, index):
        if index == 0:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Z,Phy,Rs,X')
        elif index == 1:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Epsilon,Sigma')
        elif index == 2:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Epsilon,Sigma')




















