
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
from FittingWarnings import (
    warn as _emit_warning,
    info as _emit_info,
    warn_fallback as _emit_fallback_warning,
)


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




def FittingECM(params, freq, circuit, prodata, method='least_squares', **fit_kwargs):
    """
    兼容旧 API 的拟合函数 - 已委托给 auto_fitting

    原 FittingECM 硬编码 method='least_squares'，且 ftol/xtol/gtol 硬塞；
    现改为委托给 auto_fitting，可支持全部 10 个优化方法。

    参数:
        params: lmfit Parameters 对象
        freq: 频率数组
        circuit: 电路描述列表
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        method: 优化算法名称（默认 'least_squares'）
        **fit_kwargs: 其他拟合参数

    返回:
        lmfit Result 对象
    """
    return auto_fitting(params, freq, circuit, prodata, method=method, **fit_kwargs)


def FittingresultsprocessECM(pm,freq,circuit,result,verbose=False):
    # # omega=2*pi*freq
    # # residual=result.residual

    # print(result.success)
    # print(result.message)
    if verbose:
        report_fit(result)

    # ampgo 路径下 result.x 不存在，结果存于 result.ampgo_x0；
    # 其它方法 lmfit 也会把 x 写到 result.params[par].value，所以优先用 params。
    for i, name in enumerate(result.var_names):
        x = getattr(result, 'x', None)
        if x is not None and i < len(x):
            pm[name].set(value=x[i])
        else:
            # ampgo 或其它没 x 的方法：直接用 params 里 lmfit 已写入的值
            pm[name].set(value=result.params[name].value)


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
    elif magnitude_range > 9:
        return True, f"参数量级差异{magnitude_range:.1f}太大"
    else:
        return False, f"参数可辨识，无极端条件"


# =============================================================================
# 全局方法边界自适应 + 多起点 R1 约束
# （P0-① 自适应边界 / P0-② 局部方法保留原边界 / P1 多起点 + 物理约束）
# =============================================================================

# 全局优化方法集合（与 _auto_fitting_core 中的判断保持一致）
GLOBAL_METHODS = {'differential_evolution', 'dual_annealing', 'ampgo'}

# 问题 2 修复: 无梯度局部方法(Nelder/Powell)也需要紧边界
SEMI_GLOBAL_METHODS = {'nelder', 'powell'}

# 所有需要自适应边界的方法
ALL_BOUND_SENSITIVE = GLOBAL_METHODS | SEMI_GLOBAL_METHODS

# 问题 8 修复: 不同方法使用不同的默认 tighten_factor
# Nelder/Powell 需要更紧的边界（100x），全局方法 1000x
METHOD_TIGHTEN_FACTOR = {
    'differential_evolution': 1000.0,
    'dual_annealing': 1000.0,
    'ampgo': 1000.0,
    'nelder': 100.0,      # 问题 2: Nelder 需要更紧
    'powell': 100.0,      # 问题 2: Powell 需要更紧
}

# 问题 5 修复: 各方法不同的 max_nfev
# dual_annealing 退火过程需要更多迭代
METHOD_MAX_NFEV = {
    'least_squares': int(1e5),
    'nelder': int(1e5),
    'lbfgsb': int(1e5),
    'powell': int(1e5),
    'cg': int(1e5),
    'bfgs': int(1e5),
    'differential_evolution': int(1e5),
    'dual_annealing': int(5e5),   # ← 5 倍预算
    'ampgo': int(1e5),
}


def _auto_select_loss(noise_level):
    """
    问题 4 修复: 根据噪声水平选择 least_squares 损失函数

    保守策略: 默认 soft_l1, 只在极低/极高噪声下切换
        - < 0.001 (0.1%): linear (L2, 高精度)
        - 0.001 ~ 0.10: soft_l1 (默认, 平衡)
        - > 0.10 (10%): huber (更鲁棒)

    注: 由于 init_params 偏差会被误判为噪声, 采用保守策略
        —— 大多数情况下用 soft_l1 是最安全的
    """
    if noise_level is None or not np.isfinite(noise_level):
        return 'soft_l1'
    if noise_level < 0.001:
        return 'linear'
    elif noise_level > 0.10:
        return 'huber'
    else:
        return 'soft_l1'


