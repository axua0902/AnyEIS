# -*- coding: utf-8 -*-
"""
FittingMT.py 综合测试套件

测试内容：
1. 基础功能测试：fittingmodel, fcn2min, creatdatabase
2. 标准拟合测试：FittingMT (双弛豫模型)
3. 自动拟合测试：FittingMT_auto (各种场景)
4. 不同模型类型测试：Debye, Cole-Cole, Davidson-Cole, Havriliak-Negami
5. 多参数场景测试：单、双、三弛豫
6. 结果可视化

Created on 2020-08-04, Updated on 2026-06-05
@author: takeilab
"""

import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plt
from numpy import pi, real, imag, log10
from pandas import DataFrame, Series
from lmfit import Parameters, report_fit

from EIS.FittingFile.FittingMT import (
    fittingmodel,
    fcn2min,
    FittingMT,
    FittingMT_auto,
    Fittingresultsprocess,
    creatdatabase
)

##############constant##############
eps0 = 8.854e-12  # F/m Vacuum permittivity
##############constant##############


# =============================================================================
# 辅助函数：生成合成测试数据
# =============================================================================

def generate_synthetic_data(true_params, freq, modelterm, option, noise_level=0.01, seed=42):
    """
    生成合成测试数据
    
    参数:
        true_params: 真实参数字典
        freq: 频率数组
        modelterm: 模型项列表
        option: 选项字典
        noise_level: 噪声水平
        seed: 随机种子
        
    返回:
        prodata: DataFrame格式的测试数据
    """
    omega = 2 * pi * freq
    
    # 创建参数对象
    pm_true = Parameters()
    for name, value in true_params.items():
        pm_true.add(name, value=value)
    
    # 计算理论介电谱
    eps_true = fittingmodel(pm_true, omega, modelterm, option)
    sigma_true = 1j * omega * eps_true * eps0
    
    # 添加噪声
    np.random.seed(seed)
    noise = noise_level * (np.random.randn(len(freq)) + 1j * np.random.randn(len(freq)))
    eps_measured = eps_true + noise * np.abs(eps_true)
    sigma_measured = 1j * omega * eps_measured * eps0
    
    # 构造DataFrame
    prodata = DataFrame({
        'FREQ[Hz]': freq,
        'epsRE[-]': Series(real(eps_measured)),
        'epsIM[-]': Series(-imag(eps_measured)),
        'sigmaRE[S/m]': Series(real(sigma_measured)),
        'sigmaIM[S/m]': Series(imag(sigma_measured))
    })
    
    return prodata, eps_true


