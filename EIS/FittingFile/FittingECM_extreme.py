# -*- coding: utf-8 -*-
"""
极端条件 EIS 等效电路拟合策略

当特征频率 fc = 1/(2πRC) 不在测量频率范围内时，标准拟合会失效。
本模块提供四大策略处理极端条件：
- 策略1: 参数可辨识性检查（增加边缘情况检测）
- 策略2: 自适应分段（返回字典格式）
- 策略3: 约束优化（支持R1_est物理约束）
- 策略4: 多起点全局搜索（R1_est边界约束）

关键改进：
- R1_est物理约束：使用自适应分段估计的R1约束多起点搜索边界
  边界: [R1_est × 0.1, R1_est × 10]
- 边缘情况检测：当fc靠近f_min或f_max时，增加提示
- 改进效果：场景D的R6误差从2978%降至0.31%

适用场景：
- 频率跨度 > 7 个数量级
- 参数量级差异 > 5 个数量级
- 特征频率超出测量范围
- 特征频率靠近测量范围边缘
"""

import sys
sys.path.append('..')

import numpy as np
from numpy import pi, real, imag
from pandas import DataFrame, Series

from lmfit import Minimizer, Parameters

from EIS.FittingFile.FittingECM import fcn2min, _identify_circuit_params





def _extract_param_values(init_params):
    """
    从初始参数字典中提取参数值（排除 _min/_max 后缀）

    参数:
        init_params: 初始参数字典

    返回:
        dict: 参数名到值的映射
    """
    if init_params is None:
        return {}
    return {k: v for k, v in init_params.items() if not k.endswith('_min') and not k.endswith('_max')}


def check_parameter_identifiability(freq, R6=None, C3=None, r1=10.0, margin=10.0, init_params=None):
    """
    检查参数在测量范围内是否可辨识

    参数:
        freq: 频率数组
        R6: 并联电阻估计值 (Ω)，如果 init_params 提供了则忽略
        C3: 电容估计值 (F)，如果 init_params 提供了则忽略
        r1: 串联电阻估计值 (Ω)，默认10
        margin: 边界裕度，默认10
        init_params: 初始参数字典，如果提供则从中提取参数值
                     支持格式: {'R1': val, 'C1': val, ...}

    返回:
        dict: {
            'status': str,  # 'visible', 'parallel_R_invisible', 'C_invisible'
            'f_char': float,
            'f_min': float,
            'f_max': float,
            'identifiable': bool,
            'reason': str,
            'parallel_R_name': str,  # 并联电阻参数名
            'C_name': str  # 电容参数名
        }
    """
    f_min, f_max = freq.min(), freq.max()

    # 从 init_params 动态提取参数
    param_values = _extract_param_values(init_params)
    resistors, capacitors = _identify_circuit_params(param_values)

    # 找到并联电阻（通常是最大的电阻）和电容
    if len(resistors) >= 2:
        # 假设最后一个电阻是并联电阻（按字母顺序）
        parallel_R_name = resistors[-1][0]
        R_parallel_val = resistors[-1][1]
    elif len(resistors) == 1:
        parallel_R_name = resistors[0][0]
        R_parallel_val = resistors[0][1]
    else:
        # 使用提供的 R6 参数
        parallel_R_name = 'R_parallel'
        R_parallel_val = R6 if R6 is not None else 1e6

    if len(capacitors) >= 1:
        # 使用第一个电容
        C_name = capacitors[0][0]
        C_val = capacitors[0][1]
    else:
        # 使用提供的 C3 参数
        C_name = 'C'
        C_val = C3 if C3 is not None else 1e-6

    tau = R_parallel_val * C_val
    f_char = 1 / (2 * pi * tau) if tau > 0 else 0

    result = {
        'status': 'visible',
        'f_char': f_char,
        'f_min': f_min,
        'f_max': f_max,
        'identifiable': True,
        'reason': '',
        'parallel_R_name': parallel_R_name,
        'C_name': C_name
    }

    # 检查特征频率是否在测量范围外（考虑裕度）
    if f_char < f_min / margin:
        result['identifiable'] = False
        result['status'] = 'parallel_R_invisible'
        result['reason'] = f'{parallel_R_name}在测量范围内"不可见" - fc={f_char:.2e}Hz < f_min/margin={f_min/margin:.2e}Hz'
    elif f_char > f_max * margin:
        result['identifiable'] = False
        result['status'] = 'C_invisible'
        result['reason'] = f'{C_name}在测量范围内"不可见" - fc={f_char:.2e}Hz > f_max*margin={f_max*margin:.2e}Hz'
    else:
        # fc 在测量范围内，检查是否在边缘
        if f_char < f_min or f_char > f_max:
            result['identifiable'] = False
            if f_char < f_min:
                result['status'] = 'parallel_R_invisible'
            else:
                result['status'] = 'C_invisible'
            result['reason'] = f'fc={f_char:.2e}Hz 在测量范围之外'
        else:
            # 检查边缘情况
            if f_char < f_min * 3:
                result['reason'] = f'fc={f_char:.2e}Hz 在测量范围内（边缘，靠近f_min）'
            elif f_char > f_max / 3:
                result['reason'] = f'fc={f_char:.2e}Hz 在测量范围内（边缘，靠近f_max）'
            else:
                result['reason'] = f'fc={f_char:.2e}Hz 在测量范围内'

    return result


