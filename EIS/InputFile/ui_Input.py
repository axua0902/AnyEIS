from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QHeaderView, QAbstractItemView, QButtonGroup, QGraphicsDropShadowEffect,
    QTableWidgetItem
)

from widgets.py_push_button.py_push_button2 import PyPushButton2    # 自定义按钮
from widgets.py_table_widget.py_table_widget2 import PyTableWidget2  # 自定义表格组件
from widgets.py_qcheckbox.py_qcheckbox2 import PyCheckBox2         # 自定义复选框
from widgets.py_combobox.py_combobox2 import PyComboBox2           # 自定义下拉框
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2          # 自定义输入框

from widgets.py_label.py_label2 import PyLabel2

# 导入设置和主题
from setting import Settings  # 应用设置
from themes import Themes     # 主题颜色


class InputdataUI(object):
    def init_ui(self,widget):
        settings = Settings()        # LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()        # LOAD THEME COLOR
        self.themes = themes.items


        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setGeometry(QRect(0, 0, 840, 580))
        self.contents.setStyleSheet(u"background: transparent;")

        self.verticalLayout = QVBoxLayout(self.contents)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)

        self.toplsublayout = QGridLayout()  ##定义布局
        self.toplsublayout.setSpacing(12)
        self.toplsublayout.setContentsMargins(15, 15, 15, 15)

        self.inputdataGB = QGroupBox('Input Data', widget)
        self.inputdataGB.setGeometry(0, 0, 300, 650)  #
        self.inputdataGB.setLayout(self.toplsublayout)
   

        self.verticalLayout.addWidget(self.inputdataGB)        # 将 inputdataGB 添加到主布局



        # 创建一个水平布局用于第一行的输入框和按钮
        self.inputGB_Row = QHBoxLayout()
        self.inputGB_Row.setSpacing(10)
        
# 第一行：Input Data按钮 + 输入框 + Open File按钮 + Delete按钮
        self.inputdataBtn = PyPushButton2(
            text = "Input Data",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.inputdataBtn.setMinimumHeight(38)
        self.inputdataBtn_effect = self.setup_button_hover_effect(self.inputdataBtn)        # Setup hover animation effect
        self.inputGB_Row.addWidget(self.inputdataBtn,1)
        
        
        # 输入框 - 数据类型选择下拉菜单
        self.inputdataComboBox = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  # 使用HTML中的border-radius: 4px
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            min_height=38,
            bg_color=self.themes["app_color"]["bg_two"],  # 使用白色背景
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],  # 使用浅色边框
        )
        self.inputGB_Row.addWidget(self.inputdataComboBox,2)



        self.openexfilebtn = PyPushButton2(
            text = "Open File",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["context_color"],
            bg_color_hover = self.themes["app_color"]["context_hover"],
            bg_color_pressed = self.themes["app_color"]["context_pressed"],
            border_color = "transparent",
        )
        self.openexfilebtn.setMinimumHeight(38)
        self.openexfilebtn_effect = self.setup_button_hover_effect(self.openexfilebtn)        # Setup hover animation effect
        self.inputGB_Row.addWidget(self.openexfilebtn,1)


        self.deletexfilebtn = PyPushButton2(
            text = "Delete",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["red_primary"],
            bg_color_hover = self.themes["app_color"]["red_hover"],
            bg_color_pressed = self.themes["app_color"]["red_pressed"],
            border_color = "transparent",
        )
        self.deletexfilebtn.setMinimumHeight(38)
        self.deletexfilebtn_effect = self.setup_button_hover_effect(self.deletexfilebtn)
        self.inputGB_Row.addWidget(self.deletexfilebtn,1)


        self.toplsublayout.addLayout(self.inputGB_Row, 0, 0, 1, 4)        # 将水平布局添加到主布局






