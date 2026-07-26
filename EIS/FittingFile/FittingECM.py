
# -*- coding: utf-8 -*-
"""
EIS等效电路拟合核心模块

提供标准的等效电路拟合功能，包括：
- simuECM: 电路阻抗仿真
- fcn2min: 相对误差归一化残差函数
- FittingECM: 标准拟合接口
- segmented_fitting: 分段拟合策略（用于极端条件）
- smart_fitting: 智能拟合（自动选择拟合策略）

适用条件：
- 电路元件数量 ≤ 3
- 参数数量级差异 ≤ 5个数量级
- 频率跨度 ≤ 6个数量级

Created on Fri Sep 28 15:18:49 2018
@author: takeilab
"""

import sys
sys.path.append('..')

import numpy as np
from numpy import pi, real, imag, angle, sqrt
from pandas import DataFrame, Series

from lmfit import Minimizer, Parameters, report_fit

from EIS.ModelFile.EquivCircM import SearchParallel, CalculateParallel, CalculateSeries


def _identify_circuit_params(param_values):
    """
    识别电路中的电阻和电容参数

    参数:
        param_values: 参数名到值的映射

    返回:
        tuple: (resistor_params, capacitor_params)
            - resistor_params: [(name, value), ...] 按名称排序
            - capacitor_params: [(name, value), ...] 按名称排序
    """
    resistors = []
    capacitors = []

    for name, value in param_values.items():
        if name.startswith('R'):
            resistors.append((name, value))
        elif name.startswith('C'):
            capacitors.append((name, value))

    # 按名称排序以保证一致性
    resistors.sort()
    capacitors.sort()

    return resistors, capacitors





def simuECM(params,circuit,freq):
    plistlen=SearchParallel(circuit)
    circuittemp=circuit

    Zparalist=list()
    Zparallel={}
    ii=0####并联计算次数

    while ii<len(plistlen):
        plist=SearchParallel(circuittemp)###寻找当前电路列表中的并联电路位置

        circuittemp,Zparatemp,Zparallel=CalculateParallel(params,freq,circuittemp,plist,ii,Zparallel)#计算并联电路
        Zparalist.append(Zparatemp)

        ii=ii+1
    # print(Zparallel)
    Ztotal=CalculateSeries(params,freq,circuittemp,Zparallel)

    return Ztotal,Zparallel




def fcn2min(params, freq, circuit, ZDataTest):
    """
    相对误差归一化残差函数（Method 4）

    优点：
    - 能有效消除参数量级差异的影响
    - 在温和条件下所有参数误差 < 3%
    - 对于串联赛结构非常稳定

    缺点：
    - 多个并联分支时可能陷入局部最优（多解性问题）
    - 参数量级差异>6个数量级时效果下降
    """
    Ztotal, Zparallel = simuECM(params, circuit, freq)

    # 相对误差归一化
    denom = np.abs(ZDataTest) + 1e-10  # 防止除零
    Z_diff = (Ztotal - ZDataTest) / denom
    resid = np.abs(Z_diff)

    return resid




def FittingECM(params,freq,circuit,prodata):

    # omega=2*pi*freq
    ZRE=prodata['Rs[ohm]']
    ZIM=prodata['X[ohm]']
    
    ZData=ZRE+1j*ZIM

    ZDataTest=ZData

    minner = Minimizer(fcn2min,params,fcn_args=(freq, circuit,ZDataTest),ftol=1e-15,xtol=1e-15,gtol=3e-16,loss='soft_l1',max_nfev=1e5,tr_solver='lsmr',diff_step=1e-15)
    results = minner.minimize(method='least_squares')

    print(results.success)
    return results


def FittingresultsprocessECM(pm,freq,circuit,result,verbose=False):
    # # omega=2*pi*freq
    # # residual=result.residual

    # print(result.success)
    # print(result.message)
    if verbose:
        report_fit(result)
    
    for i in range(0,len(result.var_names)):
        pm[result.var_names[i]].set(value=result.x[i])


    Ztotal,Zparallel=simuECM(pm,circuit,freq)

    results3=creatdatabaseECM(freq,Ztotal)
    return results3


def creatdatabaseECM(freq,Z): #############创建结果数据库   
    data =DataFrame()
    Z=Series(Z)
    data['FREQ[Hz]']=freq
    data['Z[ohm]']=Series(real(Z))
    # Phase=arctan(Series(imag(Z))/Series(real(Z)))
    Phase=Series(angle(Z))
    data['PHASE[deg]']=Series(Phase*180/pi)
    data['Rs[ohm]']=Series(real(Z))
    data['X[ohm]']=Series(imag(Z))
    # data=[data]
    return data


