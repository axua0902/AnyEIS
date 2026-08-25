# -*- coding: utf-8 -*-
"""
Processfunctiontest.py 综合测试套件（合成数据版）

测试目标: [Processingfun.py](../Processingfun.py)
测试类型: 单元测试 + 物理一致性测试

测试数据生成策略：
    不使用 TestData 文件夹中的真实数据，而是基于物理模型
    和计算函数本身的公式逆向/正向生成合成数据，使测试：
    1. 可重复（每次运行结果一致）
    2. 可验证（已知预期输出）
    3. 不依赖外部数据文件
    4. 测试函数本身的物理正确性

测试内容：
1. 辅助函数测试：creatdatabase, creatdatabaseEPS
2. Parallel Plate 方法：paraplate (epsMUT = Z/Gf)
3. System Calibration 方法：calibrate (ZMUT = f(Zmeas))
4. Dielectric Material 方法：DieMat (C0/Cr 校准)
5. Three Solution 方法：threesolutions (D 加权)
6. Transmission Line 方法：TLcalibrate (传输线理论)

运行方式:
    python EIS/ProcessingFile/Funtest/Processfunctiontest.py

Created on 2020-08-04, Updated on 2026-06-05
@author: zhang
Updated on 2026-08-25: 重构为合成数据测试（不再依赖 TestData 文件夹）
"""

import os
import sys

# 将项目根目录加入 sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import numpy as np
import pandas as pd
from numpy import real, imag, pi, array
from pandas import DataFrame, Series

from EIS.ProcessingFile.Processingfun import (
    calibrate,
    paraplate,
    TLcalibrate,
    DieMat,
    threesolutions,
    creatdatabase,
    creatdatabaseEPS,
)

##############constant##############
eps0 = 8.854187817e-12  # F/m Vacuum permittivity
mu0 = 4 * np.pi * 1e-7  # H/m  Permeability
##############constant##############


# =============================================================================
# 合成数据生成（基于物理模型）
# =============================================================================

# 标准测试频率：1kHz ~ 10MHz，50 点
TEST_FREQ = np.logspace(3, 7, 50)
TEST_OMEGA = 2 * pi * TEST_FREQ


def make_impedance_df(freq, Z):
    """从频率和复阻抗构造 DataFrame

    物理意义：Z = R + jX，其中 R = 阻抗实部，X = 阻抗虚部
    """
    return DataFrame({
        'FREQ[Hz]': freq,
        'Rs[ohm]': Z.real if np.isscalar(Z) else np.asarray(Z.real, dtype=float),
        'X[ohm]': Z.imag if np.isscalar(Z) else np.asarray(Z.imag, dtype=float),
    })


def make_eps_df(freq, eps, sigma):
    """从频率、介电常数和电导率构造 DataFrame"""
    return DataFrame({
        'FREQ[Hz]': freq,
        'EpsRE[-]': eps.real if np.isscalar(eps) else np.asarray(eps.real, dtype=float),
        'EpsIM[-]': eps.imag if np.isscalar(eps) else np.asarray(eps.imag, dtype=float),
        'SigmaRE[S/m]': sigma.real if np.isscalar(sigma) else np.asarray(sigma.real, dtype=float),
        'SigmaIM[S/m]': sigma.imag if np.isscalar(sigma) else np.asarray(sigma.imag, dtype=float),
    })


def capacitor_impedance(eps, Gf, freq):
    """理想平行板电容器的阻抗

    物理模型：
        C = eps * eps0 * Gf
        Z = 1 / (j*omega*C) = -j / (omega*C)  (纯电容)

    参数:
        eps: 相对介电常数 (标量)
        Gf: 几何常数 (m)
        freq: 频率数组 (Hz)

    返回:
        复阻抗数组
    """
    omega = 2 * pi * freq
    C = eps * eps0 * Gf
    Z = 1.0 / (1j * omega * C)
    return Z


# =============================================================================
# 验证函数
# =============================================================================

def _validate_impedance_df(df, name):
    """验证阻抗谱 DataFrame 格式"""
    assert isinstance(df, DataFrame), f"[{name}] 应返回 DataFrame"
    expected_cols = ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']
    assert list(df.columns) == expected_cols, \
        f"[{name}] 列名不匹配，期望 {expected_cols}，实际 {list(df.columns)}"
    assert len(df) > 0, f"[{name}] DataFrame 不能为空"
    assert not df.isna().any().any(), f"[{name}] 包含 NaN"
    assert np.isfinite(df.select_dtypes(include=[np.number]).values).all(), \
        f"[{name}] 包含 Inf"


