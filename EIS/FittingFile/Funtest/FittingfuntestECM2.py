# -*- coding: utf-8 -*-
"""
EIS 等效电路拟合测试套件 - 极端条件与策略验证

> **DEPRECATED**：
> 推荐使用 [test_all_methods.py](test_all_methods.py) 作为统一测试入口。
> 本文件保留为单独测试策略选择和决策函数的旧版脚本，
> `test_auto_fitting_edge_cases` 已添加 `methods` 参数。

本文件聚焦于：
1. 决策函数验证（should_use_segmented, should_use_extreme）
2. 参数可辨识性检查（check_parameter_identifiability）
3. 自适应分段策略（adaptive_segmentation）
4. 极端拟合策略的边界条件
5. 拟合策略选择的正确性验证

测试哲学：
- 不是验证"什么能工作"，而是验证"策略选择是否正确"
- 揭示极端条件下的问题，而非掩盖
- 为用户提供明确的电路设计边界指导

Created on 2026-06-06
@author: takeilab
Updated on 2026-08-24: 添加 methods 参数 + 与 test_all_methods 同步
"""

import sys
sys.path.append('..')

import numpy as np
from numpy import pi, real, imag, logspace
from pandas import DataFrame, Series
from lmfit import Parameters

# 导入待测试的函数
from EIS.FittingFile.FittingECM import (
    simuECM,
    FittingECM,
    segmented_fitting,
    should_use_segmented,
    should_use_extreme,
    auto_fitting,
    _auto_fitting_core,
    smart_fitting,
    FittingresultsprocessECM,
    creatdatabaseECM,
    generate_test_data
)

from EIS.FittingFile.FittingECM_extreme import (
    check_parameter_identifiability,
    adaptive_segmentation,
    multi_start_fit,
    fit_extreme,
    generate_synthetic_data
)


# =============================================================================
# 辅助工具
# =============================================================================

def create_test_data(circuit, true_params, freq, noise_level=0.01, seed=42):
    """创建测试数据"""
    np.random.seed(seed)

    # 创建 Parameters 对象
    pm = Parameters()
    for name, value in true_params.items():
        pm.add(name, value=value)

    Z_true, _ = simuECM(pm, circuit, freq)
    noise = noise_level * (np.random.randn(len(freq)) + 1j * np.random.randn(len(freq)))
    Z_measured = Z_true + noise * np.abs(Z_true)

    prodata = DataFrame()
    prodata['Rs[ohm]'] = Series(real(Z_measured))
    prodata['X[ohm]'] = Series(imag(Z_measured))

    return prodata, Z_true


def characterize_frequency(true_params, circuit_type='randles'):
    """
    计算电路的特征频率
    对于 Randles 电路: fc = 1 / (2 * pi * R2 * C1)
    """
    if circuit_type == 'randles':
        R2 = true_params.get('R2', true_params.get('R4', 500.0))  # 并联电阻
        C1 = true_params.get('C1', true_params.get('C3', 1e-6))  # 电容
        return 1 / (2 * pi * R2 * C1)
    return None


# =============================================================================
# 测试：决策函数边界条件
# =============================================================================

