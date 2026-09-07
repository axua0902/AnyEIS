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
from .ProcessingMethodUIs import ProcessingMethodUIs


class DataprocessUI(object):
    def __init__(self):
        self.parent_processing_instance = None
    
    def set_parent_processing_instance(self, parent_instance):
        """设置父Processing实例的引用，用于信号连接"""
        self.parent_processing_instance = parent_instance
    
    def dataprocessUI(self, widget):
        settings = Settings()        # load settings
        self.settings = settings.items
        themes = Themes()        # load themes
        self.themes = themes.items

        # Initialize UI component handlers
        self.processing_method_uis = ProcessingMethodUIs(self)


        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["black"]};
            }}
        """)

        main_layout = QVBoxLayout(self.contents)  # processDataSection only
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(2, 2, 2, 2)


        self.processDataSection = QWidget()
        self.processDataSection.setObjectName("processDataSection")
        self.processDataSectionLayout = QVBoxLayout(self.processDataSection)
        self.processDataSectionLayout.setSpacing(2)
        self.processDataSectionLayout.setContentsMargins(1, 1, 1, 1)
        self.processDataSection.setFixedWidth(480)

        # self.processDataSection.setStyleSheet(f"""
        #     QWidget {{
        #         background-color: {self.themes["app_color"]["bg_two"]};
        #         border-radius: 8px;
        #         border: 1px solid {self.themes["app_color"]["blue"]};
        #     }}
        # """)
        self.processDataSection.setStyleSheet(f"""
            QWidget#processDataSection {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["orange"]};
            }}
        """)


        # Part 1: Process Data Title (Height: 40)
        self.processDataTitle = PyLabel2(
            text="Process Data",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_normal"],
            font_family=self.settings["font"]["family"],
            font_weight=700,

        )
        self.processDataTitle.setFixedHeight(35)
        self.processDataSectionLayout.addWidget(self.processDataTitle)


        # Part 2: Process Controls Container (Height: 80)
        self.processControlsContainer = QWidget()
        self.processControlsContainer.setFixedHeight(90)
        self.processControlsLayout = QVBoxLayout(self.processControlsContainer)
        self.processControlsLayout.setSpacing(1)
        self.processControlsLayout.setContentsMargins(1, 1, 1, 1)

        # First row - Process checkbox, method label, and method selection
        self.processRow1 = QWidget()
        self.processRow1Layout = QHBoxLayout(self.processRow1)
        self.processRow1Layout.setSpacing(5)
        self.processRow1Layout.setContentsMargins(1, 1, 1, 1)
        self.processRow1.setFixedHeight(40)

        self.processCheckBox = PyCheckBox2(
            text='Process',
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
        self.processCheckBox.setFixedWidth(100)

        self.processRow1Layout.addWidget(self.processCheckBox)

        self.processmethodLineEdit = PyLabel2(
            text="Method:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.processmethodLineEdit.setFixedWidth(70)

        self.processRow1Layout.addWidget(self.processmethodLineEdit)

        self.processmethodComboBox = PyComboBox2(
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
        self.processmethodComboBox.addItems([
            'Select Method','Dielectric Material Method','Parallel Plate Capacitor','Three-Solution Method',
            'RF Impedance Calibration', 'RF Dielectric Calculation','RF Impedance Calculation','System Calibration', 'Other'
        ])
        self.processmethodComboBox.setFixedWidth(230)


        self.processRow1Layout.addWidget(self.processmethodComboBox)
        self.processRow1Layout.addStretch()

        self.processControlsLayout.addWidget(self.processRow1)

        # Second row - Process and output buttons
        self.processRow2 = QWidget()
        self.processRow2Layout = QHBoxLayout(self.processRow2)
        self.processRow2Layout.setSpacing(5)
        self.processRow2Layout.setContentsMargins(2, 0, 0, 0)
        self.processRow2.setFixedHeight(40)

        self.processdataBtn = PyPushButton2(
            text="Process",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["dark_blue"],
            bg_color_hover=self.themes["app_color"]["dark_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["dark_blue_pressed"],
            border_color="transparent",
        )
        self.processdataBtn.setMinimumHeight(40)
        self.processdataBtn.setMinimumWidth(100)
        self.processdataBtn_effect = self.setup_button_hover_effect(self.processdataBtn)
        self.processRow2Layout.addWidget(self.processdataBtn)

        self.outputdataBtn2 = PyPushButton2(
            text="Original Data",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["light_blue"],
            bg_color_hover=self.themes["app_color"]["light_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["light_blue_pressed"],
            border_color="transparent",
        )
        self.outputdataBtn2.setMinimumHeight(40)
        self.outputdataBtn2.setMinimumWidth(120)
        self.outputdataBtn2_effect = self.setup_button_hover_effect(self.outputdataBtn2)
        self.processRow2Layout.addWidget(self.outputdataBtn2)

        self.outputdataBtn3 = PyPushButton2(
            text="Processed Data",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["light_blue"],
            bg_color_hover=self.themes["app_color"]["light_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["light_blue_pressed"],
            border_color="transparent",
        )
        self.outputdataBtn3.setMinimumHeight(40)
        self.outputdataBtn3.setMinimumWidth(120)
        self.outputdataBtn3_effect = self.setup_button_hover_effect(self.outputdataBtn3)
        self.processRow2Layout.addWidget(self.outputdataBtn3)

        self.processRow2Layout.addStretch()
        self.processControlsLayout.addWidget(self.processRow2)

        self.processDataSectionLayout.addWidget(self.processControlsContainer)


        # Part 3: Dynamic Content Container (for method-specific interfaces)
        self.dynamicContentContainer = QWidget()
        self.DPsublayout2 = QVBoxLayout(self.dynamicContentContainer)
        self.DPsublayout2.setSpacing(10)
        self.DPsublayout2.setContentsMargins(5, 5, 5, 5)
        self.DPsublayout2.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align widgets to top

        self.processDataSectionLayout.addWidget(self.dynamicContentContainer)







        main_layout.addWidget(self.processDataSection)

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


    def freshfilterUI(self):
        # Clear dynamic filter parameter widgets
        pass





    def defbuttn(self):
        self.refdataBtn = {}
        self.refdataComboBox = {}
        self.deletereffilebtn = {}
        self.openreffilebtn = {}
        self.refsoluionLineEdit = {}
        self.refsoluionComboBox = {}
        self.concentrationLineEdit = {}
        self.concentrationTextEdit = {}
        self.concentrationUnitLineEdit = {}
        self.ethanolConcentrationComboBox = {}  # Ethanol专用浓度下拉框 (75%/90%)
        self.temperatureLineEdit = {}
        self.temperatureTextEdit = {}
        self.temperatureUnitLineEdit = {}


    def uiUnit(self, num, numt, refdataname):  # 基本单元
        # Create container for this unit
        unitContainer = QWidget()
        unitLayout = QVBoxLayout(unitContainer)
        unitLayout.setSpacing(5)
        unitLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Ref Solution button, combo box, and file buttons
        unitRow1 = QWidget()
        unitRow1.setFixedHeight(40)
        unitRow1Layout = QHBoxLayout(unitRow1)
        unitRow1Layout.setSpacing(5)
        unitRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.refdataBtn[num] = PyPushButton2(
            text="Ref. Solution",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["purple_blue"],
            bg_color_hover=self.themes["app_color"]["purple_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["purple_blue_pressed"],
            border_color="transparent",
        )
        self.refdataBtn[num].setFixedHeight(40)
        self.refdataBtn[num].setMinimumWidth(120)
        setattr(self, f'refdataBtn{num}_effect', self.setup_button_hover_effect(self.refdataBtn[num]))
        unitRow1Layout.addWidget(self.refdataBtn[num])



        self.refdataComboBox[num] = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  # 使用HTML中的border-radius: 4px
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            min_height=35,
            bg_color=self.themes["app_color"]["bg_two"],  # 使用白色背景
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],  # 使用浅色边框
        )
        unitRow1Layout.addWidget(self.refdataComboBox[num])



        self.openreffilebtn[num] = PyPushButton2(
            text="Open File",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["context_color"],
            bg_color_hover=self.themes["app_color"]["context_hover"],
            bg_color_pressed=self.themes["app_color"]["context_pressed"],
            border_color="transparent",
        )
        self.openreffilebtn[num].setFixedHeight(40)
        self.openreffilebtn[num].setMinimumWidth(100)
        setattr(self, f'openreffilebtn{num}_effect', self.setup_button_hover_effect(self.openreffilebtn[num]))
        unitRow1Layout.addWidget(self.openreffilebtn[num])

        self.deletereffilebtn[num] = PyPushButton2(
            text="Delete File",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],

            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],


            border_color="transparent",
        )
        self.deletereffilebtn[num].setFixedHeight(40)
        self.deletereffilebtn[num].setMinimumWidth(100)
        setattr(self, f'deletereffilebtn{num}_effect', self.setup_button_hover_effect(self.deletereffilebtn[num]))
        unitRow1Layout.addWidget(self.deletereffilebtn[num])

        unitLayout.addWidget(unitRow1)

        # Second row - Solution, Concentration, and Temperature controls
        unitRow2 = QWidget()
        unitRow2.setFixedHeight(40)
        unitRow2Layout = QHBoxLayout(unitRow2)
        unitRow2Layout.setSpacing(5)
        unitRow2Layout.setContentsMargins(0, 0, 0, 0)

        self.refsoluionLineEdit[num] = PyLabel2(
            text="Solution:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        unitRow2Layout.addWidget(self.refsoluionLineEdit[num])

        # self.refsoluionComboBox[num] = QComboBox()

        self.refsoluionComboBox[num] = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  # 使用HTML中的border-radius: 4px
            font_size=self.settings["font"]["text_size_small"],
            font_weight=700,
            min_height=35,
            bg_color=self.themes["app_color"]["bg_two"],  # 使用白色背景
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],  # 使用浅色边框
        )
        self.refsoluionComboBox[num].addItems(refdataname)
        unitRow2Layout.addWidget(self.refsoluionComboBox[num])

        self.concentrationLineEdit[num] = PyLabel2(
            text="Concentration:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        unitRow2Layout.addWidget(self.concentrationLineEdit[num])

        self.concentrationTextEdit[num] = PyLineEdit2(
            text='0.1',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_small"],
            font_weight=600
        )
        self.concentrationTextEdit[num].setFixedHeight(30)
        self.concentrationTextEdit[num].setFixedWidth(45)

        unitRow2Layout.addWidget(self.concentrationTextEdit[num])

        # [新增] Ethanol 专用浓度下拉框: 只支持 75% / 90% 两个体积分数
        # (对应 standard_parameter.py 中的 paraAlcohol=75% 和 paraEthanol=90%)
        # 初始隐藏,仅当 refsoluionComboBox 选中 "Ethanol" 时显示
        self.ethanolConcentrationComboBox[num] = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings["font"]["text_size_small"],
            font_weight=600,
            min_height=30,
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["input_border"],
        )
        self.ethanolConcentrationComboBox[num].addItems(['90', '75'])
        self.ethanolConcentrationComboBox[num].setFixedHeight(30)
        self.ethanolConcentrationComboBox[num].setFixedWidth(55)
        self.ethanolConcentrationComboBox[num].hide()
        unitRow2Layout.addWidget(self.ethanolConcentrationComboBox[num])

        # 同步: combo 选择变化时, 同步到 concentrationTextEdit (下游代码读的是它)
        self.ethanolConcentrationComboBox[num].currentTextChanged.connect(
            lambda text, n=num: self.concentrationTextEdit[n].setText(text)
        )

        self.concentrationUnitLineEdit[num] = PyLabel2(
            text="mol/L",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.concentrationUnitLineEdit[num].setFixedWidth(48)
        unitRow2Layout.addWidget(self.concentrationUnitLineEdit[num])

        self.temperatureLineEdit[num] = PyLabel2(
            text="Temperature:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        unitRow2Layout.addWidget(self.temperatureLineEdit[num])

        self.temperatureTextEdit[num] = PyLineEdit2(
            text='25',
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
        self.temperatureTextEdit[num].setFixedHeight(30)
        self.temperatureTextEdit[num].setFixedWidth(42)

        unitRow2Layout.addWidget(self.temperatureTextEdit[num])

        self.temperatureUnitLineEdit[num] = PyLabel2(
            text="℃",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        unitRow2Layout.addWidget(self.temperatureUnitLineEdit[num])

        unitLayout.addWidget(unitRow2)

        self.DPsublayout2.addWidget(unitContainer)

        # Connect signals for this specific button after creation
        if hasattr(self, 'parent_processing_instance') and self.parent_processing_instance:
            # 使用闭包来捕获当前的num值，避免lambda的延迟绑定问题
            self.refdataBtn[num].clicked.connect(lambda checked, n=num: self.parent_processing_instance.GetrefFiles(n + 1))
            self.openreffilebtn[num].clicked.connect(lambda checked, n=num: self.parent_processing_instance.OpenFiles(n + 1))
            self.deletereffilebtn[num].clicked.connect(lambda checked, n=num: self.parent_processing_instance.ClearrefFiles(n + 1))



    def freshprocessUI(self):
        # Clear all dynamic widgets from the process controls container
        while self.DPsublayout2.count() > 0:
            child = self.DPsublayout2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear the reference data dictionaries if they exist
        if hasattr(self, 'refdataBtn'):
            self.refdataBtn.clear()
        if hasattr(self, 'refdataComboBox'):
            self.refdataComboBox.clear()
        if hasattr(self, 'deletereffilebtn'):
            self.deletereffilebtn.clear()
        if hasattr(self, 'openreffilebtn'):
            self.openreffilebtn.clear()
        if hasattr(self, 'refsoluionLineEdit'):
            self.refsoluionLineEdit.clear()
        if hasattr(self, 'refsoluionComboBox'):
            self.refsoluionComboBox.clear()
        if hasattr(self, 'concentrationLineEdit'):
            self.concentrationLineEdit.clear()
        if hasattr(self, 'concentrationTextEdit'):
            self.concentrationTextEdit.clear()
        if hasattr(self, 'concentrationUnitLineEdit'):
            self.concentrationUnitLineEdit.clear()
        if hasattr(self, 'temperatureLineEdit'):
            self.temperatureLineEdit.clear()
        if hasattr(self, 'temperatureTextEdit'):
            self.temperatureTextEdit.clear()
        if hasattr(self, 'temperatureUnitLineEdit'):
            self.temperatureUnitLineEdit.clear()





