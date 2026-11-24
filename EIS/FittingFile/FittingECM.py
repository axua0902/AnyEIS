
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

import os
import io
import contextlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from numpy import pi, real, imag, angle, sqrt
from pandas import DataFrame, Series

from lmfit import Minimizer, Parameters, report_fit

from EIS.ModelFile.EquivCircM import SearchParallel, CalculateParallel, CalculateSeries

# FittingWarnings 兼容多种导入方式（绝对/相对/直接），保证不同运行环境都能加载
try:
    # 1) 绝对导入（与 Fitting.py 风格一致，从项目根目录运行时）
    from EIS.FittingFile.FittingWarnings import (
        warn as _emit_warning,
        info as _emit_info,
        warn_fallback as _emit_fallback_warning,
    )
except ImportError:
    try:
        # 2) 相对导入（作为包内模块加载时）
        from .FittingWarnings import (
            warn as _emit_warning,
            info as _emit_info,
            warn_fallback as _emit_fallback_warning,
        )
    except ImportError:
        # 3) 直接导入（从 EIS/FittingFile/ 目录运行 Funtest 测试时）
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
            可选引擎级控制参数（不透传给 scipy，仅全局方法生效）:
                n_jobs  : 多解性多起点并行进程数（默认 None = 按机器核数
                          自适应，1 = 串行）。并行与串行结果逐位一致，
                          不损失拟合精度
                de_seed : 确定性种子。传入后整个拟合过程可复现，且结果
                          与并行进程数/机器核数无关（GUI 生产路径固定
                          传入，保证任意机器上结果逐位一致）

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

    # P0 修复: 统一从 result.params 取物理参数值写回。
    # lmfit 1.3.x 中仅 least_squares 的 result.x 等于物理参数值;
    # differential_evolution / nelder / lbfgsb / powell / cg / bfgs 走
    # penalty(apply_bounds_transformation=True) 的内部变换, result.x 处于
    # 角度/变换空间(实测 DE 的 x ∈ [-pi/2, pi/2]), 直接写回会被 lmfit
    # 钳位到参数边界, 拟合曲线完全错误(实测 rms_rel ≈ 100%);
    # ampgo 路径则无 result.x。lmfit 对所有方法都会把物理值写入
    # result.params[name].value, 因此统一用它。
    for name in result.var_names:
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


