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
# from widgets.py_tabwidget.py_tabwidget import PyTabWidget
from widgets.py_tabwidget.py_tabwidget2 import PyTabWidget2

from EIS.ModelFile.ECUI import Tab1Content
from EIS.ModelFile.MTMUI import Tab2Content

from EIS.SimulationFile.simulateECM import simuECM,circuitfig,creatdatabaseECM
from EIS.SimulationFile.simulateMT import simulateModel
from EIS.ModelFile.ECMFunctions import ECMFunction
from EIS.ModelFile.MTMFunctions import MTMFunction
from EIS.Other.Datacheck import ensure_paired_form



# 导入设置和主题
from setting import Settings  # 应用设置
from themes import Themes     # 主题颜色

class Simu(ECMFunction, MTMFunction, PyTabWidget2):
    datasignal =Signal(list ,list ,list ,list)

    def __init__(self ,parent=None):
        # Load settings and themes first
        settings = Settings()        # LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()        # LOAD THEME COLOR
        self.themes = themes.items
        
        # Initialize TabWidget with theme colors
        super(Simu, self).__init__(
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


        self.tab1=Tab1Content()# 创建3个选项卡小控件窗口
        self.addTab(self.tab1, "Equivalent circuit") # 将三个选项卡添加到顶层窗口中
        self.tab2 =Tab2Content()
        self.addTab(self.tab2, "Multi-terms model")

        # Removed redundant control references - using direct tab access instead

        # Connect button signals to methods
        # Tab1 (ECM) button connections

        self.tab1.addelementBtn.clicked.connect(self.addelement)
        self.tab1.addconnectionBtn.clicked.connect(self.addconnection)
        self.tab1.undoBtn.clicked.connect(self.undo)
        self.tab1.calculateBtn.clicked.connect(self.ECMcalculation)
        self.tab1.clearBtn.clicked.connect(self.clearECCalculation)
        self.tab1.modelfigBtn.clicked.connect(self.ECModelFig)

        # Tab1 (ECM) file operation button connections
        self.tab1.newBtn.clicked.connect(self.newECMModel)
        self.tab1.openModelBtn.clicked.connect(self.openECMModel)
        self.tab1.saveModelBtn.clicked.connect(self.saveECMModel)
        self.tab1.saveasModelBtn.clicked.connect(self.saveasECMModel)
        self.tab1.clearModelBtn.clicked.connect(self.clearECMModel)

        # Tab2 (MT) button connections
        self.tab2.addtermBtn.clicked.connect(self.addterm)
        self.tab2.deletetermBtn.clicked.connect(self.deleteterm)
        self.tab2.MTcalculateBtn.clicked.connect(self.MTcalculation)
        self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)
        self.tab2.EPcheckBox.stateChanged.connect(self.EPconfirm)
        self.tab2.DCcheckBox.stateChanged.connect(self.DCconfirm)
        self.tab2.clearModelBtn.clicked.connect(self.clearMTModel)
        self.tab2.inputdataBtn.clicked.connect(self.openMTModel)
        self.tab2.openexfilebtn.clicked.connect(self.saveMTModel)
        self.tab2.saveasBtn.clicked.connect(self.saveasMTModel)
        self.tab2.newBtn.clicked.connect(self.newMTModel)

        self.params = Parameters()
        self.circuit =list()
        self.ECMfreq = np.array([])

        self.termnamelist =list()
        self.modelterm =list()

        self.MTexpre =list()

        self.MTparams = Parameters()
        self.option ={'EP' :0 ,'DC Conductivity' :0}
        
        # 模型文件相关变量
        self.modelfilesnamelist = []  # 存储模型文件路径列表
        self.modelitemsnamelist = []  # 存储带序号的模型文件名列表
        self.current_model_path = None  # 当前模型文件路径

        # MT模型文件相关变量
        self.mt_modelfilesnamelist = []  # 存储MT模型文件路径列表
        self.mt_modelitemsnamelist = []  # 存储带序号的MT模型文件名列表
        self.current_mt_model_path = None  # 当前MT模型文件路径

        # MS模型文件相关变量
        self.ms_modelfilesnamelist = []  # 存储MS模型文件路径列表
        self.ms_modelitemsnamelist = []  # 存储带序号的MS模型文件名列表
        self.current_ms_model_path = None  # 当前MS模型文件路径

        # 重置 Simulation 表格表头（使用ECUI提供的统一方法）
        self.tab1.setECMTableHeader('simu')
        self.tab2.MTtable.setColumnCount(6)
        self.tab2.MTtable.setHorizontalHeaderLabels(['Name', 'Comments', 'Initial_Value', 'Max', 'Min', 'Fixed'])


    def sendsignal(self ,outputlist ,plotdataname ,plotdata ,message4):

        outputdataname =plotdataname
        outputdata =plotdata
        outputlist =outputlist
        dataInfo = message4

        # 将单条数据成对化,让下游 selectsavedata 的 i%2 逻辑可工作
        # 注意:utility 返回新列表,需要把别名也同步更新,否则 emit 的还是旧数据
        outputlist, outputdataname, outputdata, dataInfo = ensure_paired_form(
            outputlist,
            outputdataname,
            outputdata,
            dataInfo,
        )

        self.datasignal.emit(outputlist ,outputdataname ,outputdata ,dataInfo)####发送数据
        # print('Simulation Data emitted'  )###输出到状态栏
        print('Simulation emit data',outputlist, outputdataname, len(outputdata), dataInfo)
        # print(outputselectlist, outputdataname, len(outputdata))
        # print(self.outputdata)

    def ECMcalculation(self):  ###整理仿真参数，调用函数计算
        global plotdata
        ###############生成频率序列###############
        if self.tab1.ECMlowfreqTextEdit.text() != '' and self.tab1.ECMupfreqTextEdit.text() != '':
            ECMlowfreq = np.log10(float(self.tab1.ECMlowfreqTextEdit.text()))
            ECMupfreq = np.log10(float(self.tab1.ECMupfreqTextEdit.text()))
        else:
            self.tab1.ECMlowfreqTextEdit.setText('1e1')
            self.tab1.ECMupfreqTextEdit.setText('1e9')
            ECMlowfreq = np.log10(1e3)
            ECMupfreq = np.log10(1e8)

        if 'Log' == self.tab1.distributionComboBox.currentText():
            self.ECMfreq = np.logspace(ECMlowfreq, ECMupfreq, num=100)
        else:
            self.ECMfreq = np.linspace(ECMlowfreq, ECMupfreq, num=100)
        ##############生成频率序列###############
        ############### 读取表格数据 生成参数    ################
        self.params = Parameters()
        row = self.tab1.ECMtable.rowCount()  # 获取当前的行数
        for temp in range(1, row + 1):
            elementname1 = self.tab1.ECMtable.item(temp - 1, 0).text()
            # print(elementname1)
            init_val = float(self.tab1.ECMtable.item(temp - 1, 2).text())
            # print(init_val)
            self.params[elementname1] = Parameter(elementname1, value=init_val)
        ############### 读取表格数据 生成参数    ################

        # print(self.circuit)###电路
        # print(freq)##频率
        # print(self.params)####参数

        Z, Zparallel = simuECM(self.params, self.circuit, self.ECMfreq)  #########仿真函数

        plotdata = creatdatabaseECM(self.ECMfreq, Z)
        # outputECM(self.circuit)
        # print(plotdata)
        plotdataname = ['ECMSimulation']
        outputlist = [1]

        ###############仿真计算###############
        message4 = list()  ###空数据占位
        self.sendsignal(outputlist, plotdataname, plotdata, message4)



    def clearECCalculation(self):
        """
        清空 ECM 最近一次 Calculate 投递给 Figure 的仿真数据（计算行 Clear 按钮槽）。
        保留模型结构（circuit、params、connectionTextEdit、ECMtable 全部 6 列均为用户输入）。

        说明:Simulation 路径下 ECMtable 由 setECMTableHeader('simu') 初始化为 6 列
        (Name/Comments/Initial_Value/Max/Min/Fixed),无 Fitted_Value / Error [%] 等
        计算结果列,故本方法只需清空全局 plot 副本,不动表格。
        """
        # 清空全局 plot 副本（仅清仿真期追加的部分；原始数据由导入流程维护）
        try:
            global plotdata, plotdataname, outputlist
            plotdata = list()
            plotdataname = list()
            outputlist = list()
        except Exception:
            pass

        # ECMtable 在 simu 模式无计算结果列,无需清空
        print('[clearECCalculation] ECM simulation output cleared (model preserved)')

    def ECModelFig(self):
        # Generate circuit figure
        circuitfig(self.circuit)
        
        # Clear previous figure if exists
        if hasattr(self, 'modelfigureLablel'):
            self.tab1.ECfigureDisplayAreaLayout.removeWidget(self.modelfigureLablel)
            self.modelfigureLablel.deleteLater()
        
        # Load pixmap first
        pixmap = QPixmap("CircuitFigure/simulated_circuit.png")
        if not pixmap.isNull():
            # Create and configure label
            self.modelfigureLablel = QLabel()
            self.modelfigureLablel.setFixedSize(self.tab1.ECfigureDisplayArea.width() - 10, 150)
            
            # Scale pixmap with aspect ratio preservation
            scaled_pixmap = pixmap.scaled(
                self.modelfigureLablel.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.modelfigureLablel.setPixmap(scaled_pixmap)
            self.modelfigureLablel.setAlignment(Qt.AlignCenter)
            
            # Add to correct layout
            self.tab1.ECfigureDisplayAreaLayout.addWidget(self.modelfigureLablel)
            print("Circuit figure displayed successfully")
        else:
            print("Failed to load circuit figure")


    def ClearCircuitFig(self):
        """
        清除电路图显示，但不删除图片文件
        只是从界面上移除图片显示
        """
        # Check if the figure label exists and remove it from display
        if hasattr(self, 'modelfigureLablel'):
            try:
                # Remove the widget from the layout
                self.tab1.ECfigureDisplayAreaLayout.removeWidget(self.modelfigureLablel)
                # Delete the widget to free memory
                self.modelfigureLablel.deleteLater()
                # Remove the attribute reference
                delattr(self, 'modelfigureLablel')
                print("Circuit figure display cleared")
            except Exception as e:
                print(f"Error clearing circuit figure display: {str(e)}")
        else:
            print("No circuit figure to clear")


    #######################################################################################################tab1!#####################################################################################################################












    def MTcalculation(self):  ###整理仿真参数，调用函数计算
        global plotdata
        global outputlist
        global plotdataname

        ###############生成频率序列###############
        if self.tab2.MTlowfreqTextEdit.text() != '' and self.tab2.MTupfreqTextEdit.text() != '':
            MTlowfreq = np.log10(float(self.tab2.MTlowfreqTextEdit.text()))
            MTupfreq = np.log10(float(self.tab2.MTupfreqTextEdit.text()))
        else:
            MTlowfreq = np.log10(1e1)
            MTupfreq = np.log10(1e9)

        if 'Log' == self.tab2.MTdistributionComboBox.currentText():
            MTfreq = np.logspace(MTlowfreq, MTupfreq, num=100)
        else:
            MTfreq = np.linspace(MTlowfreq, MTupfreq, num=100)
        ##############生成频率序列###############

        ############### 读取表格数据 生成参数    ################
        currentRow = self.tab2.MTtable.rowCount()  # 获取当前的行数
        self.MTparams = Parameters()  # 更新参数库
        for temp in range(1, currentRow + 1):
            paraname = self.tab2.MTtable.item(temp - 1, 0).text()
            init_val = float(self.tab2.MTtable.item(temp - 1, 2).text())
            self.MTparams[paraname] = Parameter(paraname, value=init_val)
        # print(self.MTparams)
        ############### 读取表格数据 生成参数    ################

        ###############仿真计算###############
        if len(MTfreq) != 0 and len(self.MTparams) != 0 and len(self.modelterm) != 0:
            plotdata = simulateModel(self.MTparams, MTfreq, self.modelterm, self.option)
            plotdataname = ['MTSimulation']
            outputlist = [1]
        else:
            print('wrong Parameters')
            return
        ###############仿真计算###############
        message4 = list()  ###空数据占位
        self.sendsignal(outputlist, plotdataname, plotdata, message4)



    def clearMTCalculation(self):
        """
        清空 MT 最近一次 Calculate 投递给 Figure 的仿真数据（计算行 Clear 按钮槽）。
        保留模型结构（modelterm、termnamelist、MTexpre、MTparams、option、MTmultitermTextEdit、
        MTtable 全部 6 列均为用户输入、EP/DC 勾选）。

        说明:Simulation 路径下 MTtable 由 setColumnCount(6) 初始化为 6 列
        (Name/Comments/Initial_Value/Max/Min/Fixed),无 Fitted_Value / Error [%] 等
        计算结果列,故本方法只需清空全局 plot 副本,不动表格。
        """
        # 清空全局 plot 副本
        try:
            global plotdata, plotdataname, outputlist
            plotdata = list()
            plotdataname = list()
            outputlist = list()
        except Exception:
            pass

        # MTtable 在 simu 模式无计算结果列,无需清空
        print('[clearMTCalculation] MT simulation output cleared (model preserved)')




    def showequation(self):  ####选择方程类型后 展示方程
        pass













    #######tab2!################################################################################################tab2!#####################################################################################################################


























