# -*- coding: utf-8 -*-
"""
合成算例验证脚本 —— 用于回应审稿意见（Reviewer 2 意见1 / Reviewer 4 Major Comment 1）

目的
----
1. 给出 AnyEIS 等效电路拟合模块的**定量精度证据**（对应 Reviewer 2：
   "the paper states excellent accuracy, but this is not quantitatively evaluated"）：
   真值 -> 仿真 -> 拟合 -> 参数回收误差 / 卡方 / 残差 RMS / 残差随频率分布。
2. 给出 Reviewer 4 要求的"复杂度递增"算例：
   - 算例 1：双时间常数电路（两个 RC 串联支路），验证软件能否分离两个相近的弛豫；
   - 算例 2：CPE 非理想元件电路，验证 n 指数与 Q 的回收精度；
   - 算例 3：双时间常数 + CPE 组合电路。
3. 所有算例的真值已知，因此"拟合精度"可以被独立复核；真实实验数据（yeast cell）
   见同目录下的 FittingValidationYeast.py。

被测模块（不做任何修改）
------------------------
- EIS/FittingFile/FittingECM.py        : simuECM / fcn2min / FittingECM / creatdatabaseECM
- EIS/FittingFile/FittingECM_extreme.py: check_parameter_identifiability（可辨识性诊断）

关于 CPE 的说明（重要）
-----------------------
当前 EIS/ModelFile/EquivCircM.py 的 elementsZ() 只按首字母 R/C/L 解析元件，
因此名为 'CPE1' 的元件会被当作**理想电容**处理，ECM 模块目前无法真正拟合 CPE
（GUI 下拉框中的 'CPE' 仅是界面占位）。

为了在不改动任何已有源文件的前提下完成 CPE 验证，本脚本在运行时对
EquivCircM.elementsZ 打了一个**临时兼容补丁**（见 install_cpe_support），
约定：
    参数 'CPE1'  -> Q (F·s^(n-1))
    参数 'alphaCPE1' -> n (无量纲, 0.5 <= n <= 1.0)
补丁仅在本测试进程内有效，不影响 GUI 与其它模块。
正式产品化的修改方案见同目录 CPE_SUPPORT_MODIFICATION_PLAN.md。

运行
----
    python FittingValidationSynthetic.py

输出（写入本文件同目录的 results_synthetic/）
------------------------------------------------
    synthetic_case1_2RC_params.csv   算例1 各 τ 比值下的参数回收表
    synthetic_case2_CPE_params.csv   算例2 CPE 参数回收表
    synthetic_case3_2RC_CPE_params.csv 算例3 参数回收表
    synthetic_metrics.json            全部算例的定量指标（卡方/残差RMS/最大偏差）
    synthetic_case*.csv               每个算例的逐频率数据与拟合结果
    synthetic_case*.png               Nyquist / Bode / 残差图
    synthetic_tau_sweep.png           参数回收误差 vs 时间常数比值

Created on 2026-11-14
@author: takeilab
"""

import sys
import os
import json
import contextlib
import io

# 让脚本可以从任意工作目录运行
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numpy import pi, logspace
from pandas import DataFrame, Series
from lmfit import Parameters

from EIS.ModelFile import EquivCircM
from EIS.FittingFile.FittingECM import simuECM, FittingECM, creatdatabaseECM
from EIS.FittingFile.FittingECM_extreme import check_parameter_identifiability

RESULTS_DIR = os.path.join(_HERE, 'results_synthetic')

# -----------------------------------------------------------------------------
# 参数边界（物理合理范围）
# -----------------------------------------------------------------------------
BOUNDS = {
    'R': (1e-3, 1e12),
    'C': (1e-15, 1e-3),
    'CPE': (1e-15, 1e-3),
    'alpha': (0.5, 1.0),
}


def _bounds_for(name):
    if name.startswith('alpha'):
        return BOUNDS['alpha']
    if name.startswith('CPE'):
        return BOUNDS['CPE']
    if name.startswith('C'):
        return BOUNDS['C']
    return BOUNDS['R']


# -----------------------------------------------------------------------------
# CPE 运行时兼容补丁（不修改任何已有源文件）
# -----------------------------------------------------------------------------
_CPE_PATCHED = False