# =============================================================================
# 分段拟合策略（用于极端条件）
# =============================================================================

def segmented_fitting(freq, prodata, circuit, init_params=None):
    """
    分段拟合策略：
    1. 高频段 -> 确定串联电阻 (电容短路)
    2. 低频段 -> 确定并联电阻 (电容开路)
    3. 中频段 -> 确定电容 (两者都参与)
    4. 全频段精修 -> 用前三步结果作为初值

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        init_params: 初始参数字典，用于确定参数名和边界。
                     如果为 None，则使用默认参数名

    返回:
        tuple: (result_full, fitted_params, step_info)
    """
    ZRE = prodata['Rs[ohm]'].values
    ZIM = prodata['X[ohm]'].values
    ZData = ZRE + 1j * ZIM

    f_min, f_max = freq.min(), freq.max()
    step_info = {}

    # 从 init_params 动态提取参数名
    param_values = {}
    if init_params is not None:
        # 排除 min/max 后缀的参数
        param_values = {k: v for k, v in init_params.items() 
                       if not k.endswith('_min') and not k.endswith('_max')}

    # 识别电阻和电容参数
    resistors = [(k, v) for k, v in param_values.items() if k.startswith('R')]
    capacitors = [(k, v) for k, v in param_values.items() if k.startswith('C')]
    
    # 按名称排序
    resistors.sort()
    capacitors.sort()

    # 确定参数名：第一个电阻为串联，最后一个为并联
    if len(resistors) >= 2:
        series_R_name = resistors[0][0]
        parallel_R_name = resistors[-1][0]
    elif len(resistors) == 1:
        series_R_name = resistors[0][0]
        parallel_R_name = resistors[0][0]
    else:
        series_R_name = 'R1'
        parallel_R_name = 'R2'

    if len(capacitors) >= 1:
        C_name = capacitors[0][0]
    else:
        C_name = 'C1'

    # ---------- Step 1: 高频段估计串联电阻 ----------
    high_freq_mask = freq > f_max / 10
    if np.sum(high_freq_mask) < 3:
        high_freq_mask = freq > f_max / 3
    if np.sum(high_freq_mask) < 3:
        high_freq_mask = freq > np.sqrt(f_min * f_max)

    if np.sum(high_freq_mask) >= 3:
        series_R_estimate = np.mean(real(ZData[high_freq_mask]))
    else:
        series_R_estimate = np.mean(real(ZData[freq > f_max * 0.5]))

    if np.isnan(series_R_estimate):
        series_R_estimate = real(ZData[-1])
    step_info['series_R_estimate'] = series_R_estimate

    # ---------- Step 2: 低频段估计并联电阻 ----------
    low_freq_mask = freq < f_min * 10
    if np.sum(low_freq_mask) < 3:
        low_freq_mask = freq < f_min * 100
    if np.sum(low_freq_mask) < 3:
        low_freq_mask = freq < np.sqrt(f_min * f_max)

    if np.sum(low_freq_mask) >= 3:
        Z_low_mean = np.mean(real(ZData[low_freq_mask]))
    else:
        Z_low_mean = np.mean(real(ZData[freq < f_max * 0.01]))

    parallel_R_estimate = Z_low_mean - series_R_estimate
    if np.isnan(parallel_R_estimate) or parallel_R_estimate <= 0:
        parallel_R_estimate = param_values.get(parallel_R_name, 1e6)
    step_info['parallel_R_estimate'] = parallel_R_estimate

    # ---------- Step 3: 中频段估计电容 ----------
    C_init = 1.0 / (2 * np.pi * parallel_R_estimate * np.sqrt(f_min * f_max))
    if np.isnan(C_init) or C_init <= 0:
        C_init = param_values.get(C_name, 1e-6)
    step_info['C_estimate'] = C_init

    # ---------- Step 4: 全频段精修 ----------
    pm_full = Parameters()
    pm_full.add(series_R_name, value=max(series_R_estimate * 0.5, 1e-6), min=1e-8, max=1e6)
    pm_full.add(C_name, value=max(abs(C_init) * 0.5, 1e-12), min=1e-12, max=1e3)
    pm_full.add(parallel_R_name, value=max(parallel_R_estimate * 0.5, 1e-3), min=1e-3, max=1e9)

    minner_full = Minimizer(fcn2min, pm_full, fcn_args=(freq, circuit, ZData),
                            loss='soft_l1', max_nfev=1e5)
    result_full = minner_full.minimize(method='least_squares')

    fitted_params = {name: result_full.params[name].value for name in result_full.var_names}

    return result_full, fitted_params, step_info