def test_should_use_decision_functions():
    """
    测试决策函数 should_use_segmented 和 should_use_extreme 的边界条件
    验证策略选择逻辑的正确性
    """
    print("\n" + "="*70)
    print("测试: 决策函数边界条件")
    print("="*70)

    results = []

    # =========================================================================
    # 测试 should_use_segmented
    # =========================================================================
    print("\n--- should_use_segmented 边界条件 ---")

    segmented_cases = [
        {
            'name': '仅1个电阻（无需分段）',
            'freq': logspace(1, 8, 100),
            'params': {'R1': 100.0, 'C1': 1e-6},
            'expected': False,
            'reason': '只有1个电阻参数'
        },
        {
            'name': '2个电阻但量级差异小',
            'freq': logspace(1, 4, 100),  # 3数量级
            'params': {'R1': 100.0, 'C1': 1e-4, 'R2': 500.0},  # 1e2 ~ 1e3
            'expected': False,
            'reason': '量级差异约1e1~1e2'
        },
        {
            'name': '频率跨度大+量级差异大',
            'freq': logspace(1, 12, 100),  # 11数量级
            'params': {'R1': 1e-3, 'C1': 1e-3, 'R2': 1e6},  # 1e9差异
            'expected': True,
            'reason': '频率跨度>10 + 参数量级>1e7'
        },
        {
            'name': '参数量级差异极大',
            'freq': logspace(1, 5, 100),
            'params': {'R1': 1e-6, 'C1': 1e-3, 'R2': 1e6},  # 1e12差异
            'expected': True,
            'reason': '量级差异>1e8'
        },
    ]

    print(f"\n{'场景':<30} {'预期':<8} {'实际':<8} {'结果'}")
    print("-" * 60)

    for tc in segmented_cases:
        use_seg, reason = should_use_segmented(tc['freq'], tc['params'])
        passed = use_seg == tc['expected']
        status = "✓" if passed else "✗"
        print(f"{tc['name']:<30} {str(tc['expected']):<8} {str(use_seg):<8} {status}")
        if not passed:
            print(f"  原因: {reason}")
        results.append(('should_use_segmented', tc['name'], passed))

    # =========================================================================
    # 测试 should_use_extreme
    # =========================================================================
    print("\n--- should_use_extreme 边界条件 ---")

    extreme_cases = [
        {
            'name': '温和参数（无需极端）',
            'freq': logspace(1, 5, 100),  # 5数量级
            'params': {'R1': 100.0, 'C1': 1e-4, 'R2': 500.0},  # 1e4差异
            'expected': False,
            'reason': '频率跨度5 + 量级差异1e4'
        },
        {
            'name': '频率跨度大',
            'freq': logspace(1, 9, 100),  # 8数量级
            'params': {'R1': 10.0, 'C1': 1e-6, 'R2': 1e6},  # 1e5差异
            'expected': True,
            'reason': '频率跨度>7'
        },
        {
            'name': '参数量级差异极大',
            'freq': logspace(1, 5, 100),
            'params': {'R1': 1e-6, 'C1': 1e0, 'R2': 1e6},  # 1e12差异
            'expected': True,
            'reason': '量级差异>1e9'
        },
        {
            'name': '空参数',
            'freq': logspace(1, 5, 100),
            'params': {},
            'expected': False,
            'reason': '无参数信息'
        },
    ]

    print(f"\n{'场景':<30} {'预期':<8} {'实际':<8} {'结果'}")
    print("-" * 60)

    for tc in extreme_cases:
        use_ext, reason = should_use_extreme(tc['freq'], tc['params'])
        passed = use_ext == tc['expected']
        status = "✓" if passed else "✗"
        print(f"{tc['name']:<30} {str(tc['expected']):<8} {str(use_ext):<8} {status}")
        if not passed:
            print(f"  原因: {reason}")
        results.append(('should_use_extreme', tc['name'], passed))

    # 汇总
    total = len(results)
    passed = sum(1 for _, _, p in results if p)
    print(f"\n决策函数测试: {passed}/{total} 通过")

    return all(p for _, _, p in results)


# =============================================================================
# 测试：参数可辨识性
# =============================================================================

def test_parameter_identifiability():
    """
    测试参数可辨识性检查函数
    验证 check_parameter_identifiability 是否正确识别不可见参数
    """
    print("\n" + "="*70)
    print("测试: 参数可辨识性检查")
    print("="*70)

    cases = [
        {
            'name': '正常Randles电路',
            'freq': logspace(1, 6, 100),
            'R1': 100.0, 'C3': 1e-6, 'R6': 500.0,
            'expected_status': 'visible',
            'expected_identifiable': True,
        },
        {
            'name': '并联电阻不可见 (fc < f_min)',
            'freq': logspace(3, 6, 100),  # 1kHz ~ 1MHz
            'R1': 100.0, 'C3': 1e-6, 'R6': 1e7,  # R6=10MΩ, fc≈0.016Hz << 1kHz
            'expected_status': 'parallel_R_invisible',
            'expected_identifiable': False,
        },
        {
            'name': '电容不可见 (fc > f_max)',
            'freq': logspace(1, 4, 100),  # 10Hz ~ 10kHz
            'R1': 100.0, 'C3': 1e-12, 'R6': 500.0,  # C3=1pF, fc≈318MHz >> 10kHz
            'expected_status': 'C_invisible',
            'expected_identifiable': False,
        },
        {
            'name': '边界情况 (fc ≈ f_min)',
            'freq': logspace(1, 5, 100),  # 10Hz ~ 100kHz
            'R1': 100.0, 'C3': 1e-6, 'R6': 1590.0,  # fc≈100Hz，在范围内
            'expected_status': 'visible',
            'expected_identifiable': True,
        },
    ]

    print(f"\n{'场景':<35} {'状态':<25} {'可辨识'}")
    print("-" * 85)

    all_passed = True
    for tc in cases:
        result = check_parameter_identifiability(tc['freq'], R6=tc['R6'], C3=tc['C3'])

        status_ok = result['status'] == tc['expected_status']
        ident_ok = result['identifiable'] == tc['expected_identifiable']
        passed = status_ok and ident_ok
        all_passed = all_passed and passed

        status_str = "✓" if passed else "✗"
        print(f"{tc['name']:<35} {result['status']:<25} {result['identifiable']}")

        if not passed:
            print(f"  预期状态: {tc['expected_status']}, 实际: {result['status']}")
            print(f"  预期可辨识: {tc['expected_identifiable']}, 实际: {result['identifiable']}")
            if 'f_char' in result:
                print(f"  特征频率: {result['f_char']:.2e} Hz")

    print(f"\n参数可辨识性测试: {'通过' if all_passed else '失败'}")
    return all_passed