def print_fit_results(result, true_params, title="拟合结果"):
    """打印拟合结果和误差"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(f"拟合成功: {result.success}")
    print(f"chi²: {result.chisqr:.4e}")
    print(f"迭代次数: {result.nfev}")
    
    print(f"\n{'参数':<12} {'拟合值':<14} {'真值':<14} {'相对误差':<10}")
    print("-" * 55)
    
    max_error = 0
    for i, name in enumerate(result.var_names):
        fit_val = result.x[i]
        true_val = true_params.get(name, None)
        
        if true_val is not None and true_val != 0:
            rel_error = abs((fit_val - true_val) / true_val) * 100
            max_error = max(max_error, rel_error)
            status = "✓" if rel_error < 5 else ("△" if rel_error < 20 else "✗")
            print(f"{name:<12} {fit_val:<14.6e} {true_val:<14.6e} {rel_error:>8.2f}% {status}")
        else:
            print(f"{name:<12} {fit_val:<14.6e} {'N/A':<14} {'N/A':<10}")
    
    print(f"\n最大相对误差: {max_error:.2f}%")
    return max_error


# =============================================================================
# 测试1: 基础功能测试
# =============================================================================

def test_basic_functions():
    """测试基础功能：fittingmodel, fcn2min, creatdatabase"""
    print("\n" + "="*70)
    print("测试1: 基础功能测试")
    print("="*70)
    
    freq = np.logspace(3, 7, 50)
    omega = 2 * pi * freq
    
    # 参数设置
    pm = Parameters()
    pm.add('epsh', value=10.0)
    pm.add('sigmaDC', value=1e-4)
    pm.add('Deps1', value=50.0)
    pm.add('Tao1', value=1e-5)
    
    modelterm = [{'modeltype': 'Debye', 'name': '1'}]
    option = {'EP': 0, 'DC Conductivity': 1}
    
    # 测试 fittingmodel
    print("\n[测试] fittingmodel...")
    eps = fittingmodel(pm, omega, modelterm, option)
    assert isinstance(eps, np.ndarray), "返回值应为numpy数组"
    assert eps.dtype == np.complex128, "返回值应为复数类型"
    assert len(eps) == len(freq), "长度应与频率数组一致"
    print(f"  ✓ 返回值类型正确: {eps.dtype}")
    print(f"  ✓ 返回值长度: {len(eps)}")
    print(f"  ✓ ε'范围: [{real(eps).min():.2f}, {real(eps).max():.2f}]")
    
    # 测试 fcn2min
    print("\n[测试] fcn2min...")
    epsTest = eps.copy()
    resid = fcn2min(pm, omega, modelterm, epsTest, option)
    assert isinstance(resid, np.ndarray), "残差应为numpy数组"
    assert not np.any(np.isnan(resid)), "残差不应包含NaN"
    assert not np.any(np.isinf(resid)), "残差不应包含Inf"
    print(f"  ✓ 残差计算成功")
    print(f"  ✓ 残差范围: [{resid.min():.4e}, {resid.max():.4e}]")
    
    # 测试 creatdatabase
    print("\n[测试] creatdatabase...")
    result_df = creatdatabase(freq, eps)
    expected_cols = ['FREQ[Hz]', 'epsRE[-]', 'epsIM[-]', 'sigmaRE[S/m]', 'sigmaIM[S/m]']
    assert isinstance(result_df, DataFrame), "返回值应为DataFrame"
    assert list(result_df.columns) == expected_cols, "列名不匹配"
    print(f"  ✓ DataFrame格式正确")
    print(f"  ✓ 列名: {list(result_df.columns)}")
    
    print("\n[测试1] ✓ 所有基础功能测试通过")


# =============================================================================
# 测试2: 标准拟合测试 (双弛豫Debye模型)
# =============================================================================

def test_standard_fitting():
    """测试标准拟合：FittingMT (双弛豫Debye)"""
    print("\n" + "="*70)
    print("测试2: 标准拟合测试 (双弛豫Debye)")
    print("="*70)
    
    freq = np.logspace(3, 7, 100)
    
    # 真实参数
    true_params = {
        'epsh': 10.0,
        'sigmaDC': 1e-4,
        'Deps1': 50.0,
        'Tao1': 1e-5,
        'Deps2': 30.0,
        'Tao2': 1e-7
    }
    
    modelterm = [
        {'modeltype': 'Debye', 'name': '1'},
        {'modeltype': 'Debye', 'name': '2'}
    ]
    option = {'EP': 0, 'DC Conductivity': 1}
    
    # 生成测试数据
    prodata, eps_true = generate_synthetic_data(true_params, freq, modelterm, option)
    
    # 初始参数（偏离真值20%）
    pm = Parameters()
    for name, value in true_params.items():
        pm.add(name, value=value * 1.2, min=0)
    
    # 执行拟合
    result = FittingMT(pm, freq, modelterm, prodata, option)
    
    # 打印结果
    max_error = print_fit_results(result, true_params, "双弛豫Debye拟合")
    
    # 验证
    assert result.success, "拟合应成功"
    assert max_error < 20, f"最大误差{max_error:.2f}%应小于20%"
    
    print("\n[测试2] ✓ 标准拟合测试通过")
    
    return result, freq, prodata, eps_true, modelterm, option


# =============================================================================
# 测试3: FittingMT_auto 自动策略测试
# =============================================================================

def test_auto_fitting():
    """测试FittingMT_auto：自动策略选择"""
    print("\n" + "="*70)
    print("测试3: FittingMT_auto 自动策略测试")
    print("="*70)
    
    freq = np.logspace(3, 7, 100)
    
    # 场景1: 标准双弛豫
    print("\n--- 场景1: 标准双弛豫 ---")
    true_params1 = {
        'epsh': 10.0,
        'sigmaDC': 1e-4,
        'Deps1': 50.0,
        'Tao1': 1e-5,
        'Deps2': 30.0,
        'Tao2': 1e-7
    }
    
    modelterm1 = [
        {'modeltype': 'Debye', 'name': '1'},
        {'modeltype': 'Debye', 'name': '2'}
    ]
    option = {'EP': 0, 'DC Conductivity': 1}
    
    prodata1, _ = generate_synthetic_data(true_params1, freq, modelterm1, option)
    
    pm1 = Parameters()
    for name, value in true_params1.items():
        pm1.add(name, value=value * 1.2, min=0)
    
    result1 = FittingMT_auto(pm1, freq, modelterm1, prodata1, option, verbose=True)
    max_error1 = print_fit_results(result1, true_params1, "场景1: 标准双弛豫")
    
    assert result1.success, "场景1拟合应成功"
    assert max_error1 < 20, f"场景1最大误差{max_error1:.2f}%应小于20%"
    
    # 场景2: 数量级差异大
    print("\n--- 场景2: 数量级差异大 (Tao差异5个数量级) ---")
    true_params2 = {
        'epsh': 10.0,
        'sigmaDC': 1e-6,
        'Deps1': 80.0,
        'Tao1': 1e-3,
        'Deps2': 5.0,
        'Tao2': 1e-8
    }
    
    prodata2, _ = generate_synthetic_data(true_params2, freq, modelterm1, option)
    
    pm2 = Parameters()
    for name, value in true_params2.items():
        pm2.add(name, value=value * 1.2, min=0)
    
    result2 = FittingMT_auto(pm2, freq, modelterm1, prodata2, option, verbose=True)
    max_error2 = print_fit_results(result2, true_params2, "场景2: 数量级差异大")
    
    assert result2.success, "场景2拟合应成功"
    
    # 场景3: 三弛豫模型
    print("\n--- 场景3: 三弛豫模型 ---")
    true_params3 = {
        'epsh': 10.0,
        'sigmaDC': 1e-4,
        'Deps1': 50.0,
        'Tao1': 1e-5,
        'Deps2': 30.0,
        'Tao2': 1e-7,
        'Deps3': 20.0,
        'Tao3': 1e-9
    }
    
    modelterm3 = [
        {'modeltype': 'Debye', 'name': '1'},
        {'modeltype': 'Debye', 'name': '2'},
        {'modeltype': 'Debye', 'name': '3'}
    ]
    
    prodata3, _ = generate_synthetic_data(true_params3, freq, modelterm3, option)
    
    pm3 = Parameters()
    for name, value in true_params3.items():
        pm3.add(name, value=value * 1.2, min=0)
    
    result3 = FittingMT_auto(pm3, freq, modelterm3, prodata3, option, verbose=True)
    max_error3 = print_fit_results(result3, true_params3, "场景3: 三弛豫模型")
    
    assert result3.success, "场景3拟合应成功"
    
    print("\n[测试3] ✓ FittingMT_auto 自动策略测试通过")


# =============================================================================
# 测试4: 不同模型类型测试
# =============================================================================

def test_model_types():
    """测试不同模型类型：Debye, Cole-Cole, Davidson-Cole, Havriliak-Negami"""
    print("\n" + "="*70)
    print("测试4: 不同模型类型测试")
    print("="*70)
    
    freq = np.logspace(3, 7, 50)
    option = {'EP': 0, 'DC Conductivity': 1}
    
    model_configs = [
        ('Debye', {'epsh': 10.0, 'sigmaDC': 1e-4, 'Deps1': 50.0, 'Tao1': 1e-5}),
        ('Cole-Cole', {'epsh': 10.0, 'sigmaDC': 1e-4, 'Deps1': 50.0, 'Tao1': 1e-5, 'Alpha1': 0.7}),
        ('Davidson-Cole', {'epsh': 10.0, 'sigmaDC': 1e-4, 'Deps1': 50.0, 'Tao1': 1e-5, 'Beta1': 0.8}),
        ('Havriliak-Negami', {'epsh': 10.0, 'sigmaDC': 1e-4, 'Deps1': 50.0, 'Tao1': 1e-5, 'Alpha1': 0.7, 'Beta1': 0.8})
    ]
    
    for model_type, true_params in model_configs:
        print(f"\n--- 测试 {model_type} 模型 ---")
        
        modelterm = [{'modeltype': model_type, 'name': '1'}]
        
        # 生成数据
        prodata, _ = generate_synthetic_data(true_params, freq, modelterm, option)
        
        # 初始参数
        pm = Parameters()
        for name, value in true_params.items():
            pm.add(name, value=value * 1.2, min=0)
            if name.startswith('Alpha') or name.startswith('Beta'):
                pm[name].max = 1
        
        # 拟合
        result = FittingMT(pm, freq, modelterm, prodata, option)
        
        print(f"  拟合成功: {result.success}, chi²: {result.chisqr:.4e}")
        
        # 检查主要参数误差
        for name in ['epsh', 'sigmaDC', 'Deps1', 'Tao1']:
            if name in result.var_names:
                fit_val = result.params[name].value
                true_val = true_params[name]
                rel_error = abs((fit_val - true_val) / true_val) * 100
                status = "✓" if rel_error < 10 else "△"
                print(f"    {name}: 误差 {rel_error:.2f}% {status}")
        
        assert result.success, f"{model_type}模型拟合应成功"
    
    print("\n[测试4] ✓ 不同模型类型测试通过")


# =============================================================================
# 测试5: 结果可视化
# =============================================================================

def test_visualization():
    """生成拟合结果可视化"""
    print("\n" + "="*70)
    print("测试5: 结果可视化")
    print("="*70)
    
    # 使用测试2的结果
    result, freq, prodata, eps_true, modelterm, option = test_standard_fitting()
    
    # 获取拟合后的参数
    pm_fitted = Parameters()
    for i, name in enumerate(result.var_names):
        pm_fitted.add(name, value=result.x[i])
    
    # 计算拟合曲线
    omega = 2 * pi * freq
    eps_fitted = fittingmodel(pm_fitted, omega, modelterm, option)
    
    # 从prodata提取测试数据
    epsDataRE = prodata['epsRE[-]'].values
    epsDataIM = prodata['epsIM[-]'].values
    sigmaDataRE = prodata['sigmaRE[S/m]'].values
    
    epsData = epsDataRE - 1j * epsDataIM
    
    # 创建图形
    fig = plt.figure(figsize=(16, 10))
    
    # 子图1: ε' vs log(f)
    ax1 = plt.subplot(231)
    ax1.plot(log10(freq), real(epsData), 'ko', markersize=5, alpha=0.6, label='Measured')
    ax1.plot(log10(freq), real(eps_fitted), 'r-', linewidth=2, label='Fitted')
    ax1.set_xlabel("log₁₀(f) [Hz]", fontsize=11)
    ax1.set_ylabel("ε'", fontsize=11)
    ax1.set_title("Real Permittivity", fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 子图2: ε'' vs log(f)
    ax2 = plt.subplot(232)
    ax2.plot(log10(freq), -imag(epsData), 'ko', markersize=5, alpha=0.6, label='Measured')
    ax2.plot(log10(freq), -imag(eps_fitted), 'r-', linewidth=2, label='Fitted')
    ax2.set_xlabel("log₁₀(f) [Hz]", fontsize=11)
    ax2.set_ylabel("ε''", fontsize=11)
    ax2.set_title("Imaginary Permittivity", fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 子图3: σ' vs log(f)
    ax3 = plt.subplot(233)
    ax3.plot(log10(freq), sigmaDataRE, 'ko', markersize=5, alpha=0.6, label='Measured')
    sigma_fitted = real(1j * omega * eps_fitted * eps0)
    ax3.plot(log10(freq), sigma_fitted, 'r-', linewidth=2, label='Fitted')
    ax3.set_xlabel("log₁₀(f) [Hz]", fontsize=11)
    ax3.set_ylabel("σ' [S/m]", fontsize=11)
    ax3.set_title("Real Conductivity", fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 子图4: Cole-Cole图 (ε'' vs ε')
    ax4 = plt.subplot(234)
    ax4.plot(real(epsData), -imag(epsData), 'ko', markersize=5, alpha=0.6, label='Measured')
    ax4.plot(real(eps_fitted), -imag(eps_fitted), 'r-', linewidth=2, label='Fitted')
    ax4.set_xlabel("ε'", fontsize=11)
    ax4.set_ylabel("ε''", fontsize=11)
    ax4.set_title("Cole-Cole Plot", fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.axis('equal')
    
    # 子图5: 残差
    ax5 = plt.subplot(235)
    ax5.plot(log10(freq), result.residual, 'r-', linewidth=1.5)
    ax5.axhline(y=0, color='k', linestyle='--', linewidth=1)
    ax5.set_xlabel("log₁₀(f) [Hz]", fontsize=11)
    ax5.set_ylabel("Residual", fontsize=11)
    ax5.set_title("Fitting Residuals", fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # 子图6: 参数对比
    ax6 = plt.subplot(236)
    ax6.axis('off')
    
    # 构建参数对比文本
    text_lines = ["Fitted Parameters:\n"]
    text_lines.append(f"{'Parameter':<12} {'Fitted':<14} {'True':<14} {'Error%'}")
    text_lines.append("-" * 50)
    
    true_params = {
        'epsh': 10.0, 'sigmaDC': 1e-4,
        'Deps1': 50.0, 'Tao1': 1e-5,
        'Deps2': 30.0, 'Tao2': 1e-7
    }
    
    for name in result.var_names:
        fit_val = result.params[name].value
        true_val = true_params.get(name, 0)
        if true_val != 0:
            err = abs((fit_val - true_val) / true_val) * 100
            text_lines.append(f"{name:<12} {fit_val:<14.4e} {true_val:<14.4e} {err:>6.2f}%")
    
    text_lines.append("")
    text_lines.append(f"Chi²: {result.chisqr:.4e}")
    text_lines.append(f"Iterations: {result.nfev}")
    text_lines.append(f"Success: {result.success}")
    
    ax6.text(0.1, 0.5, '\n'.join(text_lines), 
             fontfamily='monospace', fontsize=9,
             verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig('FittingMT_test_results.png', dpi=150, bbox_inches='tight')
    print("  ✓ 图片已保存: FittingMT_test_results.png")
    
    plt.show()
    
    print("\n[测试5] ✓ 可视化测试完成")


# =============================================================================
# 主测试程序
# =============================================================================

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("FittingMT.py 综合测试套件")
    print("="*70)
    
    passed = 0
    failed = 0
    
    tests = [
        ("基础功能测试", test_basic_functions),
        ("标准拟合测试", lambda: test_standard_fitting()[0]),  # 仅返回result
        ("FittingMT_auto测试", test_auto_fitting),
        ("模型类型测试", test_model_types),
        ("可视化测试", test_visualization)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n正在运行: {test_name}...")
            test_func()
            passed += 1
            print(f"✓ {test_name} 通过")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 汇总
    print("\n" + "="*70)
    print("测试汇总")
    print("="*70)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ 所有测试通过！")
    else:
        print(f"\n✗ {failed} 个测试失败")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
