# -*- coding: utf-8 -*-

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from PySide6.QtWidgets import  QWidget,QTableWidget, QVBoxLayout,QHBoxLayout,QGroupBox,QComboBox,QLineEdit,QPushButton,QTableWidget,QLabel,QHeaderView
from widgets.py_push_button.py_push_button2 import PyPushButton2
from widgets.py_combobox.py_combobox2 import  PyComboBox2
from widgets.py_label.py_label2 import PyLabel2
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2          

from setting import Settings# import setting
from themes import Themes # import themes

class Tab1Content(QWidget):
    def __init__(self):
        super().__init__()
        settings = Settings()        # load settings
        self.settings = settings.items
        themes = Themes()        # load themes
        self.themes = themes.items

        self.contents = QWidget()
        self.contents.setObjectName(u"contents")


        self.main_Layout = QVBoxLayout(self.contents)
        self.main_Layout.setSpacing(5)
        self.main_Layout.setObjectName(u"main_Layout")
        self.main_Layout.setContentsMargins(1, 1, 1, 1)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.contents)

        ##############Files Section##################################################
        self.fileSection = QWidget()
        self.fileSection.setObjectName("fileSection")

        self.fileSectionLayout = QVBoxLayout(self.fileSection)
        self.fileSectionLayout.setSpacing(5)
        self.fileSectionLayout.setContentsMargins(1, 1, 1, 1)
        self.fileSection.setFixedHeight(85)

        self.fileSection.setStyleSheet(f"""
            QWidget#fileSection {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["orange"]};
            }}
        """)


        # Files title
        self.fileTitle = PyLabel2(
            text="Model Files",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.fileTitle.setFixedHeight(35)
        self.fileSectionLayout.addWidget(self.fileTitle)

        # File controls row
        self.fileRow = QWidget()
        self.fileRow.setFixedHeight(40)
        self.fileRowLayout = QHBoxLayout(self.fileRow)
        self.fileRowLayout.setSpacing(5)
        self.fileRowLayout.setContentsMargins(2, 0, 0, 0)

        self.newBtn = PyPushButton2(
            text="New",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.newBtn.setFixedHeight(40)
        self.newBtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.newBtn)

        self.openModelBtn = PyPushButton2(
            text="Open",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.openModelBtn.setFixedHeight(40)
        self.openModelBtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.openModelBtn)

        self.inputdataComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            min_height=32,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.inputdataComboBox.setMinimumWidth(150)

        self.fileRowLayout.addWidget(self.inputdataComboBox)

        self.saveModelBtn = PyPushButton2(
            text="Save",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["green_primary"],
            bg_color_hover = self.themes["app_color"]["green_hover"],
            bg_color_pressed = self.themes["app_color"]["green_pressed"],
            border_color = "transparent",
        )
        self.saveModelBtn.setFixedHeight(40)
        self.saveModelBtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.saveModelBtn)

        self.saveasModelBtn=PyPushButton2(
            text="Save as",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["green_primary"],
            bg_color_hover = self.themes["app_color"]["green_hover"],
            bg_color_pressed = self.themes["app_color"]["green_pressed"],
            border_color = "transparent",
        )
        self.saveasModelBtn.setFixedHeight(40)
        self.saveasModelBtn.setMinimumWidth(70)
        self.fileRowLayout.addWidget(self.saveasModelBtn)

        self.clearModelBtn=PyPushButton2(
            text="Clear",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],
            border_color = "transparent",
        )
        self.clearModelBtn.setFixedHeight(40)
        self.clearModelBtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.clearModelBtn)

        self.fileRowLayout.addStretch()

        self.fileSectionLayout.addWidget(self.fileRow)
        self.main_Layout.addWidget(self.fileSection)




        ##############Setting Parameters Section#################################################
        self.parameterSection = QWidget()
        self.parameterSection.setObjectName("parameterSection")

        self.parameterSectionLayout = QVBoxLayout(self.parameterSection)
        self.parameterSectionLayout.setSpacing(2)
        self.parameterSectionLayout.setContentsMargins(1, 1, 1, 2)

        self.parameterSection.setStyleSheet(f"""
            QWidget#parameterSection {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)

        # Parameters title
        self.parameterTitle = PyLabel2(
            text="Setting Parameters",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.parameterTitle.setFixedHeight(35)
        self.parameterSectionLayout.addWidget(self.parameterTitle)

        #####################Frequency Row##############
        self.frequencyRow = QWidget()
        self.frequencyRow.setFixedHeight(35)
        self.frequencyRowLayout = QHBoxLayout(self.frequencyRow)
        self.frequencyRowLayout.setSpacing(2)
        self.frequencyRowLayout.setContentsMargins(0, 0, 0, 0)

        self.frequencyRowLayout.addWidget(PyLabel2(
            text="Frequency:",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.frequencyRowLayout.addWidget(PyLabel2(
            text="Minimum [Hz]",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.ECMlowfreqTextEdit = PyLineEdit2(
            text='',
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
        self.ECMlowfreqTextEdit.setFixedHeight(35)
        self.frequencyRowLayout.addWidget(self.ECMlowfreqTextEdit)
        self.ECMlowfreqTextEdit.setText('1e1')

        self.frequencyRowLayout.addWidget(PyLabel2(
            text="Maximum [Hz]",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.ECMupfreqTextEdit = PyLineEdit2(
            text='',
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
        self.ECMupfreqTextEdit.setFixedHeight(35)
        self.frequencyRowLayout.addWidget(self.ECMupfreqTextEdit)
        self.ECMupfreqTextEdit.setText('1e9')

        self.distributionComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings["font"]["text_size_small"],
            font_weight=700,
            min_height=32,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.distributionComboBox.addItem('Log')
        self.distributionComboBox.addItem('Linear')
        self.frequencyRowLayout.addWidget(self.distributionComboBox)

        self.parameterSectionLayout.addWidget(self.frequencyRow)

        ####################Element Row#############
        self.elementRow = QWidget()
        self.elementRow.setFixedHeight(35)
        self.elementRowLayout = QHBoxLayout(self.elementRow)
        self.elementRowLayout.setSpacing(5)
        self.elementRowLayout.setContentsMargins(0, 0, 0, 0)

        self.elementRowLayout.addWidget(PyLabel2(
            text="Element:",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.elementComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  
            font_size=self.settings["font"]["text_size_small"],
            font_weight=700,
            min_height=32,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.elementComboBox.addItem('R')
        self.elementComboBox.addItem('C')
        self.elementComboBox.addItem('L')
        self.elementComboBox.addItem('CPE')

        self.elementRowLayout.addWidget(self.elementComboBox)

        self.elementnameTextEdit = PyLineEdit2(
            text='',
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
        self.elementnameTextEdit.setFixedHeight(35)
        self.elementRowLayout.addWidget(self.elementnameTextEdit)

        self.addelementBtn = PyPushButton2(
            text="Add Element",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.addelementBtn.setFixedHeight(35)
        self.addelementBtn.setMinimumWidth(100)
        self.elementRowLayout.addWidget(self.addelementBtn)

        self.elementRowLayout.addStretch()
        self.parameterSectionLayout.addWidget(self.elementRow)

        ##################Connection Row############
        self.connectionRow = QWidget()
        self.connectionRow.setFixedHeight(40)
        self.connectionRowLayout = QHBoxLayout(self.connectionRow)
        self.connectionRowLayout.setSpacing(10)
        self.connectionRowLayout.setContentsMargins(0, 0, 0, 0)

        self.connectionRowLayout.addWidget(PyLabel2(
            text="Connection:",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=700,
            padding_left="2px",
        ))

        self.connectionComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            min_height=32,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.connectionComboBox.addItem('Parallel')
        self.connectionComboBox.addItem('Series')
        self.connectionComboBox.addItem(',')
        self.connectionComboBox.addItem(')')
        self.connectionRowLayout.addWidget(self.connectionComboBox)

        self.addconnectionBtn = PyPushButton2(
            text="Add Connection",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.addconnectionBtn.setFixedHeight(35)
        self.addconnectionBtn.setMinimumWidth(120)
        self.connectionRowLayout.addWidget(self.addconnectionBtn)

        self.undoBtn = PyPushButton2(
            text="Undo Last Step",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],
            border_color = "transparent",
        )
        self.undoBtn.setFixedHeight(35)
        self.undoBtn.setMinimumWidth(120)
        self.connectionRowLayout.addWidget(self.undoBtn)

        self.connectionRowLayout.addStretch()
        self.parameterSectionLayout.addWidget(self.connectionRow)

        ##################Connection Display Row############
        self.connectionDisplayRow = QWidget()
        self.connectionDisplayRow.setFixedHeight(35)
        self.connectionDisplayRowLayout = QHBoxLayout(self.connectionDisplayRow)
        self.connectionDisplayRowLayout.setSpacing(10)
        self.connectionDisplayRowLayout.setContentsMargins(0, 0, 0, 0)

        self.connectionTextEdit = PyLineEdit2(
            text='Connection',
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
        self.connectionTextEdit.setFixedHeight(35)
        self.connectionDisplayRowLayout.addWidget(self.connectionTextEdit)

        self.parameterSectionLayout.addWidget(self.connectionDisplayRow)

        ##################Results Table############
        label = ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Fixed', 'Error [%]']
        self.ECMtable = QTableWidget()
        self.ECMtable.setRowCount(0)
        self.ECMtable.setColumnCount(len(label))
        self.ECMtable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.ECMtable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.ECMtable.resizeColumnsToContents()
        self.ECMtable.setHorizontalHeaderLabels(label)
        self.ECMtable.resizeColumnsToContents()
        # 每列增加20像素的宽松间距
        for i in range(len(label)):
            self.ECMtable.setColumnWidth(i, self.ECMtable.columnWidth(i) + 9)
        self.ECMtable.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setECMTableHeader('fit')  # 默认拟合模式

        # Set font weight for table headers using stylesheet
        self.ECMtable.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                font-weight: 700;
            }
        """)
        self.parameterSectionLayout.addWidget(self.ECMtable)





        ##########Calculation Buttons Row###########
        self.calculationRow = QWidget()
        self.calculationRow.setFixedHeight(35)
        self.calculationRowLayout = QHBoxLayout(self.calculationRow)
        self.calculationRowLayout.setSpacing(10)
        self.calculationRowLayout.setContentsMargins(2, 0, 0, 0)

        self.modelfigBtn = PyPushButton2(
            text="Show Circuit",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["btn_info"],
            bg_color_hover = self.themes["app_color"]["btn_info_hover"],
            bg_color_pressed = self.themes["app_color"]["btn_info_pressed"],
            border_color = "transparent",
        )
        self.modelfigBtn.setFixedHeight(35)
        self.modelfigBtn.setMinimumWidth(100)
        self.calculationRowLayout.addWidget(self.modelfigBtn)

        self.calculateBtn = PyPushButton2(
            text="Calculate",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["dark_blue"],
            bg_color_hover=self.themes["app_color"]["dark_blue_hover"],
            bg_color_pressed=self.themes["app_color"]["dark_blue_pressed"],
            border_color = "transparent",
        )
        self.calculateBtn.setFixedHeight(35)
        self.calculateBtn.setMinimumWidth(100)
        self.calculationRowLayout.addWidget(self.calculateBtn)

        self.clearBtn = PyPushButton2(
            text="Clear",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["gray_hover"],
            bg_color_hover = self.themes["app_color"]["bg_four"],
            bg_color_pressed = self.themes["app_color"]["bg_three"],
            border_color = "transparent",
        )
        self.clearBtn.setFixedHeight(35)
        self.clearBtn.setMinimumWidth(100)
        self.calculationRowLayout.addWidget(self.clearBtn)

        self.calculationRowLayout.addStretch()
        self.parameterSectionLayout.addWidget(self.calculationRow)

        self.main_Layout.addWidget(self.parameterSection)







        ##############Figure Equivalent Circuit Section################################################
        self.ECfigureSection = QWidget()
        self.ECfigureSection.setObjectName("ECfigureSection")

        self.ECfigureSectionLayout = QVBoxLayout(self.ECfigureSection)
        self.ECfigureSectionLayout.setSpacing(5)
        self.ECfigureSectionLayout.setContentsMargins(1, 1, 1, 1)
        self.ECfigureSection.setStyleSheet(f"""
            QWidget#ECfigureSection {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)

        # Figure title
        self.ECfigureTitle = PyLabel2(
            text="Equivalent Circuit Model",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.ECfigureTitle.setFixedHeight(35)
        self.ECfigureSectionLayout.addWidget(self.ECfigureTitle)

        # Figure display area
        self.ECfigureDisplayArea = QWidget()
        self.ECfigureDisplayArea.setObjectName("ECfigureDisplayArea")

        self.ECfigureDisplayAreaLayout = QVBoxLayout(self.ECfigureDisplayArea)
        self.ECfigureDisplayAreaLayout.setContentsMargins(5, 5, 5, 5)
        self.ECfigureDisplayAreaLayout.setSpacing(0)

        self.ECfigureDisplayArea.setFixedHeight(160)
        self.ECfigureDisplayArea.setStyleSheet(f"""
            QWidget#ECfigureDisplayArea  {{
                background-color: {self.themes["app_color"]["white"]};
                border: 1px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
            }}
        """)
        self.ECfigureSectionLayout.addWidget(self.ECfigureDisplayArea)

        self.main_Layout.addWidget(self.ECfigureSection)







    def setup_button_hover_effect(self, button):
        """Setup hover animation effect for a button"""
        effect = QGraphicsDropShadowEffect(button)
        effect.setBlurRadius(0)
        effect.setOffset(0, 0)
        effect.setColor(QColor(0, 0, 0, 0))

        def hover_enter(e):
            effect.setBlurRadius(10)
            effect.setOffset(0, 2)
            effect.setColor(QColor(0, 0, 0, 50))

        def hover_leave(e):
            effect.setBlurRadius(0)
            effect.setOffset(0, 0)
            effect.setColor(QColor(0, 0, 0, 0))

        button.enterEvent = hover_enter
        button.leaveEvent = hover_leave

        return effect

    def setECMTableHeader(self, mode='fit'):
        """
        设置ECM表格的表头

        参数:
            mode: 'fit' 表示拟合模式，'simu' 表示仿真模式
        """
        if mode == 'fit':
            # 拟合模式：显示拟合值和误差
            label = ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Fixed', 'Error [%]']
        else:
            # 仿真模式：不显示拟合值和误差
            label = ['Name', 'Comments', 'Initial_Value', 'Max', 'Min', 'Fixed']

        self.ECMtable.setColumnCount(len(label))
        self.ECMtable.setHorizontalHeaderLabels(label)