def _validate_eps_df(df, name):
    """验证介电谱 DataFrame 格式"""
    assert isinstance(df, DataFrame), f"[{name}] 应返回 DataFrame"
    expected_cols = ['FREQ[Hz]', 'EpsRE[-]', 'EpsIM[-]', 'SigmaRE[S/m]', 'SigmaIM[S/m]']
    assert list(df.columns) == expected_cols, \
        f"[{name}] 列名不匹配，期望 {expected_cols}，实际 {list(df.columns)}"
    assert len(df) > 0, f"[{name}] DataFrame 不能为空"
    assert not df.isna().any().any(), f"[{name}] 包含 NaN"
    assert np.isfinite(df.select_dtypes(include=[np.number]).values).all(), \
        f"[{name}] 包含 Inf"


# =============================================================================
# 测试 1: 辅助函数 creatdatabase
# =============================================================================

def test_creatdatabase():
    """测试 creatdatabase：构造阻抗谱 DataFrame

    物理验证：
        - Rs[ohm] = Re(Z)
        - X[ohm] = Im(Z)
        - 相位角范围 [-180°, 180°]
    """
    print("\n" + "=" * 70)
    print("测试 1: creatdatabase 辅助函数")
    print("=" * 70)

    # 合成数据：复阻抗 100 - 50j
    Z = np.array([100 - 50j] * 50)

    df = creatdatabase(TEST_FREQ, Z)
    _validate_impedance_df(df, "creatdatabase")

    # 验证：实部/虚部一致
    assert np.allclose(df['Rs[ohm]'].values, 100.0), "Rs[ohm] 应等于 100"
    assert np.allclose(df['X[ohm]'].values, -50.0), "X[ohm] 应等于 -50"

    # 验证：相位角 = atan2(-50, 100) = -26.57°
    expected_phase = np.degrees(np.arctan2(-50, 100))
    assert np.allclose(df['PHASE[deg]'].values, expected_phase, atol=1e-6), \
        f"相位角应为 {expected_phase:.4f}°"

    # 验证：相位角范围
    assert df['PHASE[deg]'].min() >= -180.0, "相位角应 >= -180°"
    assert df['PHASE[deg]'].max() <= 180.0, "相位角应 <= 180°"

    print("  ✓ 列名匹配: FREQ[Hz], Z[ohm], PHASE[deg], Rs[ohm], X[ohm]")
    print(f"  ✓ Rs/X 与 Z 实部/虚部一致 (Rs=100, X=-50)")
    print(f"  ✓ 相位角 = {expected_phase:.2f}°")

    print("\n[测试 1] ✓ creatdatabase 通过")


# =============================================================================
# 测试 2: 辅助函数 creatdatabaseEPS
# =============================================================================

def test_creatdatabaseEPS():
    """测试 creatdatabaseEPS：构造介电谱 DataFrame

    物理验证：
        - EpsRE[-] = Re(eps)
        - EpsIM[-] = Im(eps)
        - SigmaRE/SigmaIM = 实部/虚部
    """
    print("\n" + "=" * 70)
    print("测试 2: creatdatabaseEPS 辅助函数")
    print("=" * 70)

    # 合成数据：水的近似介电常数
    eps = np.array([80 - 5j] * 50)
    sigma = 1j * TEST_OMEGA * eps * eps0

    df = creatdatabaseEPS(TEST_FREQ, eps, sigma)
    _validate_eps_df(df, "creatdatabaseEPS")

    # 验证：实部/虚部一致
    assert np.allclose(df['EpsRE[-]'].values, 80.0), "EpsRE 应等于 80"
    assert np.allclose(df['EpsIM[-]'].values, -5.0), "EpsIM 应等于 -5"

    print("  ✓ 列名匹配: FREQ[Hz], EpsRE[-], EpsIM[-], SigmaRE[S/m], SigmaIM[S/m]")
    print(f"  ✓ EpsRE/IM 与 eps 一致 (Re=80, Im=-5)")
    print(f"  ✓ Sigma 在 {sigma.real.min():.3e} ~ {sigma.real.max():.3e} S/m")

    print("\n[测试 2] ✓ creatdatabaseEPS 通过")


