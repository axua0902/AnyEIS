# -*- coding: utf-8 -*-
"""
真实算例验证脚本（yeast cell）—— 用于回应审稿意见（Reviewer 4 Major Comment 2）

目的
----
Reviewer 4 要求："Section 1 highlights potential applications in lithium-ion
batteries, cell biology, and electrochemical corrosion. A representative
experimental example from at least one of these areas would strengthen the
evidence for the software's practical applicability. The corresponding datasets
and model settings should be made available to support reproducibility."

本脚本处理真实实验数据 'Impedance of yeast.xlsx'（酵母细胞悬液阻抗谱，
与 Ref. [13] 讨论的细胞生物学/介电弛豫数据一致），完成：

1. 数据读取与清洗（三个浓度：10% / 20% / 30% Living）；
2. 候选等效电路的**模型选择**（比较卡方与残差，给出选型依据）；
3. 定量拟合结果：拟合参数表（含标准误）、约化卡方、残差 RMS、残差随频率分布；
4. 可复现性交付：把处理后的数据导出成 AnyEIS 原生格式（CSV），
   并导出一份模型设置文件（JSON），供论文与复现使用。

被测模块（不做任何修改）
------------------------
- EIS/FittingFile/FittingECM.py        : simuECM / FittingECM / creatdatabaseECM
- EIS/FittingFile/FittingECM_extreme.py: check_parameter_identifiability

关于 CPE 的说明
---------------
与 FittingValidationSynthetic.py 相同：ECM 引擎目前按首字母 R/C/L 解析元件，
'CPE' 元件会被当作理想电容。本脚本在运行时对 EquivCircM.elementsZ 打临时
兼容补丁（仅本进程有效），正式产品化方案见 CPE_SUPPORT_MODIFICATION_PLAN.md。

运行
----
    python FittingValidationYeast.py

输出（写入本文件同目录的 results_yeast/）
---------------------------------------------
    yeast_<tag>_data.csv            处理后的实验数据（AnyEIS 原生列格式）
    yeast_<tag>_fit.csv             逐频率的拟合结果与残差
    yeast_model_comparison.csv      候选电路模型比较表（模型选择依据）
    yeast_fit_params.csv            三个浓度的最终拟合参数表
    yeast_model_settings.json       模型设置（电路/初值/权重/频段）
    yeast_metrics.json              定量指标
    yeast_<tag>_fit.png             Nyquist / Bode / 残差图
    yeast_summary.png               三个浓度汇总图与参数随浓度变化

Created on 2026-11-14
@author: takeilab
"""

import sys
import os
import json
import contextlib
import io

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numpy import pi
from pandas import DataFrame, Series, read_excel
from lmfit import Parameters

from EIS.ModelFile import EquivCircM
from EIS.FittingFile.FittingECM import simuECM, FittingECM, creatdatabaseECM
from EIS.FittingFile.FittingECM_extreme import check_parameter_identifiability

DATA_FILE = os.path.join(_HERE, 'Impedance of yeast.xlsx')
RESULTS_DIR = os.path.join(_HERE, 'results_yeast')

BOUNDS = {
    'R': (1e-3, 1e12),
    'C': (1e-15, 1e-3),
    'CPE': (1e-15, 1e-3),
    'alpha': (0.5, 1.0),
}

# 三个数据块在工作表中的起始列
BLOCKS = [('10% Living', 0), ('20% Living', 7), ('30% Living', 14)]

# 阻抗下限（ohm）：低于该值的点接近仪器噪声底，相对残差会被放大，
# 因此不参与拟合。该阈值会在输出中记录，并在结果中同时给出"含全部数据"的指标，
# 以便复核。
MIN_IMPEDANCE_OHM = 10.0

# 是否允许选用"含 CPE 元件"的电路。
# 注意：ECM 引擎目前把 CPE 当作理想电容（见 CPE_SUPPORT_MODIFICATION_PLAN.md），
#      含 CPE 的模型只有在产品端补齐 CPE 支持后，才能在 GUI 中原样复现。
#      设为 False 时，模型选择只在 R/C 电路中进行（GUI 可直接复现）。
ALLOW_CPE_MODELS = True


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