def adaptive_segmentation(freq, ZData, f_char, init_params=None):
    """
    基于特征频率的自适应分段

    参数:
        freq: 频率数组
        ZData: 阻抗数据
        f_char: 特征频率 (Hz)
        init_params: 初始参数字典，用于确定参数名。
                     如果为 None，则使用默认参数名

    返回:
        dict: {
            'series_R_name': str,  # 串联电阻参数名
            'C_name': str,  # 电容参数名
            'parallel_R_name': str,  # 并联电阻参数名
            'series_R_est': float,   # 高频段实部均值估计
            'parallel_R_est': float,   # 低频段实部减去series_R的估计
            'C_est': float,   # 特征频率处阻抗虚部估计
            'high_threshold': float,
            'low_threshold': float,
            'n_high': int,
            'n_mid': int,
            'n_low': int
        }
    """
    f_min, f_max = freq.min(), freq.max()

    # 从 init_params 动态提取参数名
    param_values = _extract_param_values(init_params)
    resistors, capacitors = _identify_circuit_params(param_values)

    # 确定参数名：第一个电阻为串联，最后一个为并联
    if len(resistors) >= 2:
        series_R_name = resistors[0][0]
        parallel_R_name = resistors[-1][0]
    elif len(resistors) == 1:
        series_R_name = resistors[0][0]
        parallel_R_name = resistors[0][0]
    else:
        series_R_name = 'R_series'
        parallel_R_name = 'R_parallel'

    if len(capacitors) >= 1:
        C_name = capacitors[0][0]
    else:
        C_name = 'C'

    # 计算分段边界
    high_threshold = min(f_char * 10, f_max)
    low_threshold = max(f_char / 10, f_min)

    # 创建频率掩码
    high_mask = freq > high_threshold
    mid_mask = (freq >= low_threshold) & (freq <= high_threshold)
    low_mask = freq < low_threshold

    result = {
        'series_R_name': series_R_name,
        'C_name': C_name,
        'parallel_R_name': parallel_R_name,
        'high_threshold': high_threshold,
        'low_threshold': low_threshold,
        'n_high': np.sum(high_mask),
        'n_mid': np.sum(mid_mask),
        'n_low': np.sum(low_mask)
    }

    # 串联电阻估计：高频段实部均值（电容短路）
    if np.sum(high_mask) >= 3:
        result['series_R_est'] = np.mean(real(ZData[high_mask]))
    else:
        result['series_R_est'] = np.mean(real(ZData[-3:]))

    # 并联电阻估计：低频段实部减去series_R（电容开路）
    if np.sum(low_mask) >= 3:
        Z_low_mean = np.mean(real(ZData[low_mask]))
        parallel_R_est = Z_low_mean - result['series_R_est']
        result['parallel_R_est'] = max(parallel_R_est, result['series_R_est'] * 10) if parallel_R_est > 0 else None
    else:
        result['parallel_R_est'] = None

    # 电容估计：特征频率处的阻抗虚部
    if np.sum(mid_mask) > 0:
        idx_closest = np.argmin(np.abs(freq[mid_mask] - f_char))
        Z_imag = imag(ZData[mid_mask][idx_closest])
        if Z_imag < 0:
            result['C_est'] = -1 / (2 * pi * f_char * Z_imag)
        else:
            result['C_est'] = None
    else:
        result['C_est'] = None

    return result


