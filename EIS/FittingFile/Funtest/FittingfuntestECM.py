# -*- coding: utf-8 -*-
"""
EIS 等效电路拟合测试套件 - 复杂电路与极限条件测试

测试策略：
1. 基础串联/并联电路已验证通过，本文件聚焦于复杂电路和已知失败场景
2. 展示拟合能力的边界，暴露已知的局限性
3. 为用户提供电路设计指导

测试内容：
1. 复杂混合串并联电路（元件数 > 3）
2. 多并联分支电路（已知会失败）
3. 参数量级悬殊电路（mΩ ~ MΩ）
4. 宽频率跨度电路（> 8 数量级）
5. 高噪声环境下的拟合

已知局限性：
- 多并联分支存在多解性问题，误差可达 80%+
- 极端参数量级差异时某些参数不可辨识
- 频率跨度过大时拟合收敛困难

Created on 2026-06-06
@author: takeilab
"""

import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plt
from numpy import pi, real, imag, logspace
from pandas import DataFrame, Series
from lmfit import Parameters
import random


# =============================================================================
# 电路仿真工具
# =============================================================================

def generate_circuit_impedance(circuit, params, freq):
    """根据电路描述生成阻抗数据"""
    from EIS.FittingFile.FittingECM import simuECM

    pm = Parameters()
    for name, value in params.items():
        pm.add(name, value=value)

    Z_total, _ = simuECM(pm, circuit, freq)
    return Z_total


def add_measurement_noise(Z_true, noise_level, seed=None):
    """添加测量噪声"""
    if seed is not None:
        np.random.seed(seed)
    noise = noise_level * (np.random.randn(len(Z_true)) + 1j * np.random.randn(len(Z_true)))
    return Z_true + noise * np.abs(Z_true)


def create_prodata(freq, Z):
    """创建标准 prodata DataFrame"""
    prodata = DataFrame()
    prodata['Rs[ohm]'] = Series(real(Z))
    prodata['X[ohm]'] = Series(imag(Z))
    return prodata


# =============================================================================
# 结果评估工具
# =============================================================================

def evaluate_and_print(result, true_params, title=""):
    """
    评估并打印拟合结果
    返回: (rating, max_error, is_acceptable)
    """
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(f"拟合成功: {result.success}")

    print(f"\n{'参数':<10} {'拟合值':<14} {'真值':<14} {'相对误差':<10} {'状态'}")
    print("-" * 65)

    max_error = 0
    for name in true_params:
        true_val = true_params[name]
        fit_val = result.params.get(name)
        if fit_val is None:
            continue

        fit_val = fit_val.value
        if true_val != 0:
            rel_error = abs((fit_val - true_val) / true_val) * 100
            max_error = max(max_error, rel_error)

            if rel_error < 5:
                status = "✓ 优秀"
            elif rel_error < 20:
                status = "~ 一般"
            elif rel_error < 50:
                status = "~ 较差"
            else:
                status = "✗ 失败"
        else:
            rel_error = 0
            status = "-"

        print(f"{name:<10} {fit_val:<14.6e} {true_val:<14.6e} {rel_error:>8.2f}%  {status}")

    print(f"\n最大相对误差: {max_error:.2f}%")

    # 判断是否可接受
    if max_error < 5:
        rating = "优秀"
        is_acceptable = True
    elif max_error < 20:
        rating = "一般"
        is_acceptable = True
    elif max_error < 100:
        rating = "较差"
        is_acceptable = False
    else:
        rating = "崩溃"
        is_acceptable = False

    return rating, max_error, is_acceptable


# =============================================================================
# 测试：复杂电路（串并联混合，元件数 > 3）
# =============================================================================

def test_complex_mixed_circuits():
    """
    测试复杂串并联混合电路
    电路结构: R + p(C, R) + p(C, R) + C
    预期: 部分参数拟合较好，部分参数因多解性而较差
    """
    print("\n" + "="*70)
    print("测试: 复杂串并联混合电路 (4元件)")
    print("电路: R1 + p(C1, R2) + p(C3, R4) + R5")
    print("="*70)

    # 定义电路参数
    true_params = {
        'R1': 50.0,
        'C1': 1e-5,
        'R2': 200.0,
        'C3': 1e-6,
        'R4': 500.0,
        'R5': 100.0
    }
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'p(', 'C3', ',', 'R4', ')', '+', 'R5']

    # 生成测试数据
    freq = logspace(0, 5, 150)
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    # 初始参数（偏离真值）
    init_params = {
        'R1': 30.0,
        'C1': 5e-6,
        'R2': 300.0,
        'C3': 5e-7,
        'R4': 300.0,
        'R5': 150.0
    }

    # 拟合
    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e12)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "复杂串并联混合电路结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")
    print("注意: 多个并联分支会导致多解性，部分参数可能收敛到错误解")

    return rating, max_error