def install_cpe_support():
    """让 ECM 引擎能够识别 CPE 元件（仅本进程有效）。

    约定：元件名 'CPE1' 对应参数 'CPE1'(Q) 与 'alphaCPE1'(n)。
    正式产品化方案见 CPE_SUPPORT_MODIFICATION_PLAN.md。
    """
    global _CPE_PATCHED
    if _CPE_PATCHED:
        return
    original = EquivCircM.elementsZ

    def elementsZ_with_cpe(element, pm, freq):
        if element.startswith('CPE'):
            Q = pm[element].value
            n = pm['alpha' + element].value
            return 1.0 / (Q * (1j * 2 * pi * freq) ** n)
        return original(element, pm, freq)

    EquivCircM.elementsZ = elementsZ_with_cpe
    _CPE_PATCHED = True
    print('[INFO] 已启用 CPE 运行时兼容补丁 (EquivCircM.elementsZ)')
    print('[INFO] 正式产品化方案见 CPE_SUPPORT_MODIFICATION_PLAN.md\n')


# -----------------------------------------------------------------------------
# 通用工具
# -----------------------------------------------------------------------------
def add_measurement_noise(Z_true, noise_level, seed=None):
    """按 |Z| 加性高斯噪声（与 Funtest 目录下其它测试脚本保持一致的风格）"""
    rng = np.random.default_rng(seed)
    noise = noise_level * (rng.standard_normal(len(Z_true))
                           + 1j * rng.standard_normal(len(Z_true)))
    return Z_true + noise * np.abs(Z_true)


def prodata_from_Z(Z):
    """构造 FittingECM 需要的 prodata（'Rs[ohm]' / 'X[ohm]'）"""
    data = DataFrame()
    data['Rs[ohm]'] = Series(np.real(Z))
    data['X[ohm]'] = Series(np.imag(Z))
    return data


def compute_metrics(Z_fit, Z_meas, n_params):
    """定量指标（全部基于相对误差归一化，与 fcn2min 的残差定义一致）

    chi2_red : 约化卡方 = sum(|r|^2) / (2N - p),  r = (Z_fit - Z_meas)/|Z_meas|
    rms_rel  : 相对残差均方根 (%)
    rms_abs  : 绝对残差均方根 (ohm)
    max_rel  : 最大相对偏差 (%)
    """
    r = (Z_fit - Z_meas) / np.abs(Z_meas)
    n = len(Z_meas)
    dof = max(2 * n - n_params, 1)
    return {
        'chi2_red': float(np.sum(np.abs(r) ** 2) / dof),
        'rms_rel': float(np.sqrt(np.mean(np.abs(r) ** 2)) * 100.0),
        'rms_abs': float(np.sqrt(np.mean(np.abs(Z_fit - Z_meas) ** 2))),
        'max_rel': float(np.max(np.abs(r)) * 100.0),
    }


def build_params(init_params, rng=None, factor=1.0):
    """根据初值字典构造 lmfit Parameters；rng 不为空时对初值做对数空间扰动"""
    pm = Parameters()
    for name, value in init_params.items():
        lo, hi = _bounds_for(name)
        v = value
        if rng is not None and factor != 1.0:
            v = value * factor
        if name.startswith('alpha'):
            v = min(max(v, lo), hi)
        pm.add(name, value=v, min=lo, max=hi)
    return pm


def multi_start_fit(freq, prodata, circuit, init_params, n_starts=30, seed=42):
    """多起点全局搜索（策略与 FittingECM_extreme.multi_start_fit 一致，
    但不限制参数个数：FittingECM_extreme.multi_start_fit 仅支持 3 参数的
    R1+p(C3,R6) 结构，本脚本需要 4~6 参数的电路）。

    返回 (best_result, n_success)
    """
    rng = np.random.default_rng(seed)
    best, best_err, n_ok = None, np.inf, 0

    for i in range(n_starts):
        if i == 0:
            factor = 1.0                      # 第 0 个起点使用给定的初始猜测
        else:
            factor = float(10 ** rng.uniform(-1, 1))
        pm = build_params(init_params, rng=rng, factor=factor)
        try:
            with contextlib.redirect_stdout(io.StringIO()):   # 抑制 lmfit 的逐次输出
                result = FittingECM(pm, freq, circuit, prodata)
        except Exception:
            continue
        Z_fit, _ = simuECM(result.params, circuit, freq)
        if not np.all(np.isfinite(Z_fit)):
            continue
        n_ok += 1
        Z_meas = prodata['Rs[ohm]'].to_numpy() + 1j * prodata['X[ohm]'].to_numpy()
        err = float(np.sum(np.abs((Z_fit - Z_meas) / np.abs(Z_meas)) ** 2))
        if err < best_err:
            best_err, best = err, result

    return best, n_ok


