from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget, QFrame, QComboBox
from PySide6.QtCore import QSize

from widgets.py_push_button.py_push_button2 import PyPushButton2    # 自定义按钮
from widgets.py_table_widget.py_table_widget2 import PyTableWidget2  # 自定义表格组件
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2          # 自定义输入框
from widgets.py_qcheckbox.py_qcheckbox2 import PyCheckBox2         # 自定义复选框
from widgets.py_combobox.py_combobox2 import PyComboBox2           # 自定义下拉框
from widgets.py_label.py_label2 import PyLabel2
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2    
# 导入设置和主题
from setting import Settings  # 应用设置
from themes import Themes     # 主题颜色

# 导入分离的UI组件
from .FilterMethodUIs import FilterMethodUIs



class DatafilterUI(object):
    def __init__(self):
        self.parent_filter_instance = None
    
    def set_parent_filter_instance(self, parent_instance):
        """设置父Filter实例的引用，用于信号连接"""
        self.parent_filter_instance = parent_instance
    
    def DatafilterUI(self, widget):
        settings = Settings()        # load settings
        self.settings = settings.items
        themes = Themes()        # load themes
        self.themes = themes.items

        # Initialize UI component handlers
        self.filter_method_uis = FilterMethodUIs(self)


        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["black"]};
            }}
        """)

        main_layout = QVBoxLayout(self.contents)  # 1.filterDataSection 2.processDataSection
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(2, 2, 2, 2)



        #1.数据过滤部分
        self.filterDataSection = QWidget()
        self.filterDataSection.setObjectName("filterDataSection")
        self.filterDataSectionLayout = QVBoxLayout(self.filterDataSection)  # 1.filterDataTitle 2.filterControlsContainer
        self.filterDataSectionLayout.setSpacing(5)
        self.filterDataSectionLayout.setContentsMargins(1, 1, 1, 1)
        self.filterDataSection.setFixedHeight(170)
        self.filterDataSection.setFixedWidth(480)

        self.filterDataSection.setStyleSheet(f"""
            QWidget#filterDataSection {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)

        #1.1
        self.filterDataTitle = PyLabel2(
            text="Filter Data",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_normal"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.filterDataTitle.setFixedHeight(35)

        self.filterDataSectionLayout.addWidget(self.filterDataTitle,1)

        #1.2
        self.filterControlsContainer = QWidget()
        self.DPsublayout1 = QVBoxLayout(self.filterControlsContainer)
        self.DPsublayout1.setSpacing(1)
        self.DPsublayout1.setContentsMargins(1, 1, 1, 1)

        # First row - Filter checkbox and method selection
        self.filterRow1 = QWidget()
        self.filterRow1Layout = QHBoxLayout(self.filterRow1)
        self.filterRow1Layout.setSpacing(5)
        self.filterRow1Layout.setContentsMargins(1, 1, 1, 1)

        self.filterCheckBox = PyCheckBox2(
            text='Filtrate',
            text_foreground=self.themes["app_color"]["text_foreground"],
            color_hover=self.themes["app_color"]["text_foreground"],
            input_border=self.themes["app_color"]["input_border"],
            white_background=self.themes["app_color"]["white"],
            blue_primary=self.themes["app_color"]["blue_primary"],
            font_size=16,
            font_weight=700,
            spacing=8,
            indicator_width=18,
            indicator_height=18,
            border_width=2,
            border_radius=3
        )
        self.filterCheckBox.setFixedWidth(100)
        self.filterRow1Layout.addWidget(self.filterCheckBox)

        self.filtermethodLineEdit = PyLabel2(
            text="Method:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.filtermethodLineEdit.setFixedWidth(70)
        self.filterRow1Layout.addWidget(self.filtermethodLineEdit)

        self.filtermethodComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            min_height=30,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.filtermethodComboBox.addItems([
            'Choose Method', 'Savitzky-Golay', 'Median', 'Wiener', 'Butterworth', 'Cubic spline',
            'ArithmeticAverage', 'SlidingAverage', 'MedianAverage', 'AmplitudeLimitingAverage',
            'FirstOrderLag', 'WeightedAverage', 'ShakeOff', 'AmplitudeLimitingShakeOff'
        ])
        self.filtermethodComboBox.setFixedWidth(200)

        self.filterRow1Layout.addWidget(self.filtermethodComboBox)
        self.filterRow1Layout.addStretch()



        self.DPsublayout1.addWidget(self.filterRow1)



        self.filterRow2 = QWidget()
        self.filterRow2Layout = QHBoxLayout(self.filterRow2)
        self.filterRow2Layout.setSpacing(1)
        self.filterRow2Layout.setContentsMargins(1, 1, 1, 1)

        self.filterp1LineEdit = PyLabel2(
            text="parameter 1:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.filterRow2Layout.addWidget(self.filterp1LineEdit)
        self.filterp1LineEdit.setVisible(False)

        self.filterp1TextEdit = PyLineEdit2(
            text='17',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.filterp1TextEdit.setFixedHeight(35)
        self.filterp1TextEdit.setFixedWidth(60)

        self.filterRow2Layout.addWidget(self.filterp1TextEdit)
        self.filterp1TextEdit.setVisible(False)


        self.filterp2LineEdit = PyLabel2(
            text="parameter 2:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.filterRow2Layout.addWidget(self.filterp2LineEdit)
        self.filterp2LineEdit.setVisible(False)

        self.filterp2TextEdit = PyLineEdit2(
            text='1',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.filterp2TextEdit.setFixedHeight(35)
        self.filterp2TextEdit.setFixedWidth(60)

        self.filterRow2Layout.addWidget(self.filterp2TextEdit)
        self.filterp2TextEdit.setVisible(False)


        self.filterp3LineEdit = PyLabel2(
            text="parameter 3:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.filterRow2Layout.addWidget(self.filterp3LineEdit)
        self.filterp3LineEdit.setVisible(False)

        self.filterp3TextEdit = PyLineEdit2(
            text='1',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.filterp3TextEdit.setFixedHeight(35)
        self.filterp3TextEdit.setFixedWidth(60)

        self.filterRow2Layout.addWidget(self.filterp3TextEdit)
        self.filterp3TextEdit.setVisible(False)




        self.filterp4LineEdit = PyLabel2(
            text="parameter 4:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.filterRow2Layout.addWidget(self.filterp4LineEdit)
        self.filterp4LineEdit.setVisible(False)

        self.filterp4TextEdit = PyLineEdit2(
            text='1',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.filterp4TextEdit.setFixedHeight(35)
        self.filterp4TextEdit.setFixedWidth(60)

        self.filterRow2Layout.addWidget(self.filterp4TextEdit)
        self.filterp4TextEdit.setVisible(False)


        self.filterRow2Layout.addStretch()




        self.DPsublayout1.addWidget(self.filterRow2)

        # third row - Filter and Output buttons
        self.filterRow3 = QWidget()
        self.filterRow3Layout = QHBoxLayout(self.filterRow3)
        self.filterRow3Layout.setSpacing(5)
        self.filterRow3Layout.setContentsMargins(2, 0, 0, 0)

        self.filterdataBtn = PyPushButton2(
            text="Filter",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["dark_blue"],
            bg_color_hover=self.themes["app_color"]["dark_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["dark_blue_pressed"],
            border_color="transparent",
        )
        self.filterdataBtn.setMinimumHeight(38)
        self.filterdataBtn.setMinimumWidth(100)
        self.filterdataBtn_effect = self.setup_button_hover_effect(self.filterdataBtn)
        self.filterRow3Layout.addWidget(self.filterdataBtn)

        self.outputdataBtn1 = PyPushButton2(
            text="Output",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["light_blue"],
            bg_color_hover=self.themes["app_color"]["light_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["light_blue_pressed"],
            border_color="transparent",
        )
        self.outputdataBtn1.setMinimumHeight(38)
        self.outputdataBtn1.setMinimumWidth(100)
        self.outputdataBtn1_effect = self.setup_button_hover_effect(self.outputdataBtn1)
        self.filterRow3Layout.addWidget(self.outputdataBtn1)

        self.filtercomparaisonBtn = PyPushButton2(
            text="Filter Compare",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["light_blue"],
            bg_color_hover=self.themes["app_color"]["light_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["light_blue_pressed"],
            border_color="transparent",
        )
        self.filtercomparaisonBtn.setMinimumHeight(38)
        self.filtercomparaisonBtn.setMinimumWidth(100)
        self.filtercomparaisonBtn_effect = self.setup_button_hover_effect(self.filtercomparaisonBtn)
        self.filterRow3Layout.addWidget(self.filtercomparaisonBtn)


        self.filterRow3Layout.addStretch()
        self.DPsublayout1.addWidget(self.filterRow3)

        self.filterDataSectionLayout.addWidget(self.filterControlsContainer,9)

        main_layout.addWidget(self.filterDataSection)

        return self.contents

    def setup_button_hover_effect(self, button):
        """Setup hover animation effect for a button"""
        # Create shadow effect
        effect = QGraphicsDropShadowEffect(button)
        effect.setBlurRadius(0)
        effect.setOffset(0, 0)
        effect.setColor(QColor(0, 0, 0, 0))

        # Create hover animation functions
        def hover_enter(e):
            effect.setBlurRadius(10)
            effect.setOffset(0, 2)
            effect.setColor(QColor(0, 0, 0, 50))

        def hover_leave(e):
            effect.setBlurRadius(0)
            effect.setOffset(0, 0)
            effect.setColor(QColor(0, 0, 0, 0))

        # Assign hover events
        button.enterEvent = hover_enter
        button.leaveEvent = hover_leave

        return effect