# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 15:55:38 2020

@author: takeilab
"""

import os, sys
import pandas as pd
import numpy as np

from random import randint
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget, QFrame
from PySide6.QtCore import QSize

from widgets.py_push_button.py_push_button2 import PyPushButton2
from widgets.py_combobox.py_combobox2 import  PyComboBox2
from widgets.py_label.py_label2 import PyLabel2
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2     



global plotdata
global plotdataname
global outputlist

global globalfileslist
global globalchosedfileslist
# 导入设置和主题
from setting import Settings  # 应用设置
from themes import Themes     # 主题颜色

class settingUI():
    def setupUI(self, widget):
        settings = Settings()        # LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()        # LOAD THEME COLOR
        self.themes = themes.items

        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setFixedHeight(90)  # 限制高度，配合父容器
        self.contents.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.contents.setStyleSheet(f"""
            #contents {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)

        self.verticalLayout = QVBoxLayout(self.contents)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 5)
        self.verticalLayout.setStretch(0, 0)  # settingSection 不扩展
        self.verticalLayout.setStretch(1, 0)  # resultsSection 不扩展

        ##############Fitting Setting Section##################################################
        self.settingSection = QWidget()
        self.settingSectionLayout = QVBoxLayout(self.settingSection)
        self.settingSectionLayout.setSpacing(1)
        self.settingSectionLayout.setContentsMargins(1, 1, 1, 1)

        # Setting title
        self.settingTitle = PyLabel2(
            text="Fitting Setting",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.settingTitle.setFixedHeight(35)
        self.settingSectionLayout.addWidget(self.settingTitle)

        # Method row
        self.methodRow = QWidget()
        self.methodRow.setFixedHeight(35)
        self.methodRowLayout = QHBoxLayout(self.methodRow)
        self.methodRowLayout.setSpacing(5)
        self.methodRowLayout.setContentsMargins(0, 0, 0, 0)

        self.methodRowLayout.addWidget(PyLabel2(
            text="Method:",
            color=self.themes["app_color"]["text_title"],
            font_family=self.settings["font"]["family"],
            font_size=self.settings["font"]["text_size_utralsmall"],
            font_weight=600,
        ))

        self.methodComboBox = PyComboBox2(
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
        self.methodComboBox.addItem('least_squares')
        self.methodComboBox.addItem('nelder')
        self.methodComboBox.addItem('lbfgsb')
        self.methodComboBox.addItem('differential_evolution')
        self.methodComboBox.addItem('basinhopping')
        self.methodComboBox.addItem('powell')
        self.methodComboBox.addItem('cg')
        self.methodComboBox.addItem('dual_annealing')
        self.methodComboBox.addItem('bfgs')
        self.methodComboBox.addItem('ampgo')
        self.methodComboBox.currentIndexChanged.connect(self.on_method_changed)
        self.methodRowLayout.addWidget(self.methodComboBox)
        self.methodRowLayout.addStretch()

        self.settingSectionLayout.addWidget(self.methodRow)

        self.paramRow = QWidget()
        self.paramRow.setFixedHeight(30)
        self.paramRowLayout = QHBoxLayout(self.paramRow)
        self.paramRowLayout.setSpacing(2)
        self.paramRowLayout.setContentsMargins(0, 0, 0, 0)

        self.METHOD_PARAM_COUNTS = {
            'least_squares': 3,
            'nelder': 2,
            'lbfgsb': 3,
            'differential_evolution': 6,
            'basinhopping': 6,
            'powell': 3,
            'cg': 3,
            'dual_annealing': 6,
            'bfgs': 3,
            'ampgo': 5,
        }
        self.METHOD_PARAM_NAMES = {
            'least_squares': ['xtol', 'ftol', 'gtol'],
            'nelder': ['xatol', 'fatol'],
            'lbfgsb': ['ftol', 'gtol', 'maxls'],
            'differential_evolution': ['strategy', 'maxiter', 'popsize', 'tol', 'mutation', 'recombination'],
            'basinhopping': ['T', 'niter', 'stepsize', 'accept_test', 'boltzmann_temp', 'wik'],
            'powell': ['xtol', 'ftol', 'maxit'],
            'cg': ['gtol', 'norm', 'eps'],
            'dual_annealing': ['initial_temp', 'restart_temp_ratio', 'visit', 'accept', 'maxiter', 'no_local_search'],
            'bfgs': ['gtol', 'norm', 'eps'],
            'ampgo': ['iter', 'tol', 'eps', 'maxfun', 'maxiter'],
        }
        self.current_param_count = 3
        self.current_method = 'least_squares'
        self.build_param_row(self.current_param_count, self.METHOD_PARAM_NAMES[self.current_method])
        self.settingSectionLayout.addWidget(self.paramRow)

        self.verticalLayout.addWidget(self.settingSection)

    def build_param_row(self, param_count, param_names=None):
        while self.paramRowLayout.count() > 0:
            item = self.paramRowLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i in range(1, param_count + 1):
            p_name = param_names[i-1] if param_names and i <= len(param_names) else f'p{i}'
            p_default = '1e-5'
            self.paramRowLayout.addWidget(PyLabel2(
                text=f"{p_name}:",
                color=self.themes["app_color"]["text_title"],
                font_family=self.settings["font"]["family"],
                font_size=self.settings["font"]["text_size_utralsmall"],
                font_weight=600,
            ))

            textedit = PyLineEdit2(
                text=p_default,
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
            textedit.setFixedHeight(30)
            textedit.setFixedWidth(60)
            setattr(self, f'{p_name}TextEdit', textedit)
            self.paramRowLayout.addWidget(textedit)

        self.paramRowLayout.addStretch()

    def on_method_changed(self, index):
        method_name = self.methodComboBox.currentText()
        new_count = self.METHOD_PARAM_COUNTS.get(method_name, 3)
        param_names = self.METHOD_PARAM_NAMES.get(method_name, [])
        if new_count != self.current_param_count or method_name != self.current_method:
            self.current_param_count = new_count
            self.current_method = method_name
            self.build_param_row(new_count, param_names)


class resultsUI():
    def resultsUI(self, widget):
        settings = Settings()        # LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()        # LOAD THEME COLOR
        self.themes = themes.items

        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setFixedHeight(160)  # 扩展高度，配合父容器
        self.contents.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.contents.setStyleSheet(f"""
            #contents {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes["app_color"]["blue"]};
            }}
        """)

        self.verticalLayout = QVBoxLayout(self.contents)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setStretch(0, 1)  # resultsSection 可扩展

        ##############Results Section##################################################
        self.resultsSection = QWidget()
        self.resultsSectionLayout = QVBoxLayout(self.resultsSection)
        self.resultsSectionLayout.setSpacing(2)
        self.resultsSectionLayout.setContentsMargins(1, 1, 1, 0)

        # Results title and dataset selector row
        self.resultsTitleRow = QWidget()
        self.resultsTitleRow.setFixedHeight(35)
        self.resultsTitleRowLayout = QHBoxLayout(self.resultsTitleRow)
        self.resultsTitleRowLayout.setSpacing(10)
        self.resultsTitleRowLayout.setContentsMargins(0, 0, 0, 0)

        self.resultsTitle = PyLabel2(
            text="Fitting Results",
            color=self.themes["app_color"]["text_title"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        self.resultsTitleRowLayout.addWidget(self.resultsTitle)

        # Dataset selector (hidden by default, shown when multiple datasets exist)
        self.datasetSelectorLabel = PyLabel2(
            text="Dataset:",
            color=self.themes["app_color"]["text_foreground"],
            font_size=self.settings["font"]["text_size_small"],
            font_family=self.settings["font"]["family"],
        )
        self.datasetSelectorLabel.setVisible(False)
        self.resultsTitleRowLayout.addWidget(self.datasetSelectorLabel)

        self.datasetSelector = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings["font"]["text_size_normal"],
            min_height=35,
            bg_color=self.themes["app_color"]["bg_two"],
            bg_color_hover=self.themes["app_color"]["light_three"],
            border_color=self.themes["app_color"]["light_three"],
        )
        self.datasetSelector.setVisible(False)
        self.datasetSelector.currentIndexChanged.connect(self.on_dataset_changed)
        self.resultsTitleRowLayout.addWidget(self.datasetSelector)

        self.resultsTitleRowLayout.addStretch()
        self.resultsSectionLayout.addWidget(self.resultsTitleRow)

        # Results table - 显示整体拟合指标（横向布局）
        # 初始化时设置默认的横向表头，数据更新时会重新设置
        self.resultstable = QTableWidget()
        self.resultstable.setRowCount(0)
        default_headers = ['Dataset', 'NFev', 'NData', 'R²', 'RMSE', 'χ²', 'Chi²', 'Reduced χ²', 'BIC']
        self.resultstable.setColumnCount(len(default_headers))
        self.resultstable.setHorizontalHeaderLabels(default_headers)
        self.resultstable.verticalHeader().setVisible(False)
        self.resultstable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.resultstable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.resultstable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        # 横向布局只有一行数据，高度设置为刚好能显示表头+一行数据
        self.resultstable.setFixedHeight(60)
        self.resultstable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.resultsSectionLayout.addWidget(self.resultstable)

        # Overall results table - 已废弃，现在使用 resultstable 显示指标
        self.overallresultstable = QTableWidget()
        self.overallresultstable.setRowCount(0)
        self.overallresultstable.setColumnCount(2)
        self.overallresultstable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.overallresultstable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.overallresultstable.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.overallresultstable.verticalHeader().setVisible(False)
        self.overallresultstable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.overallresultstable.setMaximumHeight(0)  # 隐藏此表格，现在使用 resultstable
        self.resultsSectionLayout.addWidget(self.overallresultstable)

        # Save button row
        self.saveButtonRow = QWidget()
        self.saveButtonRow.setFixedHeight(35)
        self.saveButtonRowLayout = QHBoxLayout(self.saveButtonRow)
        self.saveButtonRowLayout.setSpacing(10)
        self.saveButtonRowLayout.setContentsMargins(2, 0, 0, 0)

        self.savereultsbtn = PyPushButton2(
            text="Save to Excel",
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["green_primary"],
            bg_color_hover = self.themes["app_color"]["green_hover"],
            bg_color_pressed = self.themes["app_color"]["green_pressed"],
            border_color = "transparent",
        )
        self.savereultsbtn.setFixedHeight(35)
        self.savereultsbtn.setMinimumWidth(120)
        self.saveButtonRowLayout.addWidget(self.savereultsbtn)
        self.saveButtonRowLayout.addStretch()

        self.resultsSectionLayout.addWidget(self.saveButtonRow)

        self.verticalLayout.addWidget(self.resultsSection)

    def on_dataset_changed(self, index):
        """
        当用户选择不同的数据集时调用

        参数:
            index: 选择的数据集索引
        """
        print(f'选择数据集: {index}')
        # 可以在这里发出信号通知其他组件

    def setDatasetSelectorVisible(self, visible, count=0):
        """
        设置数据集选择器的可见性

        参数:
            visible: 是否可见
            count: 数据集数量
        """
        self.datasetSelectorLabel.setVisible(visible)
        self.datasetSelector.setVisible(visible)

        if visible and count > 0:
            # 填充下拉框选项
            self.datasetSelector.clear()
            for i in range(count):
                self.datasetSelector.addItem(f"Dataset {i + 1}")
            if count > 1:
                self.datasetSelector.setCurrentIndex(0)

    def getSelectedDatasetIndex(self):
        """
        获取当前选中的数据集索引

        返回:
            int: 选中的数据集索引（从0开始）
        """
        return self.datasetSelector.currentIndex()


# class bottomLWidget(QWidget):
#     def __init__(self, *args, **kwargs):
#         super(bottomLWidget, self).__init__(*args, **kwargs)
#         layout = QVBoxLayout(self)
#         layout.addWidget(ProgressBar(self, minimum=0, maximum=100, objectName="RedProgressBar"))


# class ProgressBar(QProgressBar):
#     def __init__(self, *args, **kwargs):
#         super(ProgressBar, self).__init__(*args, **kwargs)
#         self.setValue(0)
#         if self.minimum() != self.maximum():
#             self.timer = QTimer(self, timeout=self.onTimeout)
#             self.timer.start(randint(1, 3) * 1000)

#     def onTimeout(self):
#         if self.value() >= 100:
#             self.timer.stop()
#             self.timer.deleteLater()
#             del self.timer
#             return
#         self.setValue(self.value() + 1)

    def updateResultsTable(self, fit_result, Z_data=None, Z_fitted=None, dataset_index=0):
        """
        更新整体拟合结果表格

        参数:
            fit_result: lmfit 拟合结果对象
            Z_data: 原始阻抗数据 (复数数组)
            Z_fitted: 拟合阻抗数据 (复数数组)
            dataset_index: 数据集索引
        """
        print("\n" + "="*50)
        print("[updateResultsTable] 开始更新结果表格")
        print(f"[updateResultsTable] fit_result: {type(fit_result)}")
        print(f"[updateResultsTable] Z_data: {Z_data is not None}")
        print(f"[updateResultsTable] Z_fitted: {Z_fitted is not None}")
        
        # 清空表格
        self.resultstable.setRowCount(0)

        # 计算整体拟合指标
        metrics = []

        # 基本信息
        metrics.append(('Dataset', f'#{dataset_index + 1}'))
        metrics.append(('NFev', fit_result.nfev if hasattr(fit_result, 'nfev') else 'N/A'))
        metrics.append(('NData', len(fit_result.data) if hasattr(fit_result, 'data') and fit_result.data is not None else 'N/A'))

        # 计算 R² 和 RMSE（如果有原始数据）
        if Z_data is not None and Z_fitted is not None:
            Z_data = np.array(Z_data)
            Z_fitted = np.array(Z_fitted)

            # 计算残差
            residuals = Z_data - Z_fitted

            # 计算 R²
            ss_res = np.sum(np.abs(residuals) ** 2)
            ss_tot = np.sum(np.abs(Z_data - np.mean(Z_data)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            metrics.append(('R²', f'{r_squared:.6f}'))

            # 计算 RMSE
            rmse = np.sqrt(np.mean(np.abs(residuals) ** 2))
            metrics.append(('RMSE', f'{rmse:.6f}'))

            # 计算卡方
            chi_sq = np.sum(np.abs(residuals) ** 2 / np.abs(Z_data))
            metrics.append(('χ²', f'{chi_sq:.6f}'))

        # 归一化误差
        if hasattr(fit_result, 'chisqr'):
            metrics.append(('Chi²', f'{fit_result.chisqr:.6e}'))
        if hasattr(fit_result, 'red_chisqr'):
            metrics.append(('Reduced χ²', f'{fit_result.red_chisqr:.6e}'))

        # BIC（如果可用）
        if hasattr(fit_result, 'bic'):
            metrics.append(('BIC', f'{fit_result.bic:.4f}'))

        print(f"[updateResultsTable] metrics数量: {len(metrics)}")
        for name, value in metrics:
            print(f"  {name}: {value}")

        # 添加到表格 - 横向布局：第一行是表头，第二行是数值
        # 设置表格为1行（数据行），列数为指标数量
        self.resultstable.setRowCount(1)
        self.resultstable.setColumnCount(len(metrics))
        
        # 第一行：表头（参数名）
        self.resultstable.setHorizontalHeaderLabels([name for name, _ in metrics])
        
        # 第二行：数值（第一行的单元格）
        for i, (name, value) in enumerate(metrics):
            self.resultstable.setItem(0, i, QTableWidgetItem(str(value)))
        
        print(f"[updateResultsTable] 完成，表格设置: {self.resultstable.rowCount()}行 x {self.resultstable.columnCount()}列")
        print("="*50)

    def clearResultsTable(self):
        """清空结果表格"""
        self.resultstable.setRowCount(0)