# -----------------------------------------------------------------------------
# 数据读取
# -----------------------------------------------------------------------------
def load_yeast_block(col0):
    """读取工作表中的一个数据块，返回 (freq, Z, 原始数据DataFrame)

    工作表结构（header=None 读取）：
        row0 : 标题行（'10% Living' / 文件名 / ...）
        row1 : 表头（Frequency[Hz], Z[ohm], PHASE[deg], Rs[ohm], X[ohm]）
        row2+ : 数据
    """
    raw = read_excel(DATA_FILE, sheet_name=0, header=None)
    block = raw.iloc[:, [col0, col0 + 1, col0 + 2, col0 + 3, col0 + 4]].copy()
    block.columns = ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']
    block = block.iloc[2:]                       # 跳过标题行与表头行
    block = block.apply(lambda c: pd.to_numeric(c, errors='coerce'))
    block = block.dropna(subset=['FREQ[Hz]', 'Rs[ohm]', 'X[ohm]'])
    block = block[block['FREQ[Hz]'] > 0]

    # 同一频率存在重复测量时取平均（原始数据中低频段有重复点）
    grouped = block.groupby('FREQ[Hz]', as_index=False).mean()

    freq = grouped['FREQ[Hz]'].to_numpy(float)
    Z = grouped['Rs[ohm]'].to_numpy(float) + 1j * grouped['X[ohm]'].to_numpy(float)
    return freq, Z, grouped


# -----------------------------------------------------------------------------
# 通用工具
# -----------------------------------------------------------------------------
def prodata_from_Z(Z):
    data = DataFrame()
    data['Rs[ohm]'] = Series(np.real(Z))
    data['X[ohm]'] = Series(np.imag(Z))
    return data


def compute_metrics(Z_fit, Z_meas, n_params):
    r = (Z_fit - Z_meas) / np.abs(Z_meas)
    n = len(Z_meas)
    dof = max(2 * n - n_params, 1)
    return {
        'chi2_red': float(np.sum(np.abs(r) ** 2) / dof),
        'rms_rel': float(np.sqrt(np.mean(np.abs(r) ** 2)) * 100.0),
        'rms_abs': float(np.sqrt(np.mean(np.abs(Z_fit - Z_meas) ** 2))),
        'max_rel': float(np.max(np.abs(r)) * 100.0),
    }


def build_params(init_params, factor=1.0):
    pm = Parameters()
    for name, value in init_params.items():
        lo, hi = _bounds_for(name)
        v = value * factor
        if name.startswith('alpha'):
            v = min(max(v, lo), hi)
        pm.add(name, value=v, min=lo, max=hi)
    return pm


def multi_start_fit(freq, prodata, circuit, init_params, n_starts=40, seed=42):
    """多起点全局搜索（FittingECM_extreme.multi_start_fit 的通用化版本，
    后者只支持 3 参数的 R1+p(C3,R6) 结构）"""
    rng = np.random.default_rng(seed)
    Z_meas = prodata['Rs[ohm]'].to_numpy() + 1j * prodata['X[ohm]'].to_numpy()
    best, best_err, n_ok = None, np.inf, 0

    for i in range(n_starts):
        factor = 1.0 if i == 0 else float(10 ** rng.uniform(-1, 1))
        pm = build_params(init_params, factor=factor)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                result = FittingECM(pm, freq, circuit, prodata)
        except Exception:
            continue
        Z_fit, _ = simuECM(result.params, circuit, freq)
        if not np.all(np.isfinite(Z_fit)):
            continue
        n_ok += 1
        err = float(np.sum(np.abs((Z_fit - Z_meas) / np.abs(Z_meas)) ** 2))
        if err < best_err:
            best_err, best = err, result
    return best, n_ok