# 第二行：创建一个水平布局用于输入框和刷新按钮
        self.fileInputRow = QHBoxLayout()
        self.fileInputRow.setSpacing(10)
        
        # Input Data Number输入框
        self.plotTextEdit = PyLineEdit2(
            text = "",
            place_holder_text = "Input File Number",
            radius = 8,
            border_size = 1,
            color = self.themes["app_color"]["text_foreground"],
            selection_color = self.themes["app_color"]["blue_primary"],
            bg_color = self.themes["app_color"]["input_bg"],
            bg_color_active = self.themes["app_color"]["input_bg"],
            context_color = self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_small"],
            font_weight=600
        )
        self.plotTextEdit.setMinimumHeight(40)

        self.fileInputRow.addWidget(self.plotTextEdit,4)

        # clear按钮
        self.clearinputbtn = PyPushButton2(
            text = "Clear",
            font_size=16,
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["text_foreground"],
            bg_color = self.themes["app_color"]["gray_hover"],
            bg_color_hover = self.themes["app_color"]["bg_four"],
            bg_color_pressed = self.themes["app_color"]["bg_three"],
            border_color = self.themes["app_color"]["light_three"],
        )
        self.clearinputbtn.setMinimumHeight(38)
        self.clearinputbtn_effect = self.setup_button_hover_effect(self.clearinputbtn)

        self.fileInputRow.addWidget(self.clearinputbtn,1)
        
        # 将水平布局添加到主布局
        self.toplsublayout.addLayout(self.fileInputRow, 1, 0, 1, 4)