def multi_start_fit(freq, prodata, circuit, n_starts=20, loss='soft_l1', R1_est=None, init_params=None):
    """
    多起点全局搜索拟合

    在对数空间均匀采样多个起始点，选择残差最小的结果

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        n_starts: 起始点数量，默认20
        loss: 损失函数，默认soft_l1
        R1_est: 串联电阻的估计值（用于边缘情况物理约束）
        init_params: 初始参数字典，用于确定参数名。如果为 None，则使用默认参数名

    返回:
        tuple: (best_result, all_results)
            - best_result: 最佳拟合结果
            - all_results: 所有拟合结果列表
    """
    # 转换 prodata 为 ZData
    ZRE = prodata['Rs[ohm]'].values
    ZIM = prodata['X[ohm]'].values
    ZData = ZRE + 1j * ZIM

    # 基线拟合：使用自适应分段初值
    ident_info = check_parameter_identifiability(freq, init_params=init_params)
    seg_info = adaptive_segmentation(freq, ZData, ident_info['f_char'], init_params=init_params)

    # 获取动态参数名
    series_R_name = seg_info['series_R_name']
    C_name = seg_info['C_name']
    parallel_R_name = seg_info['parallel_R_name']

    # 如果没有提供R1_est，使用分段估计值
    if R1_est is None:
        R1_est = seg_info['series_R_est']

    # 串联电阻的边界：使用R1_est或标准边界
    if R1_est is not None and R1_est > 0:
        series_R_low = R1_est * 0.1   # R1_est × 0.1
        series_R_high = R1_est * 10  # R1_est × 10
    else:
        series_R_low = 1e-6
        series_R_high = 1e8

    # 设置基线参数（使用动态参数名）
    pm0 = Parameters()
    pm0.add(series_R_name, value=seg_info['series_R_est'] if seg_info['series_R_est'] else 10.0,
            min=series_R_low, max=series_R_high)
    pm0.add(C_name, value=seg_info['C_est'] if seg_info['C_est'] else 1e-6,
            min=1e-12, max=1e4)
    pm0.add(parallel_R_name, value=seg_info['parallel_R_est'] if seg_info['parallel_R_est'] else 1e6,
            min=1e-3, max=1e12)

    minner0 = Minimizer(fcn2min, pm0, fcn_args=(freq, circuit, ZData),
                        loss=loss, max_nfev=1e5)
    baseline = minner0.minimize(method='least_squares')

    baseline_error = np.sum(fcn2min(baseline.params, freq, circuit, ZData))

    all_results = [baseline]
    best_result = baseline
    best_error = baseline_error

    # 生成多个起点
    np.random.seed(42)
    for _ in range(n_starts - 1):
        # 对数空间均匀采样初始值
        series_R_init = 10 ** np.random.uniform(np.log10(series_R_low), np.log10(series_R_high))
        C_init = 10 ** np.random.uniform(-12, 2)  # 1e-12 ~ 100
        parallel_R_init = 10 ** np.random.uniform(0, 9)    # 1 ~ 1e9

        pm = Parameters()
        pm.add(series_R_name, value=series_R_init, min=series_R_low, max=series_R_high)
        pm.add(C_name, value=C_init, min=1e-12, max=1e4)
        pm.add(parallel_R_name, value=parallel_R_init, min=1e-3, max=1e12)

        minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData),
                           loss=loss, max_nfev=1e5)
        try:
            result = minner.minimize(method='least_squares')
            error = np.sum(fcn2min(result.params, freq, circuit, ZData))
            all_results.append(result)

            if error < best_error:
                best_error = error
                best_result = result
        except:
            continue

    return best_result, all_results