def _estimate_noise_level(prodata, freq, circuit, init_params):
    """
    问题 4 修复: 估计数据噪声水平

    使用 init_params 拟合残差的中位数绝对偏差 (MAD)
    加 0.10 上限: 防止 init_params 偏差过大被误判为高噪声
    """
    try:
        ZData = prodata['Rs[ohm]'].values + 1j * prodata['X[ohm]'].values
        pm = Parameters()
        for k, v in init_params.items():
            if not k.endswith('_min') and not k.endswith('_max') and np.isfinite(v):
                pm.add(k, value=float(v), min=1e-15, max=1e15)
        residuals = fcn2min(pm, freq, circuit, ZData)
        med = float(np.median(np.abs(residuals)))
        # 上限 0.10: 防止 init 偏差被误判为高噪声
        if med > 0.10:
            return 0.10
        return med if np.isfinite(med) and med > 0 else None
    except Exception:
        return None


def _compute_adaptive_bounds(init_value, method,
                              user_min=None, user_max=None,
                              tighten_factor=None,
                              circuit_type='simple_randles'):
    """
    为不同方法计算合适的参数边界

    规则:
        1. 局部方法 (LS/cg/bfgs/lbfgsb) 保留 1e-15~1e15
        2. 半全局方法 (Nelder/Powell) 收紧到 init/100~init*100
        3. 全局方法 (DE/DA/AMPGO) 收紧到 init/1000~init*1000
        4. 问题 8 修复: 根据电路类型选择不同 factor
    """
    if method not in ALL_BOUND_SENSITIVE:
        # 局部方法：完全保留原行为
        return (1e-15 if user_min is None else user_min,
                1e15  if user_max is None else user_max)

    if init_value <= 0:
        init_value = 1e-6

    # 问题 8 修复: 根据方法+电路类型选择 factor
    if tighten_factor is None:
        tighten_factor = METHOD_TIGHTEN_FACTOR.get(method, 1000.0)

    auto_min = init_value / tighten_factor
    auto_max = init_value * tighten_factor

    # 用户边界 vs 自适应边界:取更紧的
    final_min = max(user_min, auto_min) if user_min is not None else auto_min
    final_max = min(user_max, auto_max) if user_max is not None else auto_max

    if final_min >= final_max:
        final_min, final_max = auto_min, auto_max

    return (max(final_min, 1e-15), min(final_max, 1e15))


def _should_use_multi_start(init_params, method, freq=None):
    """
    判断全局方法是否需要多起点 + R1 物理约束

    触发条件（任一满足）:
        1. 全局方法 AND
        2. 电路有 ≥ 2 个 R* 参数（暗示有多个并联分支） OR
           参数量级差异 > 5 个数量级

    参数:
        init_params: 初始参数字典
        method: 优化方法名
        freq: 频率数组（暂未使用，预留）

    返回:
        bool
    """
    if method not in GLOBAL_METHODS:
        return False

    # 条件 1: 多个 R* 参数（暗示有多个并联分支 → 多解性高风险）
    R_count = sum(1 for k in init_params
                  if k.startswith('R') and not k.endswith('_min')
                  and not k.endswith('_max'))
    if R_count >= 2:
        return True

    # 条件 2: 参数量级差异 > 5 个数量级
    param_vals = [v for k, v in init_params.items()
                  if not k.endswith('_min') and not k.endswith('_max')
                  and v > 0 and np.isfinite(v)]
    if len(param_vals) >= 2:
        mag_diff = np.log10(max(param_vals)) - np.log10(min(param_vals))
        if mag_diff > 5:
            return True

    return False


# =============================================================================
# 5 改进: 多解性检测、失败检测、R1 估算（问题 4/5/6 修复）
# =============================================================================

def _detect_multi_solution_risk(circuit):
    """
    问题 6 修复: 检测电路是否存在多解性风险

    多解性特征:
        - 多个 p(C, R) 并联结构
        - 多个独立的 C 参数
    """
    if circuit is None:
        return False
    circuit_str = ' '.join(str(c) for c in circuit)
    # 多个 p(...) 嵌套
    p_count = circuit_str.count('p(')
    if p_count >= 2:
        return True
    return False