def fit_case(circuit, true_params, init_params, freq, noise_level=0.01,
             seed=42, n_starts=30, use_multistart=True):
    """完整算例：真值 -> 仿真 -> 加噪 -> 拟合 -> 指标"""
    pm_true = Parameters()
    for name, value in true_params.items():
        pm_true.add(name, value=value)
    Z_true, _ = simuECM(pm_true, circuit, freq)

    Z_noisy = add_measurement_noise(Z_true, noise_level, seed=seed)
    prodata = prodata_from_Z(Z_noisy)

    if use_multistart:
        result, n_ok = multi_start_fit(freq, prodata, circuit, init_params,
                                       n_starts=n_starts, seed=seed)
    else:
        pm = build_params(init_params)
        with contextlib.redirect_stdout(io.StringIO()):
            result = FittingECM(pm, freq, circuit, prodata)
        n_ok = 1

    Z_fit, _ = simuECM(result.params, circuit, freq)
    metrics = compute_metrics(Z_fit, Z_noisy, len(true_params))

    # 拟合模型与"真值模型"的偏差：用于区分"拟合不准"与"逆问题多解"
    # （若该偏差很小，说明拟合参数与真值参数给出几乎相同的阻抗响应，
    #   参数上的偏差来源于等效电路分解的不唯一性，而非拟合失败）
    dev = (Z_fit - Z_true) / np.abs(Z_true)
    metrics['model_vs_truth_max_dev_pct'] = float(np.max(np.abs(dev)) * 100.0)
    metrics['model_vs_truth_rms_pct'] = float(np.sqrt(np.mean(np.abs(dev) ** 2)) * 100.0)

    fitted = {name: float(result.params[name].value) for name in true_params}
    rel_err = {name: abs(fitted[name] - v) / abs(v) * 100.0
               for name, v in true_params.items()}

    # 参数可辨识性诊断（FittingECM_extreme 提供）：判断特征频率是否落在测量窗口内
    try:
        ident = check_parameter_identifiability(freq, init_params=init_params)
    except Exception:
        ident = {'status': 'n/a', 'f_char': float('nan'),
                 'identifiable': True, 'reason': 'diagnostic failed'}

    return {
        'true': dict(true_params),
        'fitted': fitted,
        'rel_err_pct': rel_err,
        'max_rel_err_pct': float(max(rel_err.values())),
        'metrics': metrics,
        'Z_true': Z_true,
        'Z_noisy': Z_noisy,
        'Z_fit': Z_fit,
        'freq': freq,
        'n_starts_ok': n_ok,
        'success': bool(result.success),
        'identifiability': ident,
        'stderr': {name: float(result.params[name].stderr or np.nan)
                   for name in true_params},
    }


# -----------------------------------------------------------------------------
# 绘图
# -----------------------------------------------------------------------------
def plot_case(case, title, fname):
    freq = case['freq']
    Z_n, Z_f = case['Z_noisy'], case['Z_fit']
    r = (Z_f - Z_n) / np.abs(Z_n)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))

    ax = axes[0]
    ax.plot(Z_n.real, -Z_n.imag, 'o', ms=4, mfc='none', mec='#1f77b4', label='data')
    ax.plot(Z_f.real, -Z_f.imag, '-', lw=1.8, color='#d62728', label='fit')
    ax.set_xlabel("Z' (ohm)"); ax.set_ylabel("-Z'' (ohm)")
    ax.set_title('Nyquist'); ax.grid(alpha=0.3); ax.legend()

    ax = axes[1]
    ax.loglog(freq, np.abs(Z_n), 'o', ms=4, mfc='none', mec='#1f77b4', label='|Z| data')
    ax.loglog(freq, np.abs(Z_f), '-', lw=1.8, color='#d62728', label='|Z| fit')
    ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('|Z| (ohm)')
    ax.set_title('Bode'); ax.grid(alpha=0.3, which='both'); ax.legend()

    ax = axes[2]
    ax.semilogx(freq, r.real * 100, 'o', ms=4, mfc='none', mec='#1f77b4',
                label="dZ'/Z")
    ax.semilogx(freq, r.imag * 100, 's', ms=4, mfc='none', mec='#2ca02c',
                label="dZ''/Z")
    ax.axhline(0, color='k', lw=0.8)
    ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('relative residual (%)')
    ax.set_title('Residuals'); ax.grid(alpha=0.3, which='both'); ax.legend()

    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, fname), dpi=200)
    plt.close(fig)