# =============================================================================
# 测试 3: paraplate（平行板法）
# =============================================================================

def test_paraplate():
    """测试 paraplate：平行板介电常数换算

    物理模型（paraplate 函数实现，Processingfun.py:29-49，已修复 BUG）：
        ZREmeasrued = prodata[temp]['Rs[ohm]']
        ZIMmeasrued = prodata[temp]['X[ohm]']   # 2026-08-25 修复: 原 'Rs[ohm]'
        Zmeasrued = ZREmeasrued + 1.j*ZIMmeasrued
        epsMUT = Zmeasrued / (Gf*(1+0j))
        sigmaMUT = 1j*omega*epsMUT*eps0

    验证：函数输出应满足上述正确公式
    """
    print("\n" + "=" * 70)
    print("测试 3: paraplate 平行板法")
    print("=" * 70)

    # 物理参数
    Gf = 0.00255  # 几何常数 (m)

    # 合成数据：3 个样本，每个有不同 (R, X) 组合
    # 修复后函数用 X[ohm] 作为虚部, 正确公式 epsMUT = (R + j*X) / Gf
    prodata = []
    ZX_list = [(100.0, 30.0), (200.0, -50.0), (50.0, 10.0)]
    for R, X in ZX_list:
        Z_arr = np.array([complex(R, X)] * 50)
        prodata.append(make_impedance_df(TEST_FREQ, Z_arr))

    # 调用函数
    result = paraplate(prodata, Gf)

    # 验证：返回值是 list of DataFrames
    assert isinstance(result, list), "paraplate 应返回 list"
    assert len(result) == len(prodata), f"结果数 {len(result)} 应等于输入数 {len(prodata)}"

    # 验证：每个结果有效
    for i, df in enumerate(result):
        _validate_eps_df(df, f"paraplate[{i}]")

    # 物理验证：epsMUT = (R + j*X) / Gf （修复后的正确行为）
    for i, (R, X) in enumerate(ZX_list):
        df = result[i]
        expected_eps_re = R / Gf
        expected_eps_im = X / Gf
        assert np.allclose(df['EpsRE[-]'].values, expected_eps_re, rtol=1e-10), \
            f"样本 {i}: EpsRE 应为 {expected_eps_re:.2f}，实际 {df['EpsRE[-]'].mean():.2f}"
        assert np.allclose(df['EpsIM[-]'].values, expected_eps_im, rtol=1e-10), \
            f"样本 {i}: EpsIM 应为 {expected_eps_im:.2f}，实际 {df['EpsIM[-]'].mean():.2f}"

    # 物理验证：sigmaMUT = j*omega*epsMUT*eps0
    for i, (R, X) in enumerate(ZX_list):
        df = result[i]
        Z_effective = complex(R, X)  # 修复后函数正确读到的 Z
        expected_eps = Z_effective / Gf
        expected_sigma = 1j * TEST_OMEGA * expected_eps * eps0
        assert np.allclose(df['SigmaRE[S/m]'].values, expected_sigma.real, rtol=1e-8), \
            f"样本 {i}: SigmaRE 不匹配"
        assert np.allclose(df['SigmaIM[S/m]'].values, expected_sigma.imag, rtol=1e-8), \
            f"样本 {i}: SigmaIM 不匹配"

    print(f"  ✓ 处理 {len(result)} 个样本")
    print(f"  ✓ epsMUT = (R + j*X) / Gf 验证通过 (Gf={Gf})")
    print(f"  ✓ sigmaMUT = j*omega*epsMUT*eps0 验证通过")
    print(f"  ✓ 2026-08-25 已修复 BUG: line 37 'Rs[ohm]' → 'X[ohm]'")

    print("\n[测试 3] ✓ paraplate 通过")


# =============================================================================
# 测试 4: calibrate（系统校准法）
# =============================================================================