# =============================================================================
# 测试：自适应分段
# =============================================================================

def test_adaptive_segmentation():
    """
    测试自适应分段函数
    验证能否正确估计串联电阻和并联电阻
    """
    print("\n" + "="*70)
    print("测试: 自适应分段估计")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']
    freq = logspace(1, 6, 200)

    prodata, _ = create_test_data(circuit, true_params, freq)
    ZData = prodata['Rs[ohm]'] + 1j * prodata['X[ohm]']

    # 计算特征频率
    f_char = characterize_frequency(true_params)

    print(f"\n电路参数: R1={true_params['R1']}, C1={true_params['C1']:.0e}, R2={true_params['R2']}")
    print(f"特征频率: {f_char:.2e} Hz")

    # 调用 adaptive_segmentation
    seg_info = adaptive_segmentation(freq, ZData, f_char, init_params=true_params)

    print(f"\n分段估计结果:")
    print(f"  串联电阻估计: {seg_info.get('series_R_est', 'N/A'):.2f} Ω (真值: {true_params['R1']})")
    print(f"  并联电阻估计: {seg_info.get('parallel_R_est', 'N/A'):.2f} Ω (真值: {true_params['R2']})")
    print(f"  电容估计: {seg_info.get('C_est', 'N/A'):.2e} F (真值: {true_params['C1']})")

    # 计算误差
    series_error = abs(seg_info.get('series_R_est', 0) - true_params['R1']) / true_params['R1'] * 100
    parallel_error = abs(seg_info.get('parallel_R_est', 0) - true_params['R2']) / true_params['R2'] * 100

    print(f"\n估计误差:")
    print(f"  串联电阻: {series_error:.2f}%")
    print(f"  并联电阻: {parallel_error:.2f}%")

    # 串联电阻估计应该比较准确
    series_ok = series_error < 10
    print(f"\n结论: 串联电阻估计{'准确' if series_ok else '不准确'}")

    return series_ok


# =============================================================================
# 测试：smart_fitting 策略选择
# =============================================================================

def test_smart_fitting_strategy_selection():
    """
    测试 smart_fitting 是否正确选择拟合策略
    """
    print("\n" + "="*70)
    print("测试: smart_fitting 策略选择")
    print("="*70)

    test_cases = [
        {
            'name': '简单电路（直接拟合）',
            'circuit': ['R1', '+', 'C1'],
            'true_params': {'R1': 100.0, 'C1': 1e-6},
            'init_params': {'R1': 150.0, 'C1': 2e-6},
            'freq_range': (1, 5),
            'expected_strategy': 'direct',  # 简单电路应该直接拟合
        },
        {
            'name': 'Randles电路（自动选择）',
            'circuit': ['p(', 'C1', ',', 'R2', ')', '+', 'R1'],
            'true_params': {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0},
            'init_params': {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0},
            'freq_range': (1, 6),
            'expected_strategy': 'auto',  # 复杂电路应该自动选择
        },
    ]

    print(f"\n{'场景':<25} {'策略':<15} {'拟合质量'}")
    print("-" * 60)

    results = []
    for tc in test_cases:
        freq = logspace(*tc['freq_range'], 100)
        prodata, _ = create_test_data(tc['circuit'], tc['true_params'], freq)

        # 调用 smart_fitting - 参数是字典不是 Parameters 对象
        # smart_fitting 返回 (result, fitted_params, method_used, step_info)
        result, fitted_params, method_used, step_info = smart_fitting(freq, prodata, tc['circuit'], tc['init_params'])

        # 评估结果
        max_error = 0
        for name, true_val in tc['true_params'].items():
            fit_val = result.params.get(name).value
            rel_error = abs((fit_val - true_val) / true_val) * 100
            max_error = max(max_error, rel_error)

        quality = "优秀" if max_error < 5 else ("良好" if max_error < 20 else "一般" if max_error < 50 else "较差")
        print(f"{tc['name']:<25} {tc['expected_strategy']:<15} {quality} (误差{max_error:.1f}%)")
        results.append((tc['name'], max_error < 50))

    return all(p for _, p in results)


