# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 11:24:01 2020

@author: takeilab
"""

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from PySide6.QtWidgets import  QWidget, QTabWidget, QVBoxLayout,QHBoxLayout,QGroupBox,QComboBox,QLineEdit,QPushButton,QTableWidget,QLabel,QHeaderView,QCheckBox
from widgets.py_push_button.py_push_button2 import PyPushButton2
from widgets.py_combobox.py_combobox2 import  PyComboBox2
from widgets.py_label.py_label2 import PyLabel2
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2          

from setting import Settings# import setting
from themes import Themes # import themes

class Tab2Content(QWidget):
    def __init__(self):
        super().__init__()
        settings = Settings()        # load settings
        self.settings = settings.items
        themes = Themes()        # load themes
        self.themes = themes.items
        
        self.contents = QWidget()
        self.contents.setObjectName(u"contents")


        self.verticalLayout = QVBoxLayout(self.contents)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)

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

        self.inputdataBtn = PyPushButton2(
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
        self.inputdataBtn.setFixedHeight(40)
        self.inputdataBtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.inputdataBtn)

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

        self.openexfilebtn = PyPushButton2(
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
        self.openexfilebtn.setFixedHeight(40)
        self.openexfilebtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.openexfilebtn)

        self.saveasBtn = PyPushButton2(
            text="Save As",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["green_primary"],
            bg_color_hover = self.themes["app_color"]["green_hover"],
            bg_color_pressed = self.themes["app_color"]["green_pressed"],
            border_color = "transparent",
        )
        self.saveasBtn.setFixedHeight(40)
        self.saveasBtn.setMinimumWidth(70)
        self.fileRowLayout.addWidget(self.saveasBtn)

        self.clearModelBtn = PyPushButton2(
            text="Clear",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["dark_blue"],
            bg_color_hover = self.themes["app_color"]["dark_blue_hover"],
            bg_color_pressed = self.themes["app_color"]["dark_blue_pressed"],
            border_color = "transparent",
        )
        self.clearModelBtn.setFixedHeight(40)
        self.clearModelBtn.setMinimumWidth(60)
        self.fileRowLayout.addWidget(self.clearModelBtn)

        self.fileRowLayout.addStretch()

        self.fileSectionLayout.addWidget(self.fileRow)
        self.verticalLayout.addWidget(self.fileSection)

        ##############Setting Parameters Section#################################################
        self.parameterSection = QWidget()
        self.parameterSection.setObjectName("parameterSection")

        self.parameterSectionLayout = QVBoxLayout(self.parameterSection)
        self.parameterSectionLayout.setSpacing(5)
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

        self.MTlowfreqTextEdit = PyLineEdit2(
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
        self.MTlowfreqTextEdit.setFixedHeight(35)
        self.frequencyRowLayout.addWidget(self.MTlowfreqTextEdit)
        self.MTlowfreqTextEdit.setText('1e1')

        self.frequencyRowLayout.addWidget(PyLabel2(
            text="Maximum [Hz]",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.MTupfreqTextEdit = PyLineEdit2(
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
        self.MTupfreqTextEdit.setFixedHeight(35)
        self.frequencyRowLayout.addWidget(self.MTupfreqTextEdit)
        self.MTupfreqTextEdit.setText('1e9')

        self.MTdistributionComboBox = PyComboBox2(
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
        self.MTdistributionComboBox.addItem('Log')
        self.MTdistributionComboBox.addItem('Linear')
        self.frequencyRowLayout.addWidget(self.MTdistributionComboBox)

        self.parameterSectionLayout.addWidget(self.frequencyRow)

        ####################Formalism Type Row#############
        self.formalismRow = QWidget()
        self.formalismRow.setFixedHeight(35)
        self.formalismRowLayout = QHBoxLayout(self.formalismRow)
        self.formalismRowLayout.setSpacing(2)
        self.formalismRowLayout.setContentsMargins(0, 0, 0, 0)

        self.FormalismtypeLabel=PyLabel2(
            text="Formalism:",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        )
        self.FormalismtypeLabel.setFixedHeight(35)
        self.FormalismtypeLabel.setFixedWidth(90)
        self.formalismRowLayout.addWidget(self.FormalismtypeLabel)


        self.termComboBox = PyComboBox2(
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
        self.termComboBox.addItem('Debye')
        self.termComboBox.addItem('Cole-Cole')
        self.termComboBox.addItem('Davidson-Cole')
        self.termComboBox.addItem('Havriliak-Negami')
        self.termComboBox.setFixedWidth(130)

        self.formalismRowLayout.addWidget(self.termComboBox)

        self.termnameTextEdit = PyLineEdit2(
            text='Name',
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
        self.termnameTextEdit.setFixedHeight(35)
        self.termnameTextEdit.setFixedWidth(70)

        self.formalismRowLayout.addWidget(self.termnameTextEdit)

        self.addtermBtn = PyPushButton2(
            text="Add Term",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.addtermBtn.setFixedHeight(35)
        self.addtermBtn.setMinimumWidth(80)
        self.formalismRowLayout.addWidget(self.addtermBtn)

        self.deletetermBtn = PyPushButton2(
            text="Delete Element",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],
            border_color = "transparent",
        )
        self.deletetermBtn.setFixedHeight(35)
        self.deletetermBtn.setMinimumWidth(100)
        self.formalismRowLayout.addWidget(self.deletetermBtn)

        self.formalismRowLayout.addStretch()
        self.parameterSectionLayout.addWidget(self.formalismRow)

        ####################Polarization and DC Row#############
        self.polarizationRow = QWidget()
        self.polarizationRow.setFixedHeight(35)
        self.polarizationRowLayout = QHBoxLayout(self.polarizationRow)
        self.polarizationRowLayout.setSpacing(10)
        self.polarizationRowLayout.setContentsMargins(0, 0, 0, 0)

        self.EPcheckBox = QCheckBox("polarization")
        self.EPcheckBox.setStyleSheet(f"""
            QCheckBox {{
                color: {self.themes["app_color"]["text_foreground"]};
                font-size: {self.settings["font"]["text_size_small"]}px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {self.themes["app_color"]["input_border"]};
                border-radius: 3px;
                background-color: {self.themes["app_color"]["white"]};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.themes["app_color"]["blue_primary"]};
            }}
        """)
        self.polarizationRowLayout.addWidget(self.EPcheckBox)

        self.polarizationRowLayout.addWidget(PyLabel2(
            text="Model:",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.EPComboBox = PyComboBox2(
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
        self.EPComboBox.addItem('CPE')
        self.polarizationRowLayout.addWidget(self.EPComboBox)

        self.DCcheckBox = QCheckBox("DC conductivity")
        self.DCcheckBox.setStyleSheet(f"""
            QCheckBox {{
                color: {self.themes["app_color"]["text_foreground"]};
                font-size: {self.settings["font"]["text_size_small"]}px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {self.themes["app_color"]["input_border"]};
                border-radius: 3px;
                background-color: {self.themes["app_color"]["white"]};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.themes["app_color"]["blue_primary"]};
            }}
        """)
        self.polarizationRowLayout.addWidget(self.DCcheckBox)

        self.polarizationRowLayout.addStretch()
        self.parameterSectionLayout.addWidget(self.polarizationRow)

        #####Equation Display Row######
        self.equationRow = QWidget()
        self.equationRow.setFixedHeight(35)
        self.equationRowLayout = QHBoxLayout(self.equationRow)
        self.equationRowLayout.setSpacing(10)
        self.equationRowLayout.setContentsMargins(0, 0, 0, 0)

        self.equationRowLayout.addWidget(PyLabel2(
            text="Eps*=",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.MTmultitermTextEdit = PyLineEdit2(
            text='Equation',
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
        self.MTmultitermTextEdit.setFixedHeight(40)
        self.equationRowLayout.addWidget(self.MTmultitermTextEdit)

        self.parameterSectionLayout.addWidget(self.equationRow)

        ##################Results Table############
        label=['Name', 'Comments', 'Initial_Value','Fitted_Value','Max','Min','Fixed','Error [%]']
        self.MTtable = QTableWidget()
        self.MTtable.setRowCount(0)
        self.MTtable.setColumnCount(len(label))
        self.MTtable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.MTtable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.MTtable.setHorizontalHeaderLabels(label)
        self.MTtable.resizeColumnsToContents()
        # 每列增加20像素的宽松间距
        for i in range(len(label)):
            self.MTtable.setColumnWidth(i, self.MTtable.columnWidth(i) + 9)
        self.MTtable.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.MTtable.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                font-weight: 700;
            }
        """)
        self.parameterSectionLayout.addWidget(self.MTtable)

        ##########Calculation Buttons Row###########
        self.calculationRow = QWidget()
        self.calculationRow.setFixedHeight(35)
        self.calculationRowLayout = QHBoxLayout(self.calculationRow)
        self.calculationRowLayout.setSpacing(10)
        self.calculationRowLayout.setContentsMargins(2, 0, 0, 0)

        self.MTcalculateBtn = PyPushButton2(
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
        self.MTcalculateBtn.setFixedHeight(40)
        self.MTcalculateBtn.setMinimumWidth(100)
        self.calculationRowLayout.addWidget(self.MTcalculateBtn)

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

        self.verticalLayout.addWidget(self.parameterSection)

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