def test_four_element_circuit():
    """
    测试4元件电路: R1 + p(C1, R2) + R3
    这是最复杂的可可靠拟合的电路结构
    """
    print("\n" + "="*70)
    print("测试: 4元件电路 R1 + p(C1, R2) + R3")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0, 'R3': 50.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'R3']

    freq = logspace(1, 6, 100)
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    # 初始参数
    init_params = {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0, 'R3': 80.0}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e12)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, is_ok = evaluate_and_print(result, true_params, "4元件电路结果")

    print(f"\n结论: {'可接受' if is_ok else '失败'} (最大误差 {max_error:.2f}%)")
    return rating, max_error


# =============================================================================
# 测试：多并联分支电路（预期失败）
# =============================================================================

def test_multi_parallel_branches():
    """
    测试多并联分支电路 - 预期失败
    电路: R + p(C,R) + p(C,R)
    这是已知的失败场景，用于验证用户指南的正确性
    """
    print("\n" + "="*70)
    print("测试: 多并联分支电路（已知会失败）")
    print("电路: R1 + p(C1, R2) + p(C3, R4)")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0, 'C3': 1e-7, 'R4': 1000.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'p(', 'C3', ',', 'R4', ')']

    freq = logspace(1, 6, 150)
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    # 初始参数
    init_params = {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0, 'C3': 5e-7, 'R4': 500.0}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e12)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "多并联分支结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")
    print("失败原因: 多并联分支存在多解性，优化器可能收敛到局部最优")

    return rating, max_error


def test_triple_parallel():
    """
    测试三并联电路: R + p(C,R) + p(C,R) + p(C,R) - 极度危险
    """
    print("\n" + "="*70)
    print("测试: 三并联分支（极度危险）")
    print("电路: R + p(C,R) + p(C,R) + p(C,R)")
    print("="*70)

    true_params = {
        'R1': 50.0,
        'C1': 1e-5, 'R2': 200.0,
        'C3': 1e-6, 'R4': 500.0,
        'C5': 1e-7, 'R6': 1000.0
    }
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')', '+', 'p(', 'C3', ',', 'R4', ')', '+', 'p(', 'C5', ',', 'R6', ')']

    freq = logspace(0, 5, 200)
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=123)
    prodata = create_prodata(freq, Z_measured)

    init_params = {k: v * 1.5 for k, v in true_params.items() if not k.startswith('C')}
    init_params.update({'C1': 5e-6, 'C3': 5e-7, 'C5': 5e-8})

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e12)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "三并联结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")
    print("警告: 3个以上并联分支的电路几乎不可能正确拟合！")

    return rating, max_error


# =============================================================================
# 测试：极端参数量级差异
# =============================================================================

def test_extreme_magnitude_mOhm_to_MOhm():
    """
    测试极端量级差异: mΩ 到 MΩ
    R1 = 1mΩ, C1 = 1mF, R2 = 1MΩ
    差异: 12 个数量级
    """
    print("\n" + "="*70)
    print("测试: 极端量级差异 (mΩ ~ MΩ)")
    print("参数: R1=1mΩ, C1=1mF, R2=1MΩ (差异 1e12)")
    print("="*70)

    true_params = {'R1': 1e-3, 'C1': 1e-3, 'R2': 1e6}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    # 需要极宽的频率范围来覆盖所有元件的特征频率
    freq = logspace(-2, 8, 300)  # 0.01Hz ~ 100MHz
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    # 初始参数
    init_params = {'R1': 1e-2, 'C1': 1e-2, 'R2': 1e7}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-15, max=1e15)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "极端量级差异结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")
    print("分析:")
    print("  - R1(串联电阻): 通常可辨识，因为所有频率下都可见")
    print("  - C1(电容): 在中频段可见，特征频率 fc=1/(2πRC) ≈ 0.16 Hz")
    print("  - R2(并联电阻): 在低频段可见，但 fc 极低可能超出测量范围")

    return rating, max_error


