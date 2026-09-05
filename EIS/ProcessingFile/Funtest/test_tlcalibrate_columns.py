# -*- coding: utf-8 -*-
"""
test_tlcalibrate_columns.py
回归测试: TLcalibrate 列名变体支持 + 缺列友好诊断 (F4 + M9 + M10)

历史背景 (FILTER_COMPARE_UI_CHANGELOG.md 14.9):
  早期实现中 TLcalibrate 硬编码 'FREQ[Hz]' / 'Rs[ohm]' / 'X[ohm]' 列名,
  当用户 prodata 列名是变体 (如 'Rs' / 'R' / 'RS[OHM]') 时 KeyError 崩溃。
  check5() 支持多种列名变体识别 EIS 数据,TLcalibrate 却不复用,
  导致 check5 通过但 TLcalibrate 内部失败。

  修复 (Processingfun.py:748-822):
  - 引入 Datacheck.resolve_column 替换硬编码
  - 缺列时打印诊断并优雅退出/跳过,不抛 KeyError
  - 支持 'Rs' / 'R' / 'RS[OHM]' / 'Rs[Ω]' 等 4 种 Rs 变体
  - 支持 'X' / 'X[OHM]' / 'X[Ω]' 等 3 种 X 变体
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest


# ----------------------------------------------------------------------
# Fixtures: 各种列名变体的样本数据
# ----------------------------------------------------------------------

@pytest.fixture
def ref_eis_standard():
    """refdata 标准列名: 'FREQ[Hz]', 'Rs[ohm]', 'X[ohm]'"""
    return pd.DataFrame({
        'FREQ[Hz]':  [1e3, 1e4, 1e5, 1e6],
        'Rs[ohm]':   [50.0, 50.5, 51.0, 51.5],
        'X[ohm]':    [-2.0, -1.5, -1.0, -0.5],
    })


@pytest.fixture
def ref_eis_variant():
    """refdata 变体列名: 'FREQ[Hz]' + 'R' + 'X' (无单位)"""
    return pd.DataFrame({
        'FREQ[Hz]':  [1e3, 1e4, 1e5, 1e6],
        'R':         [50.0, 50.5, 51.0, 51.5],
        'X':         [-2.0, -1.5, -1.0, -0.5],
    })


@pytest.fixture
def pro_eis_standard():
    """prodata 标准列名"""
    return pd.DataFrame({
        'FREQ[Hz]':  [1e3, 1e4, 1e5, 1e6],
        'Rs[ohm]':   [60.0, 60.5, 61.0, 61.5],
        'X[ohm]':    [-3.0, -2.5, -2.0, -1.5],
    })


@pytest.fixture
def pro_eis_short_columns():
    """prodata 缺列: 只有 'FREQ[Hz]' + 'Rs[ohm]',没有 'X[ohm]'"""
    return pd.DataFrame({
        'FREQ[Hz]':  [1e3, 1e4, 1e5, 1e6],
        'Rs[ohm]':   [60.0, 60.5, 61.0, 61.5],
    })


@pytest.fixture
def pro_eis_total_wrong():
    """prodata 列名完全不匹配 (DS 数据混进来)"""
    return pd.DataFrame({
        'FREQ[Hz]':    [1e3, 1e4, 1e5, 1e6],
        'EpsRE[-]':    [80.0, 78.0, 75.0, 70.0],
        'EpsIM[-]':    [10.0, 8.0, 6.0, 4.0],
        'Sigma[S/m]':  [1e-3, 8e-4, 6e-4, 4e-4],
    })


@pytest.fixture
def params_nacl():
    """标准 NaCl 参数"""
    return {
        'processing_parameters': {
            'geometric_constant': '3.874',
            'character_impedance': '50',
            'electrode_length': '0.0164',
            'solution_length': '0.002',
        },
        'solution_parameters': [{
            'solution_index': 0,
            'name': 'NaCl',
            'concentration': 0.1,
            'temperature': 25.0,
        }],
    }


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestTLcalibrateColumnVariants:
    """验证 TLcalibrate 支持列名变体 (F4 + M9)"""

    def test_standard_columns_runs(
        self, ref_eis_standard, pro_eis_standard, params_nacl
    ):
        """基线: 标准列名 'Rs[ohm]'/ 'X[ohm]' 能跑通"""
        from EIS.ProcessingFile.Processingfun import TLcalibrate
        results = TLcalibrate([ref_eis_standard], [pro_eis_standard], params_nacl)
        assert results is not None
        # 1 条 prodata → 1 条结果
        assert len(results) == 1, f'期望 1 条结果,实际 {len(results)}'

    def test_refdata_variant_columns_runs(
        self, ref_eis_variant, pro_eis_standard, params_nacl
    ):
        """
        核心 F4+M9 验证: refdata 用 'R'/'X' (无单位) 而非 'Rs[ohm]'/ 'X[ohm]'
        旧实现会 KeyError,新实现应能运行
        """
        from EIS.ProcessingFile.Processingfun import TLcalibrate
        # 旧实现: KeyError: 'Rs[ohm]'
        # 新实现: 解析到 'R' / 'X' 列,正常运行
        results = TLcalibrate([ref_eis_variant], [pro_eis_standard], params_nacl)
        assert results is not None
        assert len(results) == 1


class TestTLcalibrateMissingColumns:
    """验证 TLcalibrate 缺列时打印诊断不崩 (F4)"""

    def test_prodata_missing_x_does_not_crash(
        self, ref_eis_standard, pro_eis_short_columns, params_nacl, capsys
    ):
        """
        场景: prodata 缺 'X[ohm]'
        期望: 打印诊断 [TLcalibrate] prodata[0] 缺列 ['X']; 不抛 KeyError
        """
        from EIS.ProcessingFile.Processingfun import TLcalibrate
        # 旧实现: KeyError: 'X[ohm]'
        # 新实现: print + continue(跳过本条)
        results = TLcalibrate(
            [ref_eis_standard], [pro_eis_short_columns], params_nacl
        )
        captured = capsys.readouterr()
        # 验证诊断信息出现
        assert '缺列' in captured.out, (
            f'期望打印缺列诊断,实际 stdout: {captured.out!r}'
        )
        assert 'X' in captured.out, '诊断应提及缺 X 列'
        # resultsdata 应为空(因为 prodata 被跳过)
        assert results == [], f'期望空 resultsdata,实际 {results!r}'

    def test_refdata_missing_rs_prints_diagnostics(
        self, capsys
    ):
        """
        场景: refdata 缺 Rs 列
        期望: 打印诊断并 return,不抛 KeyError
        """
        from EIS.ProcessingFile.Processingfun import TLcalibrate
        bad_ref = pd.DataFrame({
            'FREQ[Hz]':  [1e3, 1e4, 1e5, 1e6],
            'X[ohm]':    [-2.0, -1.5, -1.0, -0.5],
            # 缺 Rs 列
        })
        good_pro = pd.DataFrame({
            'FREQ[Hz]':  [1e3, 1e4, 1e5, 1e6],
            'Rs[ohm]':   [60.0, 60.5, 61.0, 61.5],
            'X[ohm]':    [-3.0, -2.5, -2.0, -1.5],
        })
        params = {
            'processing_parameters': {
                'geometric_constant': '3.874',
                'character_impedance': '50',
                'electrode_length': '0.0164',
                'solution_length': '0.002',
            },
            'solution_parameters': [{
                'solution_index': 0, 'name': 'NaCl',
                'concentration': 0.1, 'temperature': 25.0,
            }],
        }
        # 旧实现: KeyError
        # 新实现: 打印诊断,return []
        results = TLcalibrate([bad_ref], [good_pro], params)
        captured = capsys.readouterr()
        assert '缺列' in captured.out
        assert 'Rs' in captured.out
        assert results == []

    def test_ds_prodata_skipped_via_column_diagnostics(
        self, ref_eis_standard, pro_eis_total_wrong, params_nacl, capsys
    ):
        """
        场景: prodata 实际是 DS(列名完全不匹配 EIS 变体)
        期望: 打印缺列诊断(EpsRE/EpsIM/Sigma 都不匹配 Rs/X/FREQ 变体),
              跳过本条,不崩
        """
        from EIS.ProcessingFile.Processingfun import TLcalibrate
        # 此场景主要测试 M10 之前的"内部缺列诊断" — 即使 M10 入口检查
        # 漏了(如 prodata 长度为 0),函数内部仍能优雅失败
        results = TLcalibrate(
            [ref_eis_standard], [pro_eis_total_wrong], params_nacl
        )
        captured = capsys.readouterr()
        # DS 数据没有 Rs/X/FREQ 变体 → 应打印缺 Rs/X
        assert '缺列' in captured.out
        # 跳过所有 prodata → 空 resultsdata
        assert results == []


class TestCheck5M10EntryCheck:
    """验证 check5 + M10 入口类型检查"""

    def test_check5_recognizes_variant_as_eis(self):
        """check5 应能识别 'R'/'X' 列名为 EIS 数据(老 baseline)"""
        from EIS.Other.Datacheck import check5
        df = pd.DataFrame({
            'FREQ[Hz]': [1e3, 1e4],
            'R': [50.0, 51.0],
            'X': [-2.0, -1.5],
        })
        assert check5([df]) == 'EIS', (
            'check5 应识别 R/X 变体列名为 EIS (与 TLcalibrate 修复对齐)'
        )

    def test_check5_recognizes_ds(self):
        """check5 应识别 DS 列名"""
        from EIS.Other.Datacheck import check5
        df = pd.DataFrame({
            'FREQ[Hz]':   [1e3, 1e4],
            'EpsRE[-]':   [80.0, 78.0],
            'EpsIM[-]':   [10.0, 8.0],
            'Sigma[S/m]': [1e-3, 8e-4],
        })
        assert check5([df]) == 'DS'