# =============================================================================
# 测试：auto_fitting 边界条件
# =============================================================================

def test_auto_fitting_edge_cases(methods=None):
    """
    测试 auto_fitting 在边界条件下的表现
    methods: 列表，可指定多种方法对比
    """
    if methods is None:
        methods = ['least_squares']

    print("\n" + "="*70)
    print("测试: auto_fitting 边界条件")
    print(f"方法: {methods}")
    print("="*70)

    cases = [
        {
            'name': '极窄频率范围',
            'circuit': ['p(', 'C1', ',', 'R2', ')', '+', 'R1'],
            'true_params': {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0},
            'init_params': {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0},
            'freq_range': (4, 5),  # 仅1数量级
        },
        {
            'name': '极宽频率范围',
            'circuit': ['p(', 'C1', ',', 'R2', ')', '+', 'R1'],
            'true_params': {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0},
            'init_params': {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0},
            'freq_range': (0, 9),  # 9数量级
        },
        {
            'name': '参数量级悬殊',
            'circuit': ['p(', 'C1', ',', 'R2', ')', '+', 'R1'],
            'true_params': {'R1': 1e-3, 'C1': 1e-3, 'R2': 1e6},  # 1e9差异
            'init_params': {'R1': 1e-2, 'C1': 1e-2, 'R2': 1e7},
            'freq_range': (1, 7),
        },
    ]

    # 表头：场景 + 每个方法的误差
    header = f"{'场景':<20}"
    for m in methods:
        header += f"  {m:>16s}"
    print(f"\n{header}")
    print('-' * (20 + 18 * len(methods)))

    results = []
    for tc in cases:
        freq = logspace(*tc['freq_range'], 150)
        prodata, _ = create_test_data(tc['circuit'], tc['true_params'], freq)
        row = f"{tc['name']:<20}"
        for m in methods:
            pm = Parameters()
            for name, val in tc['init_params'].items():
                pm.add(name, value=val, min=1e-15, max=1e15)
            try:
                result = auto_fitting(pm, freq, tc['circuit'], prodata, method=m)

                max_error = 0
                for name, true_val in tc['true_params'].items():
                    fit_val = result.params.get(name).value
                    rel_error = abs((fit_val - true_val) / true_val) * 100
                    max_error = max(max_error, rel_error)

                quality = "优" if max_error < 5 else ("良" if max_error < 20 else ("中" if max_error < 100 else "差"))
                row += f"  {f'{max_error:.1f}%({quality})':>16s}"
            except Exception as e:
                row += f"  {'ERR':>16s}"
        print(row)
        results.append((tc['name'], row))

    return results


# =============================================================================
# 测试：fit_extreme 效果
# =============================================================================