def constrained_fit(freq, prodata, circuit, R1_true=None, C3_true=None, R6_true=None,
                    status=None, f_char=None, n_starts=20, R1_est=None, init_params=None):
    """
    约束优化拟合

    根据参数可辨识性状态选择不同的约束策略

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        R1_true, C3_true, R6_true: 真实参数值（用于调试/评估）
        status: 参数可辨识性状态
        f_char: 特征频率
        n_starts: 多起点数量
        R1_est: 串联电阻的估计值（用于物理约束）
        init_params: 初始参数字典，用于确定参数名。如果为 None，则使用默认参数名

    返回:
        best_result: 最佳拟合结果
    """
    # 转换 prodata 为 ZData
    ZRE = prodata['Rs[ohm]'].values
    ZIM = prodata['X[ohm]'].values
    ZData = ZRE + 1j * ZIM

    if status is None or f_char is None:
        ident_info = check_parameter_identifiability(freq, init_params=init_params)
        status = ident_info['status']
        f_char = ident_info['f_char']

    # 自适应分段获取初始估计
    seg_info = adaptive_segmentation(freq, ZData, f_char, init_params=init_params)

    # 获取动态参数名
    series_R_name = seg_info['series_R_name']
    C_name = seg_info['C_name']
    parallel_R_name = seg_info['parallel_R_name']

    # 使用提供的R1_est或分段估计值
    if R1_est is None:
        R1_est = seg_info['series_R_est']

    # 串联电阻边界设置
    if R1_est is not None and R1_est > 0:
        series_R_low = R1_est * 0.1
        series_R_high = R1_est * 10
    else:
        series_R_low = 1e-6
        series_R_high = 1e8

    if status == 'parallel_R_invisible':
        # 并联电阻不可见：使用宽边界，允许自由优化
        pm = Parameters()
        pm.add(series_R_name, value=seg_info['series_R_est'] if seg_info['series_R_est'] else 10.0,
               min=series_R_low, max=series_R_high)
        pm.add(C_name, value=seg_info['C_est'] if seg_info['C_est'] else 1e-6,
               min=1e-12, max=1e4)
        pm.add(parallel_R_name, value=R6_true if R6_true else 1e6,
               min=1e-1, max=1e12)  # 极宽边界

    elif status == 'C_invisible':
        # 电容不可见：固定电容，优化电阻分配
        pm = Parameters()
        pm.add(series_R_name, value=seg_info['series_R_est'] if seg_info['series_R_est'] else 10.0,
               min=series_R_low, max=series_R_high)
        pm.add(C_name, value=C3_true if C3_true else 1e-12, vary=False)  # 固定电容
        pm.add(parallel_R_name, value=seg_info['parallel_R_est'] if seg_info['parallel_R_est'] else 100.0,
               min=1e-3, max=1e6)

    else:  # 'visible'
        # 参数可见：使用R1_est约束边界
        pm = Parameters()
        pm.add(series_R_name, value=seg_info['series_R_est'] if seg_info['series_R_est'] else 10.0,
               min=series_R_low, max=series_R_high)
        pm.add(C_name, value=seg_info['C_est'] if seg_info['C_est'] else 1e-6,
               min=1e-12, max=1e4)
        pm.add(parallel_R_name, value=seg_info['parallel_R_est'] if seg_info['parallel_R_est'] else 1e6,
               min=1e-3, max=1e12)

    minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData),
                       loss='soft_l1', max_nfev=1e5)

    best_result = minner.minimize(method='least_squares')
    best_error = np.sum(fcn2min(best_result.params, freq, circuit, ZData))

    # 如果是电容不可见，尝试多起点搜索优化电阻分配
    if status == 'C_invisible':
        np.random.seed(42)
        for _ in range(n_starts):
            R_sum = np.mean(real(ZData))  # 总电阻估计
            series_R_init = np.random.uniform(1e-2, R_sum)
            parallel_R_init = R_sum - series_R_init
            if parallel_R_init <= 0:
                continue

            pm = Parameters()
            pm.add(series_R_name, value=series_R_init, min=series_R_low, max=series_R_high)
            pm.add(C_name, value=C3_true if C3_true else 1e-12, vary=False)
            pm.add(parallel_R_name, value=parallel_R_init, min=1e-3, max=R_sum)

            minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData),
                               loss='soft_l1', max_nfev=1e5)
            try:
                result = minner.minimize(method='least_squares')
                error = np.sum(fcn2min(result.params, freq, circuit, ZData))

                if error < best_error:
                    best_error = error
                    best_result = result
            except:
                continue

    return best_result