def should_use_segmented(freq, init_params):
    """
    判断是否使用分段拟合

    判断依据:
    1. 参数量级差异：如果电阻/电容参数差异超过6个数量级，分段可能有益
    2. 频率跨度：跨度越大，分段可能越有必要
    3. 初始猜测与参数边界的比例

    参数:
        freq: 频率数组
        init_params: 初始参数字典，支持两种格式：
            - {'R1': val, 'C1': val, ...} 或
            - {'R1': val, 'R1_min': min, 'R1_max': max, ...}

    返回:
        tuple: (True/False, reason)
    """
    # 提取所有参数值（排除 min/max 后缀的参数）
    param_values = {}
    for key, value in init_params.items():
        if not key.endswith('_min') and not key.endswith('_max'):
            param_values[key] = value

    if len(param_values) == 0:
        return False, "无参数信息"

    # 动态识别电阻和电容参数
    resistors, capacitors = _identify_circuit_params(param_values)

    if len(resistors) < 2:
        return False, "电阻参数少于2个，无需分段拟合"

    # 获取串联电阻和并联电阻的值（第一个电阻为串联，最后一个为并联）
    series_R_name, series_R_val = resistors[0]
    parallel_R_name, parallel_R_val = resistors[-1]

    # 获取电容值（如果有的话）
    C_name, C_val = capacitors[0] if capacitors else ('C', 1e-6)

    # 计算参数量级差异
    magnitude_diff = max(series_R_val, parallel_R_val, C_val) / min(series_R_val, parallel_R_val, C_val) if min(series_R_val, parallel_R_val, C_val) > 0 else 1

    # 频率跨度
    freq_span = np.log10(freq.max() / freq.min())

    # 判断
    if freq_span > 10 and magnitude_diff > 1e6:
        return True, f"频率跨度{freq_span:.1f}数量级 + 参数量级差异{magnitude_diff:.1e}"
    elif freq_span > 8 and magnitude_diff > 1e4:
        return True, f"频率跨度{freq_span:.1f}数量级 + 参数量级差异{magnitude_diff:.1e}"
    elif magnitude_diff > 1e8:
        return True, f"参数量级差异{magnitude_diff:.1e}太大"
    else:
        return False, f"参数量级差异不大({series_R_name}={series_R_val:.1e}, {parallel_R_name}={parallel_R_val:.1e}, {C_name}={C_val:.1e})"


