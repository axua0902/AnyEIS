import sys
import os
sys.path.append('..')

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from EIS.FilterFile.FilterUI import DatafilterUI
from EIS.Other.Datacheck import check1, check2, check3, check4, check5, resolve_column

import matplotlib.colors as mcolors
from numpy import log10
from EIS.FilterFile.Filterfun import (
    savgol, median, wiener, butterworth, cspline, arithmeticAverage,
    slidingAverage, medianAverage, amplitudeLimitingAverage, firstOrderLag,
    weightedAverage, shakeOff, amplitudeLimitingShakeOff, calculate_multi_filter_comparison_data
)
from EIS.FigureFile.Plotfun import save_publication_figure,create_academic_canvas


# [TP-006] 滤波器完整注册表(全部 13 种方法,每种含默认参数与配色)
#   'default' 是形如 "key=value, key=value" 的字符串,供 UI 文本框编辑
METHOD_REGISTRY = [
    {'name': 'Savitzky-Golay',            'func': savgol,                    'default': 'a=11, b=1',                              'color': 'red'},
    {'name': 'Median',                    'func': median,                    'default': 'kernel_size=5',                          'color': 'green'},
    {'name': 'Wiener',                    'func': wiener,                    'default': 'noise=None',                             'color': 'magenta'},
    {'name': 'Butterworth',               'func': butterworth,               'default': 'order=2, cutoff=0.1, filter_type=filtfilt', 'color': 'orange'},
    {'name': 'Cubic spline',              'func': cspline,                   'default': 'lamb=1e-30',                             'color': 'cyan'},
    {'name': 'Arithmetic Avg',            'func': arithmeticAverage,         'default': 'window_size=5',                          'color': 'purple'},
    {'name': 'Sliding Avg',               'func': slidingAverage,            'default': 'window_size=7',                          'color': 'brown'},
    {'name': 'MedianAverage',             'func': medianAverage,             'default': 'window_size=5',                          'color': 'olive'},
    {'name': 'AmplitudeLimitingAverage',  'func': amplitudeLimitingAverage,  'default': 'window_size=5, amplitude_limit=100',     'color': 'navy'},
    {'name': 'FirstOrderLag',             'func': firstOrderLag,             'default': 'alpha=0.3',                              'color': 'pink'},
    {'name': 'WeightedAverage',           'func': weightedAverage,           'default': 'window_size=5',                          'color': 'gray'},
    {'name': 'ShakeOff',                  'func': shakeOff,                  'default': 'threshold_count=3',                      'color': 'lime'},
    {'name': 'AmplitudeLimitingShakeOff', 'func': amplitudeLimitingShakeOff, 'default': 'amplitude_limit=100, threshold_count=3', 'color': 'teal'},
]
# 对话框打开时默认勾选的 5 个方法(向后兼容)
DEFAULT_SELECTED = {'Savitzky-Golay', 'Median', 'Butterworth', 'Arithmetic Avg', 'Sliding Avg'}
# 最多同时对比的方法数(原 3×5 布局第一行 5 列)
MAX_COMPARE_METHODS = 5


def _parse_param_str(param_str):
    """把 'key=value, key=value' 字符串解析为 dict。空字符串返回空 dict。
    无效片段(如缺少 '=')会被跳过并打印警告,避免静默吞错。"""
    result = {}
    if not param_str:
        return result
    for part in param_str.split(','):
        part = part.strip()
        if not part:
            continue
        if '=' not in part:
            print(f'[Filter] Skipping invalid parameter fragment: "{part}" (missing "="). '
                  f'Use format "key=value, key=value".')
            continue
        k, v = part.split('=', 1)
        result[k.strip()] = v.strip()
    return result


"""
数据流动过程说明 (Data Flow Process):

1. 输入数据 (Input Data):
   - getsingal() 接收外部数据
   - 存储在: self.selectlist, self.prodataname, self.prodata, self.dataInfo

2. 数据处理 (Data Processing):
   - filterdata() 根据 filterCheckBox 状态决定处理方式
   - 未选中: 直接输出原始数据
   - 选中: 调用 filterring() 进行滤波处理

3. 输出数据 (Output Data):
   - 未处理: 直接输出输入数据
   - 已处理: 输出原始数据+滤波数据，存储在 self.resultsselectlist, self.resultsdataname, self.resultsdata
   - sendsignal() 发送最终数据

4. 数据检查 (Data Validation):
   - check1(), check2() 验证数据完整性
   - check_data_status() 显示当前数据状态
"""