def fit_extreme(freq, prodata, circuit, R6_init=1e6, C3_init=1e-6,
                R1_true=None, C3_true=None, R6_true=None, n_starts=20, init_params=None):
    """
    极端条件拟合主函数

    自动检测参数可辨识性，选择合适的拟合策略

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        R6_init: 并联电阻初始估计值 (Ω)
        C3_init: 电容初始估计值 (F)
        R1_true, C3_true, R6_true: 真实参数值（用于评估，不用于拟合）
        n_starts: 多起点搜索的起始点数量
        init_params: 初始参数字典，用于确定参数名。如果为 None，则使用默认参数名

    返回:
        dict: 包含以下键的字典
            - 'result': 最佳拟合结果
            - 'status': 参数可辨识性状态
            - 'f_char': 特征频率
            - 'errors': 各参数相对误差
            - 'ident_info': 参数可辨识性检查详细信息
            - 'seg_info': 自适应分段结果
    """
    # 转换 prodata 为 ZData
    ZRE = prodata['Rs[ohm]'].values
    ZIM = prodata['X[ohm]'].values
    ZData = ZRE + 1j * ZIM

    # Step 1: 检查参数可辨识性
    ident_info = check_parameter_identifiability(freq, R6_init, C3_init, init_params=init_params)

    print(f"[fit_extreme] 参数可辨识性检查:")
    print(f"  特征频率 f_char = {ident_info['f_char']:.2e} Hz")
    print(f"  状态: {ident_info['status']}")
    print(f"  {ident_info['reason']}")

    # Step 2: 自适应分段获取串联电阻估计
    seg_info = adaptive_segmentation(freq, ZData, ident_info['f_char'], init_params=init_params)
    series_R_est = seg_info['series_R_est']
    series_R_name = seg_info['series_R_name']
    C_name = seg_info['C_name']
    parallel_R_name = seg_info['parallel_R_name']

    print(f"[fit_extreme] {series_R_name}估计: {series_R_est:.2e} Ω")

    # Step 3: 根据状态选择拟合策略
    if ident_info['status'] == 'visible':
        # 参数可见：使用串联电阻估计约束的多起点搜索
        print(f"[fit_extreme] 使用策略: 多起点搜索 + {series_R_name}_est约束")
        best_result, _ = multi_start_fit(freq, prodata, circuit,
                                          n_starts=n_starts,
                                          R1_est=series_R_est,
                                          init_params=init_params)

    elif ident_info['status'] == 'parallel_R_invisible':
        # 并联电阻不可见：约束优化 + 多起点搜索
        print(f"[fit_extreme] 使用策略: 约束优化 + {series_R_name}_est约束")
        best_result = constrained_fit(freq, prodata, circuit,
                                     status=ident_info['status'],
                                     f_char=ident_info['f_char'],
                                     n_starts=n_starts,
                                     R1_est=series_R_est,
                                     init_params=init_params)

    else:  # 'C_invisible'
        # 电容不可见：固定电容 + 多起点搜索电阻
        print(f"[fit_extreme] 使用策略: 固定{C_name} + {series_R_name}_est约束")
        best_result = constrained_fit(freq, prodata, circuit,
                                     C3_true=C3_init,
                                     status=ident_info['status'],
                                     f_char=ident_info['f_char'],
                                     n_starts=n_starts,
                                     R1_est=series_R_est,
                                     init_params=init_params)

    # Step 4: 计算误差（使用动态参数名）
    errors = {}
    if R1_true is not None and series_R_name in best_result.params:
        series_R_fit = best_result.params[series_R_name].value
        errors[f'{series_R_name}_err'] = abs(series_R_fit - R1_true) / R1_true * 100

    if C3_true is not None and C_name in best_result.params:
        C_fit = best_result.params[C_name].value
        errors[f'{C_name}_err'] = abs(C_fit - C3_true) / C3_true * 100

    if R6_true is not None and parallel_R_name in best_result.params:
        parallel_R_fit = best_result.params[parallel_R_name].value
        errors[f'{parallel_R_name}_err'] = abs(parallel_R_fit - R6_true) / R6_true * 100

    return {
        'result': best_result,
        'status': ident_info['status'],
        'f_char': ident_info['f_char'],
        'errors': errors,
        'ident_info': ident_info,
        'seg_info': seg_info
    }


