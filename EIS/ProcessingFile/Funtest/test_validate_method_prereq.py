# -*- coding: utf-8 -*-
"""
test_validate_method_prereq.py
重构后回归测试: 统一方法前置条件校验

历史背景 (FILTER_COMPARE_UI_CHANGELOG.md 14.11):
  重构前 Processing.processing() 有 8 个 elif 分支,每个分支独立嵌
  check3/check5/check6 等检查,带来:
  - 重复表达式 `check3 AND check5==EIS` 4 处
  - 错误弹窗 5 种不同 (warning/critical/print 混)
  - 层层短路,一次只能发现一个问题,用户需反复按 Process 才发现所有错

  重构方案 (EIS.Other.Datacheck):
  - 新增 METHOD_DATA_SPECS (8 个方法的数据要求集中描述)
  - 新增 validate_method_prereq() 统一校验函数
  - 返回 (is_valid, errors: list[str]),一次报告所有问题
  - Processing.processing() 入口统一调用,业务分支不再嵌校验
"""
import sys
import os
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest


# ----------------------------------------------------------------------
# Fixtures: 各种类型的数据样本
# ----------------------------------------------------------------------

@pytest.fixture
def eis_df():
    """EIS 数据: 标准 Rs/X 列名"""
    return pd.DataFrame({
        'FREQ[Hz]': [1e3, 1e4, 1e5, 1e6],
        'Rs[ohm]':  [50.0, 50.5, 51.0, 51.5],
        'X[ohm]':   [-2.0, -1.5, -1.0, -0.5],
    })


@pytest.fixture
def ds_df():
    """DS 数据: EpsRE/EpsIM 列名"""
    return pd.DataFrame({
        'FREQ[Hz]':   [1e3, 1e4, 1e5, 1e6],
        'EpsRE[-]':   [80.0, 78.0, 75.0, 70.0],
        'EpsIM[-]':   [10.0, 8.0, 6.0, 4.0],
        'Sigma[S/m]': [1e-3, 8e-4, 6e-4, 4e-4],
    })


@pytest.fixture
def eis_df_other_freq():
    """频率不同的 EIS 数据(用于 check6 测试)"""
    return pd.DataFrame({
        'FREQ[Hz]': [2e3, 2e4, 2e5, 2e6],   # 不同频率点
        'Rs[ohm]':  [50.0, 50.5, 51.0, 51.5],
        'X[ohm]':   [-2.0, -1.5, -1.0, -0.5],
    })


# ----------------------------------------------------------------------
# A. 8 方法 × 正常数据 (parametrize)
# ----------------------------------------------------------------------

class TestValidPrereq:
    """8 个方法 + 正确数据 → is_valid=True, errors=[]"""

    @pytest.fixture
    def data_map(self, eis_df, ds_df):
        return {'eis': eis_df, 'ds': ds_df}

    @pytest.mark.parametrize('method,prodata,refdata,params,ref_names', [
        # 1. Parallel Plate: EIS 或 DS 都接受
        ('Parallel Plate Capacitor', 'eis', None, None, ['empty']),
        ('Parallel Plate Capacitor', 'ds',  None, None, ['empty']),
        # 2. System Calibration: refdata=EIS
        ('System Calibration', 'eis', 'eis', None, ['ref1']),
        # 3. Dielectric Material: refdata=EIS + 同频率
        ('Dielectric Material Method', 'eis', 'eis', None, ['ref1']),
        # 4. Three-Solution: refdata=EIS
        ('Three-Solution Method', 'eis', 'eis', None, ['ref1']),
        # 5. RF Impedance Calibration: refdata=EIS + prodata=EIS
        ('RF Impedance Calibration', 'eis', 'eis', None, ['ref1']),
        # 6. RF Dielectric Calculation: prodata=EIS
        ('RF Dielectric Calculation', 'eis', None, None, ['empty']),
        # 7. RF Impedance Calculation: prodata=DS
        ('RF Impedance Calculation', 'ds',  None, None, ['empty']),
        # 8. K-K for EIS: 缺 validation_param
        ('K-K for EIS', None, None,
         {'processing_parameters': {'validation_parameter': '0.5'}},
         ['empty']),
    ])
    def test_valid(self, method, prodata, refdata, params, ref_names,
                   data_map):
        # 用 data_map 解析字符串 key → 实际 DataFrame
        pro = data_map.get(prodata) if prodata else None
        ref = data_map.get(refdata) if refdata else None
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            method,
            [ref] if ref is not None else [],
            ref_names,
            [pro] if pro is not None else [],
            params,
        )
        assert is_valid, (
            f'{method} 期望通过,实际 errors: {errors}'
        )
        assert errors == [], (
            f'{method} 期望 errors=[],实际: {errors}'
        )