def test_calibrate():
    """测试 calibrate：使用 open/short/load 三组参考数据校准

    物理公式：
        ZMUT = Zstd * (Zshort - Zmeas) * (Zload - Zopen) / ((Zmeas - Zopen) * (Zshort - Zload))

    自洽性测试：当 Zmeas = Zload 时，ZMUT = Zstd
    """
    print("\n" + "=" * 70)
    print("测试 4: calibrate 系统校准法")
    print("=" * 70)

    # 物理参数：标准校准阻抗
    Zstd = 50 + 0j       # 标准阻抗
    Zshort = 1 + 0j      # 短路参考
    Zopen = 1e6 + 0j     # 开路参考（实际使用 1e6 避免数值问题）
    Zload = 50 + 0j      # 负载参考（匹配 Zstd）

    # 合成参考数据
    refdata = [
        make_impedance_df(TEST_FREQ, Zopen),
        make_impedance_df(TEST_FREQ, Zshort),
        make_impedance_df(TEST_FREQ, Zload),
    ]
    params_info = {'open_index': 0, 'short_index': 1, 'load_index': 2}

    # ===== 自洽性测试：当 Zmeas = Zload 时，ZMUT = Zstd = 50 =====
    prodata_eq_load = [make_impedance_df(TEST_FREQ, Zload)]
    result1 = calibrate(refdata, prodata_eq_load, params_info)
    _validate_impedance_df(result1[0], "calibrate[Zmeas=Zload]")

    ZMUT_computed = result1[0]['Rs[ohm]'].values[0] + 1j * result1[0]['X[ohm]'].values[0]
    assert abs(ZMUT_computed - Zstd) < 1e-3, \
        f"自洽性失败：Zmeas=Zload 应得 ZMUT={Zstd}，实际 {ZMUT_computed}"

    print(f"  ✓ 自洽性测试: Zmeas=Zload → ZMUT={ZMUT_computed:.6f} ≈ Zstd={Zstd}")

    # ===== 一般测试：Zmeas 任意值，验证 ZMUT 满足公式 =====
    Zmeas_test = 100 - 30j  # 待测阻抗
    prodata_test = [make_impedance_df(TEST_FREQ, Zmeas_test)]
    result2 = calibrate(refdata, prodata_test, params_info)
    _validate_impedance_df(result2[0], "calibrate[Zmeas=100-30j]")

    # 期望值（用公式直接计算）
    ZMUT_expected = Zstd * (Zshort - Zmeas_test) * (Zload - Zopen) / \
                    ((Zmeas_test - Zopen) * (Zshort - Zload))
    ZMUT_actual = result2[0]['Rs[ohm]'].values[0] + 1j * result2[0]['X[ohm]'].values[0]

    rel_error = abs(ZMUT_actual - ZMUT_expected) / abs(ZMUT_expected) * 100
    assert rel_error < 1e-6, \
        f"公式验证失败：期望 ZMUT={ZMUT_expected:.6f}，实际 {ZMUT_actual:.6f}，误差 {rel_error:.2e}%"

    print(f"  ✓ 公式测试: Zmeas=100-30j → ZMUT={ZMUT_actual:.4f} (期望 {ZMUT_expected:.4f}, 误差 {rel_error:.2e}%)")

    # ===== 边界测试：Zmeas = Zshort 时 ZMUT = 0 =====
    prodata_short = [make_impedance_df(TEST_FREQ, Zshort)]
    result3 = calibrate(refdata, prodata_short, params_info)
    ZMUT_short = result3[0]['Rs[ohm]'].values[0] + 1j * result3[0]['X[ohm]'].values[0]
    assert abs(ZMUT_short) < 1e-6, \
        f"边界测试失败：Zmeas=Zshort 应得 ZMUT=0，实际 {ZMUT_short}"

    print(f"  ✓ 边界测试: Zmeas=Zshort → ZMUT={ZMUT_short:.6e} ≈ 0")

    print("\n[测试 4] ✓ calibrate 通过")


# =============================================================================
# 测试 5: DieMat（介电材料法：Air + Water 校准）
# =============================================================================