class Datafilter(QWidget, DatafilterUI):
    Apdatasignal = Signal(list, list, list, list)

    # 处理后数据名称后缀(链式处理时会追加,例如 Filter 后再 Processing 会得到 _Filtered_Processed)
    # 命名习惯:Input 用原名,Filter 用 _Filtered,Processing 用 _Processed,Fitting 用 _Fitted
    _processed_suffix = '_Filtered'

    def __init__(self, parent=None):
        super(Datafilter, self).__init__(parent)
        ########变量申明###############
        self.initdata()
        ########变量申明###############

        ###########初始化###################

        self.filterui=DatafilterUI()
        self.filterui.set_parent_filter_instance(self)  # 设置父实例引用
        self.filterui.DatafilterUI(self)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 可选：移除边距
        self.main_layout.addWidget(self.filterui.contents)  # 添加 UI 内容到布局

       ###########初始化###################

        # 连接信号和槽
        self.filterui.filtermethodComboBox.currentIndexChanged.connect(self.filtermethodselec)
        self.filterui.filterdataBtn.clicked.connect(self.filterdata)
        self.filterui.outputdataBtn1.clicked.connect(self.filterdata)
        self.filterui.filtercomparaisonBtn.clicked.connect(self.filtercompare)





    def initdata(self):
        # Input data (received from getsingal())
        self.selectlist = []           # 输入数据选择列表
        self.prodataname = []          # 输入数据名称列表
        self.prodata = []              # 输入数据列表
        self.dataInfo = []             # 输入数据信息

        # 原始数据(从 2N 成对中提取的 N 条,供滤波函数使用)
        # 与 ensure_paired_form 协议兼容:配对格式则取偶数索引
        self.original_prodata = []         # 原始 DataFrame 列表(N 条)
        self.original_prodataname = []     # 原始名称列表(N 条)
        self.original_selectlist = []       # 原始选择标记(N 条)
        self.original_dataInfo = []         # 原始 dataInfo(N 条,无 synthetic 标签)

        # Processed/Output data
        self.resultsselectlist = []   # 输出数据选择列表
        self.resultsdata = []         # 输出数据列表
        self.resultsdataname = []     # 输出数据名称列表
        self.resultsdataInfo = []     # 输出 dataInfo(2N 条,奇数位带 synthetic 标签)

        # Reference data
        self.refdata = []
        self.refdataname = []


    #################################信号###########################
    def getsingal(self, inputselectlist, inputdataname, inputdata, inputmessage):  #####获得数据######
        """接收输入数据信号"""
        self.selectlist = inputselectlist.copy() if inputselectlist else []
        self.prodataname = inputdataname.copy() if inputdataname else []
        self.prodata = inputdata.copy() if inputdata else []
        self.dataInfo = inputmessage.copy() if inputmessage else []
        # 提取原始数据(从 2N 成对 → N),供后续滤波使用
        self._extract_original_data()
        print('FIlter get data',self.selectlist, self.prodataname, len(self.prodata),
              '| original N=', len(self.original_prodata))
        self.auto_forward_data()

    def _extract_original_data(self):
        """
        从 self.prodata(2N 成对 或 N 单条)中提取原始数据(N 条,不含合成副本)。
        配对格式(2N + 奇数位带 synthetic 标签):只取偶数索引
        非配对格式(N):全部保留
        """
        n = len(self.prodata)
        if (n > 0
                and n % 2 == 0
                and self.dataInfo
                and len(self.dataInfo) == n
                and any(isinstance(info, dict) and info.get('synthetic', False)
                        for info in self.dataInfo[1::2])):
            # 配对格式:只取偶数索引
            self.original_prodata = [self.prodata[i] for i in range(0, n, 2)]
            self.original_prodataname = [self.prodataname[i] for i in range(0, n, 2)]
            self.original_selectlist = [self.selectlist[i] for i in range(0, n, 2)]
            self.original_dataInfo = [self.dataInfo[i] for i in range(0, n, 2)]
        else:
            # 非配对格式:全部保留(并补齐 dataInfo)
            self.original_prodata = list(self.prodata)
            self.original_prodataname = list(self.prodataname)
            self.original_selectlist = list(self.selectlist)
            if self.dataInfo and len(self.dataInfo) == n:
                self.original_dataInfo = list(self.dataInfo)
            else:
                self.original_dataInfo = [{}] * n


    def sendsignal(self, outputselectlist, outputdataname, outputdata, outputmessage):
        """发送输出数据信号"""
        self.Apdatasignal.emit(outputselectlist, outputdataname, outputdata, outputmessage)
        print('FIlter emit data',outputselectlist, outputdataname, len(outputdata),outputmessage)

    def auto_forward_data(self):
        """
        自动转发数据到下一个模块。
        - 如果未启用处理功能,把当前 prodata 原样转发(可能是 Input 来的 2N,也可能是 1N)
        - 这样上游的数据(原始或处理)都能直接到达下游,不被截断
        """
        if len(self.prodata) > 0:
            if self.filterui.filterCheckBox.isChecked():
                # 如果启用了处理功能，等待用户手动处理
                print("Processing enabled - waiting for manual processing")
            else:
                # 关键修复:原样透传上游数据(N 条或 2N 都行,不强制截断)
                self.sendsignal(
                    self.selectlist.copy(),
                    self.prodataname.copy(),
                    self.prodata.copy(),
                    self.dataInfo.copy()
                )
                print(f'[auto_forward_data] Filter disabled, forwarding '
                      f'{len(self.prodata)} 条数据(原样透传)')


    ##################################数据检查#############################
    def check1(self):  # 全部输入数据检查
        return check1(self.selectlist, self.prodataname, self.prodata)

    def check2(self):  # 输入数据内部检查
        return check2(self.prodata)

    def check3(self, data, namelist):  # 参考数据之间检查
        return check3(data, namelist)

    def check5(self, data, namelist):  # 参考数据内部检查
        return check5(data)

    def check4(self, prodata, refdata):  # 参考数据与输入数据比较检查
        return check4(prodata, refdata)
    ##################################数据检查#############################

    def originaldata(self):  # 'orignal date'
        outputselectlist = self.selectlist
        outputdataname = self.prodataname
        outputdata = self.prodata
        outputmessage = self.dataInfo
        self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)  # 输出信号
        return

    def processeddata(self):  # 'processed date'
        for i in range(0, len(self.resultsselectlist)):
            if i % 2 == 0:
                self.resultsselectlist[i] = 0
            else:
                pass
        outputselectlist = self.resultsselectlist
        outputdataname = self.resultsdataname
        outputdata = self.resultsdata
        # 创建包含滤波信息的输出消息
        outputmessage = self.create_filtered_datainfo()
        self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)  # 输出信号
        return

    ###############################过滤#############################
    def filtermethodselec(self):
        currentfiltermethod = self.filterui.filtermethodComboBox.currentText()
        if currentfiltermethod == 'Savitzky-Golay':
            self.filterui.filter_method_uis.uiSavgol()
        elif currentfiltermethod == 'Median':
            self.filterui.filter_method_uis.uiMedian()
        elif currentfiltermethod == 'Wiener':
            self.filterui.filter_method_uis.uiWiener()
        elif currentfiltermethod == 'Butterworth':
            self.filterui.filter_method_uis.uiButterworth()
        elif currentfiltermethod == 'Cubic spline':
            self.filterui.filter_method_uis.uiCspline()
        elif currentfiltermethod == 'ArithmeticAverage':
            self.filterui.filter_method_uis.uiArithmeticAverage()
        elif currentfiltermethod == 'SlidingAverage':
            self.filterui.filter_method_uis.uiSlidingAverage()
        elif currentfiltermethod == 'MedianAverage':
            self.filterui.filter_method_uis.uiMedianAverage()
        elif currentfiltermethod == 'AmplitudeLimitingAverage':
            self.filterui.filter_method_uis.uiAmplitudeLimitingAverage()
        elif currentfiltermethod == 'FirstOrderLag':
            self.filterui.filter_method_uis.uiFirstOrderLag()
        elif currentfiltermethod == 'WeightedAverage':
            self.filterui.filter_method_uis.uiWeightedAverage()
        elif currentfiltermethod == 'ShakeOff':
            self.filterui.filter_method_uis.uiShakeOff()
        elif currentfiltermethod == 'AmplitudeLimitingShakeOff':
            self.filterui.filter_method_uis.uiAmplitudeLimitingShakeOff()
        elif currentfiltermethod == 'Choose Method':
            self.filterui.filter_method_uis.uiother()
        else:
            self.filterui.filter_method_uis.uiother()



    def filterdata(self):
        """主要的数据处理函数：根据filterCheckBox状态决定是否进行滤波处理"""
        
            
        if self.filterui.filterCheckBox.isChecked() == 0:
            # 不进行滤波处理,只输出原始数据(N 条,不含合成副本)
            print('Filter disabled - outputting original data')
            outputselectlist = list(self.original_selectlist)
            outputdataname = list(self.original_prodataname)
            outputdata = list(self.original_prodata)
            outputmessage = list(self.original_dataInfo)
            self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)
            return
        else:
            # 进行滤波处理
            if self.check1() == 0 or self.check2() == 0:
                print('Error: Data validation failed - please check input data')
                return
            else:
                print('Filter enabled - processing data')
                try:
                    self.filterring()
                    if len(self.resultsdata) == 0:
                        print('Error: No filtered data generated')
                        return
                    outputselectlist = self.resultsselectlist.copy()
                    outputdataname = self.resultsdataname.copy()
                    outputdata = self.resultsdata.copy()
                    # 创建包含滤波信息的输出消息
                    outputmessage = self.create_filtered_datainfo()
                    self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)
                except Exception as e:
                    print(f'Error during filtering: {str(e)}')
                    import traceback
                    traceback.print_exc()
                return

    def filterring(self):
        currentmethod = self.filterui.filtermethodComboBox.currentText()
        if currentmethod=='Choose Method':
            self.databasecreat(self.prodata)

        elif currentmethod == 'Savitzky-Golay':
            parameter = {'a': self.filterui.filterp1TextEdit.text(), 'b': self.filterui.filterp2TextEdit.text()}
            filteresults = savgol(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'Median':
            parameter = {'kernel_size': self.filterui.filterp1TextEdit.text()}
            filteresults = median(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'Wiener':
            parameter = {'noise': self.filterui.filterp1TextEdit.text() if self.filterui.filterp1TextEdit.text() else None}
            filteresults = wiener(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'Butterworth':
            parameter = {
                'order': self.filterui.filterp1TextEdit.text(),
                'cutoff': self.filterui.filterp2TextEdit.text(),
                'filter_type': self.filterui.filterp3TextEdit.text()
            }
            filteresults = butterworth(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'Cubic spline':
            parameter = {'lamb': self.filterui.filterp1TextEdit.text()}
            filteresults = cspline(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'ArithmeticAverage':
            parameter = {'window_size': self.filterui.filterp1TextEdit.text()}
            filteresults = arithmeticAverage(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'SlidingAverage':
            parameter = {'window_size': self.filterui.filterp1TextEdit.text()}
            filteresults = slidingAverage(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'MedianAverage':
            parameter = {'window_size': self.filterui.filterp1TextEdit.text()}
            filteresults = medianAverage(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'AmplitudeLimitingAverage':
            parameter = {
                'window_size': self.filterui.filterp1TextEdit.text(),
                'amplitude_limit': self.filterui.filterp2TextEdit.text()
            }
            filteresults = amplitudeLimitingAverage(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'FirstOrderLag':
            parameter = {'alpha': self.filterui.filterp1TextEdit.text()}
            filteresults = firstOrderLag(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'WeightedAverage':
            parameter = {'window_size': self.filterui.filterp1TextEdit.text()}
            filteresults = weightedAverage(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'ShakeOff':
            parameter = {'threshold_count': self.filterui.filterp1TextEdit.text()}
            filteresults = shakeOff(self.prodata, parameter)
            self.databasecreat(filteresults)

        elif currentmethod == 'AmplitudeLimitingShakeOff':
            parameter = {
                'amplitude_limit': self.filterui.filterp1TextEdit.text(),
                'threshold_count': self.filterui.filterp2TextEdit.text()
            }
            filteresults = amplitudeLimitingShakeOff(self.prodata, parameter)
            self.databasecreat(filteresults)

        else:
            print(f'Unknown filter method: {currentmethod}')
            pass



    def filtercompare(self):
        """创建绘图对话框对比不同过滤方法然后绘制图形"""
        
        # 检查是否有数据
        if not hasattr(self, 'prodata') or len(self.prodata) == 0:
            print("No data available for filter comparison")
            return

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('Multi-Filter Comparison Analysis')
        dialog.setModal(True)
        dialog.resize(1400, 1000)

        # 使用Plotfun.py中的create_academic_canvas函数创建学术风格画布
        canvas = create_academic_canvas(width=20, height=16, dpi=100)

        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 添加画布到布局
        main_layout.addWidget(canvas)

        # [TP-006] 方法选择与参数编辑解耦:网格布局
        # 每个方法一个紧凑的 [复选框(方法名)] [参数编辑框] [Reset] 横向小条
        # 用 QGridLayout N 列 × ceil(13/N) 行 排齐,所有方法平铺在底部
        method_rows = []  # [{name, chk, edit, default}, ...]
        GRID_COLS = 5     # 每行 5 个方法,共 3 行(13 个方法)

        # Counter label
        _count_label = QLabel(f"Selected 0/{MAX_COMPARE_METHODS}")
        _count_label.setStyleSheet("color: #1976d2; font-weight: 700;")
        _count_label.setMinimumWidth(110)
        _count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def _refresh_count_label():
            n = sum(1 for r in method_rows if r['chk'].isChecked())
            _count_label.setText(f"Selected {n}/{MAX_COMPARE_METHODS}")
            if n > MAX_COMPARE_METHODS:
                _count_label.setStyleSheet("color: #c62828; font-weight: 700;")
            else:
                _count_label.setStyleSheet("color: #1976d2; font-weight: 700;")

        # 方法网格容器
        methods_grid = QWidget()
        grid = QGridLayout(methods_grid)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        for idx, m in enumerate(METHOD_REGISTRY):
            row_idx, col_idx = divmod(idx, GRID_COLS)

            row = {'name': m['name'], 'default': m['default']}

            # 复选框(方法名作为标签)
            row['chk'] = QCheckBox(m['name'])
            row['chk'].setChecked(m['name'] in DEFAULT_SELECTED)
            row['chk'].setMinimumWidth(110)
            row['chk'].setMaximumWidth(140)
            row['chk'].setStyleSheet("font-size: 12px;")
            row['chk'].toggled.connect(_refresh_count_label)

            # 参数编辑框
            row['edit'] = QLineEdit(m['default'])
            row['edit'].setPlaceholderText("key=value")
            row['edit'].setMinimumWidth(120)
            row['edit'].setMaximumWidth(180)
            row['edit'].setStyleSheet("font-size: 12px;")
            row['edit'].setToolTip(f"{m['name']} 的参数(默认: {m['default']})")

            # Reset
            reset_btn = QPushButton("Reset")
            reset_btn.setMaximumWidth(46)
            reset_btn.setStyleSheet("font-size: 10px; padding: 2px 4px;")
            reset_btn.setToolTip(f"恢复默认参数: {m['default']}")
            def _make_reset(default_str, edit_widget):
                def _do_reset():
                    edit_widget.setText(default_str)
                return _do_reset
            reset_btn.clicked.connect(_make_reset(m['default'], row['edit']))

            # 紧凑水平布局
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(4)
            cell_layout.addWidget(row['chk'])
            cell_layout.addWidget(row['edit'])
            cell_layout.addWidget(reset_btn)

            grid.addWidget(cell_widget, row_idx, col_idx)
            method_rows.append(row)

        # 让所有列等宽
        for c in range(GRID_COLS):
            grid.setColumnStretch(c, 1)

        _refresh_count_label()

        # 构造用户配置的闭包
        def _build_user_config():
            selected_rows = [r for r in method_rows if r['chk'].isChecked()]
            if len(selected_rows) == 0:
                return None
            if len(selected_rows) > MAX_COMPARE_METHODS:
                print(f'[filtercompare] At most {MAX_COMPARE_METHODS} methods allowed, '
                      f'truncated to the first {MAX_COMPARE_METHODS}')
                selected_rows = selected_rows[:MAX_COMPARE_METHODS]
            config = {}
            for r in selected_rows:
                for m in METHOD_REGISTRY:
                    if m['name'] == r['name']:
                        params = _parse_param_str(r['edit'].text() or m['default'])
                        config[r['name']] = {'func': m['func'], 'params': params, 'color': m['color']}
                        break
            return config

        # 绘图按钮
        plot_comparison_btn = QPushButton("Generate Filter Comparison")
        plot_comparison_btn.clicked.connect(
            lambda: self.generate_filter_comparison(canvas, _build_user_config())
        )

        # 控制区:方法网格 + 计数(同一行,网格占主体,计数靠右)
        control_layout = QHBoxLayout()
        _methods_label = QLabel("Methods:")
        _methods_label.setStyleSheet("font-weight: 700; font-size: 13px;")
        control_layout.addWidget(_methods_label)
        control_layout.addWidget(methods_grid, 1)  # stretch=1 让网格占满
        control_layout.addWidget(_count_label)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.addWidget(plot_comparison_btn)
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: save_publication_figure(canvas, parent=self, save_mode='direct'))
        saveas_btn = QPushButton("Save As")
        saveas_btn.clicked.connect(lambda: save_publication_figure(canvas, parent=self, save_mode='dialog'))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(saveas_btn)
        button_layout.addWidget(close_btn)

        # 主布局:画布 + 控制区(方法网格) + 按钮行
        main_layout.addLayout(control_layout)
        main_layout.addLayout(button_layout)

        # 自动生成初始对比图
        self.generate_filter_comparison(canvas)

        # 显示对话框
        dialog.exec()


    def generate_filter_comparison(self, canvas, custom_filters_config=None):
        """生成滤波器对比图
        Args:
            canvas: matplotlib 画布
            custom_filters_config: 可选,UI 端选择的方法配置(传给 calculate_multi_filter_comparison_data)
        """
        try:
            # 调用Filterfun.py中的calculate_multi_filter_comparison_data函数获取数据
            comparison_data = calculate_multi_filter_comparison_data(
                self.prodata, self.prodataname,
                custom_filters_config=custom_filters_config
            )

            if comparison_data is None:
                print("No comparison data available")
                return

            # 调用绘图函数
            self.plot_filter_comparison_charts(canvas, comparison_data)
        except Exception as e:
            print(f"Error generating filter comparison: {e}")
            import traceback
            traceback.print_exc()



    def plot_filter_comparison_charts(self, canvas, comparison_data):
        """专门负责绘制滤波器对比图表的函数(支持 EIS 与 DS 数据)"""

        # 解包数据
        original_data = comparison_data['original_data']
        original_name = comparison_data['original_name']
        filtered_results = comparison_data['filtered_results']
        filter_stats = comparison_data['filter_stats']
        filters_config = comparison_data['filters_config']
        performance_scores = comparison_data['performance_scores']

        # [TP-005] 读取数据类型与列名映射
        data_type = comparison_data.get('data_type', 'UNKNOWN')
        col_map = comparison_data.get('column_map') or {}
        freq_col = col_map.get('freq')
        real_col = col_map.get('real')
        imag_col = col_map.get('imag')
        third_col = col_map.get('third')  # 可选

        # 兜底:如果上游没给 column_map,在本地再解析一次
        if not (freq_col and real_col and imag_col):
            freq_cands = ['FREQ[Hz]', 'Frequency[Hz]', 'Freq[Hz]', 'FREQ', 'frequency']
            if data_type == 'DS':
                real_cands = ['epsRE[-]', 'PERMITTIVITY RE', 'EPSILON RE', 'EPS RE',
                              'PERMITTIVITYRE', 'EPSILONRE', 'EPSRE', 'EpsRE[-]', 'epsRE']
                imag_cands = ['epsIM[-]', 'PERMITTIVITY IM', 'EPSILON IM', 'EPS IM',
                              'PERMITTIVITYIM', 'EPSILONIM', 'EPSIM', 'EpsIM[-]', 'epsIM']
                third_cands = ['sigmaRE[S/m]', 'CONDUCTIVITY RE', 'SIGMA RE', 'SIG RE',
                               'CONDUCTIVITYRE', 'SIGMARE', 'SIGRE', 'sigmaRE']
            else:
                real_cands = ['Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'RS[Ω]', 'Rs', 'R']
                imag_cands = ['X[ohm]', 'X[OHM]', 'X[Ω]', 'X[Ω]', 'X']
                third_cands = ['PHASE[deg]', 'Phase[deg]', 'PHASE[DEG]', 'PHASE', 'ph', 'Phase']
            freq_col  = resolve_column(original_data, freq_cands)
            real_col  = resolve_column(original_data, real_cands)
            imag_col  = resolve_column(original_data, imag_cands)
            third_col = resolve_column(original_data, third_cands) or third_col

        if not all([freq_col, real_col, imag_col]):
            missing = [n for n, c in (('FREQ', freq_col), ('real', real_col),
                                      ('imag', imag_col)) if c is None]
            print(f'[plot_filter_comparison_charts] {data_type} 数据缺少列: {missing} '
                  f'(实际列: {list(original_data.columns)})，跳过绘制')
            return

        # [TP-005] 数据类型驱动的标签与标题(两行布局 + 较小字号,避免相邻子图标题重叠)
        if data_type == 'DS':
            lbl_real, unit_real = "ε'", ""
            lbl_imag, unit_imag = "ε\"", ""
            lbl_third, unit_third = "σ'", "[S/m]"
            title1 = "Cole-Cole"
            title2 = f"{lbl_real}\nvs Frequency"
            title3 = f"{lbl_imag}\nvs Frequency"
            title4 = f"{lbl_third}\nvs Frequency"
            title_noise_real  = f"{lbl_real} Noise\nReduction"
            title_noise_imag  = f"{lbl_imag} Noise\nReduction"
            title_noise_third = f"{lbl_third} Noise\nReduction"
        else:
            lbl_real, unit_real = "Rs", "[Ohm]"
            lbl_imag, unit_imag = "X", "[Ohm]"
            lbl_third, unit_third = "Phase", "[deg]"
            title1 = "Nyquist"
            title2 = "Real Part\nvs Frequency"
            title3 = "Imag Part\nvs Frequency"
            title4 = "Phase\nvs Frequency"
            title_noise_real  = "Rs Noise\nReduction"
            title_noise_imag  = "X Noise\nReduction"
            title_noise_third = "Phase Noise\nReduction"

        def label_full(lbl, unit):
            return f"{lbl} {unit}".strip()

        # 创建大图形
        fig = canvas.figure
        fig.clear()  # 清除之前的内容

        # 从原始数据中提取数据(使用泛化的 real/imag/third 命名)
        freq_orig  = original_data[freq_col]
        real_orig  = original_data[real_col]
        imag_orig  = original_data[imag_col]
        third_orig = original_data[third_col] if third_col else None

        # 统计结果显示区域
        filter_names = list(filter_stats.keys())
        if not filter_names:
            print('[plot_filter_comparison_charts] 没有可用的滤波结果,跳过绘制')
            return
        colors = [filter_stats[name]['color'] for name in filter_names]

        # 子图1: Nyquist / Cole-Cole 图
        ax1 = fig.add_subplot(3, 5, 1)
        ax1.plot(real_orig, imag_orig, 'b-', linewidth=2, alpha=0.8, label='Original')
        for filter_name, filtered_data in filtered_results.items():
            f_real = resolve_column(filtered_data, [real_col]) or real_col
            f_imag = resolve_column(filtered_data, [imag_col]) or imag_col
            color = filters_config[filter_name]['color']
            ax1.plot(filtered_data[f_real], filtered_data[f_imag],
                    color=color, linewidth=1.5, alpha=0.7, label=filter_name)
        if data_type != 'DS':  # EIS Nyquist 习惯 Y 轴反向
            ax1.invert_yaxis()
        ax1.set_xlabel(label_full(lbl_real, unit_real))
        ax1.set_ylabel(label_full(lbl_imag, unit_imag))
        ax1.set_title(title1, fontsize=10, pad=4)
        ax1.legend(loc='lower left', fontsize=8, framealpha=0.85)
        ax1.grid(True, alpha=0.3)

        # 子图2: 频率 vs 实部
        ax2 = fig.add_subplot(3, 5, 2)
        ax2.plot(log10(freq_orig), real_orig, 'b-', linewidth=2, alpha=0.8, label='Original')
        for filter_name, filtered_data in filtered_results.items():
            f_freq = resolve_column(filtered_data, [freq_col]) or freq_col
            f_real = resolve_column(filtered_data, [real_col]) or real_col
            color = filters_config[filter_name]['color']
            ax2.plot(log10(filtered_data[f_freq]), filtered_data[f_real],
                    color=color, linewidth=1.5, alpha=0.7, label=filter_name)
        ax2.set_xlabel("Log Frequency [Hz]")
        ax2.set_ylabel(label_full(lbl_real, unit_real))
        ax2.set_title(title2, fontsize=10, pad=4)
        ax2.grid(True, alpha=0.3)

        # 子图3: 频率 vs 虚部
        ax3 = fig.add_subplot(3, 5, 3)
        ax3.plot(log10(freq_orig), imag_orig, 'b-', linewidth=2, alpha=0.8, label='Original')
        for filter_name, filtered_data in filtered_results.items():
            f_freq = resolve_column(filtered_data, [freq_col]) or freq_col
            f_imag = resolve_column(filtered_data, [imag_col]) or imag_col
            color = filters_config[filter_name]['color']
            ax3.plot(log10(filtered_data[f_freq]), filtered_data[f_imag],
                    color=color, linewidth=1.5, alpha=0.7, label=filter_name)
        ax3.set_xlabel("Log Frequency [Hz]")
        ax3.set_ylabel(label_full(lbl_imag, unit_imag))
        ax3.set_title(title3, fontsize=10, pad=4)
        if data_type != 'DS':  # EIS 习惯 Y 轴反向
            ax3.invert_yaxis()
        ax3.grid(True, alpha=0.3)

        # 子图4: 频率 vs 第三变量(Phase / sigmaRE)
        ax4 = fig.add_subplot(3, 5, 4)
        if third_orig is not None:
            ax4.plot(log10(freq_orig), third_orig, 'b-', linewidth=2, alpha=0.8, label='Original')
            for filter_name, filtered_data in filtered_results.items():
                f_freq  = resolve_column(filtered_data, [freq_col])  or freq_col
                f_third = resolve_column(filtered_data, [third_col]) or third_col
                color = filters_config[filter_name]['color']
                ax4.plot(log10(filtered_data[f_freq]), filtered_data[f_third],
                        color=color, linewidth=1.5, alpha=0.7, label=filter_name)
        ax4.set_xlabel("Log Frequency [Hz]")
        ax4.set_ylabel(label_full(lbl_third, unit_third))
        ax4.set_title(title4, fontsize=10, pad=4)
        ax4.grid(True, alpha=0.3)
        
        # 子图5: 综合性能雷达图
        ax5 = fig.add_subplot(3, 5, 5)
        overall_scores = [performance_scores[name]['overall'] for name in filter_names]
        bars = ax5.bar(range(len(filter_names)), overall_scores, color=colors, alpha=0.7)
        ax5.set_xlabel("Filter Methods")
        ax5.set_ylabel("Overall Score")
        ax5.set_title("Overall\nPerformance", fontsize=10, pad=4)
        ax5.set_xticks(range(len(filter_names)))
        ax5.set_xticklabels([name[:6] for name in filter_names], rotation=45, fontsize=8)
        ax5.grid(True, alpha=0.3)
        # 添加数值标签
        for i, (bar, val) in enumerate(zip(bars, overall_scores)):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overall_scores)*0.01, 
                    f'{val:.1f}', ha='center', va='bottom', fontsize=7)
        
        # 子图6: 噪声减少效果对比 (实部)
        ax6 = fig.add_subplot(3, 5, 6)
        noise_reduction_Rs = [filter_stats[name]['noise_reduction']['Rs'] for name in filter_names]
        bars = ax6.bar(range(len(filter_names)), noise_reduction_Rs, color=colors, alpha=0.7)
        ax6.set_xlabel("Filter Methods")
        ax6.set_ylabel("Noise Reduction (%)")
        ax6.set_title(title_noise_real, fontsize=10, pad=4)
        ax6.set_xticks(range(len(filter_names)))
        ax6.set_xticklabels([name[:6] for name in filter_names], rotation=45, fontsize=8)
        ax6.grid(True, alpha=0.3)
        # 添加数值标签
        for i, (bar, val) in enumerate(zip(bars, noise_reduction_Rs)):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(noise_reduction_Rs)*0.01,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=7)

        # 子图7: 噪声减少效果对比 (虚部)
        ax7 = fig.add_subplot(3, 5, 7)
        noise_reduction_X = [filter_stats[name]['noise_reduction']['X'] for name in filter_names]
        bars = ax7.bar(range(len(filter_names)), noise_reduction_X, color=colors, alpha=0.7)
        ax7.set_xlabel("Filter Methods")
        ax7.set_ylabel("Noise Reduction (%)")
        ax7.set_title(title_noise_imag, fontsize=10, pad=4)
        ax7.set_xticks(range(len(filter_names)))
        ax7.set_xticklabels([name[:6] for name in filter_names], rotation=45, fontsize=8)
        ax7.grid(True, alpha=0.3)
        # 添加数值标签
        for i, (bar, val) in enumerate(zip(bars, noise_reduction_X)):
            ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(noise_reduction_X)*0.01,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=7)

        # 子图8: 第三变量噪声减少效果对比 (Phase / sigmaRE)
        ax8 = fig.add_subplot(3, 5, 8)
        noise_reduction_Phase = [filter_stats[name]['noise_reduction']['Phase'] for name in filter_names]
        bars = ax8.bar(range(len(filter_names)), noise_reduction_Phase, color=colors, alpha=0.7)
        ax8.set_xlabel("Filter Methods")
        ax8.set_ylabel("Noise Reduction (%)")
        ax8.set_title(title_noise_third, fontsize=10, pad=4)
        ax8.set_xticks(range(len(filter_names)))
        ax8.set_xticklabels([name[:6] for name in filter_names], rotation=45, fontsize=8)
        ax8.grid(True, alpha=0.3)
        # 添加数值标签
        for i, (bar, val) in enumerate(zip(bars, noise_reduction_Phase)):
            ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(noise_reduction_Phase)*0.01,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=7)
        
        # 子图9: 信号保真度对比 (相关系数)
        ax9 = fig.add_subplot(3, 5, 9)
        correlation_avg = [(filter_stats[name]['correlation']['Rs'] + 
                           filter_stats[name]['correlation']['X'] + 
                           filter_stats[name]['correlation']['Phase']) / 3 
                          for name in filter_names]
        bars = ax9.bar(range(len(filter_names)), correlation_avg, color=colors, alpha=0.7)
        ax9.set_xlabel("Filter Methods")
        ax9.set_ylabel("Average Correlation")
        ax9.set_title("Signal\nFidelity", fontsize=10, pad=4)
        ax9.set_xticks(range(len(filter_names)))
        ax9.set_xticklabels([name[:6] for name in filter_names], rotation=45, fontsize=8)
        ax9.set_ylim(0.9, 1.0)  # 聚焦在高相关性区域
        ax9.grid(True, alpha=0.3)
        # 添加数值标签
        for i, (bar, val) in enumerate(zip(bars, correlation_avg)):
            ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001, 
                    f'{val:.3f}', ha='center', va='bottom', fontsize=7)
        
        # 子图10: 最佳滤波器推荐图表
        ax10 = fig.add_subplot(3, 5, 10)
        # 找到最佳滤波器
        best_filter = max(filter_names, key=lambda x: performance_scores[x]['overall'])
        best_index = filter_names.index(best_filter)
        
        # 创建推荐图表
        recommendation_colors = ['lightgray'] * len(filter_names)
        recommendation_colors[best_index] = 'gold'
        
        bars = ax10.bar(range(len(filter_names)), overall_scores, color=recommendation_colors, alpha=0.8)
        ax10.set_xlabel("Filter Methods")
        ax10.set_ylabel("Overall Score")
        ax10.set_title("[*] Recommended\nFilter", fontsize=10, pad=4)
        ax10.set_xticks(range(len(filter_names)))
        ax10.set_xticklabels([name[:6] for name in filter_names], rotation=45, fontsize=8)
        ax10.grid(True, alpha=0.3)
        
        # 高亮最佳滤波器
        bars[best_index].set_edgecolor('red')
        bars[best_index].set_linewidth(2)
        
        # 添加推荐标签
        ax10.text(best_index, overall_scores[best_index] + max(overall_scores)*0.05, 
                f'BEST\n{best_filter[:8]}\n{overall_scores[best_index]:.1f}', 
                ha='center', va='bottom', fontsize=8, fontweight='bold', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        # 子图11-15: 详细统计表格区域
        ax_table = fig.add_subplot(3, 5, (11,15))  # 占用底部5个子图位置
        ax_table.axis('off')  # 关闭坐标轴
        
        # 准备表格数据
        table_data = []
        headers = ['Filter', 'Rs Noise↓(%)', 'X Noise↓(%)', 'Phase Noise↓(%)', 
                  'Rs Corr', 'X Corr', 'Phase Corr', 'Overall Score', 'Rank']
        
        # 按综合得分排序
        sorted_filters = sorted(filter_names, key=lambda x: performance_scores[x]['overall'], reverse=True)
        
        for rank, name in enumerate(sorted_filters, 1):
            stats = filter_stats[name]
            row = [
                name,
                f"{stats['noise_reduction']['Rs']:.1f}",
                f"{stats['noise_reduction']['X']:.1f}",
                f"{stats['noise_reduction']['Phase']:.1f}",
                f"{stats['correlation']['Rs']:.3f}",
                f"{stats['correlation']['X']:.3f}",
                f"{stats['correlation']['Phase']:.3f}",
                f"{performance_scores[name]['overall']:.1f}",
                f"#{rank}"
            ]
            table_data.append(row)
        
        # 创建表格
        table = ax_table.table(cellText=table_data,
                         colLabels=headers,
                         cellLoc='center',
                         loc='center',
                         bbox=[0, 0, 1, 1])
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.8)
        
        # 为表格添加颜色
        for i, name in enumerate(sorted_filters):
            color = filters_config[name]['color']
            # 为每行添加浅色背景
            for j in range(len(headers)):
                if i == 0:  # 最佳滤波器用金色背景
                    table[(i+1, j)].set_facecolor('gold')
                    table[(i+1, j)].set_text_props(weight='bold')
                else:
                    table[(i+1, j)].set_facecolor(mcolors.to_rgba(color, alpha=0.2))
        
        # 设置标题 — 调整位置避免与第一行子图标题重叠
        fig.suptitle(f'Multi-Filter Comparison Analysis: {original_name}', fontsize=16, y=0.995)
        # fig.tight_layout()
        fig.subplots_adjust(top=0.90, bottom=0.06, hspace=0.55, wspace=0.4)
        
        canvas.draw()  # 刷新canvas
        
        # 只保留必要的程序运行提示信息
        print("Filter comparison analysis completed successfully")

    ##############################功能#############################
    def databasecreat(self, filteresults):
        """
        创建输出数据库:严格 2N 成对形式
        - 偶数位(2i): 原始数据,无 synthetic 标签
        - 奇数位(2i+1): 滤波结果,dataInfo 带 synthetic:True 标签
        名字保持原样(链式处理时仅追加自身后缀,与 Input 协议一致)。

        filteresults 自适应处理:
        - 配对格式(self.prodata 2N + 奇数位带 synthetic 标签):取前 N 作为"真实滤波结果"
        - 非配对格式(self.prodata N):全部作为滤波结果
        这样不需要在 filterring 中区分 self.prodata / self.original_prodata。
        """
        n_pro = len(self.prodata)

        # 配对格式检测:2N + dataInfo 奇数位带 synthetic 标签
        is_paired = (
            n_pro > 0
            and n_pro % 2 == 0
            and self.dataInfo
            and len(self.dataInfo) == n_pro
            and any(isinstance(info, dict) and info.get('synthetic', False)
                    for info in self.dataInfo[1::2])
        )

        if is_paired:
            n = n_pro // 2
            # 原始数据(偶数索引)
            orig_data = [self.prodata[i] for i in range(0, n_pro, 2)]
            orig_name = [self.prodataname[i] for i in range(0, n_pro, 2)]
            orig_select = [self.selectlist[i] for i in range(0, n_pro, 2)]
            orig_info_list = [self.dataInfo[i] for i in range(0, n_pro, 2)]
            # 真实滤波结果:从 filteresults 中按偶数索引取(与 orig_data 对齐)
            # 因为 filteresults 也是 2N 配对形式(原始+合成副本),前 N 个实际都是同一个数据集的滤波结果
            if filteresults and len(filteresults) == n_pro:
                real_filtered = [filteresults[i] for i in range(0, n_pro, 2)]
            else:
                # 'Choose Method' 等情况:filteresults == self.prodata,直接用前 N
                real_filtered = orig_data if (filteresults is self.prodata) else (
                    list(filteresults) if filteresults else orig_data
                )
        else:
            # 非配对格式:全部使用
            n = n_pro
            orig_data = list(self.prodata)
            orig_name = list(self.prodataname)
            orig_select = list(self.selectlist)
            orig_info_list = list(self.dataInfo) if self.dataInfo else [{}] * n
            real_filtered = list(filteresults) if filteresults else list(self.prodata)

        if not real_filtered or len(real_filtered) != n:
            print(f'Error: Filter results length ({len(real_filtered) if real_filtered else 0}) '
                  f'does not match expected length ({n})')
            return

        # 清空输出
        self.resultsdata = []
        self.resultsdataname = []
        self.resultsselectlist = []
        self.resultsdataInfo = []

        for i in range(n):
            # 偶数位: 原始数据(去除任何 synthetic 残留标签,名称保持原样)
            self.resultsdata.append(orig_data[i])
            self.resultsdataname.append(orig_name[i])
            self.resultsselectlist.append(orig_select[i] if i < len(orig_select) else 0)
            orig_info = orig_info_list[i].copy() if isinstance(orig_info_list[i], dict) else {}
            orig_info.pop('synthetic', None)
            self.resultsdataInfo.append(orig_info)

            # 奇数位: 滤波结果(带 synthetic 标签 + 滤波方法信息)
            # 命名:在原名后追加 _Filtered(链式处理时多次追加,如 _Filtered_Processed)
            self.resultsdata.append(real_filtered[i])
            self.resultsdataname.append(orig_name[i] + self._processed_suffix)
            self.resultsselectlist.append(orig_select[i] if i < len(orig_select) else 0)
            proc_info = orig_info.copy()
            proc_info['synthetic'] = True
            proc_info['filter_applied'] = True
            proc_info['filter_method'] = self.filterui.filtermethodComboBox.currentText()
            self.resultsdataInfo.append(proc_info)

        return

    def create_filtered_datainfo(self):
        """
        返回最近一次 databasecreat 填入的 resultsdataInfo(替代原来的复杂生成逻辑)
        长度 2N,奇数位 dataInfo 已包含 synthetic:True 标签
        """
        return self.resultsdataInfo

    def get_current_filter_parameters(self):
        """获取当前滤波器参数"""
        current_method = self.filterui.filtermethodComboBox.currentText()
        parameters = {}
        
        if current_method == 'Savitzky-Golay':
            parameters = {
                'window_length': self.filterui.filterp1TextEdit.text(),
                'polyorder': self.filterui.filterp2TextEdit.text()
            }
        elif current_method == 'Median':
            parameters = {
                'kernel_size': self.filterui.filterp1TextEdit.text()
            }
        elif current_method == 'Wiener':
            parameters = {
                'noise': self.filterui.filterp1TextEdit.text() if self.filterui.filterp1TextEdit.text() else 'None'
            }
        elif current_method == 'Butterworth':
            parameters = {
                'order': self.filterui.filterp1TextEdit.text(),
                'cutoff': self.filterui.filterp2TextEdit.text(),
                'filter_type': self.filterui.filterp3TextEdit.text()
            }
        elif current_method == 'Cubic spline':
            parameters = {
                'lambda': self.filterui.filterp1TextEdit.text()
            }
        elif current_method in ['ArithmeticAverage', 'SlidingAverage', 'MedianAverage', 'WeightedAverage']:
            parameters = {
                'window_size': self.filterui.filterp1TextEdit.text()
            }
        elif current_method == 'AmplitudeLimitingAverage':
            parameters = {
                'window_size': self.filterui.filterp1TextEdit.text(),
                'amplitude_limit': self.filterui.filterp2TextEdit.text()
            }
        elif current_method == 'FirstOrderLag':
            parameters = {
                'alpha': self.filterui.filterp1TextEdit.text()
            }
        elif current_method == 'ShakeOff':
            parameters = {
                'threshold_count': self.filterui.filterp1TextEdit.text()
            }
        elif current_method == 'AmplitudeLimitingShakeOff':
            parameters = {
                'amplitude_limit': self.filterui.filterp1TextEdit.text(),
                'threshold_count': self.filterui.filterp2TextEdit.text()
            }
        
        return parameters

    def get_current_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ##############################功能#############################

    ###############################过滤#############################