def _is_fitting_failed(result, init_params, max_error_threshold=0.5):
    """
    问题 4 修复: 判断拟合是否失败

    失败特征: 至少一个参数相对误差 > 50%
    """
    if result is None or not hasattr(result, 'params'):
        return True
    try:
        errors = []
        for name in init_params:
            if name.endswith('_min') or name.endswith('_max'):
                continue
            if name not in result.params:
                continue
            init_val = init_params[name]
            fit_val = result.params[name].value
            if abs(init_val) > 0 and np.isfinite(init_val) and np.isfinite(fit_val):
                err = abs((fit_val - init_val) / init_val)
                errors.append(err)
        if not errors:
            return False
        return max(errors) > max_error_threshold
    except Exception:
        return True


def _estimate_R_at_high_freq(freq, ZData, percentile=10):
    """
    问题 5 修复: 从高频段估算串联电阻 R1_est

    高频段实部 ≈ R1 (电容短路, 串联电阻主导)
    """
    f_max = freq.max()
    high_mask = freq > f_max / 10
    if np.sum(high_mask) < 3:
        high_mask = freq > f_max / 3
    if np.sum(high_mask) < 3:
        return None
    R_est = np.median(np.real(ZData[high_mask]))
    return R_est if (R_est > 0 and np.isfinite(R_est)) else None


def _compute_magnitude_range(init_params):
    """计算参数量级差 (log10 单位)"""
    param_vals = [v for k, v in init_params.items()
                  if not k.endswith('_min') and not k.endswith('_max')
                  and v > 0 and np.isfinite(v)]
    if len(param_vals) < 2:
        return 0.0
    return np.log10(max(param_vals)) - np.log10(min(param_vals))