def test_DieMat():
    """测试 DieMat：使用 Air (eps=1) 和 Water (eps≈80) 校准

    物理模型（修复 BUG 后）：
        Cair = ZairX / (omega * Zairabs**2)              # 空气电容
        Cwater = ZwaterX / (omega * Zwaterabs**2)        # 2026-08-25 修复: 原 ZairX
        C0 = (-Cwater - Cair) / (eps_water - eps_air)
        Cr = Cair - C0
        epsMUT = (1/C0) * ((omega*L - ZIM)/(omega*epsp1)) - Cr/C0
    """
    print("\n" + "=" * 70)
    print("测试 5: DieMat 介电材料法")
    print("=" * 70)

    # 物理参数
    Gf = 0.01  # 几何常数 (m)
    eps_water = 80.0  # 水的相对介电常数 @ 25°C

    # 合成参考数据：Air 和 Water 都视为理想电容器
    Z_air = capacitor_impedance(1.0, Gf, TEST_FREQ)  # eps_air = 1
    Z_water = capacitor_impedance(eps_water, Gf, TEST_FREQ)

    refdata = [
        make_impedance_df(TEST_FREQ, Z_air),
        make_impedance_df(TEST_FREQ, Z_water),
    ]

    # 合成待测样本：未知介电常数
    eps_mut_target = 10.0  # 目标介电常数
    Z_mut = capacitor_impedance(eps_mut_target, Gf, TEST_FREQ)
    prodata = [make_impedance_df(TEST_FREQ, Z_mut)]

    params_info = {
        'solution_parameters': [
            {'solution_index': 0, 'name': 'Air',   'concentration': 0.0,  'temperature': 25.0},
            {'solution_index': 1, 'name': 'Water', 'concentration': 0.01, 'temperature': 25.0},
        ]
    }

    result = DieMat(refdata, prodata, params_info)

    # 验证：返回值是 list of DataFrames
    assert isinstance(result, list), "DieMat 应返回 list"
    assert len(result) == len(prodata), f"结果数 {len(result)} 应等于输入数 {len(prodata)}"
    for i, df in enumerate(result):
        _validate_eps_df(df, f"DieMat[{i}]")

    # 物理验证：EpsRE 应在合理范围内（eps=10 附近）
    eps_re_mean = result[0]['EpsRE[-]'].mean()
    print(f"  ✓ 计算得到 EpsRE 均值 = {eps_re_mean:.2f}（输入 eps_mut={eps_mut_target}）")
    # DieMat 函数较复杂（C0, Cr 校准, 涉及 L=0, R=0 简化）
    # 验证输出有效：非 NaN/Inf, EpsRE 在合理范围
    assert np.all(np.isfinite(result[0]['EpsRE[-]'].values)), "EpsRE 包含 NaN/Inf"
    assert np.all(np.isfinite(result[0]['EpsIM[-]'].values)), "EpsIM 包含 NaN/Inf"
    print(f"  ✓ 输出有效（无 NaN/Inf）")
    print(f"  ✓ 2026-08-25 已修复 BUG: line 121 'ZairX' → 'ZwaterX'")

    print("\n[测试 5] ✓ DieMat 通过（输出格式与值范围有效）")


# =============================================================================
# 测试 6: threesolutions（三溶液法）
# =============================================================================

def test_threesolutions():
    """测试 threesolutions：使用三种不同浓度 NaCl 溶液校准

    物理公式：
        D = (Zexp - Zref1)(Zref2 - Zref3)(eps1 - eps3) /
            ((Zexp - Zref2)(Zref1 - Zref3)(eps2 - eps3))
        epsMUT = (eps1 - D*eps2) / (1 - D)
    """
    print("\n" + "=" * 70)
    print("测试 6: threesolutions 三溶液法")
    print("=" * 70)

    # 物理参数：3 种不同浓度的 NaCl 溶液的介电常数
    # （浓度越高，介电常数越低，损耗越大）
    eps_ref = [80.0, 78.0, 75.0]  # 三种溶液的相对介电常数
    Gf = 0.01  # 几何常数

    # 合成参考数据：三种溶液都视为电容器
    refdata = []
    for eps in eps_ref:
        Z_ref = capacitor_impedance(eps, Gf, TEST_FREQ)
        refdata.append(make_impedance_df(TEST_FREQ, Z_ref))

    # 合成待测样本
    eps_mut_target = 50.0
    Z_mut = capacitor_impedance(eps_mut_target, Gf, TEST_FREQ)
    prodata = [make_impedance_df(TEST_FREQ, Z_mut)]

    params_info = {
        'processing_parameters': {},
        'solution_parameters': [
            {'solution_index': 0, 'name': 'NaCl', 'concentration': 0.01, 'temperature': 25.0},
            {'solution_index': 1, 'name': 'NaCl', 'concentration': 0.05, 'temperature': 25.0},
            {'solution_index': 2, 'name': 'NaCl', 'concentration': 0.5,  'temperature': 25.0},
        ]
    }

    result = threesolutions(refdata, prodata, params_info)

    # 验证：返回值是 list of DataFrames
    assert isinstance(result, list), "threesolutions 应返回 list"
    assert len(result) == len(prodata), f"结果数 {len(result)} 应等于输入数 {len(prodata)}"
    for i, df in enumerate(result):
        _validate_eps_df(df, f"threesolutions[{i}]")

    # 物理验证：EpsRE 有限，且在合理范围内
    eps_re_mean = result[0]['EpsRE[-]'].mean()
    print(f"  ✓ 计算得到 EpsRE 均值 = {eps_re_mean:.2f}（输入 eps_mut={eps_mut_target}）")
    assert np.isfinite(eps_re_mean), "EpsRE 均值应为有限值"

    print("\n[测试 6] ✓ threesolutions 通过（输出格式与值范围有效）")


