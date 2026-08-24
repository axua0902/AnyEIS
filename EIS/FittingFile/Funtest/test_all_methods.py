# -*- coding: utf-8 -*-
"""
全方法 smoke test - 验证 _auto_fitting_core 修复
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import numpy as np
from lmfit import Parameters
from EIS.FittingFile.FittingECM import auto_fitting, generate_test_data


def main():
    freq, Z_meas, prodata, Z_true = generate_test_data(
        R1=50, C3=1e-6, R6=1000, freq_range=(1, 6),
        n_points=60, noise_level=0.01, seed=42
    )
    # 正确格式的并联电路描述
    circuit = ['R1', 'p(', 'C3', ',', 'R6', ')']
    params = Parameters()
    params.add('R1', value=60, min=1e-3, max=1e6)
    params.add('C3', value=1e-6, min=1e-12, max=1e-1)
    params.add('R6', value=800, min=1, max=1e9)

    methods = [
        'least_squares', 'nelder', 'lbfgsb', 'differential_evolution',
        'basinhopping', 'powell', 'cg', 'dual_annealing', 'bfgs', 'ampgo',
    ]

    print(f"{'method':>22s}  {'status':>6s}  {'nfev':>5s}  {'chisqr':>10s}  success  R1       C3         R6")
    print('-' * 100)
    for m in methods:
        try:
            r = auto_fitting(params, freq, circuit, prodata, method=m)
            chisqr = getattr(r, 'chisqr', float('nan'))
            nfev = getattr(r, 'nfev', -1)
            success = getattr(r, 'success', False)
            R1 = r.params['R1'].value if 'R1' in r.params else float('nan')
            C3 = r.params['C3'].value if 'C3' in r.params else float('nan')
            R6 = r.params['R6'].value if 'R6' in r.params else float('nan')
            print(f"{m:>22s}  {'OK':>6s}  {nfev:>5d}  {chisqr:>10.4e}  {str(success):>7s}  {R1:>7.3f}  {C3:>9.3e}  {R6:>8.3f}")
        except Exception as e:
            print(f"{m:>22s}  ERR   {type(e).__name__}: {str(e)[:100]}")


def test_with_ui_settings():
    """模拟 UI 端传入的字符串设置，验证 _cast_setting + 方法分桶能正确处理"""
    from EIS.FittingFile.Fitting import _cast_setting

    print('\n' + '=' * 80)
    print('模拟 UI 字符串设置 -> scipy kwargs 转换（含异常/边界值）')
    print('=' * 80)

    # 模拟从 UI 文本框获取的设置（全部是字符串）
    # 各种边界情况：空值、合法值、非法值
    test_cases = [
        # (name, raw_value, expected_type, expected_value_or_check)
        ('xtol', '1e-10', float, 1e-10),
        ('ftol', '1e-10', float, 1e-10),
        ('gtol', '1e-10', float, 1e-10),
        ('xatol', '1e-6', float, 1e-6),
        ('fatol', '1e-6', float, 1e-6),
        ('maxiter', '5000', int, 5000),
        ('maxls', '20', int, 20),
        # 关键边界：UI 默认 1e-5 → maxls 必须 > 0
        ('maxls', '1e-5', int, 20),  # 期望被修正为 20
        ('maxls', '0', int, 20),      # 期望被修正为 20
        ('maxls', '-5', int, 20),     # 期望被修正为 20
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


def test_full_ui_flow():
    """模拟 ECMcalculation 完整流程：UI settings (字符串) -> _cast_setting -> auto_fitting"""
    from EIS.FittingFile.Fitting import _cast_setting
    from EIS.FittingFile.FittingECM import FittingresultsprocessECM

    print('\n' + '=' * 80)
    print('模拟完整 UI -> Fitting.py -> auto_fitting 流程（每个方法都用 UI 字符串设置）')
    print('=' * 80)

    freq, Z_meas, prodata, Z_true = generate_test_data(
        R1=50, C3=1e-6, R6=1000, freq_range=(1, 6),
        n_points=40, noise_level=0.01, seed=42
    )
    circuit = ['R1', 'p(', 'C3', ',', 'R6', ')']

    # 模拟从 FittingSetResUI get_settings() 返回的字典（全部为字符串）
    # 每个方法使用其对应的 UI 字段
    method_settings = {
        'least_squares':          {'xtol': '1e-10', 'ftol': '1e-10', 'gtol': '1e-10'},
        'nelder':                 {'xatol': '1e-6', 'fatol': '1e-6', 'maxiter': '5000'},
        # 关键：故意用旧 UI 默认 1e-5，验证 _cast_setting 会修正
        'lbfgsb':                 {'ftol': '1e-10', 'gtol': '1e-10', 'maxls': '1e-5'},
        'differential_evolution': {'strategy': 'best1bin', 'maxiter': '200',
                                   'popsize': '15', 'tol': '0.01',
                                   'mutation': '0.5', 'recombination': '0.7'},
        'basinhopping':           {'niter': '50', 'T': '1.0', 'stepsize': '0.5',
                                   'interval': '10', 'niter_success': '5', 'seed': ''},
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
    for m, raw_settings in method_settings.items():
        # 每个方法用独立的 params（ampgo 会原地修改 params）
        params = Parameters()
        params.add('R1', value=60, min=1e-3, max=1e6)
        params.add('C3', value=1e-6, min=1e-12, max=1e-1)
        params.add('R6', value=800, min=1, max=1e9)

        try:
            # 关键转换：UI 字符串 -> scipy kwargs
            fit_kwargs = {k: _cast_setting(k, v) for k, v in raw_settings.items()}
            r = auto_fitting(params, freq, circuit, prodata, method=m, **fit_kwargs)
            # 模拟 FittingresultsprocessECM（验证 result.x 兜底逻辑）
            try:
                FittingresultsprocessECM(params, freq, circuit, r, verbose=False)
                post = 'OK'
            except Exception as e2:
                post = f'ERR: {str(e2)[:60]}'
            print(f"{m:>22s}  {'OK':>6s}  {r.nfev:>5d}  {r.chisqr:>10.4e}  {post:>12s}")
        except Exception as e:
            print(f"{m:>22s}  ERR   {type(e).__name__}: {str(e)[:120]}")


if __name__ == '__main__':
    test_with_ui_settings()
    test_full_ui_flow()
    print()
    main()
