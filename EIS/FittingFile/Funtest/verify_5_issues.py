# -*- coding: utf-8 -*-
"""
5 改进实施验证脚本

测试目标: 验证问题 2/4/5/6/8 的修复
运行方式: python EIS/FittingFile/Funtest/verify_5_issues.py
"""
import sys
import os

# 添加 AnyEIS 根目录到 sys.path, 以便 EIS 是可导入的包
# 路径: Funtest/ -> FittingFile/ -> EIS/ -> AnyEIS/
ANYEIS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ANYEIS_ROOT not in sys.path:
    sys.path.insert(0, ANYEIS_ROOT)

# 同样添加 FittingFile 以便 FittingWarnings 可导入
FITTING_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
if FITTING_DIR not in sys.path:
    sys.path.insert(0, FITTING_DIR)

import numpy as np

# 静默模式
import FittingWarnings
FittingWarnings.set_silent_mode(True)

from FittingECM import (
    GLOBAL_METHODS, SEMI_GLOBAL_METHODS, ALL_BOUND_SENSITIVE,
    _compute_adaptive_bounds, METHOD_TIGHTEN_FACTOR,
    _detect_multi_solution_risk, _is_fitting_failed,
    _estimate_R_at_high_freq, _compute_magnitude_range
)

print('=' * 70)
print('  5 改进实施验证测试')
print('=' * 70)

# ============ 问题 2: Nelder/Powell 加入紧边界 ============
print('\n--- 问题 2: Nelder/Powell 加入紧边界 ---')
print(f'GLOBAL_METHODS: {GLOBAL_METHODS}')
print(f'SEMI_GLOBAL_METHODS: {SEMI_GLOBAL_METHODS}')
print(f'ALL_BOUND_SENSITIVE: {ALL_BOUND_SENSITIVE}')
print(f'METHOD_TIGHTEN_FACTOR: {METHOD_TIGHTEN_FACTOR}')

# Nelder 用紧边界
min_v, max_v = _compute_adaptive_bounds(100.0, 'nelder')
print(f'Nelder(100): [{min_v:.3e}, {max_v:.3e}] (期望 ~[1, 1e4])')
assert min_v == 1.0 and max_v == 10000.0, f'Nelder 紧边界错误: [{min_v}, {max_v}]'

# DE 用 1000x
min_v, max_v = _compute_adaptive_bounds(100.0, 'differential_evolution')
print(f'DE(100): [{min_v:.3e}, {max_v:.3e}] (期望 ~[0.1, 1e5])')
assert min_v == 0.1 and max_v == 100000.0, f'DE 紧边界错误'

# LS 仍用 1e-15~1e15
min_v, max_v = _compute_adaptive_bounds(100.0, 'least_squares')
print(f'LS(100): [{min_v:.3e}, {max_v:.3e}] (期望 [1e-15, 1e15])')
assert min_v == 1e-15 and max_v == 1e15, f'LS 宽边界错误'
print('[OK] 问题 2 验证通过')

# ============ 问题 6: 多解性检测 ============
print('\n--- 问题 6: 多解性检测 ---')
circuit_c2 = ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'p(', 'C3', ',', 'R4', ')']
r_c2 = _detect_multi_solution_risk(circuit_c2)
print(f'C2 双并联: 多解性风险 = {r_c2} (期望 True)')
assert r_c2 == True

circuit_c1 = ['R1', '+', 'p(', 'C3', ',', 'R6', ')']
r_c1 = _detect_multi_solution_risk(circuit_c1)
print(f'C1 Randles: 多解性风险 = {r_c1} (期望 False)')
assert r_c1 == False
print('[OK] 问题 6 验证通过')

# ============ 问题 4: 失败检测 ============
print('\n--- 问题 4: 失败检测 ---')

class FakeParams:
    def __init__(self, d): self.d = d
    def __contains__(self, k): return k in self.d
    def __getitem__(self, k):
        class P: pass
        p = P(); p.value = self.d[k]; return p

class FakeResult:
    def __init__(self, params_d): self.params = FakeParams(params_d)

# 成功拟合 (R1=105, init=100, 误差 5%)
res_ok = FakeResult({'R1': 105.0})
f_ok = _is_fitting_failed(res_ok, {'R1': 100.0})
print(f'成功: 失败判定 = {f_ok} (期望 False)')
assert f_ok == False

# 失败拟合 (R1=200, init=100, 误差 100%)
res_bad = FakeResult({'R1': 200.0})
f_bad = _is_fitting_failed(res_bad, {'R1': 100.0})
print(f'失败: 失败判定 = {f_bad} (期望 True)')
assert f_bad == True
print('[OK] 问题 4 验证通过')

# ============ 问题 5: R1_est 估算 ============
print('\n--- 问题 5: R1_est 估算 ---')
freq = np.logspace(1, 6, 100)
Z_pure_R = 100.0 + 1j * np.zeros(100)
R_est = _estimate_R_at_high_freq(freq, Z_pure_R)
print(f'R1_est = {R_est:.3f} (期望 ~100)')
assert abs(R_est - 100.0) < 1.0
print('[OK] 问题 5 验证通过')

# ============ 问题 8: tighten_factor 矩阵 ============
print('\n--- 问题 8: tighten_factor 矩阵 ---')
print(f'Nelder factor = {METHOD_TIGHTEN_FACTOR["nelder"]} (期望 100.0)')
print(f'Powell factor = {METHOD_TIGHTEN_FACTOR["powell"]} (期望 100.0)')
print(f'DE factor = {METHOD_TIGHTEN_FACTOR["differential_evolution"]} (期望 1000.0)')
assert METHOD_TIGHTEN_FACTOR['nelder'] == 100.0
assert METHOD_TIGHTEN_FACTOR['differential_evolution'] == 1000.0
print('[OK] 问题 8 验证通过')

# ============ 弹窗测试 ============
print('\n--- 弹窗接口测试 ---')
FittingWarnings.warn('测试 warning')
FittingWarnings.info('测试 info')
FittingWarnings.critical('测试 critical')
print('[OK] 弹窗接口正常')

print()
print('=' * 70)
print('  [ALL PASS] 5 改进全部验证通过')
print('=' * 70)
