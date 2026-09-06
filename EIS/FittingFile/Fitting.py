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


# ---------------------------------------------------------------------------
# 设置字段类型转换工具
# ---------------------------------------------------------------------------
# UI 文本框统一返回字符串，但 scipy/lmfit 不同 kwarg 期望 int/float/str/bool。
# 例如 `maxiter` 应为 int，`no_local_search` 应为 bool，`strategy` 保留 str。
# 注意 `norm` 是 scipy 的范数阶数（int/float），不是字符串！
_INT_KEYS = {'maxiter', 'maxfun', 'maxfev', 'popsize', 'niter', 'totaliter',
             'interval', 'niter_success', 'maxls', 'seed', 'tabulistsize',
             'maxfunevals'}
_BOOL_KEYS = {'no_local_search', 'polish', 'adaptive', 'updating',
              'workers', 'no_local_search'}
_STR_KEYS = {'strategy', 'visit', 'accept', 'tabustrategy', 'init'}
# 这些字段若 UI 没填，应丢弃（不能让 None/默认 1e-5 误传到 scipy）
_NULLABLE_KEYS = {'seed', 'workers', 'init', 'polish'}

# differential_evolution 合法 strategy（scipy.optimize.differential_evolution 校验）
_DE_STRATEGIES = {
    'best1bin', 'best1exp', 'rand1bin', 'rand1exp',
    'best2bin', 'best2exp', 'rand2bin', 'rand2exp',
    'randtobest1bin', 'randtobest1exp',
    'currenttobest1bin', 'currenttobest1exp',
}


def _cast_setting(name, val):
    """
    根据字段名将 UI 文本框的字符串转换为合适类型。
    转换失败时回退到原值。
    """
    if val is None or (isinstance(val, str) and val.strip() == ''):
        # 留空：可空字段返回 None，否则用数值兜底
        if name in _NULLABLE_KEYS:
            return None
        return 1e-5
    try:
        if name in _INT_KEYS:
            ival = int(float(val))
            # maxls 必须为正（scipy 强制 > 0），非法值兜底为 20
            if name == 'maxls' and ival <= 0:
                return 20
            return ival
        if name in _BOOL_KEYS:
            if isinstance(val, bool):
                return val
            return str(val).strip().lower() in ('1', 'true', 'yes', 'y')
        if name in _STR_KEYS:
            sval = str(val)
            # strategy 必须是 scipy 认可的 DE 策略名，否则兜底为 best1bin
            if name == 'strategy' and sval not in _DE_STRATEGIES:
                return 'best1bin'
            return sval
        return float(val)
    except Exception:
        return val


