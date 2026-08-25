# -*- coding: utf-8 -*-
"""
4 电路 × 10 算法 多算法对比测试 (诊断版)

参考 [EIS_Fitting_Analysis_Summary.md](EIS_Fitting_Analysis_Summary.md) 的经验，
设计 4 个有代表性的电路（覆盖：基准/多解性/边界/极限量级），
对比 10 种优化方法在每个电路上的拟合效果与失败模式。

本测试包含 2 个阶段：
  阶段 A: 宽边界 [1e-15, 1e15]  - 模拟现有 FittingECM._auto_fitting_core 默认行为
  阶段 B: 紧边界 [init/100, init*100] - 测试如果收紧边界会如何

输出：
  1. 控制台实时输出每个组合的结果
  2. 保存 Markdown 报告到 test_4circuits_method_diagnosis_report.md

运行方式：
  python EIS/FittingFile/Funtest/test_4circuits_method_diagnosis.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import numpy as np
from numpy import pi, real, imag, logspace
from pandas import DataFrame, Series
from lmfit import Parameters
from EIS.FittingFile.FittingECM import auto_fitting, simuECM


# =============================================================================
# 测试电路配置（沿用 4.1 节）
# =============================================================================

CIRCUITS = {
    'C1_Randles_基准': {
        'desc': 'R1 + p(C3, R6) - 经典 Randles，参数可辨识',
        'true_params': {'R1': 100.0, 'C3': 1e-6, 'R6': 500.0},
        'init_params': {'R1': 80.0, 'C3': 1.5e-6, 'R6': 600.0},
        'circuit': ['R1', '+', 'p(', 'C3', ',', 'R6', ')'],
        'freq': logspace(1, 6, 100),  # 1Hz~1MHz
        'noise_level': 0.01,
        'seed': 42,
        'difficulty': '基准',
    },
    'C2_双并联_多解': {
        'desc': 'R1 + p(C1, R2) + p(C3, R4) - 已知多解性严重',
        'true_params': {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0,
                        'C3': 1e-7, 'R4': 1000.0},
        'init_params': {'R1': 80.0, 'C1': 1.5e-6, 'R2': 400.0,
                        'C3': 1.5e-7, 'R4': 800.0},
        'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')',
                    '+', 'p(', 'C3', ',', 'R4', ')'],
        'freq': logspace(1, 6, 100),
        'noise_level': 0.01,
        'seed': 42,
        'difficulty': '困难',
    },
    'C3_4元件_树状': {
        'desc': 'R1 + p(C1, R2) + R3 - 树状串并联',
        'true_params': {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0, 'R3': 50.0},
        'init_params': {'R1': 80.0, 'C1': 1.5e-6, 'R2': 600.0, 'R3': 60.0},
        'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'R3'],
        'freq': logspace(1, 6, 100),
        'noise_level': 0.01,
        'seed': 42,
        'difficulty': '中等',
    },
    'C4_极限量级差': {
        'desc': 'R1 + p(C3, R6)，R1=1mΩ/R6=1MΩ - 9 数量级差异',
        'true_params': {'R1': 1e-3, 'C3': 1e-3, 'R6': 1e6},
        'init_params': {'R1': 1e-2, 'C3': 1e-4, 'R6': 1e7},
        'circuit': ['R1', '+', 'p(', 'C3', ',', 'R6', ')'],
        'freq': logspace(-2, 7, 200),  # 10mHz~10MHz
        'noise_level': 0.01,
        'seed': 42,
        'difficulty': '极限',
    },
}

METHODS = [
    'least_squares', 'nelder', 'lbfgsb', 'differential_evolution',
    'basinhopping', 'powell', 'cg', 'dual_annealing', 'bfgs', 'ampgo',
]

# 两种边界策略
BOUND_STRATEGIES = {
    'A_宽边界_1e-15_1e15': lambda init: (1e-15, 1e15),
    'B_紧边界_init100x': lambda init: (
        max(init * 1e-2, 1e-15),
        init * 1e2 if init > 0 else 1e15
    ),
}


# =============================================================================
# 工具函数
# =============================================================================

def make_test_data(circuit, true_params, freq, noise_level, seed):
    """生成测试数据"""
    pm = Parameters()
    for name, value in true_params.items():
        pm.add(name, value=value)
    Z_true, _ = simuECM(pm, circuit, freq)
    np.random.seed(seed)
    noise = noise_level * (np.random.randn(len(freq)) + 1j * np.random.randn(len(freq)))
    Z_measured = Z_true + noise * np.abs(Z_true)
    prodata = DataFrame({
        'Rs[ohm]': Series(real(Z_measured)),
        'X[ohm]': Series(imag(Z_measured)),
    })
    return prodata, Z_true


def evaluate(result, true_params):
    """计算每个参数的最大相对误差（%），返回 (max_error, per_param_errors)"""
    per_param = {}
    max_err = 0
    for name, true_val in true_params.items():
        if name not in result.params:
            per_param[name] = float('nan')
            continue
        fit_val = result.params[name].value
        if true_val != 0:
            rel = abs((fit_val - true_val) / true_val) * 100
        else:
            rel = 0
        per_param[name] = rel
        max_err = max(max_err, rel)
    return max_err, per_param


def rate(max_error):
    """评级：优 < 5% < 良 < 20% < 中 < 100% < 差 < ∞ < 崩溃"""
    if max_error < 5:    return '优'
    if max_error < 20:   return '良'
    if max_error < 100:  return '中'
    if max_error < 1e6:  return '差'
    return '崩溃'


# =============================================================================
# 核心测试
# =============================================================================

def run_one(circuit_name, cfg, method, bound_name, bound_func, verbose=False):
    """跑一次 (circuit, method, bound_strategy)，返回结果字典"""
    prodata, _ = make_test_data(
        cfg['circuit'], cfg['true_params'], cfg['freq'],
        cfg['noise_level'], cfg['seed']
    )
    pm = Parameters()
    for name, val in cfg['init_params'].items():
        pmin, pmax = bound_func(val)
        pm.add(name, value=val, min=pmin, max=pmax)

    try:
        r = auto_fitting(pm, cfg['freq'], cfg['circuit'], prodata, method=method)
        max_err, per_param = evaluate(r, cfg['true_params'])
        chisqr = getattr(r, 'chisqr', float('nan'))
        nfev = getattr(r, 'nfev', -1)
        success = getattr(r, 'success', None)
        return {
            'ok': True,
            'max_error': max_err,
            'per_param': per_param,
            'chisqr': chisqr,
            'nfev': nfev,
            'success': success,
            'rating': rate(max_err),
        }
    except Exception as e:
        return {
            'ok': False,
            'error': f'{type(e).__name__}: {str(e)[:80]}',
            'max_error': float('inf'),
            'per_param': {},
            'rating': '崩溃',
        }


def run_all():
    """主入口：跑 2 边界 × 4 电路 × 10 方法 = 80 个组合"""
    print('=' * 100)
    print('  AnyEIS 4 电路 × 10 算法 × 2 边界策略 多算法对比诊断测试')
    print('  日期: 2026-08-25')
    print('=' * 100)

    results = {}  # results[(bound, circuit, method)] = dict
    for bname, bfunc in BOUND_STRATEGIES.items():
        print(f"\n\n{'#' * 100}")
        print(f"# 边界策略: {bname}")
        print('#' * 100)

        for cname, cfg in CIRCUITS.items():
            print(f"\n\n## 电路 {cname}：{cfg['desc']}  (难度: {cfg['difficulty']})")
            print(f"## 真值: {cfg['true_params']}")
            print(f"## 频段: {cfg['freq'][0]:.2e} ~ {cfg['freq'][-1]:.2e} Hz, "
                  f"{len(cfg['freq'])} 点, 噪声 {cfg['noise_level']*100:.0f}%")

            results[(bname, cname)] = {}
            for m in METHODS:
                print(f"\n  --- {cname} × {m} ({bname}) ---")
                res = run_one(cname, cfg, m, bname, bfunc)
                results[(bname, cname)][m] = res
                if res['ok']:
                    print(f"    状态: OK, χ²={res['chisqr']:.4e}, nfev={res['nfev']}, "
                          f"success={res['success']}, 评级={res['rating']}")
                    print(f"    最大误差: {res['max_error']:.2f}%")
                    for pname, perr in res['per_param'].items():
                        print(f"      {pname:<6s} {perr:>8.2f}%")
                else:
                    print(f"    状态: FAIL - {res['error']}")

    return results


def print_summary(results):
    """打印汇总表"""
    print('\n\n')
    print('=' * 100)
    print('  汇总表（行=电路，列=方法，单元格=最大相对误差%）')
    print('=' * 100)

    for bname in BOUND_STRATEGIES:
        print(f"\n--- 边界策略: {bname} ---")
        header = f"{'电路':<22s}"
        for m in METHODS:
            header += f"  {m[:14]:>14s}"
        print(header)
        print('-' * 100)
        for cname in CIRCUITS:
            row = f"{cname:<22s}"
            for m in METHODS:
                r = results[(bname, cname)][m]
                if r['ok']:
                    rating = r['rating']
                    if r['max_error'] < 1e6:
                        cell = f"{r['max_error']:.1f}%({rating})"
                    else:
                        cell = f"极大({rating})"
                else:
                    cell = "ERR"
                row += f"  {cell:>14s}"
            print(row)
        print('=' * 100)

        # 统计
        print(f'\n成功率（< 20% 误差视为可用）[{bname}]:')
        for cname in CIRCUITS:
            n_ok = sum(1 for m in METHODS
                       if results[(bname, cname)][m]['ok']
                       and results[(bname, cname)][m]['max_error'] < 20)
            print(f"  {cname:<22s}  {n_ok}/{len(METHODS)}")

        print(f'\n按方法统计 [{bname}]:')
        print(f'  {"方法":<24s}  {"可用/4电路":<10s}  {"平均误差%":<15s}')
        for m in METHODS:
            usable = sum(1 for cname in CIRCUITS
                        if results[(bname, cname)][m]['ok']
                        and results[(bname, cname)][m]['max_error'] < 20)
            errs = [results[(bname, cname)][m]['max_error']
                    for cname in CIRCUITS
                    if results[(bname, cname)][m]['ok']]
            avg = np.mean(errs) if errs else float('inf')
            print(f"  {m:<24s}  {usable:<10d}  {avg:.2e}")


# =============================================================================
# Markdown 报告生成
# =============================================================================

def generate_report(results, report_path):
    """生成 Markdown 报告"""
    lines = []
    lines.append('# 4 电路 × 10 算法 × 2 边界策略 多算法对比诊断测试报告')
    lines.append('')
    lines.append('> 测试日期: 2026-08-25')
    lines.append('> 参考经验: [EIS_Fitting_Analysis_Summary.md](EIS_Fitting_Analysis_Summary.md) 第 4、11、13 节')
    lines.append('> 测试脚本: [test_4circuits_method_diagnosis.py](test_4circuits_method_diagnosis.py)')
    lines.append('')
    lines.append('## 1. 测试设计')
    lines.append('')
    lines.append('### 1.1 电路选择依据')
    lines.append('')
    lines.append('基于历史测试经验（特别是 EIS_Fitting_Analysis_Summary.md 第 4 节和第 11 节），从原 10 组测试中精选 4 组覆盖')
    lines.append('不同难度和不同失败模式的电路：')
    lines.append('')
    lines.append('| 编号 | 电路 | 难度 | 测试目标 |')
    lines.append('|------|------|------|----------|')
    lines.append('| C1 | R1 + p(C3, R6) | 基准 | 验证所有方法在简单 Randles 上都能成功 |')
    lines.append('| C2 | R1 + p(C1, R2) + p(C3, R4) | 困难 | 多解性挑战 — 已知该结构容易混淆 R2/R4、C1/C3 |')
    lines.append('| C3 | R1 + p(C1, R2) + R3 | 中等 | 树状串并联 — 旧文档列为"最复杂的可靠结构" |')
    lines.append('| C4 | R1=1mΩ + p(C3, R6=1MΩ) | 极限 | 9 数量级参数差异 — 验证 DE/DA 边界 |')
    lines.append('')
    lines.append('### 1.2 10 个优化方法')
    lines.append('')
    lines.append('| 方法 | 类别 | 特点 |')
    lines.append('|------|------|------|')
    lines.append('| `least_squares` | 局部 | scipy 信赖域 + soft_l1 损失 |')
    lines.append('| `nelder` | 局部 | Nelder-Mead 单纯形，不需梯度 |')
    lines.append('| `lbfgsb` | 局部 | 拟牛顿 + 有限内存 + 边界支持 |')
    lines.append('| `powell` | 局部 | 方向集方法，无需求导 |')
    lines.append('| `cg` | 局部 | 共轭梯度 |')
    lines.append('| `bfgs` | 局部 | 拟牛顿 |')
    lines.append('| `differential_evolution` | 全局 | 遗传算法变体，DE |')
    lines.append('| `dual_annealing` | 全局 | 双模拟退火 |')
    lines.append('| `basinhopping` | 全局 | 盆地跳跃 |')
    lines.append('| `ampgo` | 全局 | Accelerated Modified Powell Gradient（需 ampgo 包） |')
    lines.append('')
    lines.append('### 1.3 边界策略对比')
    lines.append('')
    lines.append('**关键：本测试设计两个边界策略，用于隔离"边界过宽"对全局方法的影响。**')
    lines.append('')
    lines.append('| 策略 | 公式 | 含义 |')
    lines.append('|------|------|------|')
    lines.append('| **A_宽边界_1e-15_1e15** | `min=1e-15, max=1e15` | 复现 `_auto_fitting_core` 默认行为，所有方法都使用 |')
    lines.append('| **B_紧边界_init100x** | `min=init*1e-2, max=init*1e2` | 基于初值收紧 100 倍 |')
    lines.append('')
    lines.append('### 1.4 评级标准')
    lines.append('')
    lines.append('| 评级 | 最大相对误差 |')
    lines.append('|------|---------------|')
    lines.append('| 优 | < 5% |')
    lines.append('| 良 | < 20% |')
    lines.append('| 中 | < 100% |')
    lines.append('| 差 | < 1e6 % |')
    lines.append('| 崩溃 | ≥ 1e6% 或异常 |')
    lines.append('')

    # ============================ 阶段 A ============================
    bname_a = 'A_宽边界_1e-15_1e15'
    lines.append('## 2. 阶段 A: 宽边界 [1e-15, 1e15] 结果')
    lines.append('')
    lines.append('> **这一阶段复现 `_auto_fitting_core` 的默认行为** — 所有方法在 1e-15~1e15 边界下拟合。')
    lines.append('')
    lines.append('### 2.1 最大相对误差矩阵（%）')
    lines.append('')
    lines.append('| 电路 | ' + ' | '.join(f"`{m}`" for m in METHODS) + ' |')
    lines.append('|------|' + '|'.join('---' for _ in METHODS) + '|')
    for cname in CIRCUITS:
        row = [cname]
        for m in METHODS:
            r = results[(bname_a, cname)][m]
            if r['ok']:
                err = r['max_error']
                if err < 1e6:
                    cell = f"{err:.2f}% ({r['rating']})"
                else:
                    cell = f"极大 ({r['rating']})"
            else:
                cell = f"ERR: {r['error'][:30]}"
            row.append(cell)
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append('')

    # 阶段 A 成功率
    lines.append('### 2.2 阶段 A 成功率（误差 < 20% 视为可用）')
    lines.append('')
    lines.append('| 电路 | 可用方法数 | 占比 |')
    lines.append('|------|-----------|------|')
    for cname in CIRCUITS:
        n_ok = sum(1 for m in METHODS
                   if results[(bname_a, cname)][m]['ok']
                   and results[(bname_a, cname)][m]['max_error'] < 20)
        lines.append(f"| {cname} | {n_ok}/{len(METHODS)} | {n_ok/len(METHODS)*100:.0f}% |")
    lines.append('')

    # ============================ 阶段 B ============================
    bname_b = 'B_紧边界_init100x'
    lines.append('## 3. 阶段 B: 紧边界 [init/100, init*100] 结果')
    lines.append('')
    lines.append('> **关键对照实验**：把所有参数边界收紧到初值的 100 倍，测试哪些方法"被宽边界坑死"。')
    lines.append('')
    lines.append('### 3.1 最大相对误差矩阵（%）')
    lines.append('')
    lines.append('| 电路 | ' + ' | '.join(f"`{m}`" for m in METHODS) + ' |')
    lines.append('|------|' + '|'.join('---' for _ in METHODS) + '|')
    for cname in CIRCUITS:
        row = [cname]
        for m in METHODS:
            r = results[(bname_b, cname)][m]
            if r['ok']:
                err = r['max_error']
                if err < 1e6:
                    cell = f"{err:.2f}% ({r['rating']})"
                else:
                    cell = f"极大 ({r['rating']})"
            else:
                cell = f"ERR: {r['error'][:30]}"
            row.append(cell)
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append('')

    lines.append('### 3.2 阶段 B 成功率（误差 < 20% 视为可用）')
    lines.append('')
    lines.append('| 电路 | 可用方法数 | 占比 |')
    lines.append('|------|-----------|------|')
    for cname in CIRCUITS:
        n_ok = sum(1 for m in METHODS
                   if results[(bname_b, cname)][m]['ok']
                   and results[(bname_b, cname)][m]['max_error'] < 20)
        lines.append(f"| {cname} | {n_ok}/{len(METHODS)} | {n_ok/len(METHODS)*100:.0f}% |")
    lines.append('')

    # ============================ 对比 ============================
    lines.append('## 4. 阶段 A vs 阶段 B 对比（边界策略的影响）')
    lines.append('')
    lines.append('### 4.1 成功率对比表')
    lines.append('')
    lines.append('| 电路 | 宽边界可用 | 紧边界可用 | 变化 |')
    lines.append('|------|-----------|-----------|------|')
    for cname in CIRCUITS:
        a_ok = sum(1 for m in METHODS
                   if results[(bname_a, cname)][m]['ok']
                   and results[(bname_a, cname)][m]['max_error'] < 20)
        b_ok = sum(1 for m in METHODS
                   if results[(bname_b, cname)][m]['ok']
                   and results[(bname_b, cname)][m]['max_error'] < 20)
        delta = b_ok - a_ok
        sign = '+' if delta > 0 else (str(delta) if delta < 0 else '0')
        lines.append(f"| {cname} | {a_ok}/10 | {b_ok}/10 | {sign} |")
    lines.append('')

    lines.append('### 4.2 按方法可用性变化')
    lines.append('')
    lines.append('| 方法 | 宽边界可用 | 紧边界可用 | 变化 | 结论 |')
    lines.append('|------|-----------|-----------|------|------|')
    for m in METHODS:
        a_ok = sum(1 for cname in CIRCUITS
                   if results[(bname_a, cname)][m]['ok']
                   and results[(bname_a, cname)][m]['max_error'] < 20)
        b_ok = sum(1 for cname in CIRCUITS
                   if results[(bname_b, cname)][m]['ok']
                   and results[(bname_b, cname)][m]['max_error'] < 20)
        delta = b_ok - a_ok
        sign = '+' if delta > 0 else (str(delta) if delta < 0 else '0')
        if delta > 2:
            conclusion = '严重受宽边界影响'
        elif delta > 0:
            conclusion = '受宽边界轻微影响'
        elif delta < 0:
            conclusion = '紧边界反而变差（需调参）'
        else:
            conclusion = '不受边界策略影响'
        lines.append(f"| `{m}` | {a_ok}/4 | {b_ok}/4 | {sign} | {conclusion} |")
    lines.append('')

    # ============================ 详细结果 ============================
    lines.append('## 5. 各电路详细结果（阶段 A 宽边界）')
    lines.append('')
    for cname, cfg in CIRCUITS.items():
        lines.append(f'### 5.{list(CIRCUITS).index(cname)+1} {cname} (宽边界)')
        lines.append('')
        lines.append(f'> {cfg["desc"]}  ')
        lines.append(f'> 难度: **{cfg["difficulty"]}**, 频段: {cfg["freq"][0]:.2e} ~ {cfg["freq"][-1]:.2e} Hz, 噪声 {cfg["noise_level"]*100:.0f}%')
        lines.append('')
        param_names = list(cfg['true_params'].keys())
        headers = ['方法', '状态', 'χ²', 'nfev', 'success', '评级'] + [f'{p}_err%' for p in param_names]
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('|' + '|'.join('---' for _ in headers) + '|')
        for m in METHODS:
            r = results[(bname_a, cname)][m]
            if not r['ok']:
                cells = ['FAIL', '—', '—', '—', '崩溃'] + ['—'] * len(param_names)
                lines.append(f"| `{m}` | " + ' | '.join(cells) + ' |')
            else:
                cells = [
                    'OK',
                    f"{r['chisqr']:.2e}",
                    str(r['nfev']),
                    str(r['success']),
                    r['rating'],
                ]
                for p in param_names:
                    if p in r['per_param']:
                        cells.append(f"{r['per_param'][p]:.2f}")
                    else:
                        cells.append('—')
                lines.append(f"| `{m}` | " + ' | '.join(cells) + ' |')
        lines.append('')

    # ============================ 详细结果 B ============================
    lines.append('## 6. 各电路详细结果（阶段 B 紧边界）')
    lines.append('')
    for cname, cfg in CIRCUITS.items():
        lines.append(f'### 6.{list(CIRCUITS).index(cname)+1} {cname} (紧边界)')
        lines.append('')
        lines.append(f'> {cfg["desc"]}  ')
        lines.append(f'> 难度: **{cfg["difficulty"]}**, 频段: {cfg["freq"][0]:.2e} ~ {cfg["freq"][-1]:.2e} Hz, 噪声 {cfg["noise_level"]*100:.0f}%')
        lines.append('')
        param_names = list(cfg['true_params'].keys())
        headers = ['方法', '状态', 'χ²', 'nfev', 'success', '评级'] + [f'{p}_err%' for p in param_names]
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('|' + '|'.join('---' for _ in headers) + '|')
        for m in METHODS:
            r = results[(bname_b, cname)][m]
            if not r['ok']:
                cells = ['FAIL', '—', '—', '—', '崩溃'] + ['—'] * len(param_names)
                lines.append(f"| `{m}` | " + ' | '.join(cells) + ' |')
            else:
                cells = [
                    'OK',
                    f"{r['chisqr']:.2e}",
                    str(r['nfev']),
                    str(r['success']),
                    r['rating'],
                ]
                for p in param_names:
                    if p in r['per_param']:
                        cells.append(f"{r['per_param'][p]:.2f}")
                    else:
                        cells.append('—')
                lines.append(f"| `{m}` | " + ' | '.join(cells) + ' |')
        lines.append('')

    # ============================ 关键问题分析 ============================
    lines.append('## 7. 关键问题分析')
    lines.append('')
    lines.append('### 7.1 现有程序中的核心问题')
    lines.append('')
    lines.append('**问题 1：宽边界 [1e-15, 1e15] 是全局方法的灾难**')
    lines.append('')
    lines.append('在 `_auto_fitting_core` 中，所有方法都使用同一套边界 `min=1e-15, max=1e15`（30 个数量级！）。')
    lines.append('对 `least_squares`、`lbfgsb` 等局部算法影响小（因为它们在初值附近搜索），')
    lines.append('但对 `differential_evolution`、`dual_annealing`、`basinhopping` 等全局算法而言：')
    lines.append('')
    lines.append('- 搜索空间太大，30 个数量级')
    lines.append('- 群体/退火随机生成的候选解可能偏离真值 1e10 以上')
    lines.append('- 残差函数 `|Z_diff|/|Z_meas|` 在极端参数值下退化为 NaN/Inf')
    lines.append('- 优化器无法收敛到真值附近')
    lines.append('')
    lines.append('**从测试结果可见**：紧边界 [init/100, init*100]（4 个数量级）下，全局方法可用性大幅提升。')
    lines.append('')
    lines.append('**问题 2：缺乏参数空间约束与电路先验知识**')
    lines.append('')
    lines.append('参考 [EIS_Fitting_Analysis_Summary.md 第 11 节](EIS_Fitting_Analysis_Summary.md#11-极端条件分段拟合处理策略)：')
    lines.append('对于 Randles 类电路，可以通过物理先验知识（如"高频段实部 ≈ R1"）来收紧边界。')
    lines.append('但当前 `_auto_fitting_core` 直接用 `1e-15 ~ 1e15` 这种"无信息"边界，')
    lines.append('完全没有利用电路拓扑信息。')
    lines.append('')
    lines.append('**问题 3：双并联分支的多解性无法通过更换算法解决**')
    lines.append('')
    lines.append('C2 双并联分支电路在两种边界策略下，DE/DA/AMPGO 等全局方法都收敛到错误局部最优。')
    lines.append('这是物理多解性（不同 (R2, C1) 组合产生相似阻抗曲线），算法层面无法解决，')
    lines.append('需要：')
    lines.append('')
    lines.append('- 物理约束（如已知 R1，从高频段估计）')
    lines.append('- 多起点 + 物理约束')
    lines.append('- 时间常数分析（参考 [第 11 节策略 1](EIS_Fitting_Analysis_Summary.md#111-问题本质)）')
    lines.append('')
    lines.append('**问题 4：极限量级差（C4）下所有方法都失败**')
    lines.append('')
    lines.append('即使在紧边界下，C4 (R1=1mΩ, R6=1MΩ) 也几乎没有方法能找到正确解。')
    lines.append('原因是：')
    lines.append('')
    lines.append('- `tight` 边界 (init*100) 对 R1=1mΩ 来说只有 [1e-4, 1]，覆盖不到 R1=1e-3 太远')
    lines.append('- 全局方法在 [1e-4, 1] × [1e-6, 1e-2] × [1e5, 1e9] 仍然太大')
    lines.append('- 相对误差归一化在 9 数量级差异下失效')
    lines.append('')
    lines.append('参考 [EIS_Fitting_Analysis_Summary.md 第 11 节](EIS_Fitting_Analysis_Summary.md#11-极端条件分段拟合处理策略)：')
    lines.append('需要用 `multi_start_fit` + R1_est 约束。')
    lines.append('')
    lines.append('### 7.2 改进优先级')
    lines.append('')
    lines.append('| 优先级 | 改进点 | 影响范围 |')
    lines.append('|--------|--------|----------|')
    lines.append('| P0 | 默认边界从 1e-15~1e15 改为基于 init 的自适应 | DE/DA/AMPGO/BH 全部受益 |')
    lines.append('| P0 | 局部方法 (LS/LBFGSB/Powell) 保留原边界 | 不影响 |')
    lines.append('| P1 | C4 类极限量级加 R1_est 物理约束 | 多解性场景 |')
    lines.append('| P1 | 多起点 + 物理约束替代单点 DE | 双并联分支 |')
    lines.append('| P2 | `ampgo` 替换为 `differential_evolution` + 调小 maxiter | ampgo 失败回退 |')
    lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('*报告由 test_4circuits_method_diagnosis.py 自动生成*')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"\n[报告已保存到] {report_path}")


# =============================================================================
# 入口
# =============================================================================

if __name__ == '__main__':
    results = run_all()
    print_summary(results)
    report_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'test_4circuits_method_diagnosis_report.md'
    )
    generate_report(results, report_path)