# -----------------------------------------------------------------------------
# 算例 1：双时间常数（两个 RC 支路串联）
# -----------------------------------------------------------------------------
CIRCUIT_2RC = ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'p(', 'C2', ',', 'R3', ')']


def case_dual_time_constant(tau_ratio=10.0, seed=42, n_starts=40):
    """R1 + (C1||R2) + (C2||R3)，两个时间常数 tau2/tau1 = tau_ratio"""
    R1, R2, R3 = 50.0, 200.0, 500.0
    C1 = 1e-7
    tau1 = R2 * C1
    C2 = tau_ratio * tau1 / R3

    true_params = {'R1': R1, 'C1': C1, 'R2': R2, 'C2': C2, 'R3': R3}
    # 初值偏离真值（串联电阻 1.6 倍，电容 3 倍），用于检验优化器的收敛能力
    init_params = {'R1': 80.0, 'C1': 3e-7, 'R2': 200.0, 'C2': C2 * 0.3, 'R3': 500.0}

    freq = logspace(0, 6, 121)          # 0.1 Hz ~ 1 MHz (6 个数量级)
    case = fit_case(CIRCUIT_2RC, true_params, init_params, freq,
                    noise_level=0.01, seed=seed, n_starts=n_starts)
    case['tau_ratio'] = tau_ratio
    case['f1_Hz'] = 1.0 / (2 * pi * R2 * C1)
    case['f2_Hz'] = 1.0 / (2 * pi * R3 * C2)
    return case


# -----------------------------------------------------------------------------
# 算例 2：CPE 非理想元件
# -----------------------------------------------------------------------------
CIRCUIT_CPE = ['R1', '+', 'p(', 'CPE1', ',', 'R2', ')']


def case_cpe(seed=42, n_starts=40):
    """R1 + (CPE1||R2)，检验 n 与 Q 的回收精度"""
    R1, R2 = 50.0, 200.0
    Q1, n1 = 1e-6, 0.90

    true_params = {'R1': R1, 'CPE1': Q1, 'alphaCPE1': n1, 'R2': R2}
    init_params = {'R1': 80.0, 'CPE1': Q1 * 3, 'alphaCPE1': 0.80, 'R2': 150.0}

    freq = logspace(0, 6, 121)
    case = fit_case(CIRCUIT_CPE, true_params, init_params, freq,
                    noise_level=0.01, seed=seed, n_starts=n_starts)
    return case


# -----------------------------------------------------------------------------
# 算例 3：双时间常数 + CPE 组合
# -----------------------------------------------------------------------------
CIRCUIT_2RC_CPE = ['R1', '+', 'p(', 'CPE1', ',', 'R2', ')',
                    '+', 'p(', 'C2', ',', 'R3', ')']


def case_dual_with_cpe(seed=42, n_starts=60):
    """R1 + (CPE1||R2) + (C2||R3)，同时包含非理想元件与两个时间常数"""
    R1, R2, R3 = 50.0, 200.0, 500.0
    Q1, n1 = 1e-6, 0.90
    C2 = 2e-6

    true_params = {'R1': R1, 'CPE1': Q1, 'alphaCPE1': n1, 'R2': R2,
                   'C2': C2, 'R3': R3}
    init_params = {'R1': 80.0, 'CPE1': Q1 * 3, 'alphaCPE1': 0.80, 'R2': 150.0,
                   'C2': C2 * 0.3, 'R3': 800.0}

    freq = logspace(0, 6, 121)
    case = fit_case(CIRCUIT_2RC_CPE, true_params, init_params, freq,
                    noise_level=0.01, seed=seed, n_starts=n_starts)
    return case