class Fitting(ECMFunction, MTMFunction, PyTabWidget2):
    # 处理后数据名称后缀(链式处理时会追加,例如 Processing 后再 Fitting 会得到 _Processed_Fitted)
    _processed_suffix = '_Fitted'

    def __init__(self, parent=None):
        # super(Fitting, self).__init__(parent)
        settings = Settings()        # LOAD SETTINGS
        self.settings = settings.items
        themes = Themes()        # LOAD THEME COLOR
        self.themes = themes.items

        # 兜底:如果 _processed_suffix 未生效,在这里再次设置
        if not hasattr(self.__class__, '_processed_suffix') or not self.__class__._processed_suffix:
            self.__class__._processed_suffix = '_Fitted'

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
        self.tab1.clearBtn.clicked.connect(self.clearECCalculation)
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
        self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)
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

        # 配对数据支持(与 Filter/Processing 一致的协议)
        self.dataInfo = []                  # 输入数据信息(从上游接收)
        self.original_prodata = []          # 原始 N 条数据(不含合成副本)
        self.original_prodataname = []      # 原始 N 条名称
        self.original_selectlist = []       # 原始 N 条选择列表
        self.original_dataInfo = []         # 原始 N 条信息
        self.resultsdataInfo = []           # 输出数据信息(2N,与 resultsdata 对齐)

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

    def getsignal(self, message1, inputdataname, inputdata, inputmessage):
        """
        接收输入数据信号(4 参数,与上游 datasignal 对齐)
        - message1: 选择列表
        - inputdataname: 数据名
        - inputdata: 数据
        - inputmessage: dataInfo 列表(用于 synthetic 标签识别)
        """
        global outputlist
        print('接收outputlist process', len(message1) if message1 else 0)
        outputlist = message1

        global prodataname
        print('接收plotdataname process', len(inputdataname) if inputdataname else 0, inputdataname[:3] if inputdataname else '[]')
        prodataname = inputdataname

        global prodata
        print('接收plotdata process', len(inputdata) if inputdata else 0)
        prodata = inputdata

        self.dataInfo = list(inputmessage) if inputmessage else []
        print(f'[getsignal] 收到 dataInfo 长度: {len(self.dataInfo)}, 内容: {self.dataInfo}')
        self._extract_original_data()
        print(f'[getsignal] original_prodata 长度: {len(self.original_prodata)}, prodataname: {self.original_prodataname}')

    def _extract_original_data(self):
        """
        从全局 prodata 中提取原始 N 条数据(不含合成副本)。
        自适应:配对格式(2N + 奇数位带 synthetic 标签)取偶数索引,否则全部。
        """
        n_pro = len(prodata)
        print(f'[_extract_original_data] prodata 长度: {n_pro}, dataInfo 长度: {len(self.dataInfo)}')

        is_paired = (
            n_pro > 0
            and n_pro % 2 == 0
            and self.dataInfo
            and len(self.dataInfo) == n_pro
            and any(isinstance(info, dict) and info.get('synthetic', False)
                    for info in self.dataInfo[1::2])
        )
        print(f'[_extract_original_data] is_paired: {is_paired}')

        if is_paired:
            self.original_prodata = [prodata[i] for i in range(0, n_pro, 2)]
            self.original_prodataname = [prodataname[i] for i in range(0, n_pro, 2)]
            self.original_selectlist = list(outputlist[i] for i in range(0, n_pro, 2)) if outputlist else [1] * (n_pro // 2)
            self.original_dataInfo = [self.dataInfo[i] for i in range(0, n_pro, 2)]
        else:
            # 非配对格式:全部当作原始(防止上游未走新协议时漏数据)
            self.original_prodata = list(prodata)
            self.original_prodataname = list(prodataname)
            self.original_selectlist = list(outputlist) if outputlist else [1] * n_pro
            self.original_dataInfo = list(self.dataInfo) if self.dataInfo else [{}] * n_pro

        print(f'[_extract_original_data] 提取后 N={len(self.original_prodata)}, names={self.original_prodataname}')

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

        # 使用 original_prodata(N 条,不含合成副本)进行拟合
        if not self.original_prodata:
            print("[ECMcalculation] 错误: 没有可拟合的原始数据")
            return

        fit_data = self.original_prodata
        fit_names = self.original_prodataname
        n = len(fit_data)
        print(f"[ECMcalculation] 使用 N={n} 条原始数据进行拟合(已去除合成副本)")

        ECMoutputdata = list()
        fittinglist = list()
        self.fitteddata = list()  ######拟合后数据列表
        self.fittedresults = list()  ######拟合后结果列表
        self.resultsdataInfo = []   # 输出 dataInfo(2N)

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
            # 读取 Min/Max（允许空 → 用合理兜底；保证 differential_evolution
            # 等需要有限边界的优化器能正常运行）
            try:
                max_val = float(self.tab1.ECMtable.item(temp - 1, 4).text())
            except Exception:
                max_val = 1e15
            try:
                min_val = float(self.tab1.ECMtable.item(temp - 1, 5).text())
            except Exception:
                min_val = 1e-15
            # 防止下界 > 上界
            if min_val >= max_val:
                min_val, max_val = 1e-15, 1e15
            self.ECMparams[elementname1] = Parameter(
                elementname1, value=init_val, min=min_val, max=max_val
            )
            print(f"[ECMcalculation]   参数: {elementname1} = {init_val} (min={min_val}, max={max_val})")
        ############### 读取表格数据 生成参数    ################

        print(f"[ECMcalculation] fit_data数据集数量: {len(fit_data)}")

        # 读取拟合设置
        fit_method = 'least_squares'
        fit_kwargs = {}
        if self.setting_widget is not None:
            try:
                settings = self.setting_widget.get_settings()
                fit_method = settings.get('method', 'least_squares')
                for k, v in settings.items():
                    if k != 'method':
                        fit_kwargs[k] = _cast_setting(k, v)
                print(f'[ECMcalculation] Fitting settings: method={fit_method}, params={fit_kwargs}')
            except Exception as e:
                print(f'[ECMcalculation] 读取设置失败，使用默认设置: {e}')

        for i in range(0, n):  # 第i组拟合数据
            print(f"\n[ECMcalculation] 处理数据集{i}")
            ###############生成频率序列###############
            ECMfreq = fit_data[i]['FREQ[Hz]']  ##读取数据频率
            self.ECMlowfreqTextEdit.setText(str(ECMfreq.iloc[0]))
            self.ECMupfreqTextEdit.setText(str(ECMfreq.iloc[-1]))
            print(f"[ECMcalculation]   数据频率范围: {ECMfreq.iloc[0]:.2e} - {ECMfreq.iloc[-1]:.2e} Hz, 点数: {len(ECMfreq)}")
            ##############生成频率序列###############

            ################拟合计算###############
            if len(ECMfreq) != 0 and len(self.ECMparams) != 0:
                print(f"[ECMcalculation]   开始调用auto_fitting...")

                results = auto_fitting(self.ECMparams, ECMfreq, self.circuit, fit_data[i], method=fit_method, **fit_kwargs)  #########智能拟合
                self.fittedresults.append(results)  ######拟合后结果列表

                # ampgo 等方法 MinimizerResult.message 不可用，需 getattr 兜底
                msg_attr = getattr(results, 'message', None)
                if msg_attr is not None:
                    print(f"[ECMcalculation]   拟合结果message: {msg_attr}")
                else:
                    print(f"[ECMcalculation]   拟合结果message: (不可用，ampgo_msg={getattr(results, 'ampgo_msg', None)})")
                print(f"[ECMcalculation]   拟合参数数量: {len(results.var_names)}")
                print(f"[ECMcalculation]   拟合参数列表: {list(results.var_names)}")
                # results.x 在 ampgo 路径上不存在，用 getattr 兜底
                x_attr = getattr(results, 'x', None)
                if x_attr is not None:
                    print(f"[ECMcalculation]   拟合结果x: {x_attr}")
                else:
                    print(f"[ECMcalculation]   拟合结果x: (不可用，该方法返回 ampgo_x0={getattr(results, 'ampgo_x0', None)})")

                fitteddata = FittingresultsprocessECM(self.ECMparams, ECMfreq, self.circuit, results)
                print(f"[ECMcalculation]   fitteddata类型: {type(fitteddata)}, 长度: {len(fitteddata) if hasattr(fitteddata, '__len__') else 'N/A'}")

                self.fitteddata.append(fitteddata)  ######拟合后数据列表
                # 命名:原名保持原样,拟合结果追加 _Fitted(链式处理时多次追加)
                orig_name = fit_names[i] if i < len(fit_names) else f'data_{i}'
                fittinglist.append(1)  # 原始数据标记
                fittinglist.append(1)  # 拟合数据标记
                plotdataname.append(orig_name)
                plotdataname.append(orig_name + self._processed_suffix)

                ECMoutputdata.append(fit_data[i])
                ECMoutputdata.append(fitteddata)

                # 构造 dataInfo(2N):偶数=原始,奇数=拟合(带 synthetic 标签)
                orig_info = (self.original_dataInfo[i].copy()
                             if i < len(self.original_dataInfo) and isinstance(self.original_dataInfo[i], dict)
                             else {})
                orig_info.pop('synthetic', None)
                self.resultsdataInfo.append(orig_info)
                fit_info = orig_info.copy()
                fit_info['synthetic'] = True
                fit_info['fit_applied'] = True
                fit_info['fit_method'] = fit_method
                self.resultsdataInfo.append(fit_info)

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
        print(f"[ECMcalculation] 最终resultsdataInfo长度: {len(self.resultsdataInfo)}")

        print(f"[ECMcalculation] 调用processECMResults...")
        self.processECMResults()

        print(f"[ECMcalculation] 调用sendsignal发送数据(第 4 参数改为 dataInfo)...")
        # 第 4 参数原本是 fittedresults,改为 resultsdataInfo 以便下游 Figure 识别 synthetic 标签
        self.sendsignal(outputlist, plotdataname, ECMoutputdata, self.resultsdataInfo)
        print(f"[ECMcalculation] 完成")

    def clearECCalculation(self):
        """
        清空 ECM 最近一次 Calculate 的输出（计算行 Clear 按钮槽）。
        保留模型结构（circuit、termnamelist、modelterm、connectionTextEdit、ECMtable 行及
        Name/Comments/Initial_Value/Max/Min 列），
        只清空 fitteddata / fittedresults / resultsdataInfo、全局 plot 副本，以及 ECMtable
        的 Fitted_Value(3) / Error [%](6) 列。
        """
        # 清空拟合输出缓存
        self.fitteddata = list()
        self.fittedresults = list()
        self.resultsdataInfo = []

        # 清空全局 plot 副本（仅清拟合期追加的部分；原始数据由导入流程维护）
        try:
            global plotdata, plotdataname, outputlist
            plotdata = list()
            plotdataname = list()
            outputlist = list()
        except Exception:
            pass

        # Bug #006 Phase 2: 7 列表格,只清 Fitted_Value(3) / Error [%](6) 列
        # 保留 Name(0) / Comments(1) / Initial_Value(2) / Max(4) / Min(5)
        cleared_cols = (3, 6)
        for row in range(self.tab1.ECMtable.rowCount()):
            for col in cleared_cols:
                self.tab1.ECMtable.setItem(row, col, QTableWidgetItem(""))

        print('[clearECCalculation] ECM calculation output cleared (model preserved)')

    def clearMTCalculation(self):
        """
        清空 MT 最近一次 Calculate 的输出（计算行 Clear 按钮槽）。
        保留模型结构（modelterm、termnamelist、MTmultitermTextEdit、MTtable 行及
        Name/Comments/Initial_Value/Max/Min 列、EP/DC 勾选），
        只清空 fitteddata / fittedresults / resultsdataInfo、全局 plot 副本，以及 MTtable
        的 Fitted_Value(3) / Error [%](6) 列。
        """
        # 清空拟合输出缓存
        self.fitteddata = list()
        self.fittedresults = list()
        self.resultsdataInfo = []

        # 清空全局 plot 副本
        try:
            global plotdata, plotdataname, outputlist
            plotdata = list()
            plotdataname = list()
            outputlist = list()
        except Exception:
            pass

        # Bug #006 Phase 2: 7 列表格,只清 Fitted_Value(3) / Error [%](6) 列
        # 保留 Name(0) / Comments(1) / Initial_Value(2) / Max(4) / Min(5)
        cleared_cols = (3, 6)
        for row in range(self.tab2.MTtable.rowCount()):
            for col in cleared_cols:
                self.tab2.MTtable.setItem(row, col, QTableWidgetItem(""))

        print('[clearMTCalculation] MT calculation output cleared (model preserved)')

    def modelfig(self):
        self.modelfigureLablel = QLabel()
        self.modelfigureLablel.setPixmap(QPixmap("./circuit.png"))
        self.figurelayout.addWidget(self.modelfigureLablel)
    
    
    
    def MTcalculation(self):  ###整理拟合参数，调用函数计算
        global plotdata
        global outputlist
        global plotdataname

        # 使用 original_prodata(N 条,不含合成副本)进行拟合
        if not self.original_prodata:
            print("[MTcalculation] 错误: 没有可拟合的原始数据")
            return
        fit_data = self.original_prodata
        fit_names = self.original_prodataname
        n = len(fit_data)
        print(f"[MTcalculation] 使用 N={n} 条原始数据进行拟合(已去除合成副本)")

        outputdata = list()
        fittinglist = list()
        self.fitteddata = list()  ######拟合后数据列表
        self.fittedresults = list()  ######拟合后结果列表
        self.resultsdataInfo = []   # 输出 dataInfo(2N)

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
                        fit_kwargs[k] = _cast_setting(k, v)
                print(f'[MTcalculation] Fitting settings: method={fit_method}, params={fit_kwargs}')
            except Exception as e:
                print(f'[MTcalculation] 读取设置失败，使用默认设置: {e}')

        for i in range(0, n):  # 第i组拟合数据
            ###############生成频率序列###############
            MTfreq = fit_data[i]['FREQ[Hz]']  ##读取数据频率
            self.tab2.MTlowfreqTextEdit.setText(str(MTfreq[0]))
            self.tab2.MTupfreqTextEdit.setText(str(MTfreq[len(MTfreq) - 1]))
            ##############生成频率序列###############

            ################拟合计算###############
            if len(MTfreq) != 0 and len(self.MTparams) != 0 and len(self.modelterm) != 0:
                # print(fit_data)
                results = FittingMT(self.MTparams, MTfreq, self.modelterm, fit_data[i], self.option, method=fit_method, **fit_kwargs)
                self.fittedresults.append(results)  ######拟合后结果列表
                # print(results)
                # ampgo 等方法 MinimizerResult.message 不可用，getattr 兜底
                mt_msg = getattr(results, 'message', None) or getattr(results, 'ampgo_msg', None)
                print(f"[MTcalculation]   拟合结果message: {mt_msg}")
                fitteddata = Fittingresultsprocess(self.MTparams, MTfreq, self.modelterm, results, self.option)
                self.fitteddata.append(fitteddata)  ######拟合后数据列表
                # 命名:原名保持原样,拟合结果追加 _Fitted
                orig_name = fit_names[i] if i < len(fit_names) else f'data_{i}'
                fittinglist.append(1)  # 原始数据标记
                fittinglist.append(1)  # 拟合数据标记
                plotdataname.append(orig_name)
                plotdataname.append(orig_name + self._processed_suffix)

                outputdata.append(fit_data[i])
                outputdata.append(fitteddata)

                # 构造 dataInfo(2N):偶数=原始,奇数=拟合(带 synthetic 标签)
                orig_info = (self.original_dataInfo[i].copy()
                             if i < len(self.original_dataInfo) and isinstance(self.original_dataInfo[i], dict)
                             else {})
                orig_info.pop('synthetic', None)
                self.resultsdataInfo.append(orig_info)
                fit_info = orig_info.copy()
                fit_info['synthetic'] = True
                fit_info['fit_applied'] = True
                fit_info['fit_method'] = fit_method
                self.resultsdataInfo.append(fit_info)

                print(outputlist)
                print(plotdataname)
                print(len(outputdata))
            else:
                print('wrong')
                return

        print(fittinglist)
        outputlist = outputlist + fittinglist
        print(outputlist)
        ########################拟合计算###############
        self.processMTResults()
        # 第 4 参数改为 dataInfo 以便下游 Figure 识别 synthetic 标签
        self.sendsignal(outputlist, plotdataname, outputdata, self.resultsdataInfo)

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
        # ampgo 路径无 result.x，但 lmfit 已把值写入 result.params[par].value
        fit_x = getattr(fit_result, 'x', None)
        if fit_x is None:
            fit_x = [fit_result.params[n].value for n in fit_result.var_names]
        print(f"[processECMResults] fit_result.x: {fit_x}")

        # 设置表头为拟合模型
        self.tab1.setECMTableHeader('fit')
        print("[processECMResults] 表头已设置为fit模式")
        print(f"[processECMResults] ECMtable行数: {self.tab1.ECMtable.rowCount()}, 列数: {self.tab1.ECMtable.columnCount()}")

        # 写入初始值和拟合结果
        for i in range(len(fit_result.var_names)):
            paramsname = fit_result.var_names[i]
            fitted_val = fit_x[i]
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
            # Bug #006 Phase 3: 非 least_squares 算法 stderr 为 None 时,显示 'N/A' 而非 NaN
            param = fit_result.params[paramsname]
            stderr = param.stderr
            if stderr is None:
                err_str = 'N/A'
                print(f"[processECMResults]   stderr=None, 误差显示 N/A")
            else:
                err_str = 100 * round(stderr / param.value, 4)
                print(f"[processECMResults]   stderr={stderr}, 误差={err_str}%")

            # Bug #006 Phase 2: Error [%] 列已从 col 7 移至 col 6(0-indexed),与 7 列表头对齐
            self.ECMtableWrite(paramsname, err_str, 6)
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

        # ampgo 路径无 result.x，兜底从 params 里取
        fit_x = getattr(fit_result, 'x', None)
        if fit_x is None:
            fit_x = [fit_result.params[n].value for n in fit_result.var_names]

        # 写入初始值和拟合结果到MTtable
        for i in range(len(fit_result.var_names)):
            paramsname = fit_result.var_names[i]
            fitted_val = fit_x[i]

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
            # Bug #006 Phase 3: 非 least_squares 算法 stderr 为 None 时,显示 'N/A' 而非 NaN
            param = fit_result.params[paramsname]
            stderr = param.stderr
            if stderr is None:
                err_str = 'N/A'
            else:
                err_str = 100 * round(stderr / param.value, 4)

            # Bug #006 Phase 2: Error [%] 列已从 col 7 移至 col 6(0-indexed),与 7 列表头对齐
            self.MTtableWrite(paramsname, err_str, 6)

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