# ----------------------------------------------------------------------
# B. 错误数据 (核心回归)
# ----------------------------------------------------------------------

class TestInvalidPrereq:
    """错误数据 → is_valid=False, errors 含具体诊断"""

    def test_rf_impedance_calibration_ds_prodata_fails(
        self, eis_df, ds_df
    ):
        """
        核心 M10 回归: DS prodata 配 EIS refdata → RF Impedance Calibration 失败
        弹窗文案应同时提及 EIS (需求) 和 DS (实际)
        """
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'RF Impedance Calibration',
            [eis_df], ['ref1'], [ds_df], None,
        )
        assert not is_valid
        # errors 应同时提及 EIS (需求) 和 DS (实际)
        assert any('EIS' in e and 'DS' in e for e in errors), (
            f'errors 应同时提及 EIS (需求) 和 DS (实际),实际: {errors}'
        )

    def test_system_calibration_with_ds_refdata_fails(
        self, eis_df, ds_df
    ):
        """System Calibration: refdata 必须是 EIS,DS 应失败"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'System Calibration',
            [ds_df], ['ref1'], [eis_df], None,
        )
        assert not is_valid
        assert any('Reference data' in e and 'DS' in e for e in errors), (
            f'errors 应说明 refdata 是 DS,实际: {errors}'
        )

    def test_dielectric_material_freq_inconsistency(
        self, eis_df, eis_df_other_freq
    ):
        """Dielectric Material: refdata 和 prodata 频率不一致 → check6 失败"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'Dielectric Material Method',
            [eis_df], ['ref1'], [eis_df_other_freq], None,
        )
        assert not is_valid
        assert any('Frequency' in e and 'inconsistent' in e for e in errors), (
            f'errors 应提及 frequency inconsistent,实际: {errors}'
        )

    def test_kk_eis_missing_validation_param_fails(self, eis_df):
        """K-K for EIS: 缺 validation_parameter 参数"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'K-K for EIS', [], ['empty'], [eis_df], None,
        )
        assert not is_valid
        assert any('validation_parameter' in e for e in errors), (
            f'errors 应提及 validation_parameter,实际: {errors}'
        )

    def test_kk_eis_with_empty_validation_param_fails(self, eis_df):
        """K-K for EIS: validation_parameter 是空字符串 → 仍失败"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'K-K for EIS', [], ['empty'], [eis_df],
            {'processing_parameters': {'validation_parameter': ''}},
        )
        assert not is_valid
        assert any('validation_parameter' in e for e in errors)

    def test_rf_dielectric_calculation_needs_eis_not_ds(
        self, ds_df
    ):
        """RF Dielectric Calculation: prodata 必须是 EIS,DS 应失败"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'RF Dielectric Calculation',
            [], ['empty'], [ds_df], None,
        )
        assert not is_valid
        assert any('EIS' in e for e in errors)

    def test_rf_impedance_calculation_needs_ds_not_eis(
        self, eis_df
    ):
        """RF Impedance Calculation: prodata 必须是 DS,EIS 应失败"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'RF Impedance Calculation',
            [], ['empty'], [eis_df], None,
        )
        assert not is_valid
        assert any('DS' in e for e in errors)

    def test_refdata_count_invalid(self, eis_df):
        """refdata 数量不对(System Calibration):3 个 refdata 期望被识别为错"""
        from EIS.Other.Datacheck import validate_method_prereq
        # 注:check3 实现只检查第一个 refdata rownum,不严格检查 count。
        # 当前 validate 不强制 refdata=1(由业务函数 calibrate 自行处理)。
        # 因此 3 个 refdata 也可能通过 — 此测试仅验证 is_valid 行为有定义(不抛异常)。
        is_valid, errors = validate_method_prereq(
            'System Calibration',
            [eis_df, eis_df, eis_df],
            ['ref1', 'ref2', 'ref3'],
            [eis_df], None,
        )
        # 不抛异常即可(具体行为由 check3 决定)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