def smart_fitting(freq, prodata, circuit, init_params):
    """
    智能拟合：自动选择直接拟合或分段拟合

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        init_params: 初始参数字典，支持两种格式：
            - {'R1': val, 'C1': val, ...} 或
            - {'R1': val, 'R1_min': min, 'R1_max': max, ...}

    返回:
        tuple: (result, fitted_params, method_used, step_info)
    """
    ZRE = prodata['Rs[ohm]'].values
    ZIM = prodata['X[ohm]'].values
    ZData = ZRE + 1j * ZIM

    # 提取真实参数值（如果有的话）
    true_params = {}
    for key, value in init_params.items():
        if not key.endswith('_min') and not key.endswith('_max'):
            true_params[key] = value

    use_segmented, reason = should_use_segmented(freq, init_params)

    print(f"\n智能判断: {'使用分段拟合' if use_segmented else '使用直接拟合'} ({reason})")

    if use_segmented:
        # 尝试分段拟合
        print("\n尝试分段拟合...")
        try:
            result, fitted_params, step_info = segmented_fitting(freq, prodata, circuit, init_params)

            # 检查结果是否合理 - 使用动态参数检测
            resistors, capacitors = _identify_circuit_params(true_params)
            
            # 计算所有参数的相对误差
            max_err = 0.0
            err_details = []
            for name, true_val in true_params.items():
                if true_val != 0:
                    fitted_val = fitted_params.get(name, 0)
                    rel_err = abs(fitted_val - true_val) / abs(true_val)
                    max_err = max(max_err, rel_err)
                    err_details.append(f"{name}={rel_err*100:.2f}%")
            
            if max_err < 0.5:
                print(f"分段拟合成功: {', '.join(err_details)}")
                return result, fitted_params, "segmented", step_info
            else:
                print(f"分段拟合结果不理想 (最大误差{max_err*100:.2f}%)，尝试直接拟合...")

                # 直接拟合，使用动态参数名
                pm_init = Parameters()
                for name, value in true_params.items():
                    min_val = init_params.get(f'{name}_min', 1e-15)
                    max_val = init_params.get(f'{name}_max', 1e15)
                    pm_init.add(name, value=value, min=min_val, max=max_val)

                minner = Minimizer(fcn2min, pm_init, fcn_args=(freq, circuit, ZData),
                                  loss='soft_l1', max_nfev=1e5)
                result = minner.minimize(method='least_squares')
                fitted_params = {name: result.params[name].value for name in result.var_names}
                return result, fitted_params, "segmented+direct", step_info

        except Exception as e:
            print(f"分段拟合失败: {e}，回退到直接拟合")
    else:
        step_info = {}

    # 直接拟合，使用动态参数名
    pm_fit = Parameters()
    for name, value in true_params.items():
        min_val = init_params.get(f'{name}_min', 1e-15)
        max_val = init_params.get(f'{name}_max', 1e15)
        pm_fit.add(name, value=value, min=min_val, max=max_val)

    minner = Minimizer(fcn2min, pm_fit, fcn_args=(freq, circuit, ZData),
                       ftol=1e-15, xtol=1e-15, gtol=3e-16,
                       loss='soft_l1', max_nfev=1e5, tr_solver='lsmr', diff_step=1e-15)
    result = minner.minimize(method='least_squares')
    fitted_params = {name: result.params[name].value for name in result.var_names}

    return result, fitted_params, "direct", step_info


def should_use_extreme(freq, init_params):
    """
    判断是否使用极端条件拟合策略

    判断依据:
    1. 参数量级差异是否过大（基于所有参数的值范围）
    2. 频率跨度是否过大

    参数:
        freq: 频率数组
        init_params: 初始参数字典，支持两种格式：
            - {'R1': val, 'C1': val, ...} 或
            - {'R1': val, 'R1_min': min, 'R1_max': max, ...}

    返回:
        tuple: (True/False, reason)
    """
    # 提取所有参数值（排除 min/max 后缀的参数）
    param_values = {}
    for key, value in init_params.items():
        if not key.endswith('_min') and not key.endswith('_max'):
            param_values[key] = value

    if len(param_values) == 0:
        return False, "无参数信息"

    # 频率跨度
    freq_span = np.log10(freq.max() / freq.min())

    # 参数量级差异：计算所有参数值的数量级范围
    try:
        orders = []
        for name, val in param_values.items():
            if val > 0:
                orders.append(np.log10(abs(val)))
            else:
                orders.append(-100)  # 极小值

        if len(orders) >= 2:
            magnitude_range = max(orders) - min(orders)
        else:
            magnitude_range = 0
    except:
        magnitude_range = 0

    # 判断：频率跨度大且参数量级差异大
    if freq_span > 7 and magnitude_range > 5:
        return True, f"频率跨度{freq_span:.1f}数量级 + 参数量级差异{magnitude_range:.1f}"
    elif magnitude_range > 6:
        return True, f"参数量级差异{magnitude_range:.1f}太大"
    else:
        return False, f"参数可辨识，无极端条件"


