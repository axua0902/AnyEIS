# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 10:45:26 2020

@author: zhang
"""


import os
import sys


import pandas as pd
from pandas import Series,DataFrame
from numpy import real,imag,angle,absolute,pi,log,sqrt,tanh,arctanh,array
import numpy as np
from scipy import signal

import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Other'))
from Datacheck import resolve_column, check5  # [TP-004] 列名兼容容差 / [TP-005] 数据类型识别


##############constant##############
eps0=8.854187817e-12 #F/m Vacuum permittivity
mu0=4*pi*1e-7# H/m  Permeability
##############constant##############


def _is_eis_data(dataframe):
    """检测是否为EIS数据（包含频率、实部、虚部）"""
    columns = dataframe.columns.tolist()
    if len(columns) < 3:
        return False
    
    # 检查列名是否包含EIS数据的典型特征
    freq_keywords = ['FREQ', 'freq', 'Hz', 'frequency']
    real_keywords = ['Z[ohm]', 'ZRE', 'Real', 'Re', 'real']
    imag_keywords = ['PHASE', 'ZIM', 'Imag', 'Im', 'imag', 'deg']
    
    has_freq = any(keyword in columns[0] for keyword in freq_keywords)
    has_real = any(keyword in columns[1] for keyword in real_keywords)
    has_imag = any(keyword in columns[2] for keyword in imag_keywords)
    
    return has_freq and (has_real or has_imag)


def _apply_filter_unified(prodata, filter_func, filter_name, **kwargs):
    """统一的滤波处理函数"""
    resultsdata = list()
    
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            ZRE = filter_func(ZRE, **kwargs)
            ZIM = filter_func(ZIM, **kwargs)
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                colume = filter_func(colume, **kwargs)
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)
    
    print(f'{filter_name} Processed')
    return resultsdata


def savgol(prodata, parameter):
    """Savitzky-Golay滤波 - 统一处理EIS数据和一般数据"""
    a = int(parameter['a'])
    b = int(parameter['b'])
    resultsdata = list()
    
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        
        # 检查是否为EIS数据（包含实部和虚部）
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            ZRE = signal.savgol_filter(ZRE, a, b)
            ZIM = signal.savgol_filter(ZIM, a, b)
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                colume = signal.savgol_filter(colume, a, b)
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)

    print('Savgol Processed')
    return resultsdata
            



def median(prodata, parameter):
    """中值滤波 - 统一处理EIS数据和一般数据"""
    kernel_size = int(parameter['kernel_size'])
    resultsdata = list()
    
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        
        # 检查是否为EIS数据
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            ZRE = signal.medfilt(ZRE, kernel_size=kernel_size)
            ZIM = signal.medfilt(ZIM, kernel_size=kernel_size)
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                colume = signal.medfilt(colume, kernel_size=kernel_size)
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)

    print('Median Filter Processed')
    return resultsdata


def wiener(prodata, parameter):
    """Wiener滤波 - 统一处理EIS数据和一般数据"""
    noise = parameter.get('noise', None)
    resultsdata = list()
    
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            ZRE = signal.wiener(ZRE, noise=noise)
            ZIM = signal.wiener(ZIM, noise=noise)
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                colume = signal.wiener(colume, noise=noise)
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)

    print('Wiener Filter Processed')
    return resultsdata


def butterworth(prodata, parameter):
    """Butterworth滤波器 - 统一处理EIS数据和一般数据"""
    order = int(parameter['order'])
    cutoff = float(parameter['cutoff'])
    filter_type = parameter.get('filter_type', 'filtfilt')
    
    resultsdata = list()
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        
        # 设计Butterworth滤波器
        b, a = signal.butter(order, cutoff)
        
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            if filter_type == 'filtfilt':
                ZRE = signal.filtfilt(b, a, ZRE)
                ZIM = signal.filtfilt(b, a, ZIM)
            else:
                ZRE = signal.lfilter(b, a, ZRE)
                ZIM = signal.lfilter(b, a, ZIM)
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                if filter_type == 'filtfilt':
                    colume = signal.filtfilt(b, a, colume)
                else:
                    colume = signal.lfilter(b, a, colume)
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)

    print('Butterworth Filter Processed')
    return resultsdata


def cspline(prodata, parameter):
    """三次样条滤波 - 统一处理EIS数据和一般数据"""
    lamb = float(parameter['lamb'])
    resultsdata = list()
    
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            ZRE = signal.cspline1d(ZRE, lamb=lamb)
            ZIM = signal.cspline1d(ZIM, lamb=lamb)
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                colume = signal.cspline1d(colume, lamb=lamb)
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)

    print('Cubic Spline Filter Processed')
    return resultsdata


def arithmeticAverage(prodata, parameter):
    """算术平均滤波 - 统一处理EIS数据和一般数据"""
    window_size = int(parameter['window_size'])
    resultsdata = list()
    
    for i in range(0, len(prodata)):
        columename = prodata[i].columns.tolist()
        kernel = np.ones(window_size) / window_size
        
        if len(columename) >= 3 and _is_eis_data(prodata[i]):
            # EIS数据处理
            Freq = prodata[i][columename[0]]
            ZRE = prodata[i][columename[1]]
            ZIM = prodata[i][columename[2]]
            
            ZRE = np.convolve(ZRE, kernel, mode='same')
            ZIM = np.convolve(ZIM, kernel, mode='same')
            
            ZMUT = ZRE + 1.j * ZIM
            resu = creatdatabase(Freq, ZMUT)
            resultsdata.append(resu)
        else:
            # 一般数据处理
            data = DataFrame()
            dataColume1 = prodata[i][columename[0]]
            data[columename[0]] = Series(dataColume1)
            for temp in range(1, len(columename)):
                colume = prodata[i][columename[temp]]
                colume = np.convolve(colume, kernel, mode='same')
                data[columename[temp]] = Series(colume)
            resultsdata.append(data)

    print('Arithmetic Average Filter Processed')
    return resultsdata


def slidingAverage(prodata, parameter):
    """递推平均滤波 - 统一处理EIS数据和一般数据"""
    window_size = int(parameter['window_size'])
    
    def sliding_average_filter(data, window_size):
        filtered_data = np.zeros_like(data)
        filtered_data[0] = data[0]
        for j in range(1, len(data)):
            start_idx = max(0, j - window_size + 1)
            current_mean = np.mean(data[start_idx:j+1])
            prev_mean = filtered_data[j-1] if j > 0 else data[0]
            filtered_data[j] = (current_mean + prev_mean) / 2
        return filtered_data
    
    return _apply_filter_unified(prodata, sliding_average_filter, 'Sliding Average Filter', window_size=window_size)


def medianAverage(prodata, parameter):
    """中位值平均滤波 - 统一处理EIS数据和一般数据"""
    window_size = int(parameter['window_size'])
    
    def median_average_filter(data, window_size):
        filtered_data = np.zeros_like(data)
        half_window = window_size // 2
        for j in range(len(data)):
            start_idx = max(0, j - half_window)
            end_idx = min(len(data), j + half_window + 1)
            window_data = data[start_idx:end_idx].copy()
            # 去除最大值和最小值
            if len(window_data) > 2:
                window_data = np.delete(window_data, np.argmax(window_data))
                window_data = np.delete(window_data, np.argmin(window_data))
            filtered_data[j] = np.mean(window_data)
        return filtered_data
    
    return _apply_filter_unified(prodata, median_average_filter, 'Median Average Filter', window_size=window_size)


def amplitudeLimitingAverage(prodata, parameter):
    """限幅平均滤波 - 统一处理EIS数据和一般数据"""
    window_size = int(parameter['window_size'])
    amplitude_limit = float(parameter['amplitude_limit'])
    
    def amplitude_limiting_average_filter(data, window_size, amplitude_limit):
        filtered_data = np.zeros_like(data)
        filtered_data[0] = data[0]
        prev_value = data[0]
        
        for j in range(1, len(data)):
            # 限幅处理
            if abs(data[j] - prev_value) > amplitude_limit:
                limited_value = prev_value
            else:
                limited_value = data[j]
            
            # 窗口平均
            start_idx = max(0, j - window_size + 1)
            window_mean = np.mean(data[start_idx:j+1])
            prev_mean = filtered_data[j-1]
            filtered_data[j] = (window_mean + prev_mean) / 2
            prev_value = limited_value
            
        return filtered_data
    
    return _apply_filter_unified(prodata, amplitude_limiting_average_filter, 'Amplitude Limiting Average Filter', 
                                window_size=window_size, amplitude_limit=amplitude_limit)


def firstOrderLag(prodata, parameter):
    """一阶滞后滤波 - 统一处理EIS数据和一般数据"""
    alpha = float(parameter['alpha'])
    
    def first_order_lag_filter(data, alpha):
        filtered_data = np.zeros_like(data)
        filtered_data[0] = data[0]
        for j in range(1, len(data)):
            filtered_data[j] = (1 - alpha) * data[j] + alpha * filtered_data[j-1]
        return filtered_data
    
    return _apply_filter_unified(prodata, first_order_lag_filter, 'First Order Lag Filter', alpha=alpha)


def weightedAverage(prodata, parameter):
    """加权递推平均滤波 - 统一处理EIS数据和一般数据"""
    window_size = int(parameter['window_size'])
    
    def weighted_average_filter(data, window_size):
        # 创建权重数组，线性递增
        weights = np.arange(1, window_size + 1)
        weights = weights / np.sum(weights)
        
        # 使用numpy.convolve进行加权卷积
        filtered_data = np.convolve(data, weights, mode='same')
        return filtered_data
    
    return _apply_filter_unified(prodata, weighted_average_filter, 'Weighted Average Filter', window_size=window_size)


def shakeOff(prodata, parameter):
    """消抖滤波 - 统一处理EIS数据和一般数据"""
    threshold_count = int(parameter['threshold_count'])
    
    def shake_off_filter(data, threshold_count):
        filtered_data = data.copy()
        valid_value = data[0]
        count = 0
        
        for j in range(1, len(data)):
            if abs(data[j] - valid_value) > np.std(data) * 0.5:  # 使用标准差作为阈值
                count += 1
                if count >= threshold_count:
                    valid_value = data[j]
                    count = 0
                else:
                    filtered_data[j] = valid_value
            else:
                valid_value = data[j]
                count = 0
                
        return filtered_data
    
    return _apply_filter_unified(prodata, shake_off_filter, 'Shake Off Filter', threshold_count=threshold_count)


def amplitudeLimitingShakeOff(prodata, parameter):
    """限幅消抖滤波 - 统一处理EIS数据和一般数据"""
    amplitude_limit = float(parameter['amplitude_limit'])
    threshold_count = int(parameter['threshold_count'])
    
    def amplitude_limiting_shake_off_filter(data, amplitude_limit, threshold_count):
        filtered_data = data.copy()
        prev_value = data[0]
        valid_value = data[0]
        count = 0
        
        # 第一步：限幅处理
        for j in range(1, len(data)):
            if abs(data[j] - prev_value) > amplitude_limit:
                filtered_data[j] = prev_value
            prev_value = filtered_data[j]
        
        # 第二步：消抖处理
        for j in range(1, len(filtered_data)):
            if abs(filtered_data[j] - valid_value) > amplitude_limit * 0.5:
                count += 1
                if count >= threshold_count:
                    valid_value = filtered_data[j]
                    count = 0
                else:
                    filtered_data[j] = valid_value
            else:
                valid_value = filtered_data[j]
                count = 0
                
        return filtered_data
    
    return _apply_filter_unified(prodata, amplitude_limiting_shake_off_filter, 'Amplitude Limiting Shake Off Filter',
                                amplitude_limit=amplitude_limit, threshold_count=threshold_count)


def creatdatabase(freq,Z): #############创建结果数据库   
    data =DataFrame()
    Z=Series(Z)
    data['FREQ[Hz]']=freq
    data['Z[ohm]']=Series(real(Z))
    Phase=Series(angle(Z))
    data['PHASE[deg]']=Series(Phase*180/pi)
    data['Rs[ohm]']=Series(real(Z))
    data['X[ohm]']=Series(imag(Z))

    return data



##############subplot - 多种滤波方法对比#############

def calculate_multi_filter_comparison_data(prodata, prodataname, custom_filters_config=None):
    """计算多种滤波方法的对比数据，只负责数据处理，不进行绘图
    Args:
        prodata: 输入数据(DataFrame 列表)
        prodataname: 数据名列表
        custom_filters_config: 可选,用户从 UI 选择的滤波器配置
            格式: {'MethodName': {'func': callable, 'params': dict, 'color': str}, ...}
            为 None 时使用默认 5 个方法
    """

    print("\n" + "="*60)
    print("CALCULATING MULTI-FILTER COMPARISON DATA")
    print("="*60)

    if len(prodata) == 0:
        print("No data available for calculation")
        return None

    # 选择第一个数据集进行展示
    original_data = prodata[0]
    original_name = prodataname[0] if len(prodataname) > 0 else "Original Data"

    # [TP-005] 检测数据类型(EIS / DS)并定义列名候选
    data_type = check5([original_data])
    freq_cands = ['FREQ[Hz]', 'Frequency[Hz]', 'Freq[Hz]', 'FREQ', 'frequency']
    if data_type == 'DS':
        real_cands  = ['epsRE[-]', 'PERMITTIVITY RE', 'EPSILON RE', 'EPS RE',
                       'PERMITTIVITYRE', 'EPSILONRE', 'EPSRE', 'EpsRE[-]', 'epsRE']
        imag_cands  = ['epsIM[-]', 'PERMITTIVITY IM', 'EPSILON IM', 'EPS IM',
                       'PERMITTIVITYIM', 'EPSILONIM', 'EPSIM', 'EpsIM[-]', 'epsIM']
        third_cands = ['sigmaRE[S/m]', 'CONDUCTIVITY RE', 'SIGMA RE', 'SIG RE',
                       'CONDUCTIVITYRE', 'SIGMARE', 'SIGRE', 'sigmaRE']
    else:  # EIS / UNKNOWN
        real_cands  = ['Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'RS[Ω]', 'Rs', 'R']
        imag_cands  = ['X[ohm]', 'X[OHM]', 'X[Ω]', 'X[Ω]', 'X']
        third_cands = ['PHASE[deg]', 'Phase[deg]', 'PHASE[DEG]', 'PHASE', 'ph', 'Phase']

    # 定义要对比的滤波器及其参数
    # [TP-006] 优先使用用户从 UI 选择的配置,否则使用默认 5 个方法
    if custom_filters_config is not None and len(custom_filters_config) > 0:
        filters_config = custom_filters_config
        print(f"Using {len(filters_config)} user-selected filters: {list(filters_config.keys())}")
    else:
        filters_config = {
            'Savitzky-Golay': {'func': savgol, 'params': {'a': '11', 'b': '1'}, 'color': 'red'},
            'Median': {'func': median, 'params': {'kernel_size': '5'}, 'color': 'green'},
            'Butterworth': {'func': butterworth, 'params': {'order': '2', 'cutoff': '0.1', 'filter_type': 'filtfilt'}, 'color': 'orange'},
            'Arithmetic Avg': {'func': arithmeticAverage, 'params': {'window_size': '5'}, 'color': 'purple'},
            'Sliding Avg': {'func': slidingAverage, 'params': {'window_size': '7'}, 'color': 'brown'}
        }

    # 应用所有滤波器
    print("Applying filters for comparison...")
    filtered_results = {}
    filter_stats = {}

    for filter_name, config in filters_config.items():
        try:
            print(f"  - Applying {filter_name} filter...")
            result = config['func']([original_data], config['params'])
            filtered_results[filter_name] = result[0]

            # 解析列名 — 使用容差支持不同列名写法 + 支持 DS 数据
            # [TP-004] 解决 KeyError: 'Rs[ohm]' 类问题 / [TP-005] 支持 DS
            orig_freq   = resolve_column(original_data, freq_cands)
            orig_real   = resolve_column(original_data, real_cands)
            orig_imag   = resolve_column(original_data, imag_cands)
            orig_third  = resolve_column(original_data, third_cands)  # 可选
            filt_freq   = resolve_column(result[0], freq_cands)  or orig_freq
            filt_real   = resolve_column(result[0], real_cands)  or orig_real
            filt_imag   = resolve_column(result[0], imag_cands)  or orig_imag
            filt_third  = resolve_column(result[0], third_cands) or orig_third

            if not all([orig_freq, orig_real, orig_imag]):
                missing = [n for n, c in (('FREQ', orig_freq), ('real', orig_real),
                                          ('imag', orig_imag)) if c is None]
                raise KeyError(f"original_data 缺少列: {missing} (实际列: {list(original_data.columns)})")
            if not all([filt_freq, filt_real, filt_imag]):
                missing = [n for n, c in (('FREQ', filt_freq), ('real', filt_real),
                                          ('imag', filt_imag)) if c is None]
                raise KeyError(f"filtered_data 缺少列: {missing} (实际列: {list(result[0].columns)})")

            # 计算统计信息(统一使用 real/imag/third 命名,统计量键名保留 Rs/X/Phase 兼容旧版图)
            real_orig = original_data[orig_real]
            imag_orig = original_data[orig_imag]
            real_filt = result[0][filt_real]
            imag_filt = result[0][filt_imag]

            def _safe_pct(a, b):
                sa = np.std(a)
                return (sa - np.std(b)) / sa * 100 if sa > 0 else 0.0

            noise_reduction_Rs    = _safe_pct(real_orig, real_filt)
            noise_reduction_X     = _safe_pct(imag_orig, imag_filt)
            if orig_third and filt_third:
                third_orig = original_data[orig_third]
                third_filt = result[0][filt_third]
                noise_reduction_Phase = _safe_pct(third_orig, third_filt)
                correlation_Phase = float(np.corrcoef(third_orig, third_filt)[0, 1])
            else:
                noise_reduction_Phase = 0.0
                correlation_Phase = 0.0

            # 计算信号保真度 (相关系数)
            correlation_Rs = float(np.corrcoef(real_orig, real_filt)[0, 1])
            correlation_X  = float(np.corrcoef(imag_orig, imag_filt)[0, 1])

            filter_stats[filter_name] = {
                'noise_reduction': {
                    'Rs': noise_reduction_Rs,
                    'X': noise_reduction_X,
                    'Phase': noise_reduction_Phase
                },
                'correlation': {
                    'Rs': correlation_Rs,
                    'X': correlation_X,
                    'Phase': correlation_Phase
                },
                'color': config['color']
            }

        except Exception as e:
            print(f"  - Error applying {filter_name}: {e}")
            continue
    
    # 计算综合性能评分
    performance_scores = {}
    for name in filter_stats.keys():  # 只处理成功应用的滤波器
        # 综合评分 = 噪声减少效果 + 信号保真度
        noise_score = (filter_stats[name]['noise_reduction']['Rs'] + 
                      filter_stats[name]['noise_reduction']['X']) / 2
        fidelity_score = ((filter_stats[name]['correlation']['Rs'] + 
                          filter_stats[name]['correlation']['X'] + 
                          filter_stats[name]['correlation']['Phase']) / 3 - 0.9) * 1000  # 放大相关性差异
        
        performance_scores[name] = {
            'noise_reduction': max(0, noise_score),  # 确保非负
            'fidelity': max(0, fidelity_score),
            'overall': max(0, noise_score) + max(0, fidelity_score)
        }
    
    # 返回所有计算结果
    return {
        'original_data': original_data,
        'original_name': original_name,
        'filtered_results': filtered_results,
        'filter_stats': filter_stats,
        'filters_config': filters_config,
        'performance_scores': performance_scores,
        # [TP-005] 透传数据类型与列名映射给绘图层
        'data_type': data_type,
        'column_map': {
            'freq':  orig_freq,
            'real':  orig_real,
            'imag':  orig_imag,
            'third': orig_third,
        },
    }

##############subplot - 原始单个滤波结果对比#############


