# -----------------------------------------------------------------------------
# 候选电路模型（模型选择依据）
# -----------------------------------------------------------------------------
CANDIDATE_MODELS = {
    'M1: R1 + (C1||R2)': {
        'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')'],
        'init': {'R1': 2.0, 'C1': 1e-11, 'R2': 1200.0},
        'requires_cpe': False,
    },
    'M2: R1 + (CPE1||R2)': {
        'circuit': ['R1', '+', 'p(', 'CPE1', ',', 'R2', ')'],
        'init': {'R1': 2.0, 'CPE1': 1e-11, 'alphaCPE1': 0.9, 'R2': 1200.0},
        'requires_cpe': True,
    },
    'M3: R1 + (C1||R2) + (C3||R3)': {
        'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'p(', 'C3', ',', 'R3', ')'],
        'init': {'R1': 2.0, 'C1': 1e-11, 'R2': 1200.0, 'C3': 1e-12, 'R3': 200.0},
        'requires_cpe': False,
    },
    'M4: R1 + (CPE1||R2) + (C2||R3)': {
        'circuit': ['R1', '+', 'p(', 'CPE1', ',', 'R2', ')', '+', 'p(', 'C2', ',', 'R3', ')'],
        'init': {'R1': 2.0, 'CPE1': 1e-11, 'alphaCPE1': 0.9, 'R2': 1200.0,
                 'C2': 1e-12, 'R3': 200.0},
        'requires_cpe': True,
    },
}


def fit_models(freq, Z, n_starts=60, seed=42):
    """对全部候选电路做多起点拟合，返回结果列表（用于模型选择）"""
    prodata = prodata_from_Z(Z)
    results = []
    for tag, spec in CANDIDATE_MODELS.items():
        if spec['requires_cpe'] and not ALLOW_CPE_MODELS:
            continue
        best, n_ok = multi_start_fit(freq, prodata, spec['circuit'],
                                      spec['init'], n_starts=n_starts, seed=seed)
        if best is None:
            continue
        Z_fit, _ = simuECM(best.params, spec['circuit'], freq)
        metrics = compute_metrics(Z_fit, Z, len(spec['init']))
        results.append({
            'model': tag,
            'circuit': spec['circuit'],
            'n_params': len(spec['init']),
            'init_params': spec['init'],
            'requires_cpe': spec['requires_cpe'],
            'params': {k: float(best.params[k].value) for k in spec['init']},
            'stderr': {k: float(best.params[k].stderr or np.nan) for k in spec['init']},
            'metrics': metrics,
            'Z_fit': Z_fit,
            'n_starts_ok': n_ok,
        })
    return results


# -----------------------------------------------------------------------------
# 绘图 / 导出
# -----------------------------------------------------------------------------
def plot_fit(tag, freq, Z_data, Z_fit, title, fname):
    r = (Z_fit - Z_data) / np.abs(Z_data)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))

    ax = axes[0]
    ax.plot(Z_data.real, -Z_data.imag, 'o', ms=4, mfc='none', mec='#1f77b4',
            label='data')
    ax.plot(Z_fit.real, -Z_fit.imag, '-', lw=1.8, color='#d62728', label='fit')
    ax.set_xlabel("Z' (ohm)"); ax.set_ylabel("-Z'' (ohm)")
    ax.set_title('Nyquist'); ax.grid(alpha=0.3); ax.legend()

    ax = axes[1]
    ax.loglog(freq, np.abs(Z_data), 'o', ms=4, mfc='none', mec='#1f77b4',
              label='|Z| data')
    ax.loglog(freq, np.abs(Z_fit), '-', lw=1.8, color='#d62728', label='|Z| fit')
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


def export_data(freq, Z, fname):
    """用 AnyEIS 的 creatdatabaseECM 导出原生格式数据（便于在 GUI 中直接打开）"""
    db = creatdatabaseECM(freq, Z)
    db.to_csv(os.path.join(RESULTS_DIR, fname), index=False)
    return db


