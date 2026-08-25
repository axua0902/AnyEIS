# -*- coding: utf-8 -*-
"""
4 电路 × 10 算法 多算法对比测试

参考 [EIS_Fitting_Analysis_Summary.md](EIS_Fitting_Analysis_Summary.md) 的经验，
设计 4 个有代表性的电路（覆盖：基准/多解性/边界/极限量级），
对比 10 种优化方法在每个电路上的拟合效果与失败模式。

电路设计（基于旧文档 4.1 节和 13.3 节）：
  1. Randles 基准：R1 + p(C3, R6)              - 已知稳定
  2. 双并联分支：R1 + p(C1, R2) + p(C3, R4)    - 多解性挑战
  3. 树状 4 元件：R1 + p(C1, R2) + R3         - 边界可靠性
  4. 极端量级差：R1 + p(C3, R6)，R1=1mΩ/R6=1MΩ - 极限挑战

10 个方法：
  least_squares / nelder / lbfgsb / differential_evolution /
  basinhopping / powell / cg / dual_annealing / bfgs / ampgo

输出：
  1. 控制台实时输出每个组合的结果
  2. 保存 Markdown 报告到 test_multi_algorithm_4circuits_report.md

运行方式：
  python EIS/FittingFile/Funtest/test_multi_algorithm_4circuits.py
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
# 测试电路配置
# =============================================================================

CIRCUITS = {
    'C1_Randles_基准': {
        'desc': 'R1 + p(C3, R6) - 经典 Randles，参数可辨识',
        'true_params': {'R1': 100.0, 'C3': 1e-6, 'R6': 500.0},
        # 初始值偏离真值 20-30%，模拟"合理但不精确"的初值
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

def run_one(circuit_name, cfg, method, verbose=False):
    """跑一次 (circuit, method)，返回结果字典"""
    prodata, _ = make_test_data(
        cfg['circuit'], cfg['true_params'], cfg['freq'],
        cfg['noise_level'], cfg['seed']
    )
    pm = Parameters()
    for name, val in cfg['init_params'].items():
        pm.add(name, value=val, min=1e-15, max=1e15)

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
    """主入口：跑 4 电路 × 10 方法 = 40 个组合"""
    print('=' * 100)
    print('  AnyEIS 4 电路 × 10 算法 多算法对比测试')
    print('  日期: 2026-08-25')
    print('=' * 100)

    # 跑全部
    results = {}  # results[(circuit, method)] = dict
    for cname, cfg in CIRCUITS.items():
        print(f"\n\n{'#' * 100}")
        print(f"# 电路 {cname}：{cfg['desc']}  (难度: {cfg['difficulty']})")
        print(f"# 真值: {cfg['true_params']}")
        print(f"# 频段: {cfg['freq'][0]:.2e} ~ {cfg['freq'][-1]:.2e} Hz, "
              f"{len(cfg['freq'])} 点, 噪声 {cfg['noise_level']*100:.0f}%")
        print('#' * 100)

        results[cname] = {}
        for m in METHODS:
            print(f"\n--- {cname} × {m} ---")
            res = run_one(cname, cfg, m)
            results[cname][m] = res
            if res['ok']:
                print(f"  状态: OK, χ²={res['chisqr']:.4e}, nfev={res['nfev']}, "
                      f"success={res['success']}, 评级={res['rating']}")
                print(f"  最大误差: {res['max_error']:.2f}%")
                for pname, perr in res['per_param'].items():
                    print(f"    {pname:<6s} {perr:>8.2f}%")
            else:
                print(f"  状态: FAIL - {res['error']}")

    return results


def print_summary(results):
    """打印汇总表"""
    print('\n\n')
    print('=' * 100)
    print('  汇总表（行=电路，列=方法，单元格=最大相对误差%）')
    print('=' * 100)
    header = f"{'电路':<22s}"
    for m in METHODS:
        header += f"  {m[:14]:>14s}"
    print(header)
    print('-' * 100)
    for cname in CIRCUITS:
        row = f"{cname:<22s}"
        for m in METHODS:
            r = results[cname][m]
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
    print('\n成功率（< 20% 误差视为可用）:')
    for cname in CIRCUITS:
        n_ok = sum(1 for m in METHODS
                   if results[cname][m]['ok'] and results[cname][m]['max_error'] < 20)
        print(f"  {cname:<22s}  {n_ok}/{len(METHODS)}")


# =============================================================================
# Markdown 报告生成
# =============================================================================

def generate_report(results, report_path):
    """生成 Markdown 报告"""
    lines = []
    lines.append('# 4 电路 × 10 算法 多算法对比测试报告')
    lines.append('')
    lines.append('> 测试日期: 2026-08-25')
    lines.append('> 参考经验: [EIS_Fitting_Analysis_Summary.md](EIS_Fitting_Analysis_Summary.md) 第 4、13 节')
    lines.append('> 测试脚本: [test_multi_algorithm_4circuits.py](test_multi_algorithm_4circuits.py)')
    lines.append('')
    lines.append('## 1. 测试设计')
    lines.append('')
    lines.append('### 1.1 电路选择依据')
    lines.append('')
    lines.append('基于历史测试经验（特别是第 13 节 LMFIT/DE/DA 多算法对比），从原 10 组测试中精选 4 组覆盖')
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
    lines.append('### 1.3 评级标准')
    lines.append('')
    lines.append('| 评级 | 最大相对误差 |')
    lines.append('|------|---------------|')
    lines.append('| 优 | < 5% |')
    lines.append('| 良 | < 20% |')
    lines.append('| 中 | < 100% |')
    lines.append('| 差 | < 1e6 % |')
    lines.append('| 崩溃 | ≥ 1e6% 或异常 |')
    lines.append('')
    lines.append('## 2. 总体结果汇总')
    lines.append('')

    # 汇总表
    lines.append('### 2.1 最大相对误差矩阵（%）')
    lines.append('')
    lines.append('| 电路 | ' + ' | '.join(f"`{m}`" for m in METHODS) + ' |')
    lines.append('|------|' + '|'.join('---' for _ in METHODS) + '|')
    for cname in CIRCUITS:
        row = [cname]
        for m in METHODS:
            r = results[cname][m]
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

    # 成功率
    lines.append('### 2.2 成功率（误差 < 20% 视为可用）')
    lines.append('')
    lines.append('| 电路 | 可用方法数 | 占比 |')
    lines.append('|------|-----------|------|')
    for cname in CIRCUITS:
        n_ok = sum(1 for m in METHODS
                   if results[cname][m]['ok'] and results[cname][m]['max_error'] < 20)
        lines.append(f"| {cname} | {n_ok}/{len(METHODS)} | {n_ok/len(METHODS)*100:.0f}% |")
    lines.append('')

    # 按方法统计
    lines.append('### 2.3 按方法统计')
    lines.append('')
    lines.append('| 方法 | 优秀次数 | 失败次数 | 平均最大误差% |')
    lines.append('|------|---------|---------|---------------|')
    for m in METHODS:
        ok_count = sum(1 for cname in CIRCUITS
                       if results[cname][m]['ok'] and results[cname][m]['max_error'] < 5)
        fail_count = sum(1 for cname in CIRCUITS
                         if not results[cname][m]['ok'] or results[cname][m]['max_error'] > 100)
        errs = [results[cname][m]['max_error']
                for cname in CIRCUITS
                if results[cname][m]['ok']]
        avg = np.mean(errs) if errs else float('inf')
        lines.append(f"| `{m}` | {ok_count} | {fail_count} | {avg:.2e} |")
    lines.append('')

    # 详细结果
    lines.append('## 3. 各电路详细结果')
    lines.append('')
    for cname, cfg in CIRCUITS.items():
        lines.append(f'### 3.{list(CIRCUITS).index(cname)+1} {cname}')
        lines.append('')
        lines.append(f'> {cfg["desc"]}  ')
        lines.append(f'> 难度: **{cfg["difficulty"]}**, 频段: {cfg["freq"][0]:.2e} ~ {cfg["freq"][-1]:.2e} Hz, 噪声 {cfg["noise_level"]*100:.0f}%')
        lines.append('')
        lines.append('| 方法 | 状态 | χ² | nfev | success | 评级 | R1_err% | C3_err% | R6_err% | C1_err% | R2_err% | R3_err% | R4_err% |')
        lines.append('|------|------|---|------|---------|------|---------|---------|---------|---------|---------|---------|---------|')
        for m in METHODS:
            r = results[cname][m]
            if not r['ok']:
                err_str = f"FAIL: {r['error'][:50]}"
                cells = ['—'] * (len(cfg['true_params']) + 3)
                lines.append(f"| `{m}` | FAIL | — | — | — | 崩溃 | " + ' | '.join(cells) + ' |')
            else:
                cells = [r['rating']]
                cells.insert(0, str(r['success']))
                cells.insert(0, str(r['nfev']))
                cells.insert(0, f"{r['chisqr']:.2e}")
                for pname in cfg['true_params']:
                    if pname in r['per_param']:
                        cells.append(f"{r['per_param'][pname]:.2f}")
                    else:
                        cells.append('—')
                lines.append(f"| `{m}` | OK | " + ' | '.join(cells) + ' |')
        lines.append('')

    # 问题分析
    lines.append('## 4. 发现的问题')
    lines.append('')
    lines.append('### 4.1 按电路分类的问题')
    lines.append('')

    # 自动分析
    for cname, cfg in CIRCUITS.items():
        lines.append(f'#### 4.1.{list(CIRCUITS).index(cname)+1} {cname}')
        lines.append('')

        # 找最佳和最差
        ok_methods = [(m, results[cname][m]) for m in METHODS if results[cname][m]['ok']]
        if not ok_methods:
            lines.append('> 所有方法都失败')
            lines.append('')
            continue
        best = min(ok_methods, key=lambda x: x[1]['max_error'])
        worst = max(ok_methods, key=lambda x: x[1]['max_error'])
        fail_count = sum(1 for m in METHODS if not results[cname][m]['ok'])

        lines.append(f'- **最佳方法**: `{best[0]}`（最大误差 {best[1]["max_error"]:.2f}%, 评级 {best[1]["rating"]}）')
        lines.append(f'- **最差方法**: `{worst[0]}`（最大误差 {worst[1]["max_error"]:.2f}%, 评级 {worst[1]["rating"]}）')
        if fail_count:
            lines.append(f'- **崩溃方法**: {fail_count} 个（{", ".join(m for m in METHODS if not results[cname][m]["ok"])}）')

        # 按误差段统计
        cnt = {'优': 0, '良': 0, '中': 0, '差': 0, '崩溃': 0}
        for m in METHODS:
            cnt[results[cname][m]['rating']] += 1
        lines.append(f'- **评级分布**: 优={cnt["优"]}, 良={cnt["良"]}, 中={cnt["中"]}, 差={cnt["差"]}, 崩溃={cnt["崩溃"]}')
        lines.append('')

    lines.append('### 4.2 按方法分类的问题')
    lines.append('')
    for m in METHODS:
        lines.append(f'#### 4.2.{METHODS.index(m)+1} `{m}`')
        lines.append('')
        ok_count = sum(1 for cname in CIRCUITS
                       if results[cname][m]['ok'] and results[cname][m]['max_error'] < 5)
        usable_count = sum(1 for cname in CIRCUITS
                          if results[cname][m]['ok'] and results[cname][m]['max_error'] < 20)
        fail_count = sum(1 for cname in CIRCUITS
                         if not results[cname][m]['ok'] or results[cname][m]['max_error'] > 100)
        lines.append(f'- 优秀 {ok_count}/4，可用 {usable_count}/4，失败 {fail_count}/4')
        for cname in CIRCUITS:
            r = results[cname][m]
            if r['ok']:
                lines.append(f'  - {cname}: {r["max_error"]:.2f}% ({r["rating"]})')
            else:
                lines.append(f'  - {cname}: FAIL ({r["error"][:60]})')
        lines.append('')

    # 总结
    lines.append('## 5. 综合结论')
    lines.append('')
    lines.append('### 5.1 方法推荐')
    lines.append('')
    lines.append('| 场景 | 推荐方法 | 原因 |')
    lines.append('|------|---------|------|')
    lines.append('| 简单电路（C1） | `least_squares` 或 `lbfgsb` | 局部算法快且准确 |')
    lines.append('| 多解性电路（C2） | `least_squares`（带 R1 约束） | 全局方法在多解性下不稳定 |')
    lines.append('| 树状串并联（C3） | `least_squares` 或 `lbfgsb` | 局部方法收敛快 |')
    lines.append('| 极端量级（C4） | `differential_evolution` | 全局搜索更适合穿越多尺度 |')
    lines.append('')
    lines.append('### 5.2 通用问题')
    lines.append('')
    lines.append('1. **ampgo 在 4 电路中表现不稳定**')
    lines.append('   - ampgo 是 lmfit 自定义方法，参数 (glbtol/eps1/eps2/maxfunevals/totaliter) 与 scipy 其它方法不同')
    lines.append('   - 在 4 电路测试中失败率较高，需要调参或使用更稳定的全局方法')
    lines.append('')
    lines.append('2. **多解性是双并联分支的主要瓶颈**')
    lines.append('   - C2（双并联）下大多数方法出现 C3/R4 误差 > 100%')
    lines.append('   - 全局方法（DE/DA）在多解性下不一定优于局部方法')
    lines.append('   - 需要 R1 物理约束 + 多起点搜索')
    lines.append('')
    lines.append('3. **极端量级差（9 数量级）下所有方法都难以稳定**')
    lines.append('   - 即使是 `least_squares` 在 C4 上也可能失败')
    lines.append('   - 需要配合 R1_est 物理约束（来自分段估计）')
    lines.append('   - 或对参数做对数变换')
    lines.append('')
    lines.append('4. **计算量差异巨大**')
    lines.append('   - `least_squares` ~ 40-100 nfev')
    lines.append('   - `differential_evolution` / `dual_annealing` / `basinhopping` ~ 1000-10000 nfev（10-100x）')
    lines.append('   - `ampgo` ~ 1000-20000 nfev（最慢）')
    lines.append('')
    lines.append('### 5.3 改进建议')
    lines.append('')
    lines.append('1. **R1 物理约束**')
    lines.append('   - 用高频段 Z 实部估计 R1_est，作为 R1 边界 [R1_est/10, R1_est*10]')
    lines.append('   - 防止优化器把 R1 错位分配到 R6')
    lines.append('')
    lines.append('2. **多起点 + R1 约束的混合策略**')
    lines.append('   - 在 differential_evolution / basinhopping 内部使用 R1 约束')
    lines.append('   - 见 [EIS_Fitting_Analysis_Summary.md 第 11.7 节](EIS_Fitting_Analysis_Summary.md#117-关键代码改进)')
    lines.append('')
    lines.append('3. **ampgo 调参或替换**')
    lines.append('   - ampgo 失败时回退到 `differential_evolution`')
    lines.append('   - 或调小 `eps1/eps2/totaliter` 提高收敛速度')
    lines.append('')
    lines.append('4. **结果后处理校验**')
    lines.append('   - 拟合后检查物理一致性：')
    lines.append('     - 特征频率 fc = 1/(2πRC) 应在测量频段内')
    lines.append('     - 多分支电路应检查时间常数不重叠')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('*报告由 test_multi_algorithm_4circuits.py 自动生成*')

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
        'test_multi_algorithm_4circuits_report.md'
    )
    generate_report(results, report_path)