def _multi_start_with_R1_constraint(freq, prodata, circuit, init_params,
                                      method, n_starts=10, r1_tighten=10.0,
                                      rng_seed=42):
    """
    多起点 + R1_est 物理约束的全局搜索（用于多解性/极值量级场景）

    步骤:
        1. 从高频段估计 R1_est（复用 segmented_fitting 的思路）
        2. 找到第一个 R* 参数作为 R1
        3. 在 R1_est 周围 [R1_est/r1_tighten, R1_est*r1_tighten] 内
           对数空间均匀采样 n_starts 个起点
        4. 每个起点跑一次 method,选择 χ² 最小的结果

    参数:
        freq: 频率数组
        prodata: 包含 'Rs[ohm]' 和 'X[ohm]' 的 DataFrame
        circuit: 电路描述列表
        init_params: 初始参数字典（可含 _min/_max 后缀的边界）
        method: 全局优化方法名
        n_starts: 起点数量（默认 10）
        r1_tighten: R1 边界相对 R1_est 的倍数（默认 10 即 ±1 数量级）
        rng_seed: 随机种子（保证可复现）

    返回:
        lmfit Result 对象（如果全部失败则返回 None）
    """
    ZData = prodata['Rs[ohm]'].values + 1j * prodata['X[ohm]'].values
    f_min, f_max = freq.min(), freq.max()

    # Step 1: 高频段估计 R1
    high_mask = freq > f_max / 10
    if np.sum(high_mask) < 3:
        high_mask = freq > f_max / 3
    if np.sum(high_mask) < 3:
        high_mask = freq > np.sqrt(f_min * f_max)
    R1_est = float(np.mean(np.real(ZData[high_mask])))
    if not np.isfinite(R1_est) or R1_est <= 0:
        # 回退到 init_params 中的 R1 初值
        R1_est = next((v for k, v in init_params.items()
                       if k.startswith('R') and not k.endswith('_min')
                       and not k.endswith('_max')),
                      1.0)
    if R1_est <= 0:
        R1_est = 1.0

    # Step 2: 找到 R1 参数名
    R_names = sorted([k for k in init_params.keys()
                      if k.startswith('R') and not k.endswith('_min')
                      and not k.endswith('_max')])
    R1_name = R_names[0] if R_names else 'R1'
    R1_init = init_params.get(R1_name, R1_est)

    # R1 边界: [R1_est/r1_tighten, R1_est*r1_tighten]
    R1_min = R1_est / r1_tighten
    R1_max = R1_est * r1_tighten
    # 包含 R1_init（如果 R1_init 在边界外，使用 R1_init ± 50%）
    if R1_init < R1_min:
        R1_min = max(R1_init * 0.5, 1e-15)
    if R1_init > R1_max:
        R1_max = R1_init * 1.5

    # Step 3: 在对数空间均匀采样 n_starts 个 R1 起点
    rng = np.random.default_rng(rng_seed)
    log_lo = np.log10(max(R1_min, 1e-15))
    log_hi = np.log10(min(R1_max, 1e15))
    R1_starts = 10 ** rng.uniform(log_lo, log_hi, size=n_starts)
    # 保证至少一个起点等于 R1_est
    R1_starts[0] = R1_est

    # Step 4: 跑 n_starts 次拟合
    best_result = None
    best_chisqr = float('inf')
    print(f"  [多起点模式] method={method}, n_starts={n_starts}, "
          f"R1_est={R1_est:.3e}, R1_bounds=[{R1_min:.3e}, {R1_max:.3e}]")

    for i, R1_start in enumerate(R1_starts):
        pm = Parameters()
        for key, value in init_params.items():
            if key.endswith('_min') or key.endswith('_max'):
                continue
            if key == R1_name:
                pm.add(key, value=R1_start, min=R1_min, max=R1_max)
            else:
                pmin = init_params.get(f'{key}_min', None)
                pmax = init_params.get(f'{key}_max', None)
                pmin, pmax = _compute_adaptive_bounds(
                    value, method, user_min=pmin, user_max=pmax
                )
                pm.add(key, value=value, min=pmin, max=pmax)

        try:
            minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData),
                               max_nfev=int(1e4))
            r = minner.minimize(method=method)
            chisqr = getattr(r, 'chisqr', float('inf'))
            if np.isfinite(chisqr) and chisqr < best_chisqr:
                best_chisqr = chisqr
                best_result = r
        except Exception as e:
            # 单个起点失败不影响整体
            print(f"    [start {i+1}/{n_starts}] 失败: {type(e).__name__}: {str(e)[:50]}")
            continue

    if best_result is not None:
        print(f"  [多起点模式] 完成: best χ²={best_chisqr:.4e}")
    else:
        print(f"  [多起点模式] 全部起点失败")

    return best_result


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

        # ====== 问题 6: 多解性场景预判 (弹窗建议全局方法) ======
        if _detect_multi_solution_risk(circuit) and method in (
                'nelder', 'powell', 'cg', 'bfgs', 'lbfgsb'):
            _emit_warning(
                f"⚠️ 当前电路可能存在多解性，{method} 是局部方法，\n"
                f"容易陷入局部最优。\n\n"
                f"建议切换到以下全局方法之一:\n"
                f"  • differential_evolution (推荐, 稳定)\n"
                f"  • dual_annealing (快)\n"
                f"  • ampgo (最准, 但慢)\n"
                f"\n(继续用 {method} 拟合, 可能得到次优解)"
            )

        # ====== 问题 5: mΩ-MΩ 量级差 R 物理约束 ======
        # 在添加参数前先估算 R1_est 并约束 R 参数边界
        ZData = prodata['Rs[ohm]'].values + 1j * prodata['X[ohm]'].values
        magnitude_range = _compute_magnitude_range(init_params)
        if magnitude_range > 5:
            R1_est = _estimate_R_at_high_freq(freq, ZData)
            if R1_est is not None:
                # 自动收紧 R 参数边界
                R_names = [k for k in init_params
                           if k.startswith('R') and not k.endswith('_min')
                           and not k.endswith('_max')]
                for rn in R_names:
                    est_min = R1_est * 1e-3
                    est_max = R1_est * 1e4
                    cur_min = init_params.get(f'{rn}_min', 1e-15)
                    cur_max = init_params.get(f'{rn}_max', 1e15)
                    init_params[f'{rn}_min'] = max(cur_min, est_min)
                    init_params[f'{rn}_max'] = min(cur_max, est_max)
                print(f"  [R 物理约束] R1_est={R1_est:.3e}, "
                      f"范围 [{est_min:.3e}, {est_max:.3e}]")

        # 提取所有参数（排除 min/max 后缀）
        # P0-①: 使用 _compute_adaptive_bounds 根据 method 自动收紧全局方法边界
        for key, value in init_params.items():
            if key.endswith('_min') or key.endswith('_max'):
                continue

            # 获取用户显式 min/max（如果存在）
            user_min = init_params.get(f'{key}_min', None)
            user_max = init_params.get(f'{key}_max', None)

            # P0-①: 调用自适应边界计算
            #   - 局部方法 (LS/LBFGSB/CG/BFGS) 保持 1e-15~1e15
            #   - 半全局方法 (Nelder/Powell) 收紧到 init/100~init*100  (问题 2)
            #   - 全局方法 (DE/DA/AMPGO) 收紧到 init/1000~init*1000
            min_val, max_val = _compute_adaptive_bounds(
                value, method,
                user_min=user_min, user_max=user_max,
            )

            pm.add(key, value=value, min=min_val, max=max_val)

        # 仅 least_squares 专属，绝不能透传给 minimize/DE/DA/...
        LS_ONLY = {'ftol', 'xtol', 'gtol', 'tr_solver', 'diff_step'}
        # 这些方法专有收敛阈值需要塞进 scipy.optimize.minimize 的 options
        OPTIONS_KEYS = {'xatol', 'fatol', 'xtol', 'ftol', 'gtol', 'maxls',
                        'maxiter', 'maxfev', 'maxfun', 'eps', 'norm',
                        'maxcor', 'adaptive', 'iprint', 'finite_diff_rel_step',
                        'finite_diff_bounds_step', 'direc'}

        # 过滤用户传入的 fit_kwargs，去掉 least_squares 专属项
        safe_kwargs = {k: v for k, v in fit_kwargs.items() if k not in LS_ONLY}

        if method == 'least_squares':
            # 问题 4 修复: 智能 loss（保守策略）
            # 由于 init_params 偏差会被误判为噪声, 实际很难准确估算真实噪声
            # 采用保守策略: 默认 soft_l1, 只在极端情况下切换
            # 同时允许用户通过 fit_kwargs 强制指定 loss (如 loss='linear')
            user_loss = safe_kwargs.get('loss', None)
            if user_loss is not None:
                loss = user_loss
                print(f"  [LS 用户指定 loss] {loss}")
            else:
                noise_level = _estimate_noise_level(prodata, freq, circuit, init_params)
                loss = _auto_select_loss(noise_level)
                print(f"  [LS 智能 loss] noise={noise_level}, loss={loss}")
            minner = Minimizer(
                fcn2min, pm, fcn_args=(freq, circuit, ZData),
                **{**safe_kwargs,
                   'ftol': 1e-15, 'xtol': 1e-15, 'gtol': 3e-16,
                   'loss': loss, 'max_nfev': int(1e5),
                   'tr_solver': 'lsmr', 'diff_step': 1e-15}
            )
            result = minner.minimize(method='least_squares')
        elif method in ('differential_evolution', 'dual_annealing', 'ampgo'):
            # P1: 多解性/极值量级场景下,自动使用多起点 + R1 物理约束
            if _should_use_multi_start(init_params, method, freq):
                multi_result = _multi_start_with_R1_constraint(
                    freq, prodata, circuit, init_params, method,
                    n_starts=10, r1_tighten=10.0, rng_seed=42
                )
                if multi_result is not None:
                    return {
                        'result': multi_result,
                        'method': 'multi_start',
                        'ident_info': None
                    }
                # 多起点全部失败时,回退到单点 DE/DA/BH/AMPGO
                print(f"  [回退] 多起点失败,使用单点 {method}")

            # 进化/全局方法：参数直传给 scipy 对应函数（不接受 options=）
            # 问题 5 修复: dual_annealing max_nfev 提升到 5e5
            # max_nfev 必须是 int（scipy 用作 maxiter）
            direct_kwargs = {k: v for k, v in safe_kwargs.items() if k not in OPTIONS_KEYS}
            # 过滤掉 None（_cast_setting 对可空字段返回 None，scipy 不接受）
            direct_kwargs = {k: v for k, v in direct_kwargs.items() if v is not None}
            # 问题 5 修复: 按方法选择 max_nfev
            max_nfev_method = METHOD_MAX_NFEV.get(method, int(1e5))
            minner = Minimizer(
                fcn2min, pm, fcn_args=(freq, circuit, ZData),
                **{**direct_kwargs, 'max_nfev': max_nfev_method}
            )
            result = minner.minimize(method=method)
        else:
            # 其它走 scipy.optimize.minimize 的方法：所有方法专有收敛阈值必须进 options
            direct_kwargs = {k: v for k, v in safe_kwargs.items() if k not in OPTIONS_KEYS}
            options_kwargs = {k: v for k, v in safe_kwargs.items() if k in OPTIONS_KEYS}
            # 过滤掉 None
            direct_kwargs = {k: v for k, v in direct_kwargs.items() if v is not None}
            options_kwargs = {k: v for k, v in options_kwargs.items() if v is not None}
            minner = Minimizer(
                fcn2min, pm, fcn_args=(freq, circuit, ZData),
                **{**direct_kwargs, 'max_nfev': int(1e5),
                   'options': options_kwargs or None}
            )
            result = minner.minimize(method=method)

        # ====== 问题 3: 拟合后失败检测 (弹窗方案 B - 完整对比) ======
        original_result = result
        original_method = method
        original_chisqr = float(getattr(result, 'chisqr', float('inf'))) if result is not None else float('inf')
        fallback_used = False

        if (result is not None
                and method in ('lbfgsb', 'cg', 'bfgs', 'powell', 'nelder')
                and _is_fitting_failed(result, init_params)):
            # 第一阶段弹窗: 告知原方法失败, 即将降级
            _emit_fallback_warning(
                method=method,
                original_result=original_result,
                fallback_result=None,
                original_chisqr=original_chisqr,
                fallback_chisqr=0.0,
            )
            print(f"  [自动降级] {method} → differential_evolution")
            # 用 DE 重试
            try:
                de_pm = Parameters()
                for key, value in init_params.items():
                    if key.endswith('_min') or key.endswith('_max'):
                        continue
                    umin = init_params.get(f'{key}_min', None)
                    umax = init_params.get(f'{key}_max', None)
                    mn, mx = _compute_adaptive_bounds(
                        value, 'differential_evolution',
                        user_min=umin, user_max=umax)
                    de_pm.add(key, value=value, min=mn, max=mx)
                de_minner = Minimizer(
                    fcn2min, de_pm, fcn_args=(freq, circuit, ZData),
                    max_nfev=METHOD_MAX_NFEV.get('differential_evolution', int(1e5)))
                result = de_minner.minimize(method='differential_evolution')
                fallback_used = True
                fallback_chisqr = float(getattr(result, 'chisqr', float('inf')))
                # 第二阶段弹窗: 显示降级前后完整对比
                _emit_fallback_warning(
                    method=method,
                    original_result=original_result,
                    fallback_result=result,
                    original_chisqr=original_chisqr,
                    fallback_chisqr=fallback_chisqr,
                )
            except Exception as e:
                print(f"  [降级失败] {e}")

        return {
            'result': result,
            'method': 'differential_evolution' if fallback_used else 'standard',
            'original_result': original_result if fallback_used else None,
            'original_method': original_method if fallback_used else None,
            'fallback_chain': [
                (original_method, 'failed', original_chisqr, 'max_err>50%'),
                ('differential_evolution', 'success',
                 float(getattr(result, 'chisqr', 0.0)), 'auto-degrade'),
            ] if fallback_used else [],
            'fallback_reason': 'method result abnormal' if fallback_used else '',
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
        # 收紧 ±inf 兜底，避免 differential_evolution/dual_annealing 抛
        # 'requires finite bound for all varying parameters'
        pmin = param.min if np.isfinite(param.min) else 1e-15
        pmax = param.max if np.isfinite(param.max) else 1e15
        # 防止下界 > 上界
        if pmin >= pmax:
            pmin, pmax = 1e-15, 1e15
        init_params[f'{name}_min'] = pmin
        init_params[f'{name}_max'] = pmax

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




