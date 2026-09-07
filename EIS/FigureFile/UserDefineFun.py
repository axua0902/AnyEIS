"""
Data Structure Analysis / 数据结构分析:
Based on the validation functions, the expected data structures are:
根据验证函数分析，预期的数据结构如下：

1. Main Data Lists / 主要数据列表:
   - selectlist: List of selection flags/indices (1=selected, 0=not selected) / 选择标志/索引列表(1=已选择,0=未选择）
     Example / 示例: [1, 1, 1, 1, 1]
   
   - prodataname: List of processing data names / 处理数据名称列表  
     Example / 示例: ['name1', 'name2', 'name3', 'name4', 'name5']
   
   - prodata: List of pandas DataFrames containing processing data / 包含处理数据的pandas DataFrame列表
     Example / 示例: Each DataFrame contains EIS measurement data with columns:
     每个DataFrame包含EIS/DS测量数据,列包括：
     * FREQ[Hz]: Frequency in Hz / 频率（赫兹）
     * Z[ohm]: Impedance magnitude in ohms / 阻抗幅值（欧姆）
     * PHASE[deg]: Phase angle in degrees / 相位角（度）
     * Rs[ohm]: Series resistance in ohms / 串联电阻（欧姆）
     * X[ohm]: Reactance in ohms / 电抗（欧姆）
     Typical size: 200 rows x 5 columns / 典型尺寸:200行x5列
   
   - refdata: List of pandas DataFrames containing reference data / 包含参考数据的pandas DataFrame列表
     Same structure as prodata, used for comparison / 与prodata结构相同,用于比较
   
   - dataInfo: Additional data information list (can be empty) / 附加数据信息列表（可为空）
     Example / 示例: []
     
        print(self.selectlist)
        [1, 1, 1, 1, 1]

        print(self.prodataname)
        ['name1', 'name2', 'name3', 'name4', 'name5']

        print(self.prodata)
        [       FREQ[Hz]    Z[ohm]  PHASE[deg]   Rs[ohm]    X[ohm]
        0       1000000  131.3670      -6.152  130.6110  -14.0793
        1       1000000  131.3790      -6.145  130.6240  -14.0628
        2       1100000  130.4170      -6.520  129.5740  -14.8085
        ..          ...       ...         ...       ...       ...
        198  2881700000  115.5250     -77.610   24.7885 -112.8340
        199  3000000000  126.9770     -78.427   25.4741 -124.3950
            [200 rows x 5 columns],

        print(self.refdata)
        [       FREQ[Hz]    Z[ohm]  PHASE[deg]   Rs[ohm]    X[ohm]
        0       1000000  138.3640      -8.027  137.0080  -19.3210
        1       1000000  138.3790      -8.016  137.0270  -19.2976
        2       1100000  136.9670      -8.388  135.5020  -19.9791
        ..          ...       ...         ...       ...       ...
        198  2881700000  116.7160     -77.330   25.5997 -113.8740
        199  3000000000  128.3470     -78.126   26.4084 -125.6010
            [200 rows x 5 columns],

        print(self.dataInfo)
        []  

2. Data Format / 数据格式:
   - Each DataFrame has .shape attribute (rows, columns) / 每个DataFrame具有.shape属性(行数,列数）
     Example / 示例: (200, 5) - 200 data points with 5 measurement parameters
   - Each DataFrame has .columns attribute for column names / 每个DataFrame具有.columns属性用于列名
     Example / 示例: ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']
   - All DataFrames in the same list should have consistent dimensions / 同一列表中的所有DataFrame应具有一致的维度
   - Frequency range typically spans from 1MHz to 3GHz / 频率范围通常从1MHz到3GHz
   - Data contains both low and high frequency measurements / 数据包含低频和高频测量

3. EIS Data Columns / EIS数据列:
   - Frequency: FREQ[Hz] - Measurement frequency / 测量频率
   - Impedance: Z, absZ, Z[ohm], Z[OHM], Z[Ω] - Impedance magnitude / 阻抗幅值
   - Phase: PHASE, PHASE[deg], PHASE[DEG], ph - Phase angle (typically negative) / 相位角（通常为负值）
   - Resistance: Rs, Rs[ohm], RS[OHM], Rs[Ω], R -  resistance / 阻抗实部，电阻
   - Reactance: X, X[ohm], X[OHM], X[Ω] - Reactance (typically negative for capacitive) /阻抗虚部， 电抗（电容性通常为负值）

4. DS (Dielectric Spectroscopy) Data Columns / DS(介电谱)数据列:
   - Real Permittivity: PERMITTIVITY RE, EPSILON RE, EPS RE, epsRE[-] / 实部介电常数
   - Imaginary Permittivity: PERMITTIVITY IM, EPSILON IM, EPS IM, epsIM[-] / 虚部介电常数  
   - Real Conductivity: CONDUCTIVITY RE, SIGMA RE, SIG RE, sigmaRE[S/m] / 实部电导率
   - Imaginary Conductivity: CONDUCTIVITY IM, SIGMA IM, SIG IM, sigmaIM[S/m] / 虚部电导率

5. Validation Rules / 验证规则:
   - All related lists must have equal lengths / 所有相关列表必须具有相等的长度
     Example / 示例: len(selectlist) = len(prodataname) = len(prodata) = 5
   - All DataFrames in a list must have same row count / 列表中所有DataFrame必须具有相同的行数
     Example / 示例: All DataFrames have 200 rows / 所有DataFrame都有200行
   - All DataFrames in a list must have same column count / 列表中所有DataFrame必须具有相同的列数
     Example / 示例: All DataFrames have 5 columns / 所有DataFrame都有5列
   - Processing data and reference data must have compatible dimensions / 处理数据和参考数据必须具有兼容的维度

"""

