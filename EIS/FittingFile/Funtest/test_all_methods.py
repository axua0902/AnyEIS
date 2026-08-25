# -*- coding: utf-8 -*-
"""
全方法综合回归测试 - 验证 _auto_fitting_core 修复

测试目标: [FittingECM.py](../FittingECM.py) `_auto_fitting_core`
测试类型: 综合回归测试（7 测试组）

集中入口：
- 旧 FittingfuntestECM / FittingfuntestECM2 / FittingTest 的核心功能
- 9 个优化方法全跑通（不含 basinhopping）
- UI 文本框字符串 -> 后端 kwargs 转换
- 后处理（FittingresultsprocessECM / Fittingresultsprocess）兼容 ampgo
- 策略选择函数 (should_use_segmented / should_use_extreme) 边界

7 组测试内容：
1. 参数类型转换（type casting）
2. 方法 smoke test
3. UI 流程（文本框 → kwargs）
4. 决策函数（should_use_segmented / should_use_extreme）
5. 极端条件测试
6. MT 路径
7. 噪声对比

运行方式：
    python EIS/FittingFile/Funtest/test_all_methods.py
    python EIS/FittingFile/Funtest/test_all_methods.py --method lbfgsb   # 只跑一个方法
    python EIS/FittingFile/Funtest/test_all_methods.py --quick          # 只跑主流程

Created on 2026-08-24
@author: takeilab
Updated on 2026-08-25: 规范化头注释（测试目标/测试类型/运行方式）
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import numpy as np
from numpy import pi, real, imag, logspace
from pandas import DataFrame, Series
from lmfit import Parameters
from EIS.FittingFile.FittingECM import (
    auto_fitting, generate_test_data, simuECM,
    should_use_segmented, should_use_extreme,
    FittingresultsprocessECM, FittingECM,
    _auto_fitting_core,
)
from EIS.FittingFile.FittingMT import FittingMT, Fittingresultsprocess


ALL_METHODS = [
    'least_squares', 'nelder', 'lbfgsb', 'differential_evolution',
    'powell', 'cg', 'dual_annealing', 'bfgs', 'ampgo',
]
QUICK_METHODS = ['least_squares', 'lbfgsb', 'differential_evolution', 'ampgo']


# =============================================================================
# 1. _cast_setting 单元测试
# =============================================================================

def test_cast_setting_unit():
    """_cast_setting 边界用例单元测试"""
    from EIS.FittingFile.Fitting import _cast_setting

    print('\n' + '=' * 80)
    print('1. _cast_setting 单元测试（21 个边界用例）')
    print('=' * 80)

    test_cases = [
        ('xtol', '1e-10', float, 1e-10),
        ('ftol', '1e-10', float, 1e-10),
        ('gtol', '1e-10', float, 1e-10),
        ('xatol', '1e-6', float, 1e-6),
        ('fatol', '1e-6', float, 1e-6),
        ('maxiter', '5000', int, 5000),
        ('maxls', '20', int, 20),
        # 关键边界：UI 默认 1e-5 → maxls 必须 > 0
        ('maxls', '1e-5', int, 20),  # 期望被修正为 20
        ('maxls', '0', int, 20),     # 期望被修正为 20
        ('maxls', '-5', int, 20),    # 期望被修正为 20
        ('strategy', 'best1bin', str, 'best1bin'),
        # 关键边界：UI 默认 1e-5 → strategy 非法
        ('strategy', '1e-5', str, 'best1bin'),  # 期望被修正为 best1bin
        ('strategy', 'best1exp', str, 'best1exp'),  # 合法
        ('strategy', 'randtobest1bin', str, 'randtobest1bin'),  # 合法
        ('strategy', 'invalid_strategy', str, 'best1bin'),  # 非法 → 兜底
        ('popsize', '15', int, 15),
        ('seed', '', type(None), None),  # 空 → None
        ('norm', 'inf', float, float('inf')),
        ('glbtol', '1e-5', float, 1e-5),
        ('eps1', '0.02', float, 0.02),
        ('totaliter', '20', int, 20),
    ]
    ok = 0
    for name, raw, expected_type, expected in test_cases:
        got = _cast_setting(name, raw)
        is_type_ok = isinstance(got, expected_type)
        is_value_ok = got == expected
        status = 'OK' if (is_type_ok and is_value_ok) else 'FAIL'
        if status == 'OK':
            ok += 1
        print(f"  [{status}] {name:>14s}={repr(raw):>20s}  ->  {got!r}  "
              f"(expected {expected!r})")
    print(f"\n  {ok}/{len(test_cases)} passed")
    return ok == len(test_cases)


# =============================================================================
# 2. 全方法 auto_fitting smoke test
# =============================================================================

def test_all_methods_basic(methods=None):
    """全方法 auto_fitting smoke test（不传 UI 字段，使用各方法默认值）"""
    if methods is None:
        methods = ALL_METHODS

    print('\n' + '=' * 80)
    print('2. 全方法 auto_fitting smoke test（基础数据 R1=50/C3=1e-6/R6=1000）')
    print('=' * 80)

    freq, Z_meas, prodata, Z_true = generate_test_data(
        R1=50, C3=1e-6, R6=1000, freq_range=(1, 6),
        n_points=60, noise_level=0.01, seed=42
    )
    circuit = ['R1', 'p(', 'C3', ',', 'R6', ')']

    print(f"{'method':>22s}  {'status':>6s}  {'nfev':>5s}  {'chisqr':>10s}  success  R1       C3         R6")
    print('-' * 100)
    results = {}
    for m in methods:
        params = Parameters()
        params.add('R1', value=60, min=1e-3, max=1e6)
        params.add('C3', value=1e-6, min=1e-12, max=1e-1)
        params.add('R6', value=800, min=1, max=1e9)
        try:
            r = auto_fitting(params, freq, circuit, prodata, method=m)
            chisqr = getattr(r, 'chisqr', float('nan'))
            nfev = getattr(r, 'nfev', -1)
            success = getattr(r, 'success', False)
            R1 = r.params['R1'].value if 'R1' in r.params else float('nan')
            C3 = r.params['C3'].value if 'C3' in r.params else float('nan')
            R6 = r.params['R6'].value if 'R6' in r.params else float('nan')
            print(f"{m:>22s}  {'OK':>6s}  {nfev:>5d}  {chisqr:>10.4e}  {str(success):>7s}  {R1:>7.3f}  {C3:>9.3e}  {R6:>8.3f}")
            results[m] = True
        except Exception as e:
            print(f"{m:>22s}  ERR   {type(e).__name__}: {str(e)[:100]}")
            results[m] = False
    return all(results.values())


# =============================================================================
# 3. 完整 UI 字符串 -> auto_fitting -> 后处理流程
# =============================================================================

def test_full_ui_flow(methods=None):
    """模拟 ECMcalculation 完整流程"""
    if methods is None:
        methods = ALL_METHODS

    print('\n' + '=' * 80)
    print('3. 完整 UI 流程 (UI 字符串 -> _cast_setting -> auto_fitting -> 后处理)')
    print('=' * 80)

    from EIS.FittingFile.Fitting import _cast_setting

    freq, Z_meas, prodata, Z_true = generate_test_data(
        R1=50, C3=1e-6, R6=1000, freq_range=(1, 6),
        n_points=40, noise_level=0.01, seed=42
    )
    circuit = ['R1', 'p(', 'C3', ',', 'R6', ')']

    method_settings = {
        'least_squares':          {'xtol': '1e-10', 'ftol': '1e-10', 'gtol': '1e-10'},
        'nelder':                 {'xatol': '1e-6', 'fatol': '1e-6', 'maxiter': '5000'},
        'lbfgsb':                 {'ftol': '1e-10', 'gtol': '1e-10', 'maxls': '1e-5'},
        'differential_evolution': {'strategy': 'best1bin', 'maxiter': '200',
                                   'popsize': '15', 'tol': '0.01',
                                   'mutation': '0.5', 'recombination': '0.7'},
        'powell':                 {'xtol': '1e-8', 'ftol': '1e-8', 'maxiter': '1000'},
        'cg':                     {'gtol': '1e-5', 'norm': 'inf', 'eps': '1e-8'},
        'dual_annealing':         {'initial_temp': '5230', 'restart_temp_ratio': '2e-5',
                                   'maxiter': '200'},
        'bfgs':                   {'gtol': '1e-5', 'norm': 'inf', 'eps': '1e-8'},
        'ampgo':                  {'glbtol': '1e-5', 'eps1': '0.02', 'eps2': '0.1',
                                   'maxfunevals': '5000', 'totaliter': '5'},
    }

    print(f"{'method':>22s}  {'status':>6s}  {'nfev':>5s}  {'chisqr':>10s}  {'postprocess':>12s}")
    print('-' * 80)
    results = {}
    for m in methods:
        params = Parameters()
        params.add('R1', value=60, min=1e-3, max=1e6)
        params.add('C3', value=1e-6, min=1e-12, max=1e-1)
        params.add('R6', value=800, min=1, max=1e9)
        try:
            raw_settings = method_settings.get(m, {})
            fit_kwargs = {k: _cast_setting(k, v) for k, v in raw_settings.items()}
            r = auto_fitting(params, freq, circuit, prodata, method=m, **fit_kwargs)
            try:
                FittingresultsprocessECM(params, freq, circuit, r, verbose=False)
                post = 'OK'
            except Exception as e2:
                post = f'ERR: {str(e2)[:60]}'
            print(f"{m:>22s}  {'OK':>6s}  {r.nfev:>5d}  {r.chisqr:>10.4e}  {post:>12s}")
            results[m] = (post == 'OK')
        except Exception as e:
            print(f"{m:>22s}  ERR   {type(e).__name__}: {str(e)[:120]}")
            results[m] = False
    return all(results.values())


# =============================================================================
# 4. 决策函数边界条件（原 FittingfuntestECM2）
# =============================================================================

def test_decision_functions():
    """验证 should_use_segmented / should_use_extreme 的边界条件"""
    print('\n' + '=' * 80)
    print('4. 决策函数边界条件 (should_use_segmented / should_use_extreme)')
    print('=' * 80)

    results = []

    # should_use_segmented
    print('\n--- should_use_segmented ---')
    seg_cases = [
        ('仅2参数无需分段', logspace(1, 8, 100), {'R1': 100.0, 'C1': 1e-6}, False),
        ('量级差异1e1~1e2', logspace(1, 4, 100), {'R1': 100.0, 'C1': 1e-4, 'R2': 500.0}, False),
        ('跨度>10+量级>1e7', logspace(1, 12, 100), {'R1': 1e-3, 'C1': 1e-3, 'R2': 1e6}, True),
        ('量级差异1e12', logspace(1, 5, 100), {'R1': 1e-6, 'C1': 1e-3, 'R2': 1e6}, True),
    ]
    for name, freq, params, expected in seg_cases:
        use_seg, reason = should_use_segmented(freq, params)
        passed = use_seg == expected
        results.append(('should_use_segmented', name, passed))
        print(f"  [{'OK' if passed else 'FAIL'}] {name:<25s} expected={expected!s:<6s} got={use_seg!s:<6s}")

    # should_use_extreme（threshold: magnitude_range > 6 或 freq_span > 7 & magnitude_range > 5）
    print('\n--- should_use_extreme ---')
    ext_cases = [
        # 阈值恰好在边界: R1=100, C1=1e-3, R2=500 → log10 max - log10 min = 2.7 - (-3) = 5.7 (< 6)
        ('温和参数', logspace(1, 5, 100), {'R1': 100.0, 'C1': 1e-3, 'R2': 500.0}, False),
        ('跨度8数量级', logspace(1, 9, 100), {'R1': 10.0, 'C1': 1e-6, 'R2': 1e6}, True),
        ('量级差异1e12', logspace(1, 5, 100), {'R1': 1e-6, 'C1': 1e0, 'R2': 1e6}, True),
        ('空参数', logspace(1, 5, 100), {}, False),
    ]
    for name, freq, params, expected in ext_cases:
        use_ext, reason = should_use_extreme(freq, params)
        passed = use_ext == expected
        results.append(('should_use_extreme', name, passed))
        print(f"  [{'OK' if passed else 'FAIL'}] {name:<25s} expected={expected!s:<6s} got={use_ext!s:<6s}")

    passed = sum(1 for _, _, p in results if p)
    print(f"\n  决策函数: {passed}/{len(results)} 通过")
    return passed == len(results)


# =============================================================================
# 5. 复杂电路/极限条件测试（原 FittingfuntestECM）
# =============================================================================

def _evaluate(test_name, true_params, result):
    """评估并打印拟合结果"""
    max_error = 0
    print(f"\n  {test_name}:")
    for name, true_val in true_params.items():
        if name not in result.params:
            continue
        fit_val = result.params[name].value
        if true_val != 0:
            rel_error = abs((fit_val - true_val) / true_val) * 100
            max_error = max(max_error, rel_error)
        print(f"    {name:<6s} 拟合={fit_val:>12.4e}  真值={true_val:>12.4e}  误差={rel_error:>7.2f}%")
    return max_error


def _make_params(init_params, bounds=(1e-12, 1e12)):
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=bounds[0], max=bounds[1])
    return pm


def test_extreme_conditions(methods=None):
    """复杂电路/极限条件测试，支持多方法"""
    if methods is None:
        methods = ['least_squares', 'lbfgsb', 'differential_evolution']

    print('\n' + '=' * 80)
    print('5. 复杂电路/极限条件测试（多方法对比）')
    print('=' * 80)

    cases = [
        {
            'name': '4元件电路 R1+p(C1,R2)+R3',
            'true': {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0, 'R3': 50.0},
            'init': {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0, 'R3': 80.0},
            'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'R3'],
            'freq': logspace(1, 6, 100),
        },
        {
            'name': 'mΩ~MΩ量级差',
            'true': {'R1': 1e-3, 'C1': 1e-3, 'R2': 1e6},
            'init': {'R1': 1e-2, 'C1': 1e-2, 'R2': 1e7},
            'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')'],
            'freq': logspace(-2, 8, 200),
        },
        {
            'name': '宽频率跨度10数量级',
            'true': {'R1': 50.0, 'C1': 1e-6, 'R2': 500.0},
            'init': {'R1': 80.0, 'C1': 5e-6, 'R2': 300.0},
            'circuit': ['R1', '+', 'p(', 'C1', ',', 'R2', ')'],
            'freq': logspace(1, 11, 200),
        },
    ]

    for tc in cases:
        print(f"\n--- {tc['name']} ---")
        # 生成数据
        pm = _make_params(tc['true'])
        Z_true, _ = simuECM(pm, tc['circuit'], tc['freq'])
        np.random.seed(42)
        noise = 0.01 * (np.random.randn(len(tc['freq'])) + 1j * np.random.randn(len(tc['freq'])))
        Z_meas = Z_true + noise * np.abs(Z_true)
        prodata = DataFrame({
            'Rs[ohm]': Series(real(Z_meas)),
            'X[ohm]': Series(imag(Z_meas)),
        })

        for m in methods:
            pm_init = _make_params(tc['init'])
            try:
                r = auto_fitting(pm_init, tc['freq'], tc['circuit'], prodata, method=m)
                err = _evaluate(f"[{m}]", tc['true'], r)
            except Exception as e:
                print(f"  [{m}] ERR {type(e).__name__}: {str(e)[:80]}")

    return True


# =============================================================================
# 6. MT 路径测试
# =============================================================================

def test_mt_flow(methods=None):
    """FittingMT + Fittingresultsprocess 全方法 smoke test"""
    if methods is None:
        methods = ['least_squares', 'lbfgsb', 'differential_evolution']

    print('\n' + '=' * 80)
    print('6. MT 路径 FittingMT + Fittingresultsprocess 全方法')
    print('=' * 80)

    freq = logspace(1, 5, 50)
    omega = 2 * pi * freq
    eps_inf, eps_s, tau = 5.0, 50.0, 1e-8
    eps_re = eps_inf + (eps_s - eps_inf) / (1 + (omega * tau)**2)
    eps_im = (eps_s - eps_inf) * omega * tau / (1 + (omega * tau)**2)
    np.random.seed(42)
    eps_re_n = eps_re + np.random.normal(0, 0.5, len(freq))
    eps_im_n = eps_im + np.random.normal(0, 0.5, len(freq))
    eps0 = 8.854e-12
    sigma = omega * eps0 * eps_im_n
    mt_data = DataFrame({
        'FREQ[Hz]': freq,
        'epsRE[-]': eps_re_n,
        'sigmaRE[S/m]': sigma,
    })
    option = {'EP': 0, 'DC Conductivity': 0}
    modelterm = [{'name': 'term1', 'modeltype': 'Debye'}]

    print(f"{'method':>22s}  {'status':>6s}  {'nfev':>5s}  {'chisqr':>10s}  {'postprocess':>12s}")
    print('-' * 80)
    results = {}
    for m in methods:
        MTparams = Parameters()
        MTparams.add('epsh', value=10.0, min=1, max=100)
        MTparams.add('Depsterm1', value=50.0, min=1, max=200)
        MTparams.add('Taoterm1', value=1e-8, min=1e-12, max=1e-4)
        try:
            r = FittingMT(MTparams, freq, modelterm, mt_data, option, method=m)
            try:
                Fittingresultsprocess(MTparams, freq, modelterm, r, option)
                post = 'OK'
            except Exception as e2:
                post = f'ERR: {str(e2)[:60]}'
            print(f"{m:>22s}  {'OK':>6s}  {r.nfev:>5d}  {r.chisqr:>10.4e}  {post:>12s}")
            results[m] = (post == 'OK')
        except Exception as e:
            print(f"{m:>22s}  ERR   {type(e).__name__}: {str(e)[:100]}")
            results[m] = False
    return all(results.values())


# =============================================================================
# 7. 高噪声环境多方法对比
# =============================================================================

def test_noise_levels(methods=None):
    """不同噪声水平下各方法的拟合质量"""
    if methods is None:
        methods = ['least_squares', 'lbfgsb', 'dual_annealing', 'bfgs']

    print('\n' + '=' * 80)
    print('7. 高噪声环境多方法对比（1%, 5%, 10%, 20%）')
    print('=' * 80)

    true = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']
    freq = logspace(1, 6, 100)
    pm_true = _make_params(true)
    Z_true, _ = simuECM(pm_true, circuit, freq)

    noise_levels = [0.01, 0.05, 0.10, 0.20]
    # 列宽统一 25 字符，兼容 differential_evolution(23) 等长方法名；
    # 数值 < 1e6 用 % 显示，否则用科学计数法，列对齐
    COL_W = 25
    print(f"\n{'noise':<8s}" + "".join(f"{m:>{COL_W}s}" for m in methods))
    print('-' * (8 + COL_W * len(methods)))
    for noise in noise_levels:
        np.random.seed(42)
        n = noise * (np.random.randn(len(freq)) + 1j * np.random.randn(len(freq)))
        Z_m = Z_true + n * np.abs(Z_true)
        prodata = DataFrame({
            'Rs[ohm]': Series(real(Z_m)),
            'X[ohm]': Series(imag(Z_m)),
        })
        row = f"{noise*100:>5.1f}%  "
        for m in methods:
            pm = _make_params({'R1': 150.0, 'C1': 2e-6, 'R2': 300.0})
            try:
                r = auto_fitting(pm, freq, circuit, prodata, method=m)
                max_err = max(
                    abs((r.params[n].value - true[n]) / true[n]) * 100
                    for n in true
                )
                if abs(max_err) < 1e6:
                    val_str = f"{max_err:>12.4f}%"
                else:
                    val_str = f"{max_err:>12.2e}%"
                row += val_str.ljust(COL_W)
            except Exception:
                row += f"{'ERR':>{COL_W}s}"
        print(row)
    return True


# =============================================================================
# 主入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='全方法拟合测试')
    parser.add_argument('--method', help='只测试指定方法（如 lbfgsb）')
    parser.add_argument('--quick', action='store_true', help='只跑主流程（4 个方法）')
    args = parser.parse_args()

    if args.quick:
        methods = QUICK_METHODS
    elif args.method:
        if args.method not in ALL_METHODS:
            print(f"未知方法: {args.method}，可选: {ALL_METHODS}")
            return 1
        methods = [args.method]
    else:
        methods = ALL_METHODS

    print('=' * 80)
    print('  AnyEIS Fitting 修复验证 - 全方法 smoke test')
    print('  日期: 2026-08-24')
    print(f'  测试方法: {methods}')
    print('=' * 80)

    results = {}

    # 1. _cast_setting 单元测试（与 method 无关）
    results['1. _cast_setting'] = test_cast_setting_unit()

    # 2. 全方法 auto_fitting smoke test
    results['2. 全方法基础'] = test_all_methods_basic(methods)

    # 3. UI 字符串 -> 后处理全流程
    results['3. 完整 UI 流程'] = test_full_ui_flow(methods)

    # 4. 决策函数（与 method 无关）
    results['4. 决策函数'] = test_decision_functions()

    # 5. 复杂电路/极限条件
    if not args.method:  # 默认全跑
        results['5. 极限条件'] = test_extreme_conditions(
            methods if args.quick else ['least_squares', 'lbfgsb', 'differential_evolution']
        )

    # 6. MT 路径
    results['6. MT 路径'] = test_mt_flow(
        methods if args.quick else ['least_squares', 'lbfgsb', 'differential_evolution']
    )

    # 7. 高噪声对比
    if not args.method:
        results['7. 噪声对比'] = test_noise_levels(methods)

    # 汇总
    print('\n' + '=' * 80)
    print('  测试汇总')
    print('=' * 80)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        status = 'OK  通过' if ok else 'FAIL'
        print(f"  {name:<25s}  {status}")
    print(f"\n  {passed}/{total} 测试组通过")
    print('=' * 80)
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