def test_high_resistance_extreme():
    """
    测试高阻值极端情况: R2 = 10MΩ
    这种情况下并联电阻在测量范围内可能"不可见"
    """
    print("\n" + "="*70)
    print("测试: 高阻值极端 (R2=10MΩ)")
    print("预期: 并联电阻可能因特征频率过低而不可辨识")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 1e7}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    # 标准频率范围
    freq = logspace(0, 6, 150)  # 1Hz ~ 1MHz
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    init_params = {'R1': 150.0, 'C1': 2e-6, 'R2': 5e6}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e15)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "高阻值结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")

    # 计算特征频率
    f_char = 1 / (2 * pi * true_params['R2'] * true_params['C1'])
    print(f"\n特征频率分析:")
    print(f"  R2={true_params['R2']:.0e}Ω, C1={true_params['C1']:.0e}F")
    print(f"  fc = 1/(2πRC) = {f_char:.2e} Hz")
    print(f"  测量频率范围: {freq[0]:.0e} ~ {freq[-1]:.0e} Hz")
    if f_char < freq[0]:
        print(f"  警告: fc < f_min，并联电阻在测量范围内不可见！")

    return rating, max_error


def test_low_capacitance_extreme():
    """
    测试低容值极端情况: C1 = 1pF
    特征频率会非常高，可能超出测量范围
    """
    print("\n" + "="*70)
    print("测试: 低容值极端 (C1=1pF)")
    print("预期: 电容特征频率过高，无法辨识")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-12, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    freq = logspace(3, 9, 150)  # 1kHz ~ 1GHz
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    init_params = {'R1': 150.0, 'C1': 5e-12, 'R2': 300.0}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-15, max=1e12)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "低容值结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")

    f_char = 1 / (2 * pi * true_params['R2'] * true_params['C1'])
    print(f"\n特征频率分析:")
    print(f"  R2={true_params['R2']:.0e}Ω, C1={true_params['C1']:.0e}F")
    print(f"  fc = {f_char:.2e} Hz")
    print(f"  测量频率范围: {freq[0]:.0e} ~ {freq[-1]:.0e} Hz")
    if f_char > freq[-1]:
        print(f"  警告: fc > f_max，电容在测量范围内不可见！")

    return rating, max_error


# =============================================================================
# 测试：宽频率跨度
# =============================================================================

def test_wide_frequency_span():
    """
    测试宽频率跨度: 10 数量级
    这对拟合算法是一个挑战
    """
    print("\n" + "="*70)
    print("测试: 宽频率跨度 (10 数量级)")
    print("频率范围: 10Hz ~ 100MHz")
    print("="*70)

    true_params = {'R1': 50.0, 'C1': 1e-6, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    freq = logspace(1, 11, 200)  # 10数量级
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    init_params = {'R1': 80.0, 'C1': 5e-6, 'R2': 300.0}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e12)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "宽频率跨度结果")

    print(f"\n结论: {rating} (最大误差 {max_error:.2f}%)")
    print("注意: 宽频率跨度会导致不同频段数据尺度差异大，影响拟合收敛")

    return rating, max_error


# =============================================================================
# 测试：高噪声环境
# =============================================================================

def test_high_noise_environment():
    """
    测试高噪声环境 (10% 噪声)
    模拟真实测量条件
    """
    print("\n" + "="*70)
    print("测试: 高噪声环境 (10% 噪声)")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-6, 'R2': 500.0}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    freq = logspace(1, 6, 100)
    Z_true = generate_circuit_impedance(circuit, true_params, freq)

    # 测试不同噪声水平
    noise_levels = [0.01, 0.05, 0.10, 0.20]
    results = []

    print(f"\n噪声水平对比:")
    print(f"{'噪声水平':<12} {'最大误差':<12} {'评级'}")
    print("-" * 40)

    for noise in noise_levels:
        Z_measured = add_measurement_noise(Z_true, noise, seed=42 + int(noise*100))
        prodata = create_prodata(freq, Z_measured)

        init_params = {'R1': 150.0, 'C1': 2e-6, 'R2': 300.0}

        from EIS.FittingFile.FittingECM import FittingECM
        pm = Parameters()
        for name, val in init_params.items():
            pm.add(name, value=val, min=1e-12, max=1e12)

        result = FittingECM(pm, freq, circuit, prodata)

        max_error = 0
        for name, true_val in true_params.items():
            fit_val = result.params.get(name).value
            if true_val != 0:
                rel_error = abs((fit_val - true_val) / true_val) * 100
                max_error = max(max_error, rel_error)

        rating = "优秀" if max_error < 5 else ("良好" if max_error < 20 else "较差" if max_error < 100 else "崩溃")
        print(f"{noise*100:>6.1f}%       {max_error:>8.2f}%     {rating}")
        results.append((noise, max_error, rating))

    return results


