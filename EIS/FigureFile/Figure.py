import sys,os
sys.path.append('..')
from datetime import datetime

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *



from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


from EIS.FigureFile.Plotfun import MyMplCanvas, create_academic_canvas, save_publication_figure
from EIS.FigureFile.ui_Figure import FigureUI

from EIS.FigureFile.Figurefun import creatanyfile,writeanydata,EISfiguremaker,EPSfiguremaker
from EIS.FigureFile.OtherFigurefun import TIMEfiguremaker,Generalfiguremaker
from EIS.FigureFile.UserDefineFun import userdefine1, userdefine2, userdefine3, userdefine4, userdefine5
from setting import Settings


def _ensure_writable_dir(dir_path):
    """
    确保目录存在且可写,失败时返回 False。
    - 目录不存在则尝试创建
    - 存在但不可写则返回 False
    """
    if not dir_path:
        return False
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f'Created results directory: {dir_path}')
        except Exception as e:
            print(f'Failed to create directory {dir_path}: {e}')
            return False
    if not os.path.isdir(dir_path):
        return False
    # 尝试创建临时文件,验证可写
    try:
        test_file = os.path.join(dir_path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception as e:
        print(f'Directory not writable: {dir_path} ({e})')
        return False


def _resolve_excel_dir():
    """
    解析 Excel 文件所在目录。
    1. 优先用项目根目录下的 Results(默认/推荐)
    2. 若该目录不可用,回退到 base_settings.json 中 top_settings.paths.results_data + working_path
    3. 都不可用则返回 None
    """
    # 1. 默认优先:项目根目录下的 Results
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_dir = os.path.join(project_root, 'Results')
    if _ensure_writable_dir(default_dir):
        return default_dir

    # 2. 回退:base_settings.json 中配置的 results_data(自动解析相对/绝对路径)
    try:
        settings = Settings()
        fallback = settings.get_path('top_settings', 'paths', 'results_data',
                                     default='Results')
    except Exception as e:
        print(f'Failed to load settings: {e}')
        fallback = None

    print(f'Default results dir not writable: {default_dir}\nFalling back to: {fallback}')

    if fallback and _ensure_writable_dir(fallback):
        return fallback

    # 都不行:返回默认目录(由调用方处理)
    return default_dir if default_dir else fallback





class FigWidget(QWidget ,FigureUI):
    def __init__(self, parent=None):
        super(FigWidget, self).__init__(parent)
        ########变量申明###############
        self.plotdata = list()      # 所有数据 
        self.plotdataname = list()  # 被选中的数据名 
        self.outputlist = list()    # 被选中的数据 
        self.message = list()      # 数据信息 

        ########变量申明###############

        ###########布局初始化###################
        self.mpl = MyMplCanvas(self, width=8, height=10, dpi=100)
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mpl.setSizePolicy(size_policy)
        
        self.figuregui = FigureUI()
        self.control_panel = self.figuregui.figureUI(self)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.mpl, 6)      # 画布占60%空间
        main_layout.addWidget(self.control_panel, 4) # 控制面板占40%空间
        ###########布局初始化###################

        self.figuregui.drawbtn.clicked.connect(self.drawfigure)
        self.figuregui.clearbtn.clicked.connect(self.clearfigure)
        self.figuregui.toolbtn.clicked.connect(self.toolbar)
        self.figuregui.PaperFigurebtn.clicked.connect(self.PaperFigure)

        self.figuregui.datatypeComboBox.currentIndexChanged.connect(self.selectionchange)
        self.figuregui.savebtn.clicked.connect(self.saveasexcel)
        self.figuregui.openExcelbtn.clicked.connect(self.OpenExcelFiles)

        # Original/Processed 复选框状态变化时自动重绘(Filter/Processing/Fitting 模式)
        self.figuregui.origindataCheckBox.stateChanged.connect(self._on_processing_state_changed)
        self.figuregui.processeddataCheckBox.stateChanged.connect(self._on_processing_state_changed)

        self.figuregui.userdefine1btn.clicked.connect(lambda: userdefine1(self))
        self.figuregui.userdefine2btn.clicked.connect(lambda: userdefine2(self))
        self.figuregui.userdefine3btn.clicked.connect(lambda: userdefine3(self))
        self.figuregui.userdefine4btn.clicked.connect(lambda: userdefine4(self))
        self.figuregui.userdefine5btn.clicked.connect(lambda: userdefine5(self))

        self.figuregui.AllOption.clicked.connect(self.on_all_option_clicked)

        # 初始化按钮状态
        self.selectionchange()

        # 默认:Original/Processed checkbox 可用(Processing/Fitting 页面)
        # Plotting 页面(纯 Input)会调用 set_processing_state_enabled(False) 关闭它们
        self._processing_state_enabled = True

        # 默认:绘图时显示 synthetic 数据(Filter/Processing/Fitting 行为)
        # Plotting 页面会通过 set_processing_state_enabled(False) 同步关闭它
        self._display_synthetic = True

    def set_processing_state_enabled(self, enabled):
        """
        控制 Original / Processed 复选框的可用性。
        Input/Simulation 模式下传入 False,关闭这两个无意义的复选框;
        Processing/Fitting 模式下保持 True(默认)。
        同步联动 _display_synthetic:关闭复选框时也隐藏 synthetic 曲线。
        """
        self._processing_state_enabled = enabled
        self._display_synthetic = enabled
        self.figuregui.origindataCheckBox.setEnabled(enabled)
        self.figuregui.processeddataCheckBox.setEnabled(enabled)
        # 禁用时同时取消勾选,避免残留状态影响后续保存逻辑
        if not enabled:
            self.figuregui.origindataCheckBox.setChecked(False)
            self.figuregui.processeddataCheckBox.setChecked(False)

    def set_display_synthetic(self, enabled):
        """
        单独控制绘图时是否显示 synthetic(合成/处理后)数据。
        True  → 同时绘制原始和处理后曲线(Filter/Processing/Fitting)
        False → 只绘制原始曲线(Input/Simulation,避免与原始重叠)
        """
        self._display_synthetic = enabled

    def _on_processing_state_changed(self):
        """
        Original/Processed 复选框状态变化时的槽函数:
        - Filter/Processing/Fitting 模式下:立即重绘图窗以反映新选择
        - Input/Simulation 模式下:复选框被禁用,此槽不会被触发
        """
        if getattr(self, '_processing_state_enabled', True) and self.plotdata:
            # 已有数据才重绘(避免初始化时的空重绘)
            self.drawfigure()







    def getsignal(self, message1, message2, message3, message4):
        self.outputlist = message1
        self.plotdataname = message2
        self.plotdata = message3
        self.message = message4

        # column_headers = self.plotdata[0].columns.tolist() if self.plotdata else "No data available"
        # print('Inputdata emitted', self.selectlist, self.plotdataname, column_headers, self.message)

        print('obtained by Figure',self.outputlist, self.plotdataname, len(self.plotdata), self.message)
        # print(self.selectlist)
        # print(self.plotdataname)
        # print(self.plotdata)
        # print(self.dataInfo)




    def selectionchange(self):
        data_type = self.figuregui.datatypeComboBox.currentText()
        
        if data_type == 'f-Z,Phase,Re(Z),Im(Z)':
            self._set_button_states({
                'NyquistOption': {'text': "Nyquist\nRe(Z)-Im(Z)", 'enabled': True, 'checked': True},
                'BodeReOption': {'text': "Bode\nf-Re(Z)", 'enabled': True, 'checked': True},
                'BodeImOption': {'text': "Bode\nf-Im(Z)", 'enabled': True, 'checked': True},
                'BodePhyOption': {'text': "Bode\nf-Phase", 'enabled': True, 'checked': True},
                'AllOption': {'enabled': True, 'checked': True},
                'timeorderOption': {'enabled': False, 'checked': False},
                'normalOption': {'enabled': False, 'checked': False}
            })

        elif data_type == 'f-Epsilon,Sigma':
            self._set_button_states({
                'NyquistOption': {'text': "Nyquist\nEpsilon-Sigma", 'enabled': True, 'checked': True},
                'BodeReOption': {'text': "Bode\nf-Sigma", 'enabled': True, 'checked': True},
                'BodeImOption': {'text': "Bode\nf-Epsilon", 'enabled': True, 'checked': True},
                'BodePhyOption': {'text': "Bode\n f-theta", 'enabled': True, 'checked': True},
                'AllOption': {'enabled': True, 'checked': True},
                'timeorderOption': {'enabled': False, 'checked': False},
                'normalOption': {'enabled': False, 'checked': False}
            })

        elif data_type == "Time order":
            self._set_button_states({
                'NyquistOption': {'text': "Nyquist\nRe(Z)-Im(Z)", 'enabled': False, 'checked': False},
                'BodeReOption': {'text': "Bode\nf-Re(Z)", 'enabled': False, 'checked': False},
                'BodeImOption': {'text': "Bode\nf-Im(Z)", 'enabled': False, 'checked': False},
                'BodePhyOption': {'text': "Bode\nf-Phase", 'enabled': False, 'checked': False},
                'AllOption': {'enabled': False, 'checked': False},
                'timeorderOption': {'enabled': True, 'checked': True},
                'normalOption': {'enabled': False, 'checked': False}
            })

        else:  # General 或其他
            self._set_button_states({
                'NyquistOption': {'text': "Nyquist\nRe(Z)-Im(Z)", 'enabled': False, 'checked': False},
                'BodeReOption': {'text': "Bode\nf-Re(Z)", 'enabled': False, 'checked': False},
                'BodeImOption': {'text': "Bode\nf-Im(Z)", 'enabled': False, 'checked': False},
                'BodePhyOption': {'text': "Bode\nf-Phase", 'enabled': False, 'checked': False},
                'AllOption': {'enabled': False, 'checked': False},
                'timeorderOption': {'enabled': False, 'checked': False},
                'normalOption': {'enabled': True, 'checked': True}
            })


    def _set_button_states(self, buttons_config):
        """辅助方法：批量设置按钮状态"""
        for button_name, config in buttons_config.items():
            button = getattr(self.figuregui, button_name)
            if 'text' in config:
                button.setText(config['text'])
            if 'enabled' in config:
                button.setEnabled(config['enabled'])
            if 'checked' in config:
                button.setChecked(config['checked'])




    def _filter_synthetic_for_display(self, outputlist, plotdataname, plotdata, message):
        """
        根据当前页面模式和复选框状态过滤要显示的条目。
        - Input/Simulation 模式(_display_synthetic=False):过滤掉 synthetic
        - Filter/Processing/Fitting 模式(_display_synthetic=True):按复选框状态决定
            - Original 勾选:保留偶数位(原始)
            - Processed 勾选:保留奇数位(处理后)
            - 两个都勾选:全部保留
        saveasexcel/selectsavedata 不调用此方法,仍使用完整列表。
        """
        # Input/Simulation 模式:强制隐藏 synthetic
        if not getattr(self, '_display_synthetic', True):
            if not message or len(message) != len(plotdata):
                return outputlist, plotdataname, plotdata
            keep_indices = [
                i for i, info in enumerate(message)
                if not (isinstance(info, dict) and info.get('synthetic', False))
            ]
            return (
                [outputlist[i] for i in keep_indices],
                [plotdataname[i] for i in keep_indices],
                [plotdata[i] for i in keep_indices],
            )

        # Filter/Processing/Fitting 模式:按 Original/Processed 复选框状态过滤
        show_orig = self.figuregui.origindataCheckBox.isChecked()
        show_proc = self.figuregui.processeddataCheckBox.isChecked()

        # 没有 message 或长度不匹配 → 不做基于 synthetic 的过滤
        if not message or len(message) != len(plotdata):
            return outputlist, plotdataname, plotdata

        keep_indices = []
        for i, info in enumerate(message):
            is_synthetic = isinstance(info, dict) and info.get('synthetic', False)
            if is_synthetic and show_proc:
                keep_indices.append(i)
            elif (not is_synthetic) and show_orig:
                keep_indices.append(i)

        return (
            [outputlist[i] for i in keep_indices],
            [plotdataname[i] for i in keep_indices],
            [plotdata[i] for i in keep_indices],
        )

    def drawfigure(self):
        self.clearfigure()
        self.mpl.fig.clear()

        # 临时替换 self.outputlist/plotdataname/plotdata 为过滤掉 synthetic 的版本,
        # 画图结束后用 finally 恢复,这样下游 saveasexcel/selectsavedata 仍看到完整列表
        outputlist_draw, plotdataname_draw, plotdata_draw = self._filter_synthetic_for_display(
            self.outputlist, self.plotdataname, self.plotdata, self.message
        )
        saved_outputlist, saved_plotdataname, saved_plotdata = (
            self.outputlist, self.plotdataname, self.plotdata
        )
        self.outputlist, self.plotdataname, self.plotdata = (
            outputlist_draw, plotdataname_draw, plotdata_draw
        )

        try:
            data_type = self.figuregui.datatypeComboBox.currentText()

            if data_type == 'f-Z,Phase,Re(Z),Im(Z)':
                # 获取被选中的按钮
                main_buttons = [
                    ('Nyquist', self.figuregui.NyquistOption),
                    ('BodeRe', self.figuregui.BodeReOption),
                    ('BodeIm', self.figuregui.BodeImOption),
                    ('BodePhy', self.figuregui.BodePhyOption)
                ]
                checked_buttons = [name for name, button in main_buttons if button.isChecked()]
                checked_count = len(checked_buttons)

                if self.figuregui.AllOption.isChecked() or checked_count == 4:
                    self.mpl.plotZall(self.outputlist, self.plotdataname, self.plotdata)
                elif checked_count == 1:
                    figpos = 111
                    self._plot_figure(checked_buttons[0], figpos, data_type=data_type)
                elif checked_count == 2:
                    figposup = 211
                    figposdown = 212
                    self._plot_figure(checked_buttons[0], figposup, data_type=data_type)
                    self._plot_figure(checked_buttons[1], figposdown, data_type=data_type)
                elif checked_count == 3:
                    # 左侧上下各一幅图,右侧一幅图
                    figpos_left_up = 221
                    figpos_left_down = 223
                    figpos_right = 122
                    self._plot_figure(checked_buttons[0], figpos_left_up, data_type=data_type)
                    self._plot_figure(checked_buttons[1], figpos_left_down, data_type=data_type)
                    self._plot_figure(checked_buttons[2], figpos_right, data_type=data_type)
                else:
                    # 默认绘制所有图表
                    self.mpl.plotZall(self.outputlist, self.plotdataname, self.plotdata)

            elif data_type == 'f-Epsilon,Sigma':
                # 获取被选中的按钮
                main_buttons = [
                    ('Nyquist', self.figuregui.NyquistOption),
                    ('BodeRe', self.figuregui.BodeReOption),
                    ('BodeIm', self.figuregui.BodeImOption),
                    ('BodePhy', self.figuregui.BodePhyOption)
                ]
                checked_buttons = [name for name, button in main_buttons if button.isChecked()]
                checked_count = len(checked_buttons)

                if self.figuregui.AllOption.isChecked() or checked_count == 4:
                    self.mpl.plotEpsall(self.outputlist, self.plotdataname, self.plotdata)
                elif checked_count == 1:
                    figpos = 111
                    self._plot_figure(checked_buttons[0], figpos, data_type=data_type)
                elif checked_count == 2:
                    figposup = 211
                    figposdown = 212
                    self._plot_figure(checked_buttons[0], figposup, data_type=data_type)
                    self._plot_figure(checked_buttons[1], figposdown, data_type=data_type)
                elif checked_count == 3:
                    # 左侧上下各一幅图,右侧一幅图
                    figpos_left_up = 221
                    figpos_left_down = 223
                    figpos_right = 122
                    self._plot_figure(checked_buttons[0], figpos_left_up, data_type=data_type)
                    self._plot_figure(checked_buttons[1], figpos_left_down, data_type=data_type)
                    self._plot_figure(checked_buttons[2], figpos_right, data_type=data_type)
                else:
                    # 默认绘制所有图表
                    self.mpl.plotEpsall(self.outputlist, self.plotdataname, self.plotdata)

            elif data_type == "Time order":
                if self.figuregui.timeorderOption.isChecked():
                    # 使用统一的plotNormal函数,自动布局
                    self.mpl.plotNormal(self.outputlist, self.plotdataname, self.plotdata)
            else:
                # General 或其他情况
                if self.figuregui.normalOption.isChecked():
                    # 使用统一的plotNormal函数,自动布局
                    self.mpl.plotNormal(self.outputlist, self.plotdataname, self.plotdata)
        finally:
            # 恢复原始数据,确保 saveasexcel/selectsavedata 看到完整列表
            self.outputlist, self.plotdataname, self.plotdata = (
                saved_outputlist, saved_plotdataname, saved_plotdata
            )



    def _plot_figure(self, plot_type, figpos=111, canvas=None, data_type=None):
        """统一的绘图函数，根据数据类型和绘图类型绘制相应图形
        
        Args:
            plot_type: 绘图类型 ('Nyquist', 'BodeRe', 'BodeIm', 'BodePhy')
            figpos: 图形位置 (默认111)
            canvas: 画布对象 (如果为None则使用self.mpl)
            data_type: 数据类型 (如果为None则从ComboBox获取)
        """
        # 确定使用的画布
        target_canvas = canvas if canvas is not None else self.mpl
        
        # 确定数据类型
        if data_type is None:
            data_type = self.figuregui.datatypeComboBox.currentText()
        
        try:
            # 如果是外部画布（对话框），需要清除之前的内容
            if canvas is not None:
                canvas.fig.clear()
            
            if data_type == 'f-Z,Phy,Rs,X':
                # 阻抗数据绘图
                if plot_type == 'Nyquist':
                    target_canvas.plotNyquist(self.outputlist, self.plotdataname, self.plotdata, figpos)
                elif plot_type == 'BodeRe':
                    target_canvas.plotRs(self.outputlist, self.plotdataname, self.plotdata, figpos)
                elif plot_type == 'BodeIm':
                    target_canvas.plotX(self.outputlist, self.plotdataname, self.plotdata, figpos)
                elif plot_type == 'BodePhy':
                    target_canvas.plotPhy(self.outputlist, self.plotdataname, self.plotdata, figpos)
                    
            elif data_type == 'f-Epsilon,Sigma':
                # 介电数据绘图
                if plot_type == 'Nyquist':
                    target_canvas.plotColeCole(self.outputlist, self.plotdataname, self.plotdata, figpos)
                elif plot_type == 'BodeRe':
                    target_canvas.plotSigma(self.outputlist, self.plotdataname, self.plotdata, figpos)
                elif plot_type == 'BodeIm':
                    target_canvas.plotEps(self.outputlist, self.plotdataname, self.plotdata, figpos)
                elif plot_type == 'BodePhy':
                    target_canvas.plotTheta(self.outputlist, self.plotdataname, self.plotdata, figpos)
            elif data_type == 'Time order':
                target_canvas.plotNormal(self.outputlist, self.plotdataname, self.plotdata, figpos)
            elif data_type == 'General':
                # 通用数据绘图，使用统一的plotNormal函数
                target_canvas.plotNormal(self.outputlist, self.plotdataname, self.plotdata, figpos)
            else:
                pass
                
            # 如果是外部画布，需要手动刷新
            if canvas is not None:
                canvas.draw()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"绘图失败: {str(e)}")
            print(f"Plot error: {e}")

    def on_all_option_clicked(self):
        if self.figuregui.AllOption.isChecked():
            self.figuregui.NyquistOption.setChecked(True)
            self.figuregui.BodeReOption.setChecked(True)
            self.figuregui.BodeImOption.setChecked(True)
            self.figuregui.BodePhyOption.setChecked(True)
        else:
            self.figuregui.NyquistOption.setChecked(False)
            self.figuregui.BodeReOption.setChecked(False)
            self.figuregui.BodeImOption.setChecked(False)
            self.figuregui.BodePhyOption.setChecked(False)

    def clearfigure(self):
        self.mpl.fig.clf()
        self.axes = self.mpl.fig.add_subplot(111)
        self.axes.grid(True)
        self.mpl.draw()

        dt = datetime.now()  ##获得当前时间
        excelname = str(dt.strftime('%y%m%d%H%M%S'))
        self.figuregui.excelnameTextEdit.setText('data' + '_' + excelname)

    def toolbar(self):
        if self.figuregui.toolbtn.text() == 'Tools':
            # 创建NavigationToolbar（如果还没有创建）
            if not hasattr(self, 'mpl_ntb'):
                self.mpl_ntb = NavigationToolbar(self.mpl, self)
            # 添加到布局并显示
            self.figuregui.basicOperationButtonsLayout.addWidget(self.mpl_ntb)

            self.mpl_ntb.show()
            self.figuregui.toolbtn.setText('Hide Tools')
        else:
            # 从布局中移除并隐藏
            if hasattr(self, 'mpl_ntb'):
                self.figuregui.basicOperationButtonsLayout.removeWidget(self.mpl_ntb)
                self.mpl_ntb.hide()
            self.figuregui.toolbtn.setText('Tools')

    def removetoolbar(self):
        self.figuregui.basicOperationButtonsLayout.remove(self.mpl_ntb)




    def saveasexcel(self):
        savelist = self.outputlist.copy()
        print(f'[saveasexcel] _processing_state_enabled={getattr(self, "_processing_state_enabled", True)}, '
              f'outputlist长度={len(self.outputlist)}, plotdata长度={len(self.plotdata)}')

        # Input/Simulation 模式:复选框被禁用,plotdata 是 2N(原始+合成副本,同引用)
        # 跳过 selectsavedata 的奇偶筛选,只取偶数索引(原始)避免重复保存
        if not getattr(self, '_processing_state_enabled', True):
            inputdata = []
            inputdataname = []
            savelist_new = []
            for i in range(0, len(self.plotdata), 2):
                # 选中状态只看偶数位;奇数位的合成副本自动跳过
                selected = (i < len(savelist) and savelist[i] == 1)
                if selected:
                    inputdata.append(self.plotdata[i])
                    inputdataname.append(self.plotdataname[i])
                savelist_new.append(1 if selected else 0)
            # savelist 补齐到 2N 长度,供下游使用
            savelist = savelist_new + [0] * (len(self.plotdata) - len(savelist_new))
            print(f'[saveasexcel] Input/Simulation模式:保存 {len(inputdata)} 条数据')
        else:
            inputdata, inputdataname, savelist = self.selectsavedata(savelist)
            print(f'[saveasexcel] Filter/Processing/Fitting模式:保存 {len(inputdata)} 条数据')

        excelname = self.figuregui.excelnameTextEdit.text()
        results_dir = _resolve_excel_dir()
        if not results_dir or not os.path.isdir(results_dir):
            print(f'Results directory not available: {results_dir}')
            return
        wbname = os.path.join(results_dir, excelname + '.xlsx')

        if self.figuregui.datatypeComboBox.currentText() == 'f-Z,Phase,Re(Z),Im(Z)':
            #############创建excel文件,定义文件名,数据名,列名
            workbook, worksheet, dataInfo, writeInfo = creatanyfile(wbname, inputdataname, inputdata)
            ##############写入数据
            workbook, worksheet, dataInfo, writeInfo = writeanydata(workbook, worksheet, inputdataname, inputdata,
                                                                    dataInfo,
                                                                    writeInfo)
            workbook = EISfiguremaker(workbook, worksheet, dataInfo, writeInfo)  ###########画图
            print('EIS Figure saved')
        elif self.figuregui.datatypeComboBox.currentText() == 'f-Epsilon,Sigma':
            #############创建excel文件,定义文件名,数据名,列名
            workbook, worksheet, dataInfo, writeInfo = creatanyfile(wbname, inputdataname, inputdata)
            ##############写入数据
            workbook, worksheet, dataInfo, writeInfo = writeanydata(workbook, worksheet, inputdataname, inputdata,
                                                                    dataInfo,
                                                                    writeInfo)
            workbook = EPSfiguremaker(workbook, worksheet, dataInfo, writeInfo)  ###########画图
            print('DS Figure saved')


        elif self.figuregui.datatypeComboBox.currentText() == 'General':
            #############创建excel文件,定义文件名,数据名,列名
            workbook, worksheet, dataInfo, writeInfo = creatanyfile(wbname, inputdataname, inputdata)
            ##############写入数据
            workbook, worksheet, dataInfo, writeInfo = writeanydata(workbook, worksheet, inputdataname, inputdata,
                                                                    dataInfo,
                                                                    writeInfo)
            workbook = Generalfiguremaker(workbook, worksheet, dataInfo, writeInfo)  ###########画图
            print('General Figure saved')
        elif self.figuregui.datatypeComboBox.currentText() == 'Time order':
            #############创建excel文件,定义文件名,数据名,列名
            workbook, worksheet, dataInfo, writeInfo = creatanyfile(wbname, inputdataname, inputdata)
            ##############写入数据
            workbook, worksheet, dataInfo, writeInfo = writeanydata(workbook, worksheet, inputdataname, inputdata,
                                                                    dataInfo,
                                                                    writeInfo)
            workbook = TIMEfiguremaker(workbook, worksheet, dataInfo, writeInfo)  ###########画图
            print('Time order Figure saved')
        else:
            pass

        workbook.close()
        return


    def selectsavedata(self, savelist):
        inputdata = list()
        inputdataname = list()
        # 防御性检查:Input/Simulation 模式(复选框被禁用)直接返回全部数据
        if not getattr(self, '_processing_state_enabled', True):
            for i in range(0, len(self.plotdata)):
                if savelist[i] == 1:
                    inputdata.append(self.plotdata[i])
                    inputdataname.append(self.plotdataname[i])
            print(f'[selectsavedata] Input/Simulation模式:返回 {len(inputdata)} 条')
            return inputdata, inputdataname, savelist

        orig_state = self.figuregui.origindataCheckBox.isChecked()
        proc_state = self.figuregui.processeddataCheckBox.isChecked()
        print(f'[selectsavedata] 复选框状态 Original={orig_state}, Processed={proc_state}, '
              f'plotdata长度={len(self.plotdata)}')

        if orig_state == 0 and proc_state == 1:
            for i in range(0, len(savelist)):
                if i % 2 == 0:  ###偶数
                    savelist[i] = 0
                else:
                    pass
            for i in range(0, len(self.plotdata)):
                if savelist[i] == 1:
                    inputdata.append(self.plotdata[i])
                    inputdataname.append(self.plotdataname[i])
                else:
                    pass

        elif self.figuregui.origindataCheckBox.isChecked() == 1 and self.figuregui.processeddataCheckBox.isChecked() == 0:
            for i in range(0, len(savelist)):
                if i % 2 != 0:  ####奇数
                    savelist[i] = 0
                else:
                    pass
            for i in range(0, len(self.plotdata)):
                if savelist[i] == 1:
                    inputdata.append(self.plotdata[i])
                    inputdataname.append(self.plotdataname[i])
                else:
                    pass
        else:
            for i in range(0, len(self.plotdata)):
                if savelist[i] == 1:
                    inputdata.append(self.plotdata[i])
                    inputdataname.append(self.plotdataname[i])
        return inputdata, inputdataname, savelist



    def OpenExcelFiles(self):  ###用外部工具打开当前excel文件
        excel_filename = self.figuregui.excelnameTextEdit.text().strip()
        if excel_filename == '':
            print('No excel file name specified')
            QMessageBox.warning(self, "Warning", "No excel file name specified")
            return

        # 清理文件名，移除可能的无效字符
        excel_filename = excel_filename.replace(',', '').replace(' ', '_')

        # 确保扩展名正确
        if not excel_filename.endswith('.xlsx'):
            if excel_filename.endswith('.xls') or excel_filename.endswith('.xsx'):
                excel_filename = excel_filename.rsplit('.', 1)[0] + '.xlsx'
            else:
                excel_filename = excel_filename + '.xlsx'

        # 与 saveasexcel 使用相同的路径解析策略:
        # 1. 优先 base_settings.json 中 top_settings.paths.results_data
        # 2. 回退到项目根目录下的 Results
        results_dir = _resolve_excel_dir()
        if not results_dir or not os.path.isdir(results_dir):
            print(f'Results directory not found: {results_dir}')
            QMessageBox.warning(
                self, "Warning",
                f"Results directory not found.\n{results_dir}\n"
                "Please export data to Excel first to create the directory.")
            return

        excel_path = os.path.join(results_dir, excel_filename)

        # 检查文件是否存在
        if os.path.exists(excel_path):
            try:
                os.startfile(excel_path)
                print(f'Opening excel file: {excel_path}')
            except Exception as e:
                print(f'Failed to open excel file: {e}')
                QMessageBox.warning(self, "Warning", f"Failed to open excel file: {str(e)}")
        else:
            print(f'Excel file not found: {excel_path}')
            QMessageBox.warning(self, "Warning", f"Excel file not found: {excel_path}\nPlease export data to Excel first.")




    def PaperFigure(self):
        """创建绘图对话框并使用学术画布绘制图形"""
        if not self.plotdata or not self.outputlist:
            QMessageBox.warning(self, "Warning", "No data to plot!")
            return
            
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('Academic Figure for Paper')
        dialog.setModal(True)
        dialog.resize(1200, 900)
        
        # 使用Plotfun.py中的create_academic_canvas函数创建学术风格画布
        canvas = create_academic_canvas(width=12, height=10, dpi=150)
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加画布到布局
        main_layout.addWidget(canvas)
        
        # 创建统一的按钮布局（绘图按钮靠左，控制按钮靠右）
        button_layout = QHBoxLayout()
        
        # 创建绘图按钮
        nyquist_btn = QPushButton("Nyquist")
        bode_re_btn = QPushButton("Bode Rs")
        bode_im_btn = QPushButton("Bode X")
        bode_phy_btn = QPushButton("Bode Phase")
        
        # 获取当前数据类型
        current_data_type = self.figuregui.datatypeComboBox.currentText()
        
        # 连接按钮点击事件到绘图函数
        nyquist_btn.clicked.connect(lambda: self._plot_figure('Nyquist', canvas=canvas, data_type=current_data_type))
        bode_re_btn.clicked.connect(lambda: self._plot_figure('BodeRe', canvas=canvas, data_type=current_data_type))
        bode_im_btn.clicked.connect(lambda: self._plot_figure('BodeIm', canvas=canvas, data_type=current_data_type))
        bode_phy_btn.clicked.connect(lambda: self._plot_figure('BodePhy', canvas=canvas, data_type=current_data_type))
        
        # 添加绘图按钮到布局（靠左放置）
        button_layout.addWidget(nyquist_btn)
        button_layout.addWidget(bode_re_btn)
        button_layout.addWidget(bode_im_btn)
        button_layout.addWidget(bode_phy_btn)
        
        # 添加弹性空间，将后面的按钮推到右侧
        button_layout.addStretch()
        
        # 创建保存和关闭按钮
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: save_publication_figure(canvas, parent=self, save_mode='direct'))
        
        saveas_btn = QPushButton("Save As")
        saveas_btn.clicked.connect(lambda: save_publication_figure(canvas, parent=self, save_mode='dialog'))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        
        # 添加保存和关闭按钮到布局（靠右放置）
        button_layout.addWidget(save_btn)
        button_layout.addWidget(saveas_btn)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # 默认绘制Nyquist图
        self._plot_figure('Nyquist', canvas=canvas, data_type=current_data_type)
        
        # 显示对话框
        dialog.exec()