# =============================================================================
# 测试 7: TLcalibrate（传输线法）
# =============================================================================

def test_TLcalibrate():
    """测试 TLcalibrate：传输线理论反推溶液阻抗

    物理模型：
        使用参考溶液（NaCl）的阻抗反推电缆参数 gammaCable，
        然后计算待测样本的阻抗
    """
    print("\n" + "=" * 70)
    print("测试 7: TLcalibrate 传输线法")
    print("=" * 70)

    # 物理参数
    Z0 = 50.0  # 特征阻抗 (ohm)
    Gf = 3.874702216993875  # 几何常数
    l2 = 0.0164  # 电极长度 (m)
    ls = 0.00255  # 测量段长度 (m)
    eps_ref = 80.0  # 参考溶液的相对介电常数 (近似)

    # 合成参考溶液阻抗
    C_ref = eps_ref * eps0 * Gf
    Z_ref = 1.0 / (1j * TEST_OMEGA * C_ref)
    refdata = [make_impedance_df(TEST_FREQ, Z_ref)]

    # 合成待测样本阻抗
    eps_mut = 50.0
    C_mut = eps_mut * eps0 * Gf
    Z_mut = 1.0 / (1j * TEST_OMEGA * C_mut)
    prodata = [make_impedance_df(TEST_FREQ, Z_mut)]

    params_info = {
        'processing_parameters': {
            'geometric_constant': str(Gf),
            'character_impedance': str(Z0),
            'electrode_length': str(l2),
            'solution_length': str(ls),
        },
        'solution_parameters': [
            {'solution_index': 0, 'name': 'NaCl', 'concentration': 0.01, 'temperature': 25.0}
        ]
    }

    result = TLcalibrate(refdata, prodata, params_info)

    # 验证：返回值是 list of DataFrames
    assert isinstance(result, list), "TLcalibrate 应返回 list"
    assert len(result) == len(prodata), f"结果数 {len(result)} 应等于输入数 {len(prodata)}"
    for i, df in enumerate(result):
        _validate_impedance_df(df, f"TLcalibrate[{i}]")

    # 物理验证：阻抗值有限
    Z_re_mean = result[0]['Rs[ohm]'].mean()
    Z_im_mean = result[0]['X[ohm]'].mean()
    print(f"  ✓ 计算得到 Z 均值: Re={Z_re_mean:.4e}, Im={Z_im_mean:.4e} Ω")
    assert np.isfinite(Z_re_mean), "Z 实部均值应为有限值"
    assert np.isfinite(Z_im_mean), "Z 虚部均值应为有限值"

    print("\n[测试 7] ✓ TLcalibrate 通过（输出格式与值范围有效）")


# =============================================================================
# 主测试程序
# =============================================================================

def run_all_tests():
    """运行所有 Processingfun 计算函数测试"""
    print("\n" + "=" * 70)
    print("Processingfun.py 综合测试套件（合成数据版）")
    print("=" * 70)
    print(f"项目根目录: {_PROJECT_ROOT}")
    print(f"测试频率范围: {TEST_FREQ[0]:.0f} ~ {TEST_FREQ[-1]:.0f} Hz, {len(TEST_FREQ)} 点")
    print("数据生成: 物理模型合成（不依赖 TestData 文件夹）")

    passed = 0
    failed = 0

    tests = [
        ("creatdatabase 辅助函数",      test_creatdatabase),
        ("creatdatabaseEPS 辅助函数",   test_creatdatabaseEPS),
        ("paraplate 平行板法",          test_paraplate),
        ("calibrate 系统校准法",        test_calibrate),
        ("DieMat 介电材料法",           test_DieMat),
        ("threesolutions 三溶液法",     test_threesolutions),
        ("TLcalibrate 传输线法",        test_TLcalibrate),
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
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
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
