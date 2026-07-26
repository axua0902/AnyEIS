from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtSvgWidgets import *

from GUI.functions.functions import Functions

class Ui_MainPagesHome(object):
    def __init__(self):
        # 创建主页面 QWidget
        self.page_home = QWidget()
        self.page_home.setObjectName(u"page_home")

        # 主页面的垂直布局
        self.page_home_layout = QVBoxLayout(self.page_home)
        self.page_home_layout.setSpacing(1)
        self.page_home_layout.setObjectName(u"page_home_layout")
        self.page_home_layout.setContentsMargins(2, 2, 2, 2)

        # 欢迎区域的 QFrame
        self.welcome_base = QFrame(self.page_home)
        self.welcome_base.setObjectName(u"welcome_base")
        self.welcome_base.setMinimumSize(QSize(350, 150))
        self.welcome_base.setMaximumSize(QSize(350, 150))
        self.welcome_base.setFrameShape(QFrame.Shape.NoFrame)
        self.welcome_base.setFrameShadow(QFrame.Shadow.Raised)

        # 欢迎区域的垂直布局
        self.center_page_layout = QVBoxLayout(self.welcome_base)
        self.center_page_layout.setSpacing(10)
        self.center_page_layout.setObjectName(u"center_page_layout")
        self.center_page_layout.setContentsMargins(0, 0, 0, 0)

        # logo 区域的 QFrame
        self.logo = QFrame(self.welcome_base)
        self.logo.setObjectName(u"logo")
        self.logo.setMinimumSize(QSize(350, 150))
        self.logo.setMaximumSize(QSize(350, 150))
        self.logo.setFrameShape(QFrame.Shape.NoFrame)
        self.logo.setFrameShadow(QFrame.Shadow.Raised)

        # logo 区域的垂直布局
        self.logo_layout = QVBoxLayout(self.logo)
        self.logo_layout.setSpacing(0)
        self.logo_layout.setObjectName(u"logo_layout")
        self.logo_layout.setContentsMargins(0, 0, 0, 0)

        # 将 logo 区域添加到欢迎区域布局
        self.center_page_layout.addWidget(self.logo)


        # 加载 SVG 格式的 logo 图标
        self.logo_svg = QSvgWidget(Functions.set_svg_image("logo_home.svg"))
        self.logo_layout.addWidget(self.logo_svg, Qt.AlignmentFlag.AlignCenter, Qt.AlignmentFlag.AlignCenter)


        # 将欢迎区域添加到主页面布局，并居中显示
        self.page_home_layout.addWidget(self.welcome_base, 0, Qt.AlignmentFlag.AlignHCenter)