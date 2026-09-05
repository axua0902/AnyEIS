from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# IMPORT SETTINGS
from setting import Settings
# IMPORT THEME COLORS
from  themes import Themes


from EIS.InputFile.Input import inputWidget
from EIS.FilterFile.Filter import Datafilter
from EIS.FigureFile.Figure import FigWidget
from EIS.ProcessingFile.Processing import Dataprocess

class Ui_ProcessingPage(object):
    def __init__(self):
        settings = Settings()# LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()# LOAD THEME COLOR
        self.themes = themes.items

        # 设置页面 Processing
        self.Processing = QWidget()
        self.Processing.setObjectName(u"Processing")
        self.Processing_layout = QHBoxLayout(self.Processing) # 1.left_layout 2.middle_layout 3.right_layout
        self.Processing_layout.setSpacing(5)
        self.Processing_layout.setObjectName(u"Processing_layout")
        self.Processing_layout.setContentsMargins(1, 1, 1, 1)

        # 初始化inputWidget和FigWidget
        self.inputWg = inputWidget()# 数据输入区
        self.filterWg=Datafilter()#滤波区
        self.dataprocessWg=Dataprocess()#数据处理区域
        self.figureWg=FigWidget()#绘图区


        # 左侧区域 - 数据输入和拟合处理
        self.left_widget = QWidget(self.Processing)
        self.left_widget.setObjectName("LeftWidget")
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.addWidget(self.inputWg)# 左侧数据输入区
        self.Processing_layout.addWidget(self.left_widget, 3)

        self.left_widget.setStyleSheet(f"""
            QWidget#LeftWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 左侧背景 */
                border-radius: 6px;
            }}
        """)

        # 中间区域 - 数据处理区
        self.middle_widget = QWidget(self.Processing)
        self.middle_widget.setObjectName("MiddleWidget")
        self.middle_layout = QVBoxLayout(self.middle_widget)
        self.middle_layout.addWidget(self.filterWg,1)# 中间滤波区
        self.middle_layout.addWidget(self.dataprocessWg,5)# 中间数据处理区
        self.Processing_layout.addWidget(self.middle_widget, 4)

        self.middle_widget.setStyleSheet(f"""
            QWidget#MiddleWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 中间背景 */
                border-radius: 6px;
            }}
        """)

        # 右侧区域 - 绘图
        self.right_widget = QWidget(self.Processing)
        self.right_widget.setObjectName("RightWidget")
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.addWidget(self.figureWg)# 右侧
        self.Processing_layout.addWidget(self.right_widget, 3)

        self.right_widget.setStyleSheet(f"""
            QWidget#RightWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};      /* 右侧背景 */
                border-radius: 6px;
            }}
        """)

        # 建立信号连接链：Input → Filter → Processing → Figure
        self.inputWg.datasignal.connect(self.filterWg.getsingal)        # 从输入类向过滤类发送数据
        self.filterWg.Apdatasignal.connect(self.dataprocessWg.getsingal) # 从过滤类向数据处理类发送数据
        self.dataprocessWg.Apdatasignal.connect(self.figureWg.getsignal) # 从数据处理类向绘制图表类发送数据

        # Original/Processed 复选框互斥逻辑：
        # - Process 勾选时 (Process 模块激活) -> 启用互斥，数据可能改变类型 (EIS→DS) 需强制单选
        # - Process 未勾选时 (仅 Filter 激活) -> 关闭互斥，允许两者同时勾选用于对比
        self.dataprocessWg.processui.processCheckBox.stateChanged.connect(
            lambda state: self.figureWg.set_mutual_exclusion_enabled(bool(state))
        )