# =============================================================================
# 测试：小电容 + 大电阻组合
# =============================================================================

def test_small_capacitance_large_resistance():
    """
    测试小电容 + 大电阻组合
    特征频率可能非常低，导致参数不可辨识
    """
    print("\n" + "="*70)
    print("测试: 小电容 + 大电阻组合")
    print("C1=1nF, R2=10MΩ, fc ≈ 0.016 Hz")
    print("="*70)

    true_params = {'R1': 100.0, 'C1': 1e-9, 'R2': 1e7}
    circuit = ['R1', '+', 'p(', 'C1', ',', 'R2', ')']

    # 标准频率范围
    freq = logspace(0, 6, 150)
    Z_true = generate_circuit_impedance(circuit, true_params, freq)
    Z_measured = add_measurement_noise(Z_true, 0.01, seed=42)
    prodata = create_prodata(freq, Z_measured)

    init_params = {'R1': 150.0, 'C1': 5e-9, 'R2': 5e6}

    from EIS.FittingFile.FittingECM import FittingECM
    pm = Parameters()
    for name, val in init_params.items():
        pm.add(name, value=val, min=1e-12, max=1e15)

    result = FittingECM(pm, freq, circuit, prodata)
    rating, max_error, _ = evaluate_and_print(result, true_params, "小C大R结果")

    f_char = 1 / (2 * pi * true_params['R2'] * true_params['C1'])
    print(f"\n特征频率: {f_char:.2e} Hz (低于 {freq[0]:.0f}Hz 测量下限)")

    return rating, max_error


# =============================================================================
# 主测试函数
# =============================================================================

def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*70)
    print("# EIS 等效电路拟合测试套件 - 复杂电路与极限条件")
    print("#"*70)

    results = {}

    # 1. 复杂电路测试
    print("\n\n" + "="*70)
    print("=" + " "*20 + "复杂电路测试" + " "*38 + "=")
    print("="*70)

    rating, error = test_four_element_circuit()
    results['4元件电路'] = (rating, error)

    rating, error = test_complex_mixed_circuits()
    results['复杂串并联'] = (rating, error)

    # 2. 多并联分支测试（预期失败）
    print("\n\n" + "="*70)
    print("=" + " "*15 + "多并联分支电路测试（已知失败场景）" + " "*15 + "=")
    print("="*70)

    rating, error = test_multi_parallel_branches()
    results['双并联分支'] = (rating, error)

    rating, error = test_triple_parallel()
    results['三并联分支'] = (rating, error)

    # 3. 极端量级差异测试
    print("\n\n" + "="*70)
    print("=" + " "*20 + "极端量级差异测试" + " "*35 + "=")
    print("="*70)

    rating, error = test_extreme_magnitude_mOhm_to_MOhm()
    results['mΩ~MΩ量级差'] = (rating, error)

    rating, error = test_high_resistance_extreme()
    results['高阻值极端'] = (rating, error)

    rating, error = test_low_capacitance_extreme()
    results['低容值极端'] = (rating, error)

    # 4. 宽频率跨度测试
    print("\n\n" + "="*70)
    print("=" + " "*20 + "宽频率跨度测试" + " "*38 + "=")
    print("="*70)

    rating, error = test_wide_frequency_span()
    results['10数量级跨度'] = (rating, error)

    # 5. 高噪声测试
    print("\n\n" + "="*70)
    print("=" + " "*20 + "高噪声环境测试" + " "*38 + "=")
    print("="*70)

    results['高噪声环境'] = test_high_noise_environment()

    # 6. 小电容大电阻组合
    print("\n\n" + "="*70)
    print("=" + " "*15 + "小电容大电阻组合测试" + " "*33 + "=")
    print("="*70)

    rating, error = test_small_capacitance_large_resistance()
    results['小C大R组合'] = (rating, error)

    # 汇总
    print("\n\n" + "#"*70)
    print("# 测试结果汇总")
    print("#"*70)

    print(f"\n{'测试项':<20} {'最大误差':<12} {'评级'}")
    print("-" * 45)

    for name, (rating, error) in results.items():
        if isinstance(error, tuple):
            error_str = f"{error[0]*100:.1f}%~{error[-1]*100:.1f}%"
        else:
            error_str = f"{error:.2f}%"
        print(f"{name:<20} {error_str:<12} {rating}")

    print("\n" + "="*70)
    print("测试完成")
    print("="*70)

    return results


if __name__ == "__main__":
    run_all_tests()