# 第三行：创建一个水平布局用于复选框
        self.checkboxRow = QHBoxLayout()
        self.checkboxRow.setSpacing(24)  #
        
        # All Files复选框
        self.allCheckBox = PyCheckBox2(
            text='All Files',
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
        self.checkboxRow.addWidget(self.allCheckBox)

        # Selected File复选框
        self.selectedCheckBox = PyCheckBox2(
            text="Selected File",
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
        self.checkboxRow.addWidget(self.selectedCheckBox)
        
        
        self.selection_files_group = QButtonGroup()
        self.selection_files_group.addButton(self.allCheckBox)
        self.selection_files_group.addButton(self.selectedCheckBox)
        self.selection_files_group.setExclusive(True)

        # 默认不选择(导入文件后会在 Input.GetInputFiles 中自动设为 All)
        self.allCheckBox.setChecked(False)
        self.selectedCheckBox.setChecked(False)


        # 添加弹性空间，使复选框靠左对齐
        self.checkboxRow.addStretch()
        
        # 将水平布局添加到主布局
        self.toplsublayout.addLayout(self.checkboxRow, 2, 0, 1, 4)





# 第四行：创建一个水平布局用于输入框和刷新按钮
        self.dataInputRow = QHBoxLayout()
        self.dataInputRow.setSpacing(10)
        
        # Input Data Number输入框
        self.dataTextEdit = PyLineEdit2(
            text = "",
            place_holder_text = "Input Data Number",
            radius = 8,
            border_size = 1,
            color = self.themes["app_color"]["text_foreground"],
            selection_color = self.themes["app_color"]["blue_primary"],
            bg_color = self.themes["app_color"]["input_bg"],
            bg_color_active = self.themes["app_color"]["input_bg"],
            context_color = self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_small"],
            font_weight=600
        )
        self.dataTextEdit.setMinimumHeight(40)

        self.dataInputRow.addWidget(self.dataTextEdit)


        # Refresh按钮
        self.freshbtn = PyPushButton2(
            text = "Refresh",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["green_primary"],
            bg_color_hover = self.themes["app_color"]["green_hover"],
            bg_color_pressed = self.themes["app_color"]["green_pressed"],
            border_color = "transparent",
        )
        self.freshbtn.setMinimumHeight(38)
        self.freshbtn_effect = self.setup_button_hover_effect(self.freshbtn)
        self.dataInputRow.addWidget(self.freshbtn)
        
        # 将水平布局添加到主布局
        self.toplsublayout.addLayout(self.dataInputRow, 3, 0, 1, 4)




# 第五行：创建一个水平布局用于选择按钮
        self.selectdataCBRow = QHBoxLayout()
        self.selectdataCBRow.setSpacing(24)
        
        # "All Data
        self.selectallBtn = PyCheckBox2(
            text='All Data',
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
        self.selectdataCBRow.addWidget(self.selectallBtn)

        # Select Data
        self.selectdataBtn = PyCheckBox2(
            text="Selected Data",
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
        self.selectdataCBRow.addWidget(self.selectdataBtn)
        
        self.selection_data_group = QButtonGroup()
        self.selection_data_group.addButton(self.selectallBtn)
        self.selection_data_group.addButton(self.selectdataBtn)
        self.selection_data_group.setExclusive(True)

        # 默认不选择(导入文件后会在 Input.GetInputFiles 中自动设为 All)
        self.selectallBtn.setChecked(False)
        self.selectdataBtn.setChecked(False)

        # 添加弹性空间，使复选框靠左对齐
        self.selectdataCBRow.addStretch()
       
        # 将水平布局添加到主布局
        self.toplsublayout.addLayout(self.selectdataCBRow, 4, 0, 1, 4)



# 创建表格容器并设置边框样式
        self.tableContainer = QWidget()
        self.tableContainerLayout = QVBoxLayout(self.tableContainer)
        self.tableContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.tableContainerLayout.setSpacing(0)
                
        # 创建表格组件 - 使用PyTableWidget2并应用主题颜色
        self.tableWidget = PyTableWidget2(
            radius = 6,                                              # 表格圆角半径
            color = self.themes["app_color"]["text_foreground"],     # 文本颜色
            selection_color = self.themes["app_color"]["context_color"], # 选中项颜色
            bg_color = self.themes["app_color"]["bg_two"],           # 背景颜色
            header_horizontal_color = self.themes["app_color"]["bg_three"], # 水平表头颜色
            header_vertical_color = self.themes["app_color"]["bg_three"],   # 垂直表头颜色
            bottom_line_color = self.themes["app_color"]["light_three"],    # 底部线条颜色
            grid_line_color = self.themes["app_color"]["light_three"],      # 网格线颜色
            scroll_bar_bg_color = self.themes["app_color"]["bg_one"],       # 滚动条背景颜色
            scroll_bar_btn_color = self.themes["app_color"]["dark_four"],   # 滚动条按钮颜色
            context_color = self.themes["app_color"]["context_color"],      # 上下文颜色
            header_font_size = "14px",                               # 表头字体大小
            header_font_weight = 600                                 # 表头字体粗细
        )

        headers=['Check','Data Name', 'File Name','Comments','Path']        # 设置表格列和表头
        self.tableWidget.setColumnCount(len(headers))
        for idx, header in enumerate(headers):
            column = QTableWidgetItem(header)
            column.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 表头文本居中对齐
            self.tableWidget.setHorizontalHeaderItem(idx, column)

        # 设置表头字体加粗
        self.tableWidget.horizontalHeader().setStyleSheet("QHeaderView::section { font-weight: 700; }")


        # 设置"Check"列的列宽为60像素
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tableWidget.setColumnWidth(0, 70)
        
        # 其他列设置为可交互调整宽度
        for i in range(1, len(headers)):
            self.tableWidget.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            
        # 设置初始列宽（可选）
        self.tableWidget.setColumnWidth(1, 150)  # Data Name
        self.tableWidget.setColumnWidth(2, 140)  # File Name
        self.tableWidget.setColumnWidth(3, 126)  # Comments
        self.tableWidget.setColumnWidth(4, 60)  # Path

            
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)      # 允许多选
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)     # 按行选择

        self.tableWidget.verticalHeader().setDefaultSectionSize(40)  # 设置默认行高
        self.tableWidget.horizontalHeader().setFixedHeight(40)  # 设置表头高度

        self.tableWidget.setShowGrid(True)                         # 显示网格线
        self.tableWidget.setAlternatingRowColors(True)             # 启用交替行颜色
        

        self.tableWidget.verticalHeader().setVisible(True)         # 显示行号
        self.tableWidget.verticalHeader().setFixedWidth(30)        # 设置行号列宽
        self.tableWidget.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # 行号居中对齐

        
        # 添加初始空行
        for i in range(10):
            row_number = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_number)
            

        self.tableContainerLayout.addWidget(self.tableWidget)        # 将表格添加到容器中
        self.verticalLayout.addWidget(self.tableContainer)        # 将表格容器添加到主布局


        return  self.contents


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




