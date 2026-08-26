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
# from PySide6.QtSvgWidgets import *
from PySide6.QtCore import Signal

global plotdata
global plotdataname
global outputlist

global globalfileslist
global globalchosedfileslist

# import numpy as np
# import matplotlib.pyplot as plt

# import Other.EISplot as Ep
# import Other.standard_parameter as Sp

# from lmfit import Minimizer, Parameters, report_fit
# from lmfit import  fit_report, minimize


from EIS.FittingFile.FittingSetResUI import settingUI, resultsUI


class settingWidget(QWidget):  ##############输入仿真参数
    Settingsignal = Signal(list, list, list)

    def __init__(self, parent=None):
        super(settingWidget, self).__init__(parent)
        ########变量申明###############
        self.outputlist = list()  #############被选中的数据###########
        self.plotdata = list()  #############所有数据###########
        self.plotdataname = list()  #############被选中的数据名###########
        self.message = list()  ########数据信息

        self.filesnamelist = list()
        ########变量申明###############

        self.settingui = settingUI()  # 输入UI界面
        self.settingui.setupUI(self)

        # Add canvas to layout if necessary
        setting_main_layout = QVBoxLayout(self)
        setting_main_layout.addWidget(self.settingui.contents)

    def sendsignal(self, outputlist, prodataname, resultsdata):
        outputdataname = prodataname
        outputdata = resultsdata
        self.Settingsignal.emit(outputlist, outputdataname, outputdata)  ####发送数据
        print('Data emitted process')  ###输出到状态栏

    def get_settings(self):
        """
        获取当前 Fitting 设置
        返回: dict 包含 method 和对应的参数名/值
        """
        method = self.settingui.methodComboBox.currentText()
        param_names = self.settingui.METHOD_PARAM_NAMES.get(method, [])
        settings = {'method': method}
        for name in param_names:
            textedit = getattr(self.settingui, f'{name}TextEdit', None)
            if textedit:
                settings[name] = textedit.text()
        return settings