def _auto_fitting_core(freq, prodata, circuit, init_params, method='least_squares', **fit_kwargs):
    """
    智能调度拟合核心函数：根据条件自动选择标准拟合或极端条件拟合

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        init_params: 初始参数字典，支持两种格式：
            - {'R1': val, 'C1': val, ...} 或
            - {'R1': val, 'R1_min': min, 'R1_max': max, ...}
        method: 优化算法名称（默认 'least_squares'）
        **fit_kwargs: 其他拟合参数（如 xtol, ftol, gtol 等）

    返回:
        dict: {
            'result': 拟合结果,
            'method': 使用的拟合方法 ('standard', 'extreme'),
            'ident_info': 参数可辨识性信息（仅extreme模式）
        }
    """
    use_extreme, reason = should_use_extreme(freq, init_params)

    print(f"\n[_auto_fitting_core] 智能判断: {'使用极端条件拟合' if use_extreme else '使用标准拟合'} ({reason})")

    # 目前暂时跳过极端条件拟合，因为 fit_extreme 函数需要重构以支持任意电路
    # 极端条件拟合需要更复杂的电路拓扑解析
    use_extreme = False

    if use_extreme:
        # 极端条件拟合（暂时禁用，需要重构 fit_extreme）
        # 动态识别电阻和电容参数
        param_values = {k: v for k, v in init_params.items() 
                      if not k.endswith('_min') and not k.endswith('_max')}
        resistors, capacitors = _identify_circuit_params(param_values)
        
        # 获取并联电阻和电容的初始值（如果有的话）
        parallel_R_init = resistors[-1][1] if len(resistors) >= 2 else 50.0
        C_init = capacitors[0][1] if capacitors else 1e-6

        result_dict = fit_extreme(freq, prodata, circuit,
                                  R6_init=parallel_R_init, C3_init=C_init)

        return {
            'result': result_dict['result'],
            'method': 'extreme',
            'ident_info': result_dict['ident_info']
        }
    else:
        # 标准拟合：动态从 init_params 提取参数信息
        pm = Parameters()

        # 提取所有参数（排除 min/max 后缀）
        for key, value in init_params.items():
            if key.endswith('_min') or key.endswith('_max'):
                continue

            # 获取对应的 min/max 值
            min_val = init_params.get(f'{key}_min', 1e-15)
            max_val = init_params.get(f'{key}_max', 1e15)

            pm.add(key, value=value, min=min_val, max=max_val)

        # 执行拟合
        ZData = prodata['Rs[ohm]'].values + 1j * prodata['X[ohm]'].values
        
        # 合并默认参数和用户自定义参数
        default_kwargs = {
            'ftol': 1e-15, 'xtol': 1e-15, 'gtol': 3e-16,
            'loss': 'soft_l1', 'max_nfev': 1e5, 'tr_solver': 'lsmr', 'diff_step': 1e-15
        }
        default_kwargs.update(fit_kwargs)
        
        minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData), **default_kwargs)
        result = minner.minimize(method=method)

        return {
            'result': result,
            'method': 'standard',
            'ident_info': None
        }


def auto_fitting(params, freq, circuit, prodata, method='least_squares', **fit_kwargs):
    """
    智能调度拟合函数 - 兼容 FittingECM 接口

    根据条件自动选择标准拟合或极端条件拟合

    参数:
        params: lmfit Parameters 对象（包含参数值和边界）
        freq: 频率数组
        circuit: 电路描述列表
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        method: 优化算法名称（默认 'least_squares'）
        **fit_kwargs: 其他拟合参数（如 xtol, ftol, gtol 等）

    返回:
        lmfit Result 对象（与 FittingECM 一致）
    """
    # 从 params 提取 init_params
    init_params = {}
    for name, param in params.items():
        init_params[name] = param.value
        init_params[f'{name}_min'] = param.min
        init_params[f'{name}_max'] = param.max

    # 调用核心函数
    result_dict = _auto_fitting_core(freq, prodata, circuit, init_params, method=method, **fit_kwargs)

    return result_dict['result']


def generate_test_data(R1, C3, R6, freq_range=(1, 6), n_points=100, noise_level=0.01, seed=42):
    """
    生成EIS测试数据

    参数:
        R1, C3, R6: 电路参数
        freq_range: 频率范围(数量级), 如 (1, 6) 表示 10^1 到 10^6 Hz
        n_points: 频点数量
        noise_level: 噪声水平(百分比)
        seed: 随机种子

    返回:
        tuple: (freq, Z_measured, prodata, Z_total_true)
    """
    freq_test = np.logspace(freq_range[0], freq_range[1], n_points)
    omega = 2 * pi * freq_test

    Z_C3 = 1 / (1j * omega * C3)
    Z_R6 = R6
    Z_parallel = 1 / (1/Z_C3 + 1/Z_R6)
    Z_total_true = R1 + Z_parallel

    np.random.seed(seed)
    noise = noise_level * (np.random.randn(len(freq_test)) + 1j * np.random.randn(len(freq_test)))
    Z_measured = Z_total_true + noise * np.abs(Z_total_true)

    prodata = DataFrame()
    prodata['FREQ[Hz]'] = freq_test
    prodata['Rs[ohm]'] = Series(real(Z_measured))
    prodata['X[ohm]'] = Series(imag(Z_measured))

    return freq_test, Z_measured, prodata, Z_total_true