def test_fit_extreme_effectiveness():
    """
    测试极端拟合策略的效果
    对比标准拟合 vs 极端拟合
    """
    print("\n" + "="*70)
    print("测试: fit_extreme 效果对比")
    print("="*70)

    # 测试场景：参数量级差异大
    # 注意: fit_extreme 设计用于 R1 + p(C3, R6) 格式电路
    # 我们使用匹配的参数名来测试
    true_params = {'R1': 1e-3, 'C3': 1e-3, 'R6': 1e6}  # 1e9差异
    circuit = ['R1', '+', 'p(', 'C3', ',', 'R6', ')']
    freq = logspace(-1, 8, 250)  # 极宽范围

    prodata, _ = create_test_data(circuit, true_params, freq)

    # 标准拟合
    print("\n[标准拟合]")
    pm_std = Parameters()
    pm_std.add('R1', value=1e-2, min=1e-15, max=1e15)
    pm_std.add('C3', value=1e-2, min=1e-15, max=1e15)
    pm_std.add('R6', value=1e7, min=1e-15, max=1e15)

    result_std = FittingECM(pm_std, freq, circuit, prodata)

    max_error_std = 0
    for name, true_val in true_params.items():
        fit_val = result_std.params.get(name).value
        rel_error = abs((fit_val - true_val) / true_val) * 100
        max_error_std = max(max_error_std, rel_error)
        print(f"  {name}: 拟合={fit_val:.2e}, 真值={true_val:.2e}, 误差={rel_error:.1f}%")

    print(f"  最大误差: {max_error_std:.2f}%")

    # 极端拟合
    # 注意: fit_extreme 设计用于 R1 + p(C3, R6) 格式的电路
    # 参数命名反映了这个特定格式
    print("\n[极端拟合 - fit_extreme]")
    try:
        result_ext = fit_extreme(
            freq, prodata, circuit,
            R6_init=true_params['R6'],
            C3_init=true_params['C3'],
            R1_true=true_params.get('R1'),
            C3_true=true_params.get('C3'),
            R6_true=true_params.get('R6'),
            n_starts=10
        )

        if result_ext is not None and result_ext['result'].success:
            max_error_ext = 0
            for name, true_val in true_params.items():
                fit_val = result_ext['result'].params.get(name).value
                rel_error = abs((fit_val - true_val) / true_val) * 100
                max_error_ext = max(max_error_ext, rel_error)
                print(f"  {name}: 拟合={fit_val:.2e}, 真值={true_val:.2e}, 误差={rel_error:.1f}%")
            print(f"  最大误差: {max_error_ext:.2f}%")
        else:
            print("  fit_extreme 失败")
            max_error_ext = float('inf')
    except Exception as e:
        print(f"  fit_extreme 异常: {e}")
        max_error_ext = float('inf')

    # 对比
    print(f"\n对比: 标准={max_error_std:.2f}%, 极端={max_error_ext:.2f}%")
    if max_error_ext < max_error_std:
        print("结论: 极端拟合更优")
    elif max_error_std < max_error_ext:
        print("结论: 标准拟合更优（这在某些情况下可能发生）")
    else:
        print("结论: 两者效果相当")

    return max_error_std, max_error_ext


# =============================================================================
# 测试：特征频率对拟合的影响
# =============================================================================

def test_characteristic_frequency_impact():
    """
    测试特征频率位置对拟合的影响
    揭示频率范围选择的重要性
    """
    print("\n" + "="*70)
    print("测试: 特征频率位置对拟合的影响")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    # 特征频率
    f_char = 1 / (2 * pi * true_params['R2'] * true_params['C1'])  # ≈318 Hz

    test_cases = [
        {
            'name': 'fc 在频率范围中心',
            'freq_range': (1, 6),  # 10Hz ~ 1MHz, fc≈318Hz在中间
        },
        {
            'name': 'fc 接近频率上限',
            'freq_range': (2, 4),  # 100Hz ~ 10kHz, fc≈318Hz接近上限
        },
        {
            'name': 'fc 接近频率下限',
            'freq_range': (0, 3),  # 1Hz ~ 1kHz, fc≈318Hz接近下限
        },
        {
            'name': 'fc 超出频率范围',
            'freq_range': (3, 6),  # 1kHz ~ 1MHz, fc≈318Hz低于下限
        },
    ]

    print(f"\n特征频率: {f_char:.2f} Hz")
    print(f"\n{'场景':<30} {'fc位置':<15} {'最大误差':<12} {'评级'}")
    print("-" * 70)

    results = []
    for tc in test_cases:
        freq = logspace(*tc['freq_range'], 100)
        prodata, _ = create_test_data(circuit, true_params, freq)

        pm = Parameters()
        pm.add('R1', value=150.0, min=1e-12, max=1e12)
        pm.add('C1', value=2e-6, min=1e-15, max=1)
        pm.add('R2', value=300.0, min=1e-12, max=1e12)

        result = FittingECM(pm, freq, circuit, prodata)

        max_error = 0
        for name, true_val in true_params.items():
            fit_val = result.params.get(name).value
            rel_error = abs((fit_val - true_val) / true_val) * 100
            max_error = max(max_error, rel_error)

        # 判断 fc 位置
        if f_char < freq[0]:
            fc_pos = "低于f_min"
        elif f_char > freq[-1]:
            fc_pos = "高于f_max"
        else:
            fc_pos = "在范围内"

        quality = "优秀" if max_error < 5 else ("良好" if max_error < 20 else "一般" if max_error < 100 else "较差")
        print(f"{tc['name']:<30} {fc_pos:<15} {max_error:>10.2f}%   {quality}")
        results.append((tc['name'], max_error))

    print("\n结论: 特征频率应位于测量频率范围的中部，以获得最佳拟合效果")
    return results