from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFormLayout
from PySide6.QtCore import Qt
import numpy as np
import pandas as pd

from EIS.FigureFile.Error_stat import calculate_relative_errors,calculate_statistical_indicators,calculate_single_dataset_statistics
from EIS.FigureFile.Plotfun import plot_multi_dataset_results, plot_single_dataset_results
from EIS.Other.standard_parameter import paraNaCl,paraWater,paraNaCl01,paraEthanol

class ParameterInputDialog(QDialog):
    """参数输入对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("介电参数参数设置")
        self.setModal(True)
        self.resize(300, 250)
        
        # 创建布局
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 创建输入控件
        self.ramin_edit = QLineEdit("6")  # log10(1e6) = 6, 对应1MHz
        self.ramax_edit = QLineEdit("9.3")  # log10(2e9) ≈ 9.3, 对应2GHz
        self.stnum_edit = QLineEdit("200")
        self.temperature_edit = QLineEdit("25")
        self.concentration_edit = QLineEdit("0.1")
        
        # 溶液类型选择
        self.solution_combo = QComboBox()
        self.solution_combo.addItems(["water", "NaCl", "Ethanol"])
        self.solution_combo.setCurrentText("NaCl")
        
        # 添加到表单布局
        form_layout.addRow("溶液类型:", self.solution_combo)
        form_layout.addRow("浓度 (mol/L):", self.concentration_edit)
        form_layout.addRow("温度 (°C):", self.temperature_edit)
        form_layout.addRow("频率范围最小值 (ramin, log10值):", self.ramin_edit)
        form_layout.addRow("频率范围最大值 (ramax, log10值):", self.ramax_edit)
        form_layout.addRow("数据点数 (stnum):", self.stnum_edit)
        layout.addLayout(form_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def get_parameters(self):
        """获取输入的参数"""
        try:
            return {
                'ramin': float(self.ramin_edit.text()),
                'ramax': float(self.ramax_edit.text()),
                'stnum': int(self.stnum_edit.text()),
                'temperature': float(self.temperature_edit.text()),
                'concentration': float(self.concentration_edit.text()),
                'solution_type': self.solution_combo.currentText()
            }
        except ValueError:
            return None


def userdefine1(self):#####生成标准数据
    print(self.plotdata)
    print(self.outputlist)
    print(self.plotdataname)
    print(self.message)

    # 弹出参数输入对话框
    dialog = ParameterInputDialog(self)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return  # 用户取消了对话框
    
    # 获取用户输入的参数
    params = dialog.get_parameters()
    if params is None:
        QMessageBox.warning(self, "错误", "参数输入格式错误，请检查输入值！")
        return
    
    ramin = params['ramin']
    ramax = params['ramax']
    stnum = params['stnum']
    temperature = params['temperature']
    concentration = params['concentration']
    solution_type = params['solution_type']
    
    # print(f"用户选择的参数: ramin={ramin}, ramax={ramax}, stnum={stnum}, temperature={temperature}, concentration={concentration}, solution_type={solution_type}")
    
    # 生成频率范围和角频率
    # ramin=6对应1MHz (10^6 Hz), ramax=9.3对应约2GHz (2×10^9 Hz)
    freq = np.logspace(ramin, ramax, num=stnum)
    omega = list(2*np.pi*freq)
    
    # 根据选择的溶液类型计算eps和sigma
    try:
        if solution_type == "water":
            eps_complex, sigma_complex = paraWater(omega)
            data_name = f'Water_{temperature}C'
        elif solution_type == "NaCl":
            eps_complex, sigma_complex = paraNaCl(omega, temperature, concentration)
            data_name = f'NaCl_{concentration}M_{temperature}C'
        elif solution_type == "Ethanol":
            eps_complex, sigma_complex = paraEthanol(omega)
            data_name = f'Ethanol_{temperature}C'
        else:
            QMessageBox.warning(self, "错误", f"不支持的溶液类型: {solution_type}")
            return
        
        # 将复数数据分离为实部和虚部
        eps_real = np.real(eps_complex)  # 介电常数实部 ε'
        eps_imag = np.imag(eps_complex)  # 介电常数虚部 ε''
        sigma_real = np.real(sigma_complex)  # 电导率实部 σ'
        sigma_imag = np.imag(sigma_complex)  # 电导率虚部 σ''
        
        # 创建DataFrame
        solution_data = pd.DataFrame({
            'FREQ[Hz]': freq,
            'EPS RE[-]': eps_real,
            'EPS IM[-]': eps_imag,
            'SIGMA RE[S/m]': sigma_real,
            'SIGMA IM[S/m]': sigma_imag
        })
        
        # 准备绘图参数
        outputlist = [1]  # 选择绘制第一个数据集
        dataname = [data_name]  # 数据名称
        data = [solution_data]  # 数据列表
        
        # 更新类属性
        self.plotdata = data
        self.plotdataname = dataname
        self.outputlist = outputlist
                
        QMessageBox.information(self, "成功", f"成功生成 {solution_type} 溶液的介电参数数据！\n数据点数: {len(solution_data)}\n频率范围: {freq[0]:.2e} - {freq[-1]:.2e} Hz")
        
    except Exception as e:
        print(f"计算过程中出现错误: {e}")
        QMessageBox.critical(self, "错误", f"计算过程中出现错误: {str(e)}")
    
    return











def userdefine2(self):
    print(self.plotdata)
    print(self.outputlist)
    print(self.plotdataname)
    print(self.message)
    # 创建模拟数据
    x = np.logspace(start=0, stop=10, num=5, base=10)  # 生成5个对数分布的点
    y = [2, 3, 5, 7, 11]
    data = [pd.DataFrame({
        'Time': x,
        'Value': y,
        'Other1': [1, 4, 6, 8, 10],
        'Other2': [1.5, 2.5, 3.5, 4.5, 5.5],
        'Other3': [1.5, 2.5, 3.5, 4.5, 5.5],
        'Other4': [1.5, 2.5, 3.5, 4.5, 5.5]
    })]
    self.mpl.plotZall([1], ['DataName'], data)
    return




def _reset_figure_state(self):
    """
    彻底清理 figure 残留状态:
    - 移除所有 axes
    - clf() 清空 figure
    - 重置 layout engine,防止 constrained_layout/tight_layout 把单 subplot 切成多列
    - draw_idle() + flush_events() 强制刷新 UI
    - 删除 Plotfun 在 MplCanvas 上可能残留的 axes 引用(axRs/axNyquist/...),
      防止下次绘图复用旧的 stale 坐标轴
    """
    fig = self.mpl.fig
    for ax in list(fig.axes):
        ax.remove()
    fig.clf()
    try:
        fig.set_layout_engine('none')
    except Exception:
        pass
    self.mpl.draw_idle()
    try:
        self.mpl.flush_events()
    except Exception:
        pass
    for stale_attr in ('axRs', 'axbodeX', 'axPhy', 'axNyquist',
                       'axEps', 'axSigma', 'axColeCole', 'axTheta',
                       'axEpsIM', 'axSigmaIM'):
        if hasattr(self.mpl, stale_attr):
            try:
                delattr(self.mpl, stale_attr)
            except Exception:
                pass


def _iter_processed_synthetic(self):
    """
    遍历 plotdata 中的有效条目,跳过 original 配对,
    只保留 processed synthetic(避免原始曲线与处理曲线完全重叠)。
    注意:不按 id() 去重,同一对的 original 与 synthetic 是不同的 DataFrame 对象,
    仅靠 self.message[i]['synthetic'] 即可完成筛选。
    """
    for i, data in enumerate(self.plotdata):
        if data is None:
            continue
        info = self.message[i] if i < len(self.message) else {}
        is_synthetic = isinstance(info, dict) and info.get('synthetic', False)
        if not is_synthetic:
            continue
        yield data, self.plotdataname[i], self.outputlist[i]


def userdefine3(self):
    """数据处理方法1：数据平滑处理和异常值检测"""
    if not self.plotdata or not self.outputlist:
        QMessageBox.warning(self, "Warning", "No data available for processing!")
        return

    print("=== UserDefine3: Data Smoothing & Outlier Detection ===")
    print(f"Original data count: {len(self.plotdata)}")
    print(f"Selected data: {self.outputlist}")
    print(f"Data names: {self.plotdataname}")

    try:
        # 创建处理后的数据列表
        processed_data = []
        processed_names = []
        processed_selection = []

        for data, name, selected in _iter_processed_synthetic(self):
            if selected != 1:
                continue

            colnames = list(data.columns)
            processed_df = data.copy()

            # 方法1：移动平均平滑处理
            window_size = min(5, len(data))  # 窗口大小不超过数据长度
            if len(colnames) > 1:
                for col in colnames[1:]:  # 跳过第一列（通常是频率）
                    if processed_df[col].dtype in ['float64', 'int64']:
                        processed_df[col] = processed_df[col].rolling(
                            window=window_size, center=True, min_periods=1
                        ).mean()

            # 异常值检测和处理（使用IQR方法）
            for col in colnames[1:]:
                if processed_df[col].dtype in ['float64', 'int64']:
                    Q1 = processed_df[col].quantile(0.25)
                    Q3 = processed_df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    processed_df[col] = processed_df[col].clip(lower_bound, upper_bound)

            processed_data.append(processed_df)
            processed_names.append(f"{name}_Smoothed")
            processed_selection.append(1)

            print(f"Processed: {name} -> {name}_Smoothed")

        if processed_data:
            _reset_figure_state(self)

            data_type = self.figuregui.datatypeComboBox.currentText()

            if data_type == 'f-Z,Phase,Re(Z),Im(Z)':
                self.mpl.plotNyquist(processed_selection, processed_names, processed_data, 111)
            elif data_type == 'f-Epsilon,Sigma':
                self.mpl.plotColeCole(processed_selection, processed_names, processed_data, 111)
            else:
                self.mpl.plotNormal(processed_selection, processed_names, processed_data, 111)

            print("Data smoothing and outlier detection completed!")
            QMessageBox.information(self, "Success",
                f"Data processing completed!\nProcessed {len(processed_data)} datasets with smoothing and outlier detection.")
        else:
            QMessageBox.warning(self, "Warning", "No valid data selected for processing!")

    except Exception as e:
        print(f"Error in userdefine3: {e}")
        QMessageBox.critical(self, "Error", f"Data processing failed: {str(e)}")

    return


def userdefine4(self):
    """数据处理方法2：数据归一化和频率范围筛选"""

    if not self.plotdata or not self.outputlist:
        QMessageBox.warning(self, "Warning", "No data available for processing!")
        return

    print("=== UserDefine4: Data Normalization & Frequency Filtering ===")
    print(f"Original data count: {len(self.plotdata)}")
    print(f"Selected data: {self.outputlist}")
    print(f"Data names: {self.plotdataname}")

    try:
        # 创建处理后的数据列表
        processed_data = []
        processed_names = []
        processed_selection = []

        # 频率筛选范围改按每个数据集实际上下界自适应取值,
        # 避免与 1MHz~3GHz 的实际数据范围错位导致筛选后无数据
        FREQ_MARGIN = 0.05  # 上下界各留 5% 边距

        for data, name, selected in _iter_processed_synthetic(self):
            if selected != 1:
                continue

            colnames = list(data.columns)
            processed_df = data.copy()

            # 方法2a：按数据集自适应频率范围筛选
            freq_col = colnames[0] if len(colnames) > 0 else None
            if freq_col is not None and freq_col in processed_df.columns and len(processed_df) > 0:
                fmin = float(processed_df[freq_col].min())
                fmax = float(processed_df[freq_col].max())
                if fmax > fmin:
                    freq_min = fmin * (1.0 - FREQ_MARGIN)
                    freq_max = fmax * (1.0 + FREQ_MARGIN)
                    freq_mask = (processed_df[freq_col] >= freq_min) & (processed_df[freq_col] <= freq_max)
                    processed_df = processed_df[freq_mask].reset_index(drop=True)

            # 方法2b：数据归一化（Min-Max归一化）
            for col in colnames[1:]:  # 跳过频率列
                if processed_df[col].dtype in ['float64', 'int64'] and len(processed_df) > 0:
                    col_min = processed_df[col].min()
                    col_max = processed_df[col].max()
                    if col_max != col_min:  # 避免除零
                        processed_df[col] = (processed_df[col] - col_min) / (col_max - col_min)
                    else:
                        processed_df[col] = 0  # 所有值相同时归一化结果置 0

            if len(processed_df) > 0:  # 确保筛选后还有数据
                processed_data.append(processed_df)
                processed_names.append(f"{name}_Normalized")
                processed_selection.append(1)

                print(f"Processed: {name} -> {name}_Normalized (Points: {len(processed_df)})")

        if processed_data:
            _reset_figure_state(self)

            data_type = self.figuregui.datatypeComboBox.currentText()

            if data_type == 'f-Z,Phase,Re(Z),Im(Z)':
                self.mpl.plotRs(processed_selection, processed_names, processed_data, 111)
            elif data_type == 'f-Epsilon,Sigma':
                self.mpl.plotEps(processed_selection, processed_names, processed_data, 111)
            else:
                self.mpl.plotNormal(processed_selection, processed_names, processed_data, 111)

            print("Data normalization and frequency filtering completed!")
            QMessageBox.information(self, "Success",
                f"Data processing completed!\nProcessed {len(processed_data)} datasets with normalization and frequency filtering.")
        else:
            QMessageBox.warning(self, "Warning", "No valid data remained after frequency filtering!")

    except Exception as e:
        print(f"Error in userdefine4: {e}")
        QMessageBox.critical(self, "Error", f"Data processing failed: {str(e)}")

    return


def userdefine5(self):
    """数据误差计算：多数据集相对误差分析或单数据集内部统计误差"""
    
    if not self.plotdata or not self.outputlist:
        QMessageBox.warning(self, "Warning", "No data available for processing!")
        return
        
    print("=== UserDefine5: 数据误差计算和统计分析 ===")
    print(f"数据总数: {len(self.plotdata)}")
    print(f"选中数据: {self.outputlist}")
    print(f"数据名称: {self.plotdataname}")
    
    try:
        # 获取选中的数据索引
        selected_indices = [i for i, selected in enumerate(self.outputlist) if selected == 1]
        
        if len(selected_indices) == 0:
            QMessageBox.warning(self, "Warning", "No data selected!")
            return
        
        if len(selected_indices) > 1:
            # 多数据集情况：以第一个数据为基准计算相对误差和统计分析
            print("Multi-dataset mode: Relative error analysis and statistical analysis")
            
            # 使用Error_stat.py中的函数计算相对误差
            error_df_list, error_stats = calculate_relative_errors(self.plotdata, self.outputlist, self.plotdataname)
            
            # 使用Error_stat.py中的函数计算统计指标
            stats_list, stats_summary = calculate_statistical_indicators(self.plotdata, self.outputlist, self.plotdataname)
            
            if error_df_list is None and stats_list is None:
                QMessageBox.warning(self, "Warning", "Failed to calculate error analysis!")
                return
            
            # 清除之前的图形
            self.clearfigure()
            
            # 绘制多数据集误差分析结果
            plot_multi_dataset_results(self, error_df_list, stats_list, error_stats, stats_summary)
            
            print("Multi-dataset error analysis completed!")
            QMessageBox.information(self, "Success", 
                f"Multi-dataset error analysis completed!\nProcessed {len(selected_indices)} datasets.")
            
        else:
            # 单数据集情况：计算内部统计误差
            print("Single dataset mode: Internal statistical error analysis")
            
            # 使用Error_stat.py中的函数计算单数据集统计
            stats_dfs_list, single_stats_summary = calculate_single_dataset_statistics(
                self.plotdata, self.outputlist, self.plotdataname
            )
            
            if stats_dfs_list is None:
                QMessageBox.warning(self, "Warning", "Invalid dataset or insufficient data points!")
                return
            
            # 清除之前的图形
            self.clearfigure()
            
            # 绘制单数据集统计分析结果
            plot_single_dataset_results(self, stats_dfs_list, single_stats_summary, self.plotdataname[selected_indices[0]])
            
            print("Single dataset statistical analysis completed!")
            QMessageBox.information(self, "Success", 
                f"Single dataset statistical analysis completed!\nAnalyzed dataset: {self.plotdataname[selected_indices[0]]}")
            
    except Exception as e:
        print(f"Error in userdefine5: {e}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(self, "Error", f"Error calculation failed: {str(e)}")
    
    return