def export_fit(freq, Z_data, Z_fit, fname):
    db = creatdatabaseECM(freq, Z_fit)
    r = (Z_fit - Z_data) / np.abs(Z_data)
    db['Z_data_real[ohm]'] = np.real(Z_data)
    db['Z_data_imag[ohm]'] = np.imag(Z_data)
    db['residual_real_pct'] = r.real * 100
    db['residual_imag_pct'] = r.imag * 100
    db.to_csv(os.path.join(RESULTS_DIR, fname), index=False)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    install_cpe_support()

    print('=' * 78)
    print('真实算例：yeast cell 阻抗谱（来自 Impedance of yeast.xlsx）')
    print('=' * 78)

    comparison_rows = []
    param_rows = []
    metrics_all = {}
    summary = {}
    all_results = {}
    datasets = {}

    for tag, col0 in BLOCKS:
        freq_all, Z_all, raw = load_yeast_block(col0)
        mask = np.abs(Z_all) >= MIN_IMPEDANCE_OHM
        freq, Z = freq_all[mask], Z_all[mask]
        n_excluded = int((~mask).sum())
        print(f'\n----- {tag} : {len(freq_all)} points, '
              f'{freq_all.min():.3e} ~ {freq_all.max():.3e} Hz '
              f'(排除 |Z| < {MIN_IMPEDANCE_OHM} ohm 的 {n_excluded} 点，'
              f'参与拟合 {len(freq)} 点) -----')

        results = fit_models(freq, Z)
        results.sort(key=lambda d: d['metrics']['chi2_red'])
        all_results[tag] = results
        datasets[tag] = (freq_all, Z_all, freq, Z, n_excluded)

        print(f'{"model":>32} {"nPar":>5} {"chi2_red":>12} {"RMSrel(%)":>10} '
              f'{"maxRes(%)":>10}')
        for d in results:
            m = d['metrics']
            print(f'{d["model"]:>32} {d["n_params"]:>5} {m["chi2_red"]:>12.4e} '
                  f'{m["rms_rel"]:>10.3f} {m["max_rel"]:>10.3f}')
            comparison_rows.append({
                'dataset': tag, 'model': d['model'], 'n_params': d['n_params'],
                'requires_cpe': d['requires_cpe'],
                'chi2_red': m['chi2_red'], 'rms_rel_pct': m['rms_rel'],
                'rms_abs_ohm': m['rms_abs'], 'max_rel_pct': m['max_rel'],
            })

    # ---------------- 统一模型选择（三个浓度使用同一等效电路） ----------------
    model_names = [r['model'] for r in all_results[BLOCKS[0][0]]]
    pooled = {}
    for name in model_names:
        vals = []
        for tag, _ in BLOCKS:
            for d in all_results[tag]:
                if d['model'] == name:
                    vals.append(d['metrics']['chi2_red'])
        pooled[name] = float(np.mean(vals))
    selected_model = min(pooled, key=pooled.get)

    print('\n' + '=' * 78)
    print('模型选择（三个浓度合并判据：平均约化卡方）')
    print('-' * 78)
    for name, val in sorted(pooled.items(), key=lambda kv: kv[1]):
        mark = '  <= 选定' if name == selected_model else ''
        needs_cpe = any(d['requires_cpe'] for tag, _ in BLOCKS
                        for d in all_results[tag] if d['model'] == name)
        cpe_mark = '  (含 CPE, 需产品端支持)' if needs_cpe else ''
        print(f'  {name:>32}  mean chi2_red = {val:.4e}{mark}{cpe_mark}')
    if CANDIDATE_MODELS[selected_model]['requires_cpe']:
        print('  NOTE: 选定模型含 CPE 元件。当前 ECM 引擎尚未实现 CPE，'
              'GUI 中复现需先落实 CPE_SUPPORT_MODIFICATION_PLAN.md；')
        print('        若暂不修改产品，可将 ALLOW_CPE_MODELS 设为 False，'
              '改用 R/C 电路（GUI 可直接复现）。')

    for tag, _ in BLOCKS:
        freq_all, Z_all, freq, Z, n_excluded = datasets[tag]

        best = next(d for d in all_results[tag] if d['model'] == selected_model)
        m = best['metrics']
        print(f'\n----- {tag}: 选定模型 {best["model"]} -----')
        print(f'{"parameter":>12} {"fitted":>16} {"stderr":>14}')
        for name, value in best['params'].items():
            print(f'{name:>12} {value:>16.6e} {best["stderr"][name]:>14.3e}')

        # 特征频率与低频截距（解释性信息）
        note = []
        if 'C1' in best['params'] and 'R2' in best['params']:
            fc = 1.0 / (2 * pi * best['params']['R2'] * best['params']['C1'])
            note.append(f'f_c = 1/(2*pi*R2*C1) = {fc:.4g} Hz')
        if 'CPE1' in best['params'] and 'R2' in best['params']:
            Q, n = best['params']['CPE1'], best['params']['alphaCPE1']
            fc = 1.0 / (2 * pi * (best['params']['R2'] * Q) ** (1.0 / n))
            note.append(f'f_c (CPE) = {fc:.4g} Hz')
        if 'R2' in best['params']:
            note.append(f'低频截距 R1+R2 = '
                        f'{best["params"]["R1"] + best["params"]["R2"]:.4g} ohm')
        for s in note:
            print('  ' + s)

        try:
            ident = check_parameter_identifiability(freq, init_params=best['init_params'])
            print(f'  可辨识性: {ident["status"]} (f_char={ident["f_char"]:.4g} Hz) '
                  f'- {ident["reason"]}')
        except Exception:
            ident = {}

        print(f'  约化卡方 chi2_red = {m["chi2_red"]:.4e}')
        print(f'  残差 RMS (相对)   = {m["rms_rel"]:.3f} %')
        print(f'  残差 RMS (绝对)   = {m["rms_abs"]:.4f} ohm')
        print(f'  最大相对残差      = {m["max_rel"]:.3f} %')

        # 用同一组参数对"全部数据点"重新评估指标（便于复核阻抗下限阈值的影响）
        pm_best = Parameters()
        for k, v in best['params'].items():
            pm_best.add(k, value=v)
        Z_fit_all, _ = simuECM(pm_best, best['circuit'], freq_all)
        metrics_full = compute_metrics(Z_fit_all, Z_all, best['n_params'])
        print(f'  [含全部数据点] chi2_red = {metrics_full["chi2_red"]:.4e}, '
              f'RMSrel = {metrics_full["rms_rel"]:.3f} %, '
              f'maxRes = {metrics_full["max_rel"]:.3f} %')

        # 导出
        slug = tag.split()[0]
        export_data(freq, Z, f'yeast_{slug}_data.csv')
        export_fit(freq, Z, best['Z_fit'], f'yeast_{slug}_fit.csv')
        plot_fit(slug, freq, Z, best['Z_fit'],
                 f'Yeast cell {tag}: ECM fit (model {best["model"]})',
                 f'yeast_{slug}_fit.png')

        for name, value in best['params'].items():
            param_rows.append({
                'dataset': tag, 'model': best['model'], 'parameter': name,
                'fitted_value': value, 'stderr': best['stderr'][name],
                'requires_cpe': best['requires_cpe'],
                'chi2_red': m['chi2_red'], 'rms_rel_pct': m['rms_rel'],
                'rms_abs_ohm': m['rms_abs'], 'max_rel_pct': m['max_rel'],
            })

        metrics_all[tag] = {'model': best['model'], 'metrics': m,
                            'requires_cpe': best['requires_cpe'],
                            'metrics_full_range': metrics_full,
                            'params': best['params'], 'stderr': best['stderr'],
                            'identifiability': ident, 'notes': note,
                            'n_points_total': int(len(freq_all)),
                            'n_points_used': int(len(freq)),
                            'n_points_excluded_below_impedance_floor': n_excluded,
                            'impedance_floor_ohm': MIN_IMPEDANCE_OHM,
                            'freq_range_Hz': [float(freq.min()), float(freq.max())]}
        summary[tag] = {'Z_data': Z, 'Z_fit': best['Z_fit'], 'freq': freq,
                        'model': best['model'], 'params': best['params']}

    # ---------------- 汇总输出 ----------------
    DataFrame(comparison_rows).to_csv(
        os.path.join(RESULTS_DIR, 'yeast_model_comparison.csv'), index=False)
    DataFrame(param_rows).to_csv(
        os.path.join(RESULTS_DIR, 'yeast_fit_params.csv'), index=False)

    with open(os.path.join(RESULTS_DIR, 'yeast_metrics.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(metrics_all, fh, indent=2, ensure_ascii=False)

    # 模型设置文件（可复现性交付物）
    settings = {
        'dataset_file': os.path.basename(DATA_FILE),
        'dataset_description': '酵母细胞悬液阻抗谱（MHz-GHz），来自 Ref. [13] 相关实验数据',
        'blocks': {tag: {'columns_in_sheet': col0} for tag, col0 in BLOCKS},
        'preprocessing': ['跳过标题行与表头行',
                          '丢弃缺失值与非正频率',
                          '同频率重复测量取平均',
                          '按频率排序',
                          f'剔除 |Z| < {MIN_IMPEDANCE_OHM} ohm 的点（接近仪器噪声底）'],
        'weighting': 'relative error |Z_fit - Z_meas| / |Z_meas| '
                     '(同 FittingECM.fcn2min 的归一化方式)',
        'optimizer': 'lmfit least_squares, loss=soft_l1, '
                     '多起点对数空间搜索 (n_starts=60, seed=42)',
        'candidate_models': {k: {'circuit': v['circuit'], 'init': v['init'],
                                 'requires_cpe': v['requires_cpe']}
                             for k, v in CANDIDATE_MODELS.items()},
        'selected_model': {tag: metrics_all[tag]['model'] for tag, _ in BLOCKS},
        'selected_model_requires_cpe': CANDIDATE_MODELS[selected_model]['requires_cpe'],
        'reproducibility_note':
            '含 CPE 的模型需要在 GUI 中先实现 CPE 元件支持'
            '（见 CPE_SUPPORT_MODIFICATION_PLAN.md）；'
            '将 ALLOW_CPE_MODELS 设为 False 可得到纯 R/C 的可复现模型。',
    }
    with open(os.path.join(RESULTS_DIR, 'yeast_model_settings.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)

    # 汇总图：三个浓度叠加 + 参数随浓度变化
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for (tag, _), color in zip(BLOCKS, colors):
        s = summary[tag]
        axes[0].plot(s['Z_data'].real, -s['Z_data'].imag, 'o', ms=3, mfc='none',
                      mec=color, label=f'{tag} data')
        axes[0].plot(s['Z_fit'].real, -s['Z_fit'].imag, '-', lw=1.6, color=color,
                     label=f'{tag} fit')
    axes[0].set_xlabel("Z' (ohm)"); axes[0].set_ylabel("-Z'' (ohm)")
    axes[0].set_title('Nyquist (all concentrations)'); axes[0].grid(alpha=0.3)
    axes[0].legend(fontsize=8)

    for (tag, _), color in zip(BLOCKS, colors):
        s = summary[tag]
        axes[1].loglog(s['freq'], np.abs(s['Z_data']), 'o', ms=3, mfc='none',
                       mec=color, label=f'{tag}')
    axes[1].set_xlabel('Frequency (Hz)'); axes[1].set_ylabel('|Z| (ohm)')
    axes[1].set_title('Bode magnitude'); axes[1].grid(alpha=0.3, which='both')
    axes[1].legend(fontsize=8)

    conc = [float(t.split('%')[0]) for t, _ in BLOCKS]
    r2_vals = [summary[t]['params'].get('R2', np.nan) for t, _ in BLOCKS]
    axes[2].plot(conc, r2_vals, 'o-', color='#d62728')
    axes[2].set_xlabel('yeast concentration (%)')
    axes[2].set_ylabel('parallel resistance R2 (ohm)')
    axes[2].set_title('R2 vs concentration'); axes[2].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'yeast_summary.png'), dpi=200)
    plt.close(fig)

    print('\n' + '=' * 78)
    print('汇总（用于论文表格）')
    print('-' * 78)
    print(f'{"dataset":>12} {"model":>30} {"chi2_red":>12} {"RMSrel(%)":>10} '
          f'{"maxRes(%)":>10}')
    for tag, _ in BLOCKS:
        d = metrics_all[tag]
        m = d['metrics']
        print(f'{tag:>12} {d["model"]:>30} {m["chi2_red"]:>12.4e} '
              f'{m["rms_rel"]:>10.3f} {m["max_rel"]:>10.3f}')

    print(f'\n结果已写入: {RESULTS_DIR}')


if __name__ == '__main__':
    main()