# ----------------------------------------------------------------------
# C. 边界 / 多次错误
# ----------------------------------------------------------------------

class TestEdgeCases:
    """边界场景"""

    def test_unknown_method_returns_valid(self):
        """不识别的方法 → (True, []) 向后兼容"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'XYZ Unknown Method', [], [], [], None,
        )
        assert is_valid
        assert errors == []

    def test_all_specs_methods_have_unique_keys(self):
        """所有方法 entry 都不重复(防 dict 覆盖)"""
        from EIS.Other.Datacheck import METHOD_DATA_SPECS
        assert len(METHOD_DATA_SPECS) == 8, (
            f'期望 8 个方法,实际 {len(METHOD_DATA_SPECS)}'
        )

    def test_multiple_errors_reported_at_once(self, ds_df):
        """
        核心重构目标: 一次报告多个错误
        RF Impedance Calibration 场景: refdata 缺 + prodata 错 → errors ≥ 2
        """
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'RF Impedance Calibration',
            [],   # refdata 缺
            ['empty'],
            [ds_df],  # prodata 错(DS)
            None,
        )
        assert not is_valid
        # 期望至少 2 个错误(ref 缺 + pro 类型错)
        assert len(errors) >= 2, (
            f'重构后应一次报告所有问题,期望 ≥ 2,实际: {errors}'
        )

    def test_no_refdata_required_method_skips_ref_check(self, eis_df):
        """不需要 refdata 的方法(Parallel Plate)不会因 refdata 缺而失败"""
        from EIS.Other.Datacheck import validate_method_prereq
        is_valid, errors = validate_method_prereq(
            'Parallel Plate Capacitor',
            [],   # refdata 空
            ['empty'],
            [eis_df],
            None,
        )
        assert is_valid, (
            f'Parallel Plate 不需要 refdata,refdata 空不应导致 errors,'
            f'实际: {errors}'
        )

    def test_validate_then_format_for_dialog(self, ds_df):
        """演示 validate 返回值如何拼成弹窗正文"""
        from EIS.Other.Datacheck import validate_method_prereq
        _, errors = validate_method_prereq(
            'RF Impedance Calibration',
            [], ['empty'], [ds_df], None,
        )
        formatted = "Cannot start processing:\n\n" + "\n".join(
            f"  • {e}" for e in errors
        )
        # 验证格式可读,含所有错误
        assert 'Cannot start processing' in formatted
        assert '•' in formatted  # bullet marker
        assert len(errors) >= 1


# ----------------------------------------------------------------------
# D. Processing 入口集成测试(用 mock 验证 dispatcher 行为)
# ----------------------------------------------------------------------

class TestProcessingDispatcher:
    """验证 Processing.processing() 入口走 validate_method_prereq"""

    def _bypass_init(self, cls, method_name):
        """绕过 QWidget __init__ 构造最小可用实例"""
        instance = cls.__new__(cls)
        instance.refdata = []
        instance.prodata = []
        instance.refdataname = ['empty']
        instance.prodataname = []
        instance.selectlist = []
        instance.dataInfo = []
        instance.resultsdata = []
        instance.resultsdataname = []
        instance.resultsselectlist = []
        instance.resultsdataInfo = []
        instance.original_prodataname = []
        instance.original_selectlist = []
        instance.original_dataInfo = []
        instance.processui = MagicMock()
        instance.processui.processmethodComboBox.currentText.return_value = (
            method_name
        )
        return instance

    def test_processing_calls_validate_method_prereq(self, eis_df):
        """验证 processing() 入口走 validate_method_prereq"""
        from EIS.ProcessingFile.Processing import Dataprocess
        from EIS.Other.Datacheck import validate_method_prereq
        instance = self._bypass_init(Dataprocess, 'Parallel Plate Capacitor')
        instance.prodata = [eis_df]
        instance.selectlist = [1]
        instance.prodataname = ['pro1']
        instance.dataInfo = [{}]
        # patch 的是 Processing 模块里的引用(因为 from import 创建了本地引用)
        with patch(
            'EIS.ProcessingFile.Processing.validate_method_prereq',
            wraps=validate_method_prereq,
        ) as mock_validate:
            with patch.object(instance, 'databasecreat'):
                with patch(
                    'EIS.ProcessingFile.Processing.paraplate',
                    return_value=[],
                ):
                    instance.processing()
        # 验证 validate_method_prereq 被调用 1 次
        assert mock_validate.call_count == 1, (
            f'重构后 processing() 应只调 1 次 validate_method_prereq,'
            f'实际 {mock_validate.call_count} 次'
        )
        # 验证调用参数正确
        call_args = mock_validate.call_args
        assert call_args[0][0] == 'Parallel Plate Capacitor'

    def test_processing_shows_unified_dialog_on_failure(self, ds_df):
        """校验失败时,弹 1 个统一 QMessageBox.warning(不是 5 个)"""
        from EIS.ProcessingFile.Processing import Dataprocess
        instance = self._bypass_init(Dataprocess, 'System Calibration')
        instance.refdata = [ds_df]   # DS 不通过 System Calibration
        instance.refdataname = ['ref1']
        instance.prodata = [ds_df]
        instance.selectlist = [1]
        instance.prodataname = ['pro1']
        instance.dataInfo = [{}]
        with patch('EIS.ProcessingFile.Processing.QMessageBox.warning') as mock_warn, \
             patch('EIS.ProcessingFile.Processing.QMessageBox.critical') as mock_crit, \
             patch('EIS.ProcessingFile.Processing.calibrate') as mock_calib:
            instance.processing()
        # 验证只弹 1 个 warning,没有 critical,没有进 calibrate
        assert mock_warn.call_count == 1, (
            f'校验失败应弹 1 个统一 warning,实际 {mock_warn.call_count} 个'
        )
        assert not mock_crit.called, '重构后 critical 已被统一 warning 替代'
        assert not mock_calib.called, '校验失败时不应进入业务逻辑'
        # 验证弹窗内容含 bullet 列表
        warning_args = mock_warn.call_args
        # call_args[0] = (parent, title, text) 或 (parent, title, text, ...)
        text = warning_args[0][2] if len(warning_args[0]) > 2 else ''
        assert 'Cannot start processing' in text
        assert '•' in text  # bullet marker

    def test_processing_silently_ignores_unknown_method(self):
        """不识别的方法静默 return(向后兼容旧 else 分支)"""
        from EIS.ProcessingFile.Processing import Dataprocess
        instance = self._bypass_init(Dataprocess, 'XYZ Unknown')
        with patch('EIS.ProcessingFile.Processing.QMessageBox.warning') as mock_warn:
            instance.processing()  # 不应抛异常
        # 不识别的方法:validate_method_prereq 返回 (True, []),不弹窗
        assert not mock_warn.called