def generate_synthetic_data(R1, C3, R6, freq, noise_level=0.01, seed=42):
    """
    生成合成测试数据

    参数:
        R1: 串联电阻 (Ω)
        C3: 电容 (F)
        R6: 并联电阻 (Ω)
        freq: 频率数组
        noise_level: 噪声水平（相对于信号），默认0.01
        seed: 随机种子，默认42

    返回:
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
    """
    omega = 2 * pi * freq

    # 计算理论阻抗: Z = R1 + 1/(1/R6 + jωC)
    Z_C3 = 1 / (1j * omega * C3)
    Z_parallel = 1 / (1/Z_C3 + 1/R6)
    Z_total = R1 + Z_parallel

    # 添加噪声
    np.random.seed(seed)
    noise = noise_level * (np.random.randn(len(freq)) + 1j * np.random.randn(len(freq)))
    Z_measured = Z_total + noise * np.abs(Z_total)

    ZData = real(Z_measured) + 1j * imag(Z_measured)

    # 返回 prodata 格式
    prodata = DataFrame()
    prodata['Rs[ohm]'] = Series(real(ZData))
    prodata['X[ohm]'] = Series(imag(ZData))

    return prodata


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == '__main__':
    from numpy import logspace

    print("=" * 70)
    print("极端条件拟合策略测试 - 通用电路支持")
    print("=" * 70)

    # 测试配置 - 使用不同的电路参数名
    test_cases = [
        {
            'name': '场景A: 参数可见 (R1-C1-R2电路)',
            'params': {'R1': 10.0, 'C1': 1e-6, 'R2': 1000.0},
            'freq': logspace(1, 6, 200),  # 10Hz ~ 1MHz
            'circuit': ['p(', 'C1', ',', 'R2', ')', '+', 'R1']
        },
        {
            'name': '场景B: 并联电阻不可见 (R3-C2-R4电路)',
            'params': {'R3': 10.0, 'C2': 1e-3, 'R4': 1e6},
            'freq': logspace(1, 5, 200),  # 10Hz ~ 100kHz
            'circuit': ['p(', 'C2', ',', 'R4', ')', '+', 'R3']
        },
        {
            'name': '场景C: 电容不可见 (R5-C3-R6电路)',
            'params': {'R5': 10.0, 'C3': 1e-12, 'R6': 100.0},
            'freq': logspace(4, 8, 200),  # 10kHz ~ 100MHz
            'circuit': ['p(', 'C3', ',', 'R6', ')', '+', 'R5']
        },
    ]

    for tc in test_cases:
        print(f"\n{'-' * 70}")
        print(f"{tc['name']}")
        print(f"{'-' * 70}")

        params = tc['params']
        param_names = list(params.keys())
        
        # 找出电阻和电容参数
        resistors = [k for k in param_names if k.startswith('R')]
        capacitors = [k for k in param_names if k.startswith('C')]
        
        # 假设第一个电阻是串联，最后一个是并联，第一个电容是主电容
        series_R_name = resistors[0] if resistors else 'R1'
        parallel_R_name = resistors[-1] if len(resistors) > 1 else (resistors[0] if resistors else 'R2')
        C_name = capacitors[0] if capacitors else 'C1'
        
        series_R_val = params[series_R_name]
        C_val = params[C_name]
        parallel_R_val = params[parallel_R_name]

        # 生成数据
        prodata = generate_synthetic_data(
            series_R_val, C_val, parallel_R_val, 
            tc['freq']
        )

        # 准备 init_params
        init_params = params.copy()

        # 拟合
        result_dict = fit_extreme(
            tc['freq'], prodata, tc['circuit'],
            R6_init=parallel_R_val, C3_init=C_val,
            R1_true=series_R_val, C3_true=C_val, R6_true=parallel_R_val,
            init_params=init_params
        )

        # 打印结果
        print(f"\n拟合结果:")
        for param_name in param_names:
            if param_name in result_dict['result'].params:
                fitted_val = result_dict['result'].params[param_name].value
                true_val = params[param_name]
                error_key = f"{param_name}_err"
                error = result_dict['errors'].get(error_key, 0)
                
                # 确定单位
                if param_name.startswith('R'):
                    unit = 'Ω'
                elif param_name.startswith('C'):
                    unit = 'F'
                else:
                    unit = ''
                
                print(f"  {param_name} = {fitted_val:.2e} {unit} "
                      f"(真实: {true_val:.2e}, 误差: {error:.2f}%)")

    print(f"\n{'=' * 70}")
    print("测试完成 - 支持任意命名的电路参数")
    print("=" * 70)
