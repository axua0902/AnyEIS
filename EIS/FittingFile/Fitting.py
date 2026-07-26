# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 15:55:38 2020

@author: takeilab
"""

import sys

sys.path.append('..')

import numpy as np
import json
import os
from datetime import datetime

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal

from lmfit import Parameters, Parameter

from EIS.ModelFile.ECUI import Tab1Content
from EIS.ModelFile.MTMUI import Tab2Content

from EIS.FittingFile.FittingECM import FittingECM, FittingresultsprocessECM, auto_fitting
from EIS.FittingFile.FittingMT import FittingMT, Fittingresultsprocess
from EIS.ModelFile.ECMFunctions import ECMFunction
from EIS.ModelFile.MTMFunctions import MTMFunction
from widgets.py_tabwidget.py_tabwidget2 import PyTabWidget2

# from FittingFile.FittingMS import FittingMS


# from MKPUI import tab4UI
# from TLMUI import tab5UI
# from NMUI import tab6UI

global plotdata
global plotdataname
global outputlist

outputlist = list()
plotdataname = list()
plotdata = list()

global globalfileslist
global globalchosedfileslist
# 导入设置和主题
from setting import Settings  # 应用设置
from themes import Themes     # 主题颜色

class Fitting(ECMFunction, MTMFunction, PyTabWidget2):
    def __init__(self, parent=None):
        # super(Fitting, self).__init__(parent)
        settings = Settings()        # LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()        # LOAD THEME COLOR
        self.themes = themes.items

        # Initialize TabWidget with theme colors
        super(Fitting, self).__init__(
            parent=parent,
            radius=8,
            color=self.themes["app_color"]["text_foreground"],
            bg_color=self.themes["app_color"]["bg_two"], 
            selection_color=self.themes["app_color"]["bg_three"],
            bottom_line_color=self.themes["app_color"]["light_three"],
            tab_bg_color=self.themes["app_color"]["light_one"],
            tab_text_color=self.themes["app_color"]["text_foreground"],
            tab_active_color=self.themes["app_color"]["context_color"],
            tab_active_text_color=self.themes["app_color"]["text_title"],
            tab_hover_color=self.themes["app_color"]["light_three"],
            tab_hover_text_color=self.themes["app_color"]["text_title"],
            tab_hover_border_color=self.themes["app_color"]["context_hover"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight = 700,
            font_style = "normal",
            text_align = "center",
        )


        self.tab1 = Tab1Content()  # 创建3个选项卡小控件窗口
        self.addTab(self.tab1, "Equivalent circuit")  # 将三个选项卡添加到顶层窗口中
        self.tab1.ECfigureSection.setVisible(False)

        self.tab2 = Tab2Content()
        self.addTab(self.tab2, "Multi-terms model")

        # Reference controls from tab1 (ECUI)
        self.ECMlowfreqTextEdit = self.tab1.ECMlowfreqTextEdit
        self.ECMupfreqTextEdit = self.tab1.ECMupfreqTextEdit
        self.distributionComboBox = self.tab1.distributionComboBox

        # Connect button signals to methods
        # Tab1 (ECM) button connections
        self.tab1.addelementBtn.clicked.connect(self.addelement)
        self.tab1.addconnectionBtn.clicked.connect(self.addconnection)
        self.tab1.undoBtn.clicked.connect(self.undo)
        self.tab1.calculateBtn.clicked.connect(self.ECMcalculation)
        self.tab1.clearBtn.clicked.connect(self.clearCalculation)
        self.tab1.modelfigBtn.clicked.connect(self.modelfig)
        self.tab1.newBtn.clicked.connect(self.newECMModel)
        self.tab1.openModelBtn.clicked.connect(self.openECMModel)
        self.tab1.saveModelBtn.clicked.connect(self.saveECMModel)
        self.tab1.saveasModelBtn.clicked.connect(self.saveasECMModel)
        self.tab1.clearModelBtn.clicked.connect(self.clearECMModel)

        # Tab2 (MT) button connections
        self.tab2.addtermBtn.clicked.connect(self.addterm)
        self.tab2.deletetermBtn.clicked.connect(self.deleteterm)
        self.tab2.MTcalculateBtn.clicked.connect(self.MTcalculation)
        self.tab2.EPcheckBox.stateChanged.connect(self.EPconfirm)
        self.tab2.DCcheckBox.stateChanged.connect(self.DCconfirm)
        self.tab2.newBtn.clicked.connect(self.newMTModel)
        self.tab2.inputdataBtn.clicked.connect(self.openMTModel)
        self.tab2.openexfilebtn.clicked.connect(self.saveMTModel)
        self.tab2.saveasBtn.clicked.connect(self.saveasMTModel)
        self.tab2.clearModelBtn.clicked.connect(self.clearMTModel)

        self.params = Parameters()
        self.circuit = list()

        self.termnamelist = list()
        self.MTexpre = list()
        self.MTexpretype = list()
        self.MTparams = Parameters()
        self.modelterm = list()  ######模型类型列表

        self.MSparams = Parameters()  ######Multi-Shell模型参数

        self.fitteddata = list()  ######拟合后数据列表
        self.fittedresults = list()  ######拟合后结果列表

        self.option = {'EP': 0, 'DC Conductivity': 0}
        self.setting_widget = None

        # Model file tracking variables
        # Tab1 (ECM) model files
        self.modelfilesnamelist = []
        self.modelitemsnamelist = []
        self.current_model_path = None

        # Tab2 (MT) model files
        self.mt_modelfilesnamelist = []
        self.mt_modelitemsnamelist = []
        self.current_mt_model_path = None

        # Tab3 (MS) model files
        self.ms_modelfilesnamelist = []
        self.ms_modelitemsnamelist = []
        self.current_ms_model_path = None

    def set_setting_widget(self, widget):
        self.setting_widget = widget
        if widget is not None:
            widget.Settingsignal.connect(self.get_settings_signal)

    def get_settings_signal(self, outputlist, prodataname, resultsdata):
        print('收到设置信号:', outputlist, prodataname, resultsdata)

    Fittingdatasignal = Signal(list, list, list, list)

    def getsignal(self, message1, inputdataname, inputdata):
        global outputlist
        print('接收outputlist process')
        outputlist = message1

        global prodataname
        print('接收plotdataname process')
        prodataname = inputdataname

        global prodata
        print('接收plotdata process')
        prodata = inputdata

    def sendsignal(self, outputlist, prodataname, resultsdata, fittedresults):
        print("\n" + "-"*40)
        print("[sendsignal] 开始发送数据")
        print(f"[sendsignal] outputlist: {outputlist}")
        print(f"[sendsignal] prodataname: {prodataname}")
        print(f"[sendsignal] resultsdata长度: {len(resultsdata) if resultsdata else 0}")
        print(f"[sendsignal] fittedresults长度: {len(fittedresults) if fittedresults else 0}")
        if resultsdata:
            for i, d in enumerate(resultsdata):
                print(f"[sendsignal]   resultsdata[{i}]类型: {type(d)}, 长度: {len(d) if hasattr(d, '__len__') else 'N/A'}")
        
        outputdataname = prodataname
        outputdata = resultsdata
        self.Fittingdatasignal.emit(outputlist, outputdataname, outputdata, fittedresults)
        print("[sendsignal] Fittingdatasignal已发送")

    def ECMcalculation(self):  ###整理仿真参数，调用函数计算
        global plotdata
        global outputlist
        global plotdataname

        print("\n" + "="*60)
        print("[ECMcalculation] 开始拟合计算")
        print("="*60)
        
        # 重置全局变量
        outputlist = []
        plotdataname = []
        
        ECMoutputdata = list()
        fittinglist = list()
        self.fitteddata = list()  ######拟合后数据列表
        self.fittedresults = list()  ######拟合后结果列表
        
        ###############生成频率序列###############
        if self.ECMlowfreqTextEdit.text() != '' and self.ECMupfreqTextEdit.text() != '':
            ECMlowfreq = np.log10(float(self.ECMlowfreqTextEdit.text()))
            ECMupfreq = np.log10(float(self.ECMupfreqTextEdit.text()))
        else:
            self.ECMlowfreqTextEdit.setText('1e1')
            self.ECMupfreqTextEdit.setText('1e9')
            ECMlowfreq = np.log10(1e1)
            ECMupfreq = np.log10(1e9)

        if 'Log' == self.distributionComboBox.currentText():
            ECMfreq = np.logspace(ECMlowfreq, ECMupfreq, num=100)
        else:
            ECMfreq = np.linspace(ECMlowfreq, ECMupfreq, num=100)
        print(f"[ECMcalculation] 频率范围: {ECMlowfreq:.2f} - {ECMupfreq:.2f} (log10), 点数: {len(ECMfreq)}")
        ##############生成频率序列###############
        
        ############### 读取表格数据 生成参数    ################
        self.ECMparams = Parameters()
        row = self.tab1.ECMtable.rowCount()  # 获取当前的行数
        print(f"[ECMcalculation] ECMtable行数: {row}")
        print(f"[ECMcalculation] 电路配置: {self.circuit}")
        
        for temp in range(1, row + 1):
            elementname1 = self.tab1.ECMtable.item(temp - 1, 0).text()
            init_val = float(self.tab1.ECMtable.item(temp - 1, 2).text())
            self.ECMparams[elementname1] = Parameter(elementname1, value=init_val)
            print(f"[ECMcalculation]   参数: {elementname1} = {init_val}")
        ############### 读取表格数据 生成参数    ################
        
        print(f"[ECMcalculation] prodata数据集数量: {len(prodata)}")

        # 读取拟合设置
        fit_method = 'least_squares'
        fit_kwargs = {}
        if self.setting_widget is not None:
            try:
                settings = self.setting_widget.get_settings()
                fit_method = settings.get('method', 'least_squares')
                for k, v in settings.items():
                    if k != 'method':
                        fit_kwargs[k] = float(v) if v else 1e-5
                print(f'[ECMcalculation] Fitting settings: method={fit_method}, params={fit_kwargs}')
            except Exception as e:
                print(f'[ECMcalculation] 读取设置失败，使用默认设置: {e}')

        for i in range(0, len(prodata)):  # 第i组拟合数据
            print(f"\n[ECMcalculation] 处理数据集{i}")
            ###############生成频率序列###############
            ECMfreq = prodata[i]['FREQ[Hz]']  ##读取数据频率
            self.ECMlowfreqTextEdit.setText(str(ECMfreq.iloc[0]))
            self.ECMupfreqTextEdit.setText(str(ECMfreq.iloc[-1]))
            print(f"[ECMcalculation]   数据频率范围: {ECMfreq.iloc[0]:.2e} - {ECMfreq.iloc[-1]:.2e} Hz, 点数: {len(ECMfreq)}")
            ##############生成频率序列###############

            ################拟合计算###############
            if len(ECMfreq) != 0 and len(self.ECMparams) != 0:
                print(f"[ECMcalculation]   开始调用auto_fitting...")
                
                results = auto_fitting(self.ECMparams, ECMfreq, self.circuit, prodata[i], method=fit_method, **fit_kwargs)  #########智能拟合
                self.fittedresults.append(results)  ######拟合后结果列表
                
                print(f"[ECMcalculation]   拟合结果message: {results.message}")
                print(f"[ECMcalculation]   拟合参数数量: {len(results.var_names)}")
                print(f"[ECMcalculation]   拟合参数列表: {list(results.var_names)}")
                print(f"[ECMcalculation]   拟合结果x: {results.x}")
                
                fitteddata = FittingresultsprocessECM(self.ECMparams, ECMfreq, self.circuit, results)
                print(f"[ECMcalculation]   fitteddata类型: {type(fitteddata)}, 长度: {len(fitteddata) if hasattr(fitteddata, '__len__') else 'N/A'}")

                self.fitteddata.append(fitteddata)  ######拟合后数据列表
                # outputlist: 原始数据和拟合数据都需要绘制，所以添加[1, 1]
                fittinglist.append(1)  # 原始数据标记
                fittinglist.append(1)  # 拟合数据标记
                plotdataname.append('Origin' + str(i))
                plotdataname.append('ECMFitting' + str(i))

                ECMoutputdata.append(prodata[i])
                ECMoutputdata.append(fitteddata)

                print(f"[ECMcalculation]   fittinglist: {fittinglist}")
                print(f"[ECMcalculation]   plotdataname: {plotdataname}")
                print(f"[ECMcalculation]   ECMoutputdata长度: {len(ECMoutputdata)}")
            else:
                print(f"[ECMcalculation]   错误: len(ECMfreq)={len(ECMfreq)}, len(self.ECMparams)={len(self.ECMparams)}")
                return

        print(f"\n[ECMcalculation] 最终fittinglist: {fittinglist}")
        outputlist = outputlist + fittinglist
        print(f"[ECMcalculation] 最终outputlist: {outputlist}")
        print(f"[ECMcalculation] 最终plotdataname: {plotdataname}")

        print(f"[ECMcalculation] 调用processECMResults...")
        self.processECMResults()
        
        print(f"[ECMcalculation] 调用sendsignal发送数据...")
        self.sendsignal(outputlist, plotdataname, ECMoutputdata, self.fittedresults)
        print(f"[ECMcalculation] 完成")

    def clearCalculation(self):
        return

    def modelfig(self):
        self.modelfigureLablel = QLabel()
        self.modelfigureLablel.setPixmap(QPixmap("./circuit.png"))
        self.figurelayout.addWidget(self.modelfigureLablel)
    
    
    
    def MTcalculation(self):  ###整理拟合参数，调用函数计算
        global plotdata
        global outputlist
        global plotdataname

        outputdata = list()
        fittinglist = list()
        self.fitteddata = list()  ######拟合后数据列表
        self.fittedresults = list()  ######拟合后结果列表

        ############## 读取表格数据 生成参数################
        currentRow = self.tab2.MTtable.rowCount()  # 获取当前的行数
        self.MTparams = Parameters()  # 更新参数列表
        for temp in range(1, currentRow + 1):
            paraname = self.tab2.MTtable.item(temp - 1, 0).text()
            init_val = float(self.tab2.MTtable.item(temp - 1, 2).text())
            max_val = float(self.tab2.MTtable.item(temp - 1, 4).text())
            min_val = float(self.tab2.MTtable.item(temp - 1, 5).text())
            self.MTparams[paraname] = Parameter(paraname, value=init_val, max=max_val, min=min_val)
        ############# 读取表格数据 生成参数################

        # 读取拟合设置
        fit_method = 'least_squares'
        fit_kwargs = {}
        if self.setting_widget is not None:
            try:
                settings = self.setting_widget.get_settings()
                fit_method = settings.get('method', 'least_squares')
                for k, v in settings.items():
                    if k != 'method':
                        fit_kwargs[k] = float(v) if v else 1e-5
                print(f'[MTcalculation] Fitting settings: method={fit_method}, params={fit_kwargs}')
            except Exception as e:
                print(f'[MTcalculation] 读取设置失败，使用默认设置: {e}')

        for i in range(0, len(prodata)):  # 第i组拟合数据
            ###############生成频率序列###############
            MTfreq = prodata[i]['FREQ[Hz]']  ##读取数据频率
            self.tab2.MTlowfreqTextEdit.setText(str(MTfreq[0]))
            self.tab2.MTupfreqTextEdit.setText(str(MTfreq[len(MTfreq) - 1]))
            ##############生成频率序列###############

            ################拟合计算###############
            if len(MTfreq) != 0 and len(self.MTparams) != 0 and len(self.modelterm) != 0:
                # print(prodata)
                results = FittingMT(self.MTparams, MTfreq, self.modelterm, prodata[i], self.option, method=fit_method, **fit_kwargs)
                self.fittedresults.append(results)  ######拟合后结果列表
                # print(results)
                print(results.message)
                fitteddata = Fittingresultsprocess(self.MTparams, MTfreq, self.modelterm, results, self.option)
                self.fitteddata.append(fitteddata)  ######拟合后数据列表
                # outputlist: 原始数据和拟合数据都需要绘制，所以添加[1, 1]
                fittinglist.append(1)  # 原始数据标记
                fittinglist.append(1)  # 拟合数据标记
                # outputlist=[1]
                plotdataname.append('Origin' + str(i))
                plotdataname.append('MTFitting' + str(i))

                outputdata.append(prodata[i])
                outputdata.append(fitteddata)

                print(outputlist)
                print(plotdataname)
                # print(self.fitteddata)
                # print(self.fittedresults)
                print(len(outputdata))
            else:
                print('wrong')
                return

        print(fittinglist)
        outputlist = outputlist + fittinglist
        print(outputlist)
        ########################拟合计算###############
        self.processMTResults()
        self.sendsignal(outputlist, plotdataname, outputdata, self.fittedresults)

    def processECMResults(self, dataset_index=None):
        """
        处理ECM拟合结果并写入ECMtable

        参数:
            dataset_index: 要处理的数据集索引，None表示处理所有数据集
        """
        print("\n" + "-"*40)
        print("[processECMResults] 开始处理ECM拟合结果")
        print(f"[processECMResults] self.fittedresults长度: {len(self.fittedresults) if self.fittedresults else 0}")
        
        if not self.fittedresults:
            print("[processECMResults] 警告: self.fittedresults为空!")
            return

        # 如果没有指定索引，设置当前索引
        if dataset_index is None:
            dataset_index = getattr(self, 'current_fitting_dataset', 0)
        else:
            self.current_fitting_dataset = dataset_index

        # 确保索引在有效范围内
        if dataset_index >= len(self.fittedresults):
            dataset_index = 0
            self.current_fitting_dataset = 0

        print(f"[processECMResults] 使用dataset_index: {dataset_index}")
        
        fit_result = self.fittedresults[dataset_index]
        print(f"[processECMResults] fit_result类型: {type(fit_result)}")
        print(f"[processECMResults] fit_result.var_names: {list(fit_result.var_names)}")
        print(f"[processECMResults] fit_result.x: {fit_result.x}")

        # 设置表头为拟合模型
        self.tab1.setECMTableHeader('fit')
        print("[processECMResults] 表头已设置为fit模式")
        print(f"[processECMResults] ECMtable行数: {self.tab1.ECMtable.rowCount()}, 列数: {self.tab1.ECMtable.columnCount()}")

        # 写入初始值和拟合结果
        for i in range(len(fit_result.var_names)):
            paramsname = fit_result.var_names[i]
            fitted_val = fit_result.x[i]
            print(f"[processECMResults] 处理参数: {paramsname} = {fitted_val}")

            # 获取初始值（从ECMtable 的第2列读取）
            init_val = None
            found_row = -1
            for row in range(self.tab1.ECMtable.rowCount()):
                if self.tab1.ECMtable.item(row, 0).text() == paramsname:
                    found_row = row
                    try:
                        init_val = float(self.tab1.ECMtable.item(row, 2).text())
                    except:
                        init_val = fitted_val
                    break
            
            print(f"[processECMResults]   在表格第{found_row}行找到参数: init_val={init_val}")

            # 写入初始值到表格(Initial_Value)
            if init_val is not None:
                self.ECMtableWrite(paramsname, init_val, 2)
                print(f"[processECMResults]   已写入初始值到表格")

            # 写入拟合值到表格(Fitted_Value)
            self.ECMtableWrite(paramsname, fitted_val, 3)
            print(f"[processECMResults]   已写入拟合值到表格")

            # 获取stderr并计算误差百分比
            param = fit_result.params[paramsname]
            stderr = param.stderr
            if stderr is None:
                errbartemp = float('nan')
                print(f"[processECMResults]   stderr=None, 误差设置为nan")
            else:
                errbartemp = 100 * round(stderr / param.value, 4)
                print(f"[processECMResults]   stderr={stderr}, 误差={errbartemp}%")

            # 写入误差到第7列(Error [%])
            self.ECMtableWrite(paramsname, errbartemp, 7)
            print(f"[processECMResults]   已写入误差到表格")

        # 注意：整体拟合效果表格由 FittingSetRes.py 的getsingal 信号处理

    def processMTResults(self, dataset_index=None):
        """
        处理MT拟合结果并写入MTtable

        参数:
            dataset_index: 要处理的数据集索引，None表示处理所有数据集
        """
        if not self.fittedresults:
            return

        # 如果没有指定索引，设置当前索引
        if dataset_index is None:
            dataset_index = getattr(self, 'current_fitting_dataset', 0)
        else:
            self.current_fitting_dataset = dataset_index

        # 确保索引在有效范围内
        if dataset_index >= len(self.fittedresults):
            dataset_index = 0
            self.current_fitting_dataset = 0

        fit_result = self.fittedresults[dataset_index]

        # 写入初始值和拟合结果到MTtable
        for i in range(len(fit_result.var_names)):
            paramsname = fit_result.var_names[i]
            fitted_val = fit_result.x[i]

            # 获取初始值（从MTtable 的第2列读取）
            init_val = None
            for row in range(self.tab2.MTtable.rowCount()):
                if self.tab2.MTtable.item(row, 0).text() == paramsname:
                    try:
                        init_val = float(self.tab2.MTtable.item(row, 2).text())
                    except:
                        init_val = fitted_val
                    break

            # 写入初始值到表格(Initial_Value)
            if init_val is not None:
                self.MTtableWrite(paramsname, init_val, 2)

            # 写入拟合值到表格(Fitted_Value)
            self.MTtableWrite(paramsname, fitted_val, 3)

            # 获取stderr并计算误差百分比
            param = fit_result.params[paramsname]
            stderr = param.stderr
            if stderr is None:
                errbartemp = float('nan')
            else:
                errbartemp = 100 * round(stderr / param.value, 4)

            # 写入误差到第7列(Error [%])
            self.MTtableWrite(paramsname, errbartemp, 7)

    def MTtableWrite(self, name, value, col):
        """
        向MTtable写入数据:

        参数:
            name: 参数名
            value: 要写入的值
            col: 列索引
        """
        for row in range(self.tab2.MTtable.rowCount()):
            if self.tab2.MTtable.item(row, 0).text() == name:
                item = QTableWidgetItem(str(value))
                self.tab2.MTtable.setItem(row, col, item)
                break

    def ECMtableWrite(self, name, value, col):
        """
        向ECMtable写入数据:

        参数:
            name: 参数名
            value: 要写入的值
            col: 列索引
        """
        for row in range(self.tab1.ECMtable.rowCount()):
            if self.tab1.ECMtable.item(row, 0).text() == name:
                item = QTableWidgetItem(str(value))
                self.tab1.ECMtable.setItem(row, col, item)
                break

    def showequation(self):  ####选择方程类型并展示方程
        # print(MTfreq)##频率
        # print(self.MTparams)####参数

        # print(self.modelterm)####公式类型
        # print(self.termnamelist)
        pass

    #######tab2!################################################################################################tab2!#####################################################################################################################