class resultWidget(QWidget):  ############输出仿真结果
    def __init__(self, parent=None):
        super(resultWidget, self).__init__(parent)
        self.resultsui = resultsUI()
        self.resultsui.resultsUI(self)

        results_main_layout = QVBoxLayout(self)
        results_main_layout.addWidget(self.resultsui.contents)

        # 连接数据集选择器信号
        self.resultsui.datasetSelector.currentIndexChanged.connect(self.on_dataset_selector_changed)

    def getsingal(self, message1, inputdataname, inputdata, message4):
        global outputlist
        print('接收outputlist process')
        outputlist = message1

        global prodataname
        print('接收plotdataname process')
        prodataname = inputdataname

        global prodata
        print('接收plotdata process')
        prodata = inputdata

        global fittedresults
        print('接收fittedresults')
        fittedresults = message4
        
        print(f"[getsingal] outputlist: {outputlist}")
        print(f"[getsingal] prodataname: {prodataname}")
        print(f"[getsingal] inputdata长度: {len(inputdata) if inputdata else 0}")
        print(f"[getsingal] fittedresults长度: {len(fittedresults) if fittedresults else 0}")

        self.update_results_table()

        # 更新整体拟合效果表格
        if fittedresults and len(fittedresults) > 0:
            # 设置数据集选择器
            n_datasets = len(fittedresults)
            self.resultsui.setDatasetSelectorVisible(n_datasets > 1, n_datasets)

            # 获取选中的数据集索引
            dataset_index = self.resultsui.getSelectedDatasetIndex()
            if dataset_index < 0:
                dataset_index = 0

            Z_data = None
            Z_fitted = None

            print(f"[getsingal] dataset_index: {dataset_index}")
            print(f"[getsingal] prodata长度: {len(prodata) if prodata else 0}")

            # 根据数据类型获取原始数据
            if prodata and len(prodata) > dataset_index:
                data_dict = prodata[dataset_index]
                print(f"[getsingal] prodata[{dataset_index}]类型: {type(data_dict)}")
                # 检测数据类型：MT数据包含 epsRE[-]，ECM数据包含 Rs[ohm]
                if 'epsRE[-]' in data_dict.columns:
                    # MT数据格式：使用 epsRE 和 sigmaRE
                    epsRE = data_dict['epsRE[-]'].values
                    sigmaRE = data_dict['sigmaRE[S/m]'].values
                    Z_data = epsRE + 1j * sigmaRE
                elif 'Rs[ohm]' in data_dict.columns:
                    # ECM数据格式：使用 Rs 和 X
                    Z_data = data_dict['Rs[ohm]'].values + 1j * data_dict['X[ohm]'].values
                    print(f"[getsingal] Z_data构建成功: {Z_data[:3]}...")

            # 获取拟合数据 - inputdata是交错排列的[原始数据, 拟合数据, 原始数据, 拟合数据, ...]
            # Z_fitted应该在inputdata的奇数索引位置
            fitted_index = dataset_index * 2 + 1
            if inputdata and len(inputdata) > fitted_index:
                fitted_dict = inputdata[fitted_index]
                print(f"[getsingal] inputdata[{fitted_index}]类型: {type(fitted_dict)}")
                if hasattr(fitted_dict, 'columns'):
                    if 'Rs[ohm]' in fitted_dict.columns:
                        # ECM 数据格式
                        Z_fitted = fitted_dict['Rs[ohm]'].values + 1j * fitted_dict['X[ohm]'].values
                        print(f"[getsingal] Z_fitted(ECM)构建成功: {Z_fitted[:3]}...")
                    elif 'epsRE[-]' in fitted_dict.columns:
                        # MT 数据格式
                        Z_fitted = fitted_dict['epsRE[-]'].values + 1j * fitted_dict['sigmaRE[S/m]'].values
                        print(f"[getsingal] Z_fitted(MT)构建成功: {Z_fitted[:3]}...")

            self.update_overall_results_table(fittedresults[dataset_index], Z_data, Z_fitted, dataset_index)

    def update_results_table(self, dataset_index=0):
        """
        更新结果表格，显示每个拟合参数的值、标准误差、初始值、上下边界

        参数:
            dataset_index: 要更新的数据集索引
        """
        table = self.resultsui.resultstable
        table.setRowCount(0)

        # 确保索引有效
        if dataset_index < 0 or dataset_index >= len(fittedresults):
            dataset_index = 0

        result = fittedresults[dataset_index]
        if not hasattr(result, 'params'):
            return

        for param_name, param in result.params.items():
            row_position = table.rowCount()
            table.insertRow(row_position)

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            table.setCellWidget(row_position, 0, checkbox)

            table.setItem(row_position, 1, QTableWidgetItem(param_name))

            value_text = f"{param.value:.4e}"
            table.setItem(row_position, 2, QTableWidgetItem(value_text))

            if param.stderr is not None:
                stderr_text = f"± {param.stderr:.4e}"
            else:
                stderr_text = "N/A"
            table.setItem(row_position, 3, QTableWidgetItem(stderr_text))

            init_text = f"{param.init_value:.4e}"
            table.setItem(row_position, 4, QTableWidgetItem(init_text))

            if param.min != -np.inf:
                min_text = f"{param.min:.4e}"
            else:
                min_text = "-∞"
            table.setItem(row_position, 5, QTableWidgetItem(min_text))

            if param.max != np.inf:
                max_text = f"{param.max:.4e}"
            else:
                max_text = "+∞"
            table.setItem(row_position, 6, QTableWidgetItem(max_text))

        print(f'更新结果表格: {table.rowCount()} 行')

    def update_overall_results_table(self, fit_result=None, Z_data=None, Z_fitted=None, dataset_index=0):
        """
        更新整体拟合结果表格，显示R²、RMSE等整体拟合质量指标

        参数:
            fit_result: lmfit 拟合结果对象
            Z_data: 原始阻抗数据 (复数数组)
            Z_fitted: 拟合阻抗数据 (复数数组)
            dataset_index: 数据集索引
        """
        print("\n" + "-"*40)
        print(f"[update_overall_results_table] 开始更新整体结果表格")
        print(f"[update_overall_results_table] fit_result: {type(fit_result)}")
        print(f"[update_overall_results_table] Z_data: {type(Z_data)}, 长度: {len(Z_data) if Z_data is not None else 'None'}")
        print(f"[update_overall_results_table] Z_fitted: {type(Z_fitted)}, 长度: {len(Z_fitted) if Z_fitted is not None else 'None'}")
        
        if fit_result is None:
            print("[update_overall_results_table] 错误: fit_result为None")
            return

        # 调用 resultsui 的 updateResultsTable 方法更新 resultstable
        self.resultsui.updateResultsTable(fit_result, Z_data, Z_fitted, dataset_index)
        print(f"[update_overall_results_table] 完成，结果已写入 resultstable")

    def on_dataset_selector_changed(self, index):
        """
        当用户在结果UI中选择不同数据集时调用

        参数:
            index: 选择的数据集索引
        """
        if index < 0 or index >= len(fittedresults):
            return

        # 更新参数结果表格
        self.update_results_table(index)

        # 更新整体拟合效果表格
        Z_data = None
        Z_fitted = None
        if prodata and len(prodata) > index:
            data_dict = prodata[index]
            # 检测数据类型：MT数据包含 epsRE[-]，ECM数据包含 Rs[ohm]
            if 'epsRE[-]' in data_dict.columns:
                # MT数据格式
                epsRE = data_dict['epsRE[-]'].values
                sigmaRE = data_dict['sigmaRE[S/m]'].values
                Z_data = epsRE + 1j * sigmaRE
            elif 'Rs[ohm]' in data_dict.columns:
                # ECM数据格式
                Z_data = data_dict['Rs[ohm]'].values + 1j * data_dict['X[ohm]'].values
        # 获取拟合数据 - prodata是交错排列的[原始数据, 拟合数据, 原始数据, 拟合数据, ...]
        # Z_fitted应该在prodata的奇数索引位置
        fitted_index = index * 2 + 1
        Z_fitted = None
        if prodata and len(prodata) > fitted_index:
            fitted_dict = prodata[fitted_index]
            if hasattr(fitted_dict, 'columns'):
                if 'Rs[ohm]' in fitted_dict.columns:
                    Z_fitted = fitted_dict['Rs[ohm]'].values + 1j * fitted_dict['X[ohm]'].values
                elif 'epsRE[-]' in fitted_dict.columns:
                    Z_fitted = fitted_dict['epsRE[-]'].values + 1j * fitted_dict['sigmaRE[S/m]'].values

        self.update_overall_results_table(fittedresults[index], Z_data, Z_fitted, index)


class bottomLWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(bottomLWidget, self).__init__(*args, **kwargs)
        # self.resize(200, 100)
        layout = QVBoxLayout(self)
        layout.addWidget(ProgressBar(self, minimum=0, maximum=100, objectName="RedProgressBar"))


class ProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        super(ProgressBar, self).__init__(*args, **kwargs)
        self.setValue(0)
        if self.minimum() != self.maximum():
            self.timer = QTimer(self, timeout=self.onTimeout)
            self.timer.start(randint(1, 3) * 1000)

    def onTimeout(self):
        if self.value() >= 100:
            self.timer.stop()
            self.timer.deleteLater()
            del self.timer
            return
        self.setValue(self.value() + 1)