# -----------------------------------------------------------------------------
# 报告
# -----------------------------------------------------------------------------
def print_case(case, title):
    print('=' * 78)
    print(title)
    print('-' * 78)
    print(f'{"parameter":>12} {"true":>14} {"fitted":>14} {"rel.err(%)":>11} {"stderr":>12}')
    for name, tv in case['true'].items():
        fv = case['fitted'][name]
        se = case['stderr'].get(name, float('nan'))
        print(f'{name:>12} {tv:>14.6e} {fv:>14.6e} '
              f'{case["rel_err_pct"][name]:>11.3f} {se:>12.3e}')
    m = case['metrics']
    print(f'  max parameter error : {case["max_rel_err_pct"]:.3f} %')
    print(f'  reduced chi-square  : {m["chi2_red"]:.4e}')
    print(f'  residual RMS (rel)  : {m["rms_rel"]:.3f} %')
    print(f'  residual RMS (abs)  : {m["rms_abs"]:.4f} ohm')
    print(f'  max residual        : {m["max_rel"]:.3f} %')
    print(f'  fitted model vs. true model : max {m["model_vs_truth_max_dev_pct"]:.3f} % / '
          f'rms {m["model_vs_truth_rms_pct"]:.3f} %')
    print(f'  successful starts   : {case["n_starts_ok"]}')
    ident = case.get('identifiability', {})
    if ident:
        print(f'  identifiability     : {ident.get("status")} '
              f'(f_char={ident.get("f_char", float("nan")):.4g} Hz) '
              f'- {ident.get("reason", "")}')
    if case['max_rel_err_pct'] > 10.0 and m['model_vs_truth_max_dev_pct'] < 5.0:
        print('  NOTE: 拟合参数与真值参数给出的阻抗响应几乎一致，'
              '参数偏差来自等效电路分解的')
        print('        不唯一性（多解性），而不是拟合失败；'
              '此时应报告残差而不是单一参数的真值。')


def save_case_data(case, stem):
    df = DataFrame()
    df['FREQ[Hz]'] = case['freq']
    df['Z_true_real[ohm]'] = np.real(case['Z_true'])
    df['Z_true_imag[ohm]'] = np.imag(case['Z_true'])
    df['Z_data_real[ohm]'] = np.real(case['Z_noisy'])
    df['Z_data_imag[ohm]'] = np.imag(case['Z_noisy'])
    df['Z_fit_real[ohm]'] = np.real(case['Z_fit'])
    df['Z_fit_imag[ohm]'] = np.imag(case['Z_fit'])
    r = (case['Z_fit'] - case['Z_noisy']) / np.abs(case['Z_noisy'])
    df['residual_real_pct'] = r.real * 100
    df['residual_imag_pct'] = r.imag * 100
    df.to_csv(os.path.join(RESULTS_DIR, stem + '_data.csv'), index=False)