def _is_fitting_failed(result, init_params, max_error_threshold=0.5,
                       rms_residual_threshold=0.10, check_drift=True):
    """
    问题 4 修复: 判断拟合是否失败

    失败特征(任一满足即判失败):
        1. 至少一个参数相对误差 > 50%（参数漂移异常, 仅 check_drift=True 时检查）
        2. P4 补充: 拟合残差 RMS > 10%（质量门槛）
           least_squares 等局部方法在残差雅可比病态时(如 CPE 的 Q/n
           强简并, 实测 cond(J)~1e15) 会停在初值附近不动 —— 参数漂移
           为 0%, 但 chi2 很差, 仅靠参数漂移检测不到, 必须直接检查
           拟合质量。阈值标定: 正常拟合 rms_rel ≈ 1.3%(合成数据,
           1% 噪声) ~ 3.5%(酵母实测), 坏拟合 > 15%, 取 10% 留余量。
           result.residual 即 fcn2min 的相对误差残差(lmfit 存的是
           scipy 的原始残差, 不受 robust loss 缩放影响)。

    check_drift=False 用于 least_squares: 漂移准则对 LS 方向是反的 ——
    健康的 LS 拟合必然把参数从粗初值移走(实测合成数据初值偏差 ~50%
    即被判"失败"), 而真正病态的 LS 停在初值不动(漂移≈0%)反而测不出。
    LS 只用残差 RMS 门槛判定。
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
        if check_drift and errors and max(errors) > max_error_threshold:
            return True

        # P4: 质量门槛 —— 拟合残差 RMS(相对误差)
        residual = getattr(result, 'residual', None)
        if residual is not None and np.size(residual) > 0:
            rms = float(np.sqrt(np.mean(
                np.asarray(residual, dtype=float) ** 2)))
            if np.isfinite(rms) and rms > rms_residual_threshold:
                return True
        return False
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


# =============================================================================
# A2 优化: 并行拟合基础设施（自适应进程数 + 多起点并行 + 数据集级批量并行）
# =============================================================================
_ENGINE_POOL = None
_ENGINE_POOL_WORKERS = 0


def _auto_n_jobs(user=None, n_tasks=None):
    """自适应并行进程数（根据计算机实际情况使用不同核数）

    优先级:
        1. user 显式传入的进程数（None 表示自动）
        2. 环境变量 ANYEIS_FIT_WORKERS（'0'/'1' = 强制串行）
        3. CPU 逻辑核数 - 1（预留 1 核给系统/GUI），不超过任务数 n_tasks
    环境变量 ANYEIS_FIT_PARALLEL=0 可完全关闭并行（返回 1）。

    返回值只影响速度，不影响任何拟合结果（确定性播种保证结果
    与并行进程数无关）。
    """
    env = os.environ.get('ANYEIS_FIT_PARALLEL', '1').strip().lower()
    if env in ('0', 'false', 'no', 'off'):
        return 1
    val = user
    env_w = os.environ.get('ANYEIS_FIT_WORKERS', '').strip()
    if val is None and env_w:
        try:
            val = int(env_w)
        except ValueError:
            pass
    if val is not None:
        return max(1, int(val))
    try:
        cpu = os.cpu_count() or 1
    except Exception:
        cpu = 1
    workers = max(1, cpu - 1)
    if n_tasks is not None:
        workers = min(workers, int(n_tasks))
    return max(1, workers)


def _engine_pool(n_jobs):
    """惰性创建/复用引擎级进程池；不可用时返回 None

    进程池在所有并行入口（多起点并行、数据集级批量并行）间共享。
    并行执行与串行执行结果逐位一致（确定性播种），因此进程池
    不可用时回退串行不影响任何结果。

    注: PyInstaller 冻结环境需在程序入口调用 multiprocessing.freeze_support()
    （main.py 已添加），否则应设 ANYEIS_FIT_PARALLEL=0 关闭并行。
    """
    global _ENGINE_POOL, _ENGINE_POOL_WORKERS
    n_jobs = max(1, int(n_jobs))
    if _ENGINE_POOL is None or _ENGINE_POOL_WORKERS < n_jobs:
        try:
            if _ENGINE_POOL is not None:
                _ENGINE_POOL.shutdown(wait=False)
            _ENGINE_POOL = ProcessPoolExecutor(max_workers=n_jobs)
            _ENGINE_POOL_WORKERS = n_jobs
        except Exception:
            _ENGINE_POOL, _ENGINE_POOL_WORKERS = None, 0
            return None
    return _ENGINE_POOL


def _start_seed(rng_seed, de_seed, i):
    """由 (rng_seed, de_seed, 起点序号) 派生每个起点的确定性随机种子

    种子确定 ⇒ 单个起点的 DE 求解只依赖自己的种子，与执行顺序、
    串行/并行方式均无关，因此并行结果与串行逐位一致，且同一环境下
    重复运行逐位可复现。
    """
    return (int(rng_seed) * 100003 + int(de_seed) * 7919
            + int(i) * 104729) % (2 ** 31 - 1)


def _multistart_worker(payload):
    """多起点并行的 worker：独立完成单个起点的全局拟合

    payload: (i, R1_start, spec, freq, circuit, ZData, method,
              max_nfev, start_seed)
        spec: [(name, value, min, max), ...]（顺序即参数添加顺序）
    返回: (i, chisqr, lmfit Result 或 None)
    """
    i, R1_start, spec, freq, circuit, ZData, method, max_nfev, seed = payload
    _worker_set_silent()
    pm = Parameters()
    for name, val, pmin, pmax in spec:
        pm.add(name, value=val, min=pmin, max=pmax)
    if seed is not None:
        np.random.seed(seed)
    try:
        minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData),
                           max_nfev=max_nfev)
        r = minner.minimize(method=method)
        return i, float(getattr(r, 'chisqr', float('inf'))), r
    except Exception:
        return i, float('inf'), None


def _worker_set_silent():
    """在并行 worker 子进程中关闭 Qt 弹窗警告

    Windows spawn 下 worker 重新导入模块，静默标志回到默认 False；
    worker 无 QApplication 时弹窗会使进程终止，故必须重新启用。
    静默模式仅把警告改为打印，不影响任何拟合数值。
    """
    try:
        try:
            from EIS.FittingFile.FittingWarnings import set_silent_mode
        except ImportError:
            try:
                from .FittingWarnings import set_silent_mode
            except ImportError:
                from FittingWarnings import set_silent_mode
        set_silent_mode(True)
    except Exception:
        pass


def _dataset_fit_worker(task):
    """数据集级批量并行 worker：完成单个数据集的完整智能拟合

    task: (params, freq, circuit, prodata, method, fit_kwargs)
    返回: lmfit Result；失败返回 None（由调用方回退串行重算）。
    """
    params, freq, circuit, prodata, method, fit_kwargs = task
    _worker_set_silent()
    de_seed = fit_kwargs.get('de_seed')
    if de_seed is not None:
        np.random.seed(int(de_seed))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return auto_fitting(params, freq, circuit, prodata,
                                method=method, **fit_kwargs)
    except Exception:
        return None


def parallel_fit_datasets(tasks, n_jobs=None):
    """数据集级批量并行拟合（GUI 多数据集批量拟合加速入口）

    tasks: [(params, freq, circuit, prodata, method, fit_kwargs), ...]
        注: task 内的 fit_kwargs 应传 n_jobs=1，避免 worker 内嵌套进程池。
    返回: 与 tasks 顺序一致的 Result 列表；任一数据集失败或并行
          不可用时返回 None（调用方回退串行逐个拟合）。
    """
    n = len(tasks)
    if n <= 1:
        return None
    n_jobs = _auto_n_jobs(n_jobs, n_tasks=n)
    if n_jobs <= 1:
        return None
    pool = _engine_pool(n_jobs)
    if pool is None:
        print("[批量并行拟合] 进程池不可用，回退串行")
        return None
    try:
        results = list(pool.map(_dataset_fit_worker, tasks))
    except Exception as e:
        print(f"[批量并行拟合失败: {type(e).__name__}: {str(e)[:60]}]，回退串行")
        return None
    if any(r is None for r in results):
        print("[批量并行拟合] 存在失败数据集，回退串行")
        return None
    return results


def _multi_start_with_R1_constraint(freq, prodata, circuit, init_params,
                                      method, n_starts=10, r1_tighten=10.0,
                                      rng_seed=42, de_seed=None, n_jobs=1):
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
        de_seed: 外层种子（可选）。传入时每个起点用
            _start_seed(rng_seed, de_seed, i) 确定性播种，使每个起点的
            求解与执行顺序无关 —— 这是启用并行(n_jobs>1)的前提。
            不传时保持原有行为（DE 消费全局 RNG 流、串行执行），
            与历史版本逐位兼容（GUI 默认路径不受影响）。
        n_jobs: 内层起点并行进程数（默认 1 串行）。仅当 de_seed
            非空时生效；并行与串行结果逐位一致。

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
    #
    # A2 优化（可选并行）：仅当调用方显式传入 de_seed 时，每个起点在
    # 求解前用 _start_seed(rng_seed, de_seed, i) 确定性播种 —— 每个起点
    # 的 DE 求解只依赖自己的种子，与执行顺序无关，因此并行执行与串行
    # 执行结果逐位一致。不传 de_seed 时保持原有行为：DE 消费全局 RNG
    # 流、串行执行（验证脚本 A1 协议依赖此行为，勿改）。
    parallel = de_seed is not None and n_jobs > 1

    def _start_spec(i):
        """构造第 i 个起点的参数规格 [(name, value, min, max), ...]"""
        R1_start = R1_starts[i]
        spec = []
        for key, value in init_params.items():
            if key.endswith('_min') or key.endswith('_max'):
                continue
            if key == R1_name:
                spec.append((key, R1_start, R1_min, R1_max))
            else:
                pmin = init_params.get(f'{key}_min', None)
                pmax = init_params.get(f'{key}_max', None)
                pmin, pmax = _compute_adaptive_bounds(
                    value, method, user_min=pmin, user_max=pmax
                )
                spec.append((key, value, pmin, pmax))
        return spec

    print(f"  [多起点模式] method={method}, n_starts={n_starts}, "
          f"R1_est={R1_est:.3e}, R1_bounds=[{R1_min:.3e}, {R1_max:.3e}]"
          + (f", parallel n_jobs={n_jobs}" if parallel else ""))

    candidates = []   # [(chisqr, result), ...]，顺序与起点序号一致

    if parallel:
        pool = _engine_pool(n_jobs)
        if pool is not None:
            payloads = [
                (i, R1_starts[i], _start_spec(i), freq, circuit, ZData,
                 method, int(1e4), _start_seed(rng_seed, de_seed, i))
                for i in range(n_starts)
            ]
            try:
                for i, chisqr, r in pool.map(_multistart_worker, payloads):
                    if r is not None and np.isfinite(chisqr):
                        candidates.append((chisqr, r))
            except Exception as e:
                print(f"    [并行多起点失败: {type(e).__name__}: {str(e)[:60]}]，"
                      f"回退串行")
                candidates = []
        else:
            print("    [并行进程池不可用，回退串行]")

    if not candidates:
        # 串行路径：de_seed=None 时为原有行为（全局 RNG 流），
        # de_seed 非空时逐起点确定性播种（与并行结果逐位一致）
        for i, R1_start in enumerate(R1_starts):
            pm = Parameters()
            for name, val, pmin, pmax in _start_spec(i):
                pm.add(name, value=val, min=pmin, max=pmax)

            if de_seed is not None:
                np.random.seed(_start_seed(rng_seed, de_seed, i))

            try:
                minner = Minimizer(fcn2min, pm, fcn_args=(freq, circuit, ZData),
                                   max_nfev=int(1e4))
                r = minner.minimize(method=method)
                chisqr = getattr(r, 'chisqr', float('inf'))
                if np.isfinite(chisqr):
                    candidates.append((chisqr, r))
            except Exception as e:
                # 单个起点失败不影响整体
                print(f"    [start {i+1}/{n_starts}] 失败: {type(e).__name__}: {str(e)[:50]}")
                continue

    best_result = None
    best_chisqr = float('inf')
    for chisqr, r in candidates:
        if chisqr < best_chisqr:
            best_chisqr = chisqr
            best_result = r

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
    # A2 优化: 引擎级控制参数（可选），从 fit_kwargs 中取出，
    # 绝不能透传给 scipy（scipy 不认识这些关键字）。
    #   n_jobs  : 多起点并行进程数（None = 按机器核数自适应，1 = 串行）
    #   de_seed : 确定性种子。传入时先播种全局 RNG（使单点全局方法
    #             也与多起点模式一样可复现），多起点模式下再逐起点
    #             确定性播种 —— 结果只依赖 de_seed，与并行进程数/
    #             机器核数无关（生产路径固定传入）。
    n_jobs_raw = fit_kwargs.pop('n_jobs', None)
    de_seed = fit_kwargs.pop('de_seed', None)
    if de_seed is not None:
        np.random.seed(int(de_seed))
    n_jobs = _auto_n_jobs(n_jobs_raw, n_tasks=10)

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
        # P4: 白名单补上 least_squares —— 它同样是局部方法, 在多解电路
        # (>= 2 个 p(...) 并联支路)上同样容易陷入局部最优/停在初值
        if _detect_multi_solution_risk(circuit) and method in (
                'least_squares', 'nelder', 'powell', 'cg', 'bfgs', 'lbfgsb'):
            # 消息为英汉双语两行格式, 不用 emoji (静默模式打印到 GBK 控制台会报错)
            _emit_warning(
                f"Multi-solution risk detected: {method} is a local "
                f"optimizer and may get stuck in a local minimum.\n"
                f"检测到多解风险：{method} 为局部方法，易陷入局部最优。\n\n"
                f"Suggested global methods / 建议改用全局方法:\n"
                f"  • differential_evolution (recommended / 推荐)\n"
                f"  • dual_annealing (fast / 快)\n"
                f"  • ampgo (most accurate / 最准, but slow / 但慢)\n\n"
                f"Continuing with {method} may give a suboptimal fit.\n"
                f"继续用 {method} 可能得到次优解。"
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
                   # P2 修复: 原硬编码 diff_step=1e-15 + tr_solver='lsmr' +
                   # ftol/xtol=1e-15 + gtol=3e-16 在残差雅可比病态时
                   # 数值上不可用 —— 1e-15 的有限差分步长远小于双精度
                   # 可有效分辨的范围, 数值梯度全是噪声; lsmr 迭代求解
                   # 又进一步放大误差(实测从全局最优解出发 χ² 反而恶化
                   # 一个数量级, 且报 success=True)。
                   # 改为: exact 三角分解 + scipy 默认差分步长 + 1e-10 容差
                   'ftol': 1e-10, 'xtol': 1e-10, 'gtol': 1e-10,
                   'loss': loss, 'max_nfev': int(1e5),
                   'tr_solver': 'exact', 'diff_step': None}
            )
            result = minner.minimize(method='least_squares')
        elif method in ('differential_evolution', 'dual_annealing', 'ampgo'):
            # P1: 多解性/极值量级场景下,自动使用多起点 + R1 物理约束
            if _should_use_multi_start(init_params, method, freq):
                multi_result = _multi_start_with_R1_constraint(
                    freq, prodata, circuit, init_params, method,
                    n_starts=10, r1_tighten=10.0, rng_seed=42,
                    de_seed=de_seed, n_jobs=n_jobs
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

        # P4: 降级白名单补上 least_squares(默认方法, 多解电路下同样
        # 需要失败降级; 原先它停在初值不动, 参数漂移检测不到, 现由
        # _is_fitting_failed 的残差 RMS 门槛兜住)
        if (result is not None
                and method in ('least_squares', 'lbfgsb', 'cg', 'bfgs',
                               'powell', 'nelder')
                and _is_fitting_failed(result, init_params,
                                       check_drift=(method != 'least_squares'))):
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
                # P4: 多解性/极值量级场景与主 DE 分支保持一致,
                # 启用固定种子(rng_seed=42)多起点全局搜索;
                # 单起点 DE 本身也可能落入局部极小
                if _should_use_multi_start(init_params,
                                           'differential_evolution', freq):
                    de_result = _multi_start_with_R1_constraint(
                        freq, prodata, circuit, init_params,
                        'differential_evolution',
                        n_starts=10, r1_tighten=10.0, rng_seed=42,
                        de_seed=de_seed, n_jobs=n_jobs)
                else:
                    de_result = None
                if de_result is None:
                    # 单起点 DE 兜底(原降级路径)
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
                    de_result = de_minner.minimize(
                        method='differential_evolution')
                # P4: 仅当 DE 结果确实更优时才替换(防止降级反而变差);
                # chisqr 两侧均为 sum(fcn2min 残差^2), 可直接比较
                de_chisqr = float(getattr(de_result, 'chisqr', float('inf')))
                if np.isfinite(de_chisqr) and de_chisqr < original_chisqr:
                    result = de_result
                    fallback_used = True
                    fallback_chisqr = de_chisqr
                    # 第二阶段弹窗: 显示降级前后完整对比
                    _emit_fallback_warning(
                        method=method,
                        original_result=original_result,
                        fallback_result=result,
                        original_chisqr=original_chisqr,
                        fallback_chisqr=fallback_chisqr,
                    )
                else:
                    print(f"  [降级取消] DE χ²={de_chisqr:.4e} 不优于 "
                          f"{method} χ²={original_chisqr:.4e}, 保留原结果")
            except Exception as e:
                print(f"  [降级失败] {e}")

        return {
            'result': result,
            'method': 'differential_evolution' if fallback_used else 'standard',
            'original_result': original_result if fallback_used else None,
            'original_method': original_method if fallback_used else None,
            'fallback_chain': [
                (original_method, 'failed', original_chisqr,
                 'rms>10%' if original_method == 'least_squares'
                 else 'param_err>50% or rms>10%'),
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




