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


class ProcessingMethodUIs:
    def __init__(self, parent):
        self.parent = parent
        self.settings = parent.settings
        self.themes = parent.themes

    def ui_calibration(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(3)
        refdataname = ['Open', 'Short', 'Load']

        # Create calibration units without solution/concentration/temperature controls
        for i in range(3):
            unitContainer = QWidget()
            unitLayout = QVBoxLayout(unitContainer)
            unitLayout.setSpacing(5)
            unitLayout.setContentsMargins(0, 0, 0, 0)

            # Only the first row with buttons
            unitRow1 = QWidget()
            unitRow1.setFixedHeight(40)
            unitRow1Layout = QHBoxLayout(unitRow1)
            unitRow1Layout.setSpacing(10)
            unitRow1Layout.setContentsMargins(0, 0, 0, 0)

            self.parent.refdataBtn[i] = PyPushButton2(
                text=refdataname[i],
                font_size=self.settings["font"]["text_size_normal"],
                font_weight=700,
                radius=4,
                font_color=self.themes["app_color"]["white"],
                bg_color=self.themes["app_color"]["purple_blue"],
                bg_color_hover=self.themes["app_color"]["purple_blue_hover"],
                bg_color_pressed=self.themes["app_color"]["purple_blue_pressed"],
                border_color="transparent",
            )
            self.parent.refdataBtn[i].setFixedHeight(40)
            self.parent.refdataBtn[i].setMinimumWidth(120)
            setattr(self.parent, f'refdataBtn{i}_effect', self.parent.setup_button_hover_effect(self.parent.refdataBtn[i]))
            unitRow1Layout.addWidget(self.parent.refdataBtn[i])

            self.parent.refdataComboBox[i] = PyComboBox2(
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
            unitRow1Layout.addWidget(self.parent.refdataComboBox[i])

            self.parent.openreffilebtn[i] = PyPushButton2(
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
            self.parent.openreffilebtn[i].setFixedHeight(40)
            self.parent.openreffilebtn[i].setMinimumWidth(100)
            setattr(self.parent, f'openreffilebtn{i}_effect', self.parent.setup_button_hover_effect(self.parent.openreffilebtn[i]))
            unitRow1Layout.addWidget(self.parent.openreffilebtn[i])

            self.parent.deletereffilebtn[i] = PyPushButton2(
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
            self.parent.deletereffilebtn[i].setFixedHeight(40)
            self.parent.deletereffilebtn[i].setMinimumWidth(100)
            setattr(self.parent, f'deletereffilebtn{i}_effect', self.parent.setup_button_hover_effect(self.parent.deletereffilebtn[i]))
            unitRow1Layout.addWidget(self.parent.deletereffilebtn[i])

            unitLayout.addWidget(unitRow1)
            self.parent.DPsublayout2.addWidget(unitContainer)
            
            # Connect signals for this specific button after creation
            if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
                # 使用闭包来捕获当前的i值，避免lambda的延迟绑定问题
                self.parent.refdataBtn[i].clicked.connect(lambda checked, n=i: self.parent.parent_processing_instance.GetrefFiles(n + 1))
                self.parent.openreffilebtn[i].clicked.connect(lambda checked, n=i: self.parent.parent_processing_instance.OpenFiles(n + 1))
                self.parent.deletereffilebtn[i].clicked.connect(lambda checked, n=i: self.parent.parent_processing_instance.ClearrefFiles(n + 1))
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def ui_ParallelPlate(self):
        self.parent.freshprocessUI()
        
        # Add geometric constant input
        ppContainer = QWidget()
        ppContainer.setFixedHeight(40)
        ppLayout = QHBoxLayout(ppContainer)
        ppLayout.setSpacing(10)
        ppLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        ppLayout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='',
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
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        ppLayout.addWidget(self.parent.GeomconstantTextEdit)

        ppLayout.addStretch()
        self.parent.DPsublayout2.addWidget(ppContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def ui_DielectricMaterial(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(2)
        refdataname = ['Water', 'Alcohol', 'Air']
        # Only show 2 units for Dielectric material
        self.parent.uiUnit(0, 2, refdataname)
        self.parent.uiUnit(1, 2, refdataname)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

        

    def ui_ThreeSolution(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(3)
        refdataname = ['NaCl', 'Water', 'Ethanol']
        self.parent.uiUnit(0, 2, refdataname)
        self.parent.uiUnit(1, 2, refdataname)
        self.parent.uiUnit(2, 2, refdataname)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()






    def ui_TransmissionLine(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(1)
        refdataname = ['NaCl', 'Water', 'Ethanol', 'Air']
        self.parent.uiUnit(0, 2, refdataname)

        # Add transmission line specific parameters
        tlContainer = QWidget()
        tlLayout = QVBoxLayout(tlContainer)
        tlLayout.setSpacing(5)
        tlLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Geometric constant and Character Impedance
        tlRow1 = QWidget()
        tlRow1.setFixedHeight(40)
        tlRow1Layout = QHBoxLayout(tlRow1)
        tlRow1Layout.setSpacing(10)
        tlRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='3.874',
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
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.GeomconstantTextEdit)

        self.parent.CharaImpedanceLineEdit = PyLabel2(
            text="Character Impedance:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.CharaImpedanceLineEdit)

        self.parent.CharaImpedanceTextEdit = PyLineEdit2(
            text='50',
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
        self.parent.CharaImpedanceTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.CharaImpedanceTextEdit)

        self.parent.CharaImpedanceUnitLineEdit = PyLabel2(
            text="Ω",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.CharaImpedanceUnitLineEdit)

        tlLayout.addWidget(tlRow1)

        # Second row - Electrode Length and Solution Length
        tlRow2 = QWidget()
        tlRow2.setFixedHeight(40)
        tlRow2Layout = QHBoxLayout(tlRow2)
        tlRow2Layout.setSpacing(10)
        tlRow2Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.ElectLengthLineEdit = PyLabel2(
            text="Electorde Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.ElectLengthLineEdit)

        self.parent.ElectLengthTextEdit = PyLineEdit2(
            text='0.0164',
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
        self.parent.ElectLengthTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.ElectLengthTextEdit)

        self.parent.ElectLengthUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.ElectLengthUnitLineEdit)

        self.parent.SoluLengthLineEdit = PyLabel2(
            text="Solution Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengthLineEdit)

        self.parent.SoluLengtTextEdit = PyLineEdit2(
            text='0.002',
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
        self.parent.SoluLengtTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.SoluLengtTextEdit)

        self.parent.SoluLengtUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengtUnitLineEdit)

        tlLayout.addWidget(tlRow2)
        self.parent.DPsublayout2.addWidget(tlContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def ui_TransmissionLine_cal(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(1)

        # Add transmission line specific parameters
        tlContainer = QWidget()
        tlLayout = QVBoxLayout(tlContainer)
        tlLayout.setSpacing(5)
        tlLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Geometric constant and Character Impedance
        tlRow1 = QWidget()
        tlRow1.setFixedHeight(40)
        tlRow1Layout = QHBoxLayout(tlRow1)
        tlRow1Layout.setSpacing(10)
        tlRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='3.874',
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
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.GeomconstantTextEdit)



        tlLayout.addWidget(tlRow1)

        # Second row - Electrode Length and Solution Length
        tlRow2 = QWidget()
        tlRow2.setFixedHeight(40)
        tlRow2Layout = QHBoxLayout(tlRow2)
        tlRow2Layout.setSpacing(10)
        tlRow2Layout.setContentsMargins(0, 0, 0, 0)




        self.parent.SoluLengthLineEdit = PyLabel2(
            text="Solution Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengthLineEdit)

        self.parent.SoluLengtTextEdit = PyLineEdit2(
            text='0.00255',
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
        self.parent.SoluLengtTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.SoluLengtTextEdit)

        self.parent.SoluLengtUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengtUnitLineEdit)

        tlLayout.addWidget(tlRow2)
        self.parent.DPsublayout2.addWidget(tlContainer)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()





    def ui_TransmissionLine_EIScal(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(1)

        # Add transmission line specific parameters
        tlContainer = QWidget()
        tlLayout = QVBoxLayout(tlContainer)
        tlLayout.setSpacing(5)
        tlLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Geometric constant and Character Impedance
        tlRow1 = QWidget()
        tlRow1.setFixedHeight(40)
        tlRow1Layout = QHBoxLayout(tlRow1)
        tlRow1Layout.setSpacing(10)
        tlRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='3.874',
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
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.GeomconstantTextEdit)



        tlLayout.addWidget(tlRow1)

        # Second row - Electrode Length and Solution Length
        tlRow2 = QWidget()
        tlRow2.setFixedHeight(40)
        tlRow2Layout = QHBoxLayout(tlRow2)
        tlRow2Layout.setSpacing(10)
        tlRow2Layout.setContentsMargins(0, 0, 0, 0)




        self.parent.SoluLengthLineEdit = PyLabel2(
            text="Solution Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengthLineEdit)

        self.parent.SoluLengtTextEdit = PyLineEdit2(
            text='0.00255',
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
        self.parent.SoluLengtTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.SoluLengtTextEdit)

        self.parent.SoluLengtUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengtUnitLineEdit)

        tlLayout.addWidget(tlRow2)
        self.parent.DPsublayout2.addWidget(tlContainer)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()








    def uiKKDS(self):
        """UI for K-K for DS method"""
        self.parent.freshprocessUI()
        
        # Add K-K for DS specific parameters
        kkdsContainer = QWidget()
        kkdsLayout = QVBoxLayout(kkdsContainer)
        kkdsLayout.setSpacing(5)
        kkdsLayout.setContentsMargins(0, 0, 0, 0)

        # Parameter input row
        paramRow = QWidget()
        paramRow.setFixedHeight(40)
        paramLayout = QHBoxLayout(paramRow)
        paramLayout.setSpacing(10)
        paramLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.kkdsParamLabel = PyLabel2(
            text="K-K Parameters:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        paramLayout.addWidget(self.parent.kkdsParamLabel)

        self.parent.kkdsParamEdit = PyLineEdit2(
            text='',
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
        self.parent.kkdsParamEdit.setFixedHeight(40)
        paramLayout.addWidget(self.parent.kkdsParamEdit)

        paramLayout.addStretch()
        kkdsLayout.addWidget(paramRow)
        self.parent.DPsublayout2.addWidget(kkdsContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def uiKKEIS(self):
        """UI for K-K for EIS method"""
        self.parent.freshprocessUI()
        
        # Add K-K for EIS specific parameters
        kkeisContainer = QWidget()
        kkeisLayout = QVBoxLayout(kkeisContainer)
        kkeisLayout.setSpacing(5)
        kkeisLayout.setContentsMargins(0, 0, 0, 0)

        # Parameter input row
        paramRow = QWidget()
        paramRow.setFixedHeight(40)
        paramLayout = QHBoxLayout(paramRow)
        paramLayout.setSpacing(10)
        paramLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.kkeisParamLabel = PyLabel2(
            text="K-K EIS Parameters:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        paramLayout.addWidget(self.parent.kkeisParamLabel)

        self.parent.kkeisParamEdit = PyLineEdit2(
            text='',
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
        self.parent.kkeisParamEdit.setFixedHeight(40)
        paramLayout.addWidget(self.parent.kkeisParamEdit)

        paramLayout.addStretch()
        kkeisLayout.addWidget(paramRow)
        self.parent.DPsublayout2.addWidget(kkeisContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def uiOther(self):
        """UI for Other method"""
        self.parent.freshprocessUI()
        
        # Add generic parameter inputs for other methods
        otherContainer = QWidget()
        otherLayout = QVBoxLayout(otherContainer)
        otherLayout.setSpacing(5)
        otherLayout.setContentsMargins(0, 0, 0, 0)

        # Parameter input row
        paramRow = QWidget()
        paramRow.setFixedHeight(40)
        paramLayout = QHBoxLayout(paramRow)
        paramLayout.setSpacing(10)
        paramLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.otherParamLabel = PyLabel2(
            text="Custom Parameters:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        paramLayout.addWidget(self.parent.otherParamLabel)

        self.parent.otherParamEdit = PyLineEdit2(
            text='',
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
        self.parent.otherParamEdit.setFixedHeight(40)
        paramLayout.addWidget(self.parent.otherParamEdit)

        paramLayout.addStretch()
        otherLayout.addWidget(paramRow)
        self.parent.DPsublayout2.addWidget(otherContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()