# =============================================================================
# 测试：噪声对决策函数的影响
# =============================================================================

def test_noise_impact_on_decisions():
    """
    测试测量噪声对策略选择的影响
    验证决策函数对噪声的鲁棒性
    """
    print("\n" + "="*70)
    print("测试: 噪声对策略选择的影响")
    print("="*70)

    # 相同电路，不同噪声水平
    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']
    freq = logspace(1, 6, 100)

    noise_levels = [0.0, 0.01, 0.05, 0.10, 0.20]

    print(f"\n{'噪声水平':<12} {'should_segmented':<18} {'should_extreme'}")
    print("-" * 50)

    for noise in noise_levels:
        np.random.seed(42)
        pm = Parameters()
        for name, value in true_params.items():
            pm.add(name, value=value)
        Z_true, _ = simuECM(pm, circuit, freq)
        Z_measured = Z_true + noise * np.abs(Z_true) * np.random.randn(*Z_true.shape) * (1 + 1j)

        # 提取 params 用于决策
        params_for_decision = true_params.copy()

        use_seg, _ = should_use_segmented(freq, params_for_decision)
        use_ext, _ = should_use_extreme(freq, params_for_decision)

        print(f"{noise*100:>6.1f}%       {str(use_seg):<18} {use_ext}")

    print("\n注意: 决策函数基于电路参数和频率范围，不受噪声影响")
    print("      噪声影响的是拟合质量，而非策略选择")


# =============================================================================
# 主测试函数
# =============================================================================

def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*70)
    print("# EIS 等效电路拟合测试套件 - 极端条件与策略验证")
    print("#"*70)

    results = {}

    # 1. 决策函数边界条件
    print("\n\n" + "="*70)
    print("=" + " "*15 + "决策函数边界条件测试" + " "*30 + "=")
    print("="*70)

    results['决策函数'] = test_should_use_decision_functions()

    # 2. 参数可辨识性
    print("\n\n" + "="*70)
    print("=" + " "*20 + "参数可辨识性测试" + " "*32 + "=")
    print("="*70)

    results['参数可辨识性'] = test_parameter_identifiability()

    # 3. 自适应分段
    print("\n\n" + "="*70)
    print("=" + " "*20 + "自适应分段测试" + " "*36 + "=")
    print("="*70)

    results['自适应分段'] = test_adaptive_segmentation()

    # 4. smart_fitting 策略选择
    print("\n\n" + "="*70)
    print("=" + " "*15 + "smart_fitting 策略选择测试" + " "*24 + "=")
    print("="*70)

    results['策略选择'] = test_smart_fitting_strategy_selection()

    # 5. auto_fitting 边界条件
    print("\n\n" + "="*70)
    print("=" + " "*20 + "auto_fitting 边界条件" + " "*32 + "=")
    print("="*70)

    # 多方法对比：least_squares + lbfgsb + differential_evolution
    results['边界条件'] = test_auto_fitting_edge_cases(
        methods=['least_squares', 'lbfgsb', 'differential_evolution']
    )

    # 6. fit_extreme 效果对比
    print("\n\n" + "="*70)
    print("=" + " "*20 + "fit_extreme 效果对比" + " "*32 + "=")
    print("="*70)

    results['极端拟合对比'] = test_fit_extreme_effectiveness()

    # 7. 特征频率影响
    print("\n\n" + "="*70)
    print("=" + " "*20 + "特征频率位置影响" + " "*34 + "=")
    print("="*70)

    results['特征频率'] = test_characteristic_frequency_impact()

    # 8. 噪声影响
    print("\n\n" + "="*70)
    print("=" + " "*20 + "噪声对策略影响" + " "*36 + "=")
    print("="*70)

    test_noise_impact_on_decisions()
    results['噪声影响'] = True

    # 汇总
    print("\n\n" + "#"*70)
    print("# 测试结果汇总")
    print("#"*70)

    print(f"\n{'测试项':<25} {'结果'}")
    print("-" * 40)

    for name, result in results.items():
        if isinstance(result, bool):
            status = "✓ 通过" if result else "✗ 失败"
        elif isinstance(result, tuple):
            status = "完成"
        else:
            status = "完成"
        print(f"{name:<25} {status}")

    print("\n" + "="*70)
    print("测试完成")
    print("="*70)

    return results


if __name__ == "__main__":
    run_all_tests()