def save_params_table(case, stem):
    rows = []
    for name, tv in case['true'].items():
        rows.append({
            'parameter': name,
            'true_value': tv,
            'fitted_value': case['fitted'][name],
            'rel_err_pct': case['rel_err_pct'][name],
            'stderr': case['stderr'].get(name, float('nan')),
            'chi2_red': case['metrics']['chi2_red'],
            'residual_rms_rel_pct': case['metrics']['rms_rel'],
            'residual_rms_abs_ohm': case['metrics']['rms_abs'],
            'max_residual_pct': case['metrics']['max_rel'],
        })
    DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, stem + '_params.csv'), index=False)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    install_cpe_support()

    all_metrics = {}

    # ---------------- 算例 1：双时间常数（含 tau 比值扫描） ----------------
    print('\n########## 算例 1：双时间常数电路 R1 + (C1||R2) + (C2||R3) ##########\n')
    sweep = []
    for ratio in [100.0, 30.0, 10.0, 5.0, 3.0]:
        case = case_dual_time_constant(tau_ratio=ratio)
        print_case(case, f'Case 1: tau2/tau1 = {ratio:g} '
                         f'(f1={case["f1_Hz"]:.4g} Hz, f2={case["f2_Hz"]:.4g} Hz)')
        sweep.append(case)
        if ratio == 10.0:
            save_case_data(case, 'synthetic_case1_2RC')
            save_params_table(case, 'synthetic_case1_2RC')
            plot_case(case,
                      'Case 1: two time constants, tau2/tau1 = 10 (1% noise)',
                      'synthetic_case1_2RC.png')
            all_metrics['case1_2RC_tau_ratio_10'] = {
                'metrics': case['metrics'],
                'max_rel_err_pct': case['max_rel_err_pct'],
                'rel_err_pct': case['rel_err_pct'],
            }

    # tau 比值扫描图
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    names = list(sweep[0]['true'].keys())
    for name in names:
        xs = [c['tau_ratio'] for c in sweep]
        ys = [c['rel_err_pct'][name] for c in sweep]
        ax.semilogx(xs, ys, 'o-', label=name)
    ax.set_xlabel('time-constant ratio  tau2/tau1')
    ax.set_ylabel('parameter recovery error (%)')
    ax.set_title('Case 1: parameter recovery vs. relaxation separation')
    ax.grid(alpha=0.3, which='both'); ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'synthetic_tau_sweep.png'), dpi=200)
    plt.close(fig)

    DataFrame([{'tau_ratio': c['tau_ratio'],
                **{f'{k}_err_pct': v for k, v in c['rel_err_pct'].items()},
                **{f'{k}_true': v for k, v in c['true'].items()},
                **{f'{k}_fit': v for k, v in c['fitted'].items()}}
               for c in sweep]).to_csv(
        os.path.join(RESULTS_DIR, 'synthetic_case1_2RC_params.csv'), index=False)

    # 单起点 vs 多起点 对比（说明初始化策略的作用）
    case_single = case_dual_time_constant(tau_ratio=10.0)
    case_single = fit_case(CIRCUIT_2RC,
                            {'R1': 50.0, 'C1': 1e-7, 'R2': 200.0,
                             'C2': (10.0 * 200.0 * 1e-7) / 500.0, 'R3': 500.0},
                            {'R1': 80.0, 'C1': 3e-7, 'R2': 200.0,
                             'C2': (10.0 * 200.0 * 1e-7) / 500.0 * 0.3, 'R3': 500.0},
                            logspace(0, 6, 121), noise_level=0.01, seed=42,
                            n_starts=1, use_multistart=False)
    print_case(case_single, 'Case 1 (single start, for comparison)')

    # ---------------- 算例 2：CPE ----------------
    print('\n########## 算例 2：CPE 非理想元件 R1 + (CPE1||R2) ##########\n')
    case2 = case_cpe()
    print_case(case2, 'Case 2: CPE element (Q and n recovery)')
    save_case_data(case2, 'synthetic_case2_CPE')
    save_params_table(case2, 'synthetic_case2_CPE')
    plot_case(case2, 'Case 2: CPE element, 1% noise', 'synthetic_case2_CPE.png')
    all_metrics['case2_CPE'] = {'metrics': case2['metrics'],
                                 'max_rel_err_pct': case2['max_rel_err_pct'],
                                 'rel_err_pct': case2['rel_err_pct']}

    # ---------------- 算例 3：双时间常数 + CPE ----------------
    print('\n########## 算例 3：双时间常数 + CPE 组合 ##########\n')
    case3 = case_dual_with_cpe()
    print_case(case3, 'Case 3: CPE branch + RC branch')
    save_case_data(case3, 'synthetic_case3_2RC_CPE')
    save_params_table(case3, 'synthetic_case3_2RC_CPE')
    plot_case(case3, 'Case 3: dual time constant with CPE, 1% noise',
              'synthetic_case3_2RC_CPE.png')
    all_metrics['case3_2RC_CPE'] = {'metrics': case3['metrics'],
                                    'max_rel_err_pct': case3['max_rel_err_pct'],
                                    'rel_err_pct': case3['rel_err_pct']}

    # ---------------- 汇总 ----------------
    all_metrics['case1_2RC_tau_ratio_10_single_start'] = {
        'metrics': case_single['metrics'],
        'max_rel_err_pct': case_single['max_rel_err_pct'],
        'rel_err_pct': case_single['rel_err_pct'],
    }
    all_metrics['case1_2RC_tau_sweep'] = [
        {'tau_ratio': c['tau_ratio'], 'max_rel_err_pct': c['max_rel_err_pct'],
         'rel_err_pct': c['rel_err_pct'], 'metrics': c['metrics']} for c in sweep]
    all_metrics['noise_level'] = 0.01
    all_metrics['frequency_range_Hz'] = [1.0, 1e6]

    with open(os.path.join(RESULTS_DIR, 'synthetic_metrics.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(all_metrics, fh, indent=2, ensure_ascii=False)

    print('\n' + '=' * 78)
    print('汇总（用于论文表格）')
    print('-' * 78)
    print(f'{"case":>34} {"maxParamErr(%)":>15} {"chi2_red":>12} '
          f'{"RMSrel(%)":>10} {"maxRes(%)":>10} {"modelDev(%)":>12}')
    for key in ['case1_2RC_tau_ratio_10', 'case1_2RC_tau_ratio_10_single_start',
                'case2_CPE', 'case3_2RC_CPE']:
        d = all_metrics[key]
        m = d['metrics']
        print(f'{key:>34} {d["max_rel_err_pct"]:>15.3f} {m["chi2_red"]:>12.3e} '
              f'{m["rms_rel"]:>10.3f} {m["max_rel"]:>10.3f} '
              f'{m.get("model_vs_truth_max_dev_pct", float("nan")):>12.3f}')

    print(f'\n结果已写入: {RESULTS_DIR}')


if __name__ == '__main__':
    main()
