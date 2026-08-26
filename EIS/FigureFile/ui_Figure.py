from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget, QFrame
from PySide6.QtCore import QSize
from datetime import datetime


from widgets.py_push_button.py_push_button2 import PyPushButton2
from widgets.py_combobox.py_combobox2 import  PyComboBox2
from widgets.py_label.py_label2 import PyLabel2
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2          
from widgets.py_qcheckbox.py_qcheckbox2 import PyCheckBox2         # 自定义复选框


from setting import Settings# import setting
from themes import Themes # import themes



class FigureUI():
    def figureUI(self, widget):
        settings = Settings()        # load settings
        self.settings = settings.items
        themes = Themes()        # load themes
        self.themes = themes.items


        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["black"]};
            }}
        """)
        main_layout = QVBoxLayout(self.contents)  # 1.dataChartTwoColumnsLayout 2.operationSectionLayout 3.userDefineSectionLayout
        main_layout.setSpacing(1)
        main_layout.setContentsMargins(2, 2, 2, 2)

        #1.数据图表类型选择区
        self.dataChartTwoColumns = QWidget()
        self.dataChartTwoColumnsLayout = QHBoxLayout(self.dataChartTwoColumns)   # 1.dataTypeContainerLayout 2.chartTypeContainerLayout
        self.dataChartTwoColumnsLayout.setSpacing(25)
        self.dataChartTwoColumnsLayout.setContentsMargins(1, 1, 1, 1)


        self.dataChartTwoColumns.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["blue"]};

            }}
        """)
        
        #1.left        
        self.dataTypeContainer = QWidget()
        self.dataTypeContainerLayout = QVBoxLayout(self.dataTypeContainer)  # 1.dataTypeContainerTitle 2.dataTypeButtonsLayout
        self.dataTypeContainerLayout.setSpacing(1)
        self.dataTypeContainerLayout.setContentsMargins(1, 1, 1, 1)

        self.dataTypeContainer.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["red"]};

            }}
        """)
        self.dataChartTwoColumnsLayout.addWidget(self.dataTypeContainer)


        #1.left.1        
        self.dataSettingsTitle = PyLabel2(
            text="Data Type",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
            padding_left="5px",
            border_left=f"3px solid {self.themes['app_color']['context_color']}"
        )
        self.dataTypeContainerLayout.addWidget(self.dataSettingsTitle)

        #1.left.2        
        self.dataTypeFormGroup = QWidget()
        self.dataTypeFormGroupLayout = QHBoxLayout(self.dataTypeFormGroup)  # 1.datatypeLineEdit 2.datatypeComboBox
        self.dataTypeFormGroupLayout.setContentsMargins(1, 0, 1, 1)

        #1.left.2.left        

        self.datatypeLineEdit = PyLabel2(
            text='Data Setting:',
            color=self.themes["app_color"]["text_foreground"],
            font_size=14,
            font_weight=500,
        )
        self.dataTypeFormGroupLayout.addWidget(self.datatypeLineEdit)

        #1.left.2.right        
        self.datatypeComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  
            font_size=self.settings["font"]["text_size_small"],
            font_weight=700,
            min_height=30,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.datatypeComboBox.addItems([ 'f-Z,Phase,Re(Z),Im(Z)', 'f-Epsilon,Sigma','General', 'Time order'])
        self.datatypeComboBox.setFixedWidth(160)
        self.dataTypeFormGroupLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.dataTypeFormGroupLayout.addWidget(self.datatypeComboBox)


        self.dataTypeContainerLayout.addWidget(self.dataTypeFormGroup)

        #1.left.3
        self.dataProcessingStateGroup = QWidget()
        self.dataProcessingStateLayout = QHBoxLayout(self.dataProcessingStateGroup)  # 1.origindataCheckBox 2.processeddataCheckBox
        self.dataProcessingStateLayout.setContentsMargins(0, 0, 0, 0)
        self.dataProcessingStateLayout.setSpacing(10)
        
        # self.origindataCheckBox = QCheckBox('Original')
        self.origindataCheckBox = PyCheckBox2(
            text='Original',
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
        self.origindataCheckBox.setChecked(False)
        self.dataProcessingStateLayout.addWidget(self.origindataCheckBox)
        
        self.processeddataCheckBox = PyCheckBox2(
            text='Processed',
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
        self.processeddataCheckBox.setChecked(False)
        self.dataProcessingStateLayout.addWidget(self.processeddataCheckBox)
        self.dataProcessingStateLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.dataTypeContainerLayout.addWidget(self.dataProcessingStateGroup)


        #1.right        
        self.chartTypeContainer = QWidget()
        self.chartTypeContainerLayout = QVBoxLayout(self.chartTypeContainer)  # 1.chartTypeTitle 2.chartTypeOptionsLayout
        self.chartTypeContainerLayout.setContentsMargins(1, 1, 1, 1)
        self.chartTypeContainerLayout.setSpacing(1)
        self.chartTypeContainer.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["red"]};

            }}
        """)
        
        #1.right.1
        self.chartTypeTitle = PyLabel2(
            text="Chart Type",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_weight=600,
            padding_left="5px",
            border_left=f"3px solid {self.themes['app_color']['context_color']}"
        )
        self.chartTypeContainerLayout.addWidget(self.chartTypeTitle)

        #1.right.2
        self.chartTypeOptions = QWidget()
        self.chartTypeOptionsLayout = QGridLayout(self.chartTypeOptions)# 1.BodeXOption 2.BodeRsOption 3.NyquistOption 4.AllOption
        self.chartTypeOptionsLayout.setContentsMargins(5, 2, 2, 2)

        self.chartTypeOptionsLayout.setSpacing(5)

        # 创建七个图表类型选项

        self.NyquistOption = QPushButton("Nyquist\nRe(Z)-Im(Z)")  # Nyquist图表选项按钮 NyquistOption
        self.NyquistOption.setCheckable(True)

        self.NyquistOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: 700;	
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        self.chartTypeOptionsLayout.addWidget(self.NyquistOption,0,0)

        self.BodeReOption = QPushButton("Bode\nf-Re(Z)")# BodeRs图表选项按钮 BodeRsOption
        self.BodeReOption.setCheckable(True)
        self.BodeReOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: 700;	
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)

 
        self.chartTypeOptionsLayout.addWidget(self.BodeReOption,0,1)


        self.BodeImOption = QPushButton("Bode\nf-Im(Z)")  # BodeX图表选项按钮 BodeXOption
        self.BodeImOption.setCheckable(True)
        self.BodeImOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;

                font-size: 12px;
                font-weight: 700;	
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        self.chartTypeOptionsLayout.addWidget(self.BodeImOption,0,2)


        self.BodePhyOption = QPushButton("Bode\nf-Phase")  # BodeX图表选项按钮 BodeXOption
        self.BodePhyOption.setCheckable(True)
        self.BodePhyOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: 700;	
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        self.chartTypeOptionsLayout.addWidget(self.BodePhyOption,0,3)
        
        self.AllOption = QPushButton("All")  # 全部图表选项按钮 AllOption
        self.AllOption.setCheckable(True)
        self.AllOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: 700;
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        self.chartTypeOptionsLayout.addWidget(self.AllOption,1,0)


        self.timeorderOption = QPushButton("Time\nOrder")  # 时间序列图表选项按钮 AllOption
        self.timeorderOption.setCheckable(True)
        self.timeorderOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: 700;	
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        self.chartTypeOptionsLayout.addWidget(self.timeorderOption,1,1)



        self.normalOption = QPushButton("Normal")  # 时间序列图表选项按钮 AllOption
        self.normalOption.setCheckable(True)
        self.normalOption.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.themes["app_color"]["light_three"]};
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: 700;	
                height: 30px;
                background-color: {self.themes["app_color"]["bg_two"]};
            }}
            QPushButton:checked {{
                border-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        self.chartTypeOptionsLayout.addWidget(self.normalOption,1,2)


        self.chartTypeContainerLayout.addWidget(self.chartTypeOptions)        # 将图表类型选项按钮布局添加到图表类型容器

        self.dataChartTwoColumnsLayout.addWidget(self.chartTypeContainer)



        #2.操作区
        self.operationSection = QWidget()
        self.operationSectionLayout = QVBoxLayout(self.operationSection)  # 1.operationSectionTitle 2.basicOperationButtonsLayout 3.excelFileGroupLayout
        self.operationSectionLayout.setSpacing(5)
        self.operationSection.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)

        #2.1
        self.operationSectionTitle = PyLabel2(
            text="Operation",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            padding_left="5px",
            border_left=f"3px solid {self.themes['app_color']['context_color']}"
        )
        self.operationSectionLayout.addWidget(self.operationSectionTitle)
        
        #2.2
        self.basicOperationButtons = QWidget()  # 基本操作按钮容器 basicOperationButtons
        self.basicOperationButtonsLayout = QHBoxLayout(self.basicOperationButtons)  # 1.drawbtn 2.clearbtn 3.toolbtn
        self.basicOperationButtonsLayout.setSpacing(20)  # 增加按钮间距从10到20
        
        self.drawbtn = PyPushButton2(  # 绘图按钮 drawbtn
            text="Draw",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["context_color"],
            bg_color_hover=self.themes["app_color"]["context_hover"],
            bg_color_pressed=self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.drawbtn.setMinimumHeight(38)
        self.drawbtn.setMinimumWidth(100)  # 增加按钮宽度
        self.drawbtn_effect = self.setup_button_hover_effect(self.drawbtn)        # Setup hover animation effect

        self.basicOperationButtonsLayout.addWidget(self.drawbtn)
        
        self.clearbtn = PyPushButton2(
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
        self.clearbtn.setMinimumHeight(38)
        self.clearbtn.setMinimumWidth(100)  # 增加按钮宽度
        self.clearbtn_effect = self.setup_button_hover_effect(self.clearbtn)
        self.basicOperationButtonsLayout.addWidget(self.clearbtn)

        self.toolbtn = PyPushButton2(
            text="Tools",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["light_blue"],
            bg_color_hover = self.themes["app_color"]["light_blue_hover"],
            bg_color_pressed = self.themes["app_color"]["light_blue_pressed"],
            border_color = "transparent",
        )
        self.toolbtn.setMinimumHeight(38)
        self.toolbtn.setMinimumWidth(100)  # 增加按钮宽度
        self.toolbtn_effect = self.setup_button_hover_effect(self.toolbtn)

        self.basicOperationButtonsLayout.addWidget(self.toolbtn)


        self.PaperFigurebtn = PyPushButton2(
            text="Paper Figure",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.PaperFigurebtn.setMinimumHeight(38)
        self.PaperFigurebtn.setMinimumWidth(100)  # 增加按钮宽度
        self.PaperFigurebtn_effect = self.setup_button_hover_effect(self.PaperFigurebtn)

        self.basicOperationButtonsLayout.addWidget(self.PaperFigurebtn)
        self.basicOperationButtonsLayout.addStretch()        # # 添加弹性空间，使按钮靠左对齐

        self.operationSectionLayout.addWidget(self.basicOperationButtons)

        #2.3
        self.excelFileGroup = QWidget()
        self.excelFileGroupLayout = QHBoxLayout(self.excelFileGroup)  # 1.excelnameLineEdit 2.excelnameTextEdit 3.savebtn
        self.excelFileGroupLayout.setContentsMargins(0, 0, 0, 0)
        self.excelFileGroupLayout.setSpacing(2)
        
        self.excelnameLineEdit = PyLabel2(  # Excel名称标签 excelnameLineEdit
            text='Excel Name:',
            color=self.themes["app_color"]["text_foreground"],
            font_size=self.settings["font"]["text_size_small"],
            font_weight=600,
        )
        self.excelnameLineEdit.setFixedWidth(110)        # 设置标签的固定宽度，确保标签不会占用太多空间
        self.excelFileGroupLayout.addWidget(self.excelnameLineEdit)
        
        dt = datetime.now()  ##获得当前时间
        excelname = str(dt.strftime('%y%m%d%H%M%S'))
        self.excelnameTextEdit = PyLineEdit2(
            text='data' + '_' + excelname,
            radius = 8,
            border_size = 1,
            color = self.themes["app_color"]["text_foreground"],
            selection_color = self.themes["app_color"]["blue_primary"],
            bg_color = self.themes["app_color"]["input_bg"],
            bg_color_active = self.themes["app_color"]["input_bg"],
            context_color = self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.excelnameTextEdit.setFixedWidth(170)        # 设置标签的固定宽度，确保标签不会占用太多空间
        self.excelnameTextEdit.setFixedHeight(40)
        self.excelFileGroupLayout.addWidget(self.excelnameTextEdit)

        self.savebtn = PyPushButton2(
            text="Export to Excel",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["green_primary"],
            bg_color_hover=self.themes["app_color"]["green_hover"],
            bg_color_pressed=self.themes["app_color"]["green_pressed"],
            border_color="transparent",
        )
        self.savebtn.setMinimumHeight(38)
        self.savebtn.setFixedWidth(130)

        self.savebtn_effect = self.setup_button_hover_effect(self.savebtn)

        self.excelFileGroupLayout.addWidget(self.savebtn)


        self.openExcelbtn = PyPushButton2(
            text="Open Excel",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["green_primary"],
            bg_color_hover=self.themes["app_color"]["green_hover"],
            bg_color_pressed=self.themes["app_color"]["green_pressed"],
            border_color="transparent",
        )
        self.openExcelbtn.setMinimumHeight(38)
        self.openExcelbtn.setFixedWidth(100)
        self.openExcelbtn_effect = self.setup_button_hover_effect(self.openExcelbtn)


        self.excelFileGroupLayout.addWidget(self.openExcelbtn)


        self.excelFileGroupLayout.addStretch()
        self.operationSectionLayout.addWidget(self.excelFileGroup)





        #3.用户定义区
        self.userDefineSection= QWidget()
        self.userDefineSectionLayout = QVBoxLayout(self.userDefineSection)  # 1.userDefineSectionTitle 2.userDefineButtonsLayout
        self.userDefineSectionLayout.setSpacing(8)
        self.userDefineSection.setStyleSheet(f"""
            QWidget {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                # border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)
        
        #3.1
        # 添加标题：用户自定义
        self.userDefineSectionTitle = PyLabel2(
            text="User Define",
            color=self.themes["app_color"]["text_title"],
            font_size=16,
            font_weight=700,
            padding_left="5px",
            border_left=f"3px solid {self.themes['app_color']['context_color']}"
        )
        self.userDefineSectionLayout.addWidget(self.userDefineSectionTitle)

        #3.2
        # 用户自定义按钮组布局
        self.userDefinedButtonsLayout = QHBoxLayout()  # 1.PaperFigurebtn 2.userdefine2btn 3.userdefine3btn 4.userdefine4btn
        self.userDefinedButtonsLayout.setSpacing(5)
        

        self.userdefine1btn = PyPushButton2(  # 用户自定义按钮1 userdefine1btn
            text="DS data creater",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.userdefine1btn.setMinimumHeight(38)
        self.userdefine1btn.setMinimumWidth(80)  # 增加按钮宽度

        self.userdefine1btn_effect = self.setup_button_hover_effect(self.userdefine1btn)
        self.userDefinedButtonsLayout.addWidget(self.userdefine1btn)


        self.userdefine2btn = PyPushButton2(  # 用户自定义按钮2 userdefine2btn
            text="User Define 2",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["purple_blue"],
            bg_color_hover = self.themes["app_color"]["purple_blue_hover"],
            bg_color_pressed = self.themes["app_color"]["purple_blue_pressed"],
            border_color = "transparent",
        )
        self.userdefine2btn.setMinimumHeight(38)
        self.userdefine2btn.setMinimumWidth(80)  # 增加按钮宽度

        self.userdefine2btn_effect = self.setup_button_hover_effect(self.userdefine2btn)

        self.userDefinedButtonsLayout.addWidget(self.userdefine2btn)

        self.userdefine3btn = PyPushButton2(  # 用户自定义按钮3 userdefine3btn
            text="User Define 3",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["btn_info"],
            bg_color_hover = self.themes["app_color"]["btn_info_hover"],
            bg_color_pressed = self.themes["app_color"]["btn_info_pressed"],
            border_color = "transparent",
        )
        self.userdefine3btn.setMinimumHeight(38)
        self.userdefine3btn.setMinimumWidth(80)  # 增加按钮宽度

        self.userdefine3btn_effect = self.setup_button_hover_effect(self.userdefine3btn)
        self.userDefinedButtonsLayout.addWidget(self.userdefine3btn)
        
        self.userdefine4btn = PyPushButton2(  # 用户自定义按钮4 userdefine4btn
            text="User Define 4",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],
            border_color = "transparent",
        )
        self.userdefine4btn.setMinimumHeight(38)
        self.userdefine4btn.setMinimumWidth(80)  # 增加按钮宽度

        self.userdefine4btn_effect = self.setup_button_hover_effect(self.userdefine4btn)
        self.userDefinedButtonsLayout.addWidget(self.userdefine4btn)

        self.userdefine5btn = PyPushButton2(  # 数据统计和误差计算
            text="Data Statistics ",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],
            border_color = "transparent",
        )
        self.userdefine5btn.setMinimumHeight(38)
        self.userdefine5btn.setMinimumWidth(80)  # 增加按钮宽度

        self.userdefine5btn_effect = self.setup_button_hover_effect(self.userdefine5btn)
        self.userDefinedButtonsLayout.addWidget(self.userdefine5btn)





        # 添加弹性空间，使按钮靠左对齐
        self.userDefinedButtonsLayout.addStretch()
        
        self.userDefineSectionLayout.addLayout(self.userDefinedButtonsLayout)



        main_layout.addWidget(self.dataChartTwoColumns) 
        main_layout.addWidget(self.operationSection)
        main_layout.addWidget(self.userDefineSection)


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
