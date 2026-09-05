# -*- coding: utf-8 -*-
"""
test_processing_dialog.py
统一入口校验回归测试 (FILTER_COMPARE_UI_CHANGELOG.md 14.11)

历史背景:
  14.10 M10 升级: RF Impedance Calibration 入口检测到 DS 数据时,弹
  QMessageBox.critical("Data type error", ...) + return。
  14.11 Phase 1+2+3 重构: 引入 METHOD_DATA_SPECS + validate_method_prereq,
  8 个方法统一走 1 个 warning 入口,errors 列表一次性报告所有问题。

本测试覆盖:
  - 入口弹窗类型:QMessageBox.warning (不再 critical)
  - 弹窗内容:方法名 + "Cannot start processing" + errors bullet 列表
  - 弹窗内容应可引导用户用正确方法(errors 提到类型 + 期望类型)
  - 通过校验的数据不应触发弹窗
  - 静态检查:关键字符串必须在源码中存在
"""
import os
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _make_eis_df():
    """EIS 数据: 标准 Rs/X 列名"""
    return pd.DataFrame({
        'FREQ[Hz]': [1e3, 1e4, 1e5, 1e6],
        'Rs[ohm]':  [50.0, 50.5, 51.0, 51.5],
        'X[ohm]':   [-2.0, -1.5, -1.0, -0.5],
    })


def _make_ds_df():
    """DS 数据: EpsRE/EpsIM 列名(check5 要求至少 2 个 DS 特征列才能识别)"""
    return pd.DataFrame({
        'FREQ[Hz]':   [1e3, 1e4, 1e5, 1e6],
        'EpsRE[-]':   [80.0, 78.0, 75.0, 70.0],
        'EpsIM[-]':   [10.0, 8.0, 6.0, 4.0],
        'Sigma[S/m]': [1e-3, 8e-4, 6e-4, 4e-4],
    })


def _bypass_init(cls):
    """
    绕过 QWidget __init__ (需要 QApplication + 完整 UI 资源),
    直接构造一个最小可用的实例用于单测 processing() 内部逻辑。
    """
    instance = cls.__new__(cls)
    # 注入 processing() 依赖的属性
    instance.refdata = []
    instance.prodata = []
    instance.refdataname = []
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
    # 模拟 processui.processmethodComboBox.currentText()
    instance.processui = MagicMock()
    return instance


def _setup_data(instance, prodata=None, refdata=None):
    """填充数据 + 配齐所有依赖属性"""
    if prodata is None:
        prodata = [_make_eis_df()]
    if refdata is None:
        refdata = [_make_eis_df()]
    instance.prodata = list(prodata)
    instance.refdata = list(refdata)
    instance.prodataname = ['pro1']
    instance.refdataname = ['ref1']
    instance.selectlist = [1] * len(prodata)
    instance.dataInfo = [{}] * len(prodata)
    return instance


# ----------------------------------------------------------------------
# Tests: 统一入口弹窗行为
# ----------------------------------------------------------------------

class TestUnifiedEntryDialog:
    """
    14.11 重构后,所有数据校验失败统一走 QMessageBox.warning,
    errors 列表一次性报告所有问题。
    """

    def _make_instance(self, method='RF Impedance Calibration'):
        """构造最小可用实例 + 默认 method"""
        from EIS.ProcessingFile.Processing import Dataprocess
        inst = _bypass_init(Dataprocess)
        inst.processui.processmethodComboBox.currentText.return_value = method
        return inst

    def test_ds_prodata_triggers_unified_warning(self):
        """
        核心回归: DS prodata + EIS refdata → 弹统一 warning + return
        - 不再是 critical
        - errors 应包含 "Processing data type" + "DS" + "EIS"
        - TLcalibrate 不应被调用
        """
        inst = self._make_instance('RF Impedance Calibration')
        # DS 数据 prodata + EIS 数据 refdata (refdata 通过校验,prodata 失败)
        _setup_data(inst, prodata=[_make_ds_df()])

        with patch('EIS.ProcessingFile.Processing.QMessageBox.warning') as mock_warn, \
             patch('EIS.ProcessingFile.Processing.QMessageBox.critical') as mock_crit, \
             patch('EIS.ProcessingFile.Processing.TLcalibrate') as mock_tl:
            inst.processing()

        # 1. 弹窗类型:统一 warning,非 critical
        assert mock_warn.called, (
            'DS 数据应触发统一 QMessageBox.warning,实际未调用'
        )
        assert not mock_crit.called, (
            '14.11 重构后已不再使用 QMessageBox.critical'
        )

        # 2. 业务逻辑被拦截
        assert not mock_tl.called, (
            'DS 数据不应进入 TLcalibrate(防止后续 KeyError)'
        )

        # 3. 弹窗内容
        args = mock_warn.call_args[0]
        title = args[1] if len(args) > 1 else mock_warn.call_args[1].get('text', '')
        text = args[2] if len(args) > 2 else ''
        # 标题含方法名
        assert 'RF Impedance Calibration' in title, (
            f'弹窗标题应含方法名,实际: {title!r}'
        )
        # 正文含 "Cannot start processing"
        assert 'Cannot start processing' in text, (
            f'弹窗正文应含 "Cannot start processing",实际: {text!r}'
        )
        # 正文含 errors bullet,提到类型信息
        assert 'Processing data type' in text, (
            f'弹窗正文应说明问题类别,实际: {text!r}'
        )
        assert 'DS' in text, (
            f'弹窗正文应说明当前类型 DS,实际: {text!r}'
        )
        assert 'EIS' in text, (
            f'弹窗正文应说明期望类型 EIS,实际: {text!r}'
        )

    def test_ds_refdata_triggers_unified_warning(self):
        """
        对偶测试: DS refdata + EIS prodata → 弹统一 warning
        - errors 应包含 "Reference data type"
        - TLcalibrate 不应被调用
        """
        inst = self._make_instance('RF Impedance Calibration')
        # refdata 是 DS (check3 通过但 check5 != 'EIS'),prodata 是 EIS
        _setup_data(inst, refdata=[_make_ds_df()])

        with patch('EIS.ProcessingFile.Processing.QMessageBox.warning') as mock_warn, \
             patch('EIS.ProcessingFile.Processing.TLcalibrate') as mock_tl:
            inst.processing()

        assert mock_warn.called, 'refdata 类型错应触发统一 warning'
        assert not mock_tl.called, 'refdata 错时不应进入 TLcalibrate'

        text = mock_warn.call_args[0][2]
        assert 'Reference data type' in text, (
            f'errors 应说明 refdata 类型错,实际: {text!r}'
        )

    def test_eis_prodata_does_not_trigger_warning(self):
        """
        通过校验的数据:不弹窗,业务正常执行
        - RF Impedance Calibration + EIS ref + EIS pro + 完整 params
        - 不应弹任何对话框
        - TLcalibrate 应被调用
        """
        inst = self._make_instance('RF Impedance Calibration')
        _setup_data(inst)  # 默认 EIS + EIS

        with patch('EIS.ProcessingFile.Processing.QMessageBox.warning') as mock_warn, \
             patch('EIS.ProcessingFile.Processing.QMessageBox.critical') as mock_crit, \
             patch('EIS.ProcessingFile.Processing.TLcalibrate') as mock_tl, \
             patch.object(inst, 'get_parameters_info', return_value={
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
             }), \
             patch.object(inst, 'databasecreat'):
            inst.processing()

        assert not mock_warn.called, 'EIS 数据不应触发 warning 弹窗'
        assert not mock_crit.called, 'EIS 数据不应触发任何弹窗'
        assert mock_tl.called, 'EIS 数据应能进入 TLcalibrate'

    def test_unified_warning_called_only_once(self):
        """
        多个错误时,只弹 1 个 warning(errors 列表一次性报告)
        - 旧实现会弹多次(每个分支一个)
        - 14.11 重构:统一 1 个 warning,errors 列表含所有问题
        """
        inst = self._make_instance('RF Impedance Calibration')
        # refdata 和 prodata 都用 DS (双错)
        _setup_data(inst, prodata=[_make_ds_df()], refdata=[_make_ds_df()])

        with patch('EIS.ProcessingFile.Processing.QMessageBox.warning') as mock_warn, \
             patch('EIS.ProcessingFile.Processing.TLcalibrate') as mock_tl:
            inst.processing()

        # 弹窗次数:恰好 1 次
        assert mock_warn.call_count == 1, (
            f'统一入口应只弹 1 次 warning,实际: {mock_warn.call_count}'
        )
        # 业务未执行
        assert not mock_tl.called

        # 弹窗内应包含 2 条错误(refdata + prodata)
        text = mock_warn.call_args[0][2]
        assert text.count('•') >= 2, (
            f'弹窗应至少 2 个 bullet,实际: {text!r}'
        )
        assert 'Reference data type' in text
        assert 'Processing data type' in text


# ----------------------------------------------------------------------
# Tests: 静态检查 — 关键字符串必须在源码中存在
# ----------------------------------------------------------------------

class TestUnifiedEntryStaticCheck:
    """
    防回退: 关键字符串 / 数据驱动表必须存在。
    """

    def test_unified_entry_strings_in_processing(self):
        """
        Processing.py 必须包含统一入口的:
        - "Cannot start processing" 标识
        - validate_method_prereq 调用
        - QMessageBox.warning 弹窗
        - 不再使用 QMessageBox.critical (除非其他合法的 critical)
        """
        proc_path = os.path.join(
            os.path.dirname(__file__), '..', 'Processing.py'
        )
        proc_path = os.path.abspath(proc_path)
        with open(proc_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # 14.11 统一入口字符串
        assert 'Cannot start processing' in source, (
            '14.11 重构: 统一入口标识 "Cannot start processing" 已丢失'
        )
        assert 'Prerequisites not met' in source, (
            '14.11 重构: 弹窗标题 "Prerequisites not met" 已丢失'
        )
        assert 'validate_method_prereq' in source, (
            '14.11 重构: validate_method_prereq 调用已丢失'
        )
        assert 'QMessageBox.warning' in source, (
            '14.11 重构: QMessageBox.warning 弹窗已丢失'
        )

    def test_method_data_specs_in_datacheck(self):
        """
        METHOD_DATA_SPECS 必须在 Datacheck.py 中定义,8 个方法全覆盖。
        """
        from EIS.Other import Datacheck
        assert hasattr(Datacheck, 'METHOD_DATA_SPECS'), (
            '14.11 重构: METHOD_DATA_SPECS 未在 Datacheck.py 中定义'
        )
        specs = Datacheck.METHOD_DATA_SPECS
        # 8 个方法全覆盖
        expected_methods = [
            'Parallel Plate Capacitor',
            'System Calibration',
            'Dielectric Material Method',
            'Three-Solution Method',
            'RF Impedance Calibration',
            'RF Dielectric Calculation',
            'RF Impedance Calculation',
            'K-K for EIS',
        ]
        for m in expected_methods:
            assert m in specs, f'METHOD_DATA_SPECS 缺少方法: {m}'

    def test_validate_method_prereq_in_datacheck(self):
        """
        validate_method_prereq 函数必须在 Datacheck.py 中导出。
        """
        from EIS.Other import Datacheck
        assert hasattr(Datacheck, 'validate_method_prereq'), (
            '14.11 重构: validate_method_prereq 未在 Datacheck.py 中导出'
        )
        # 函数签名:返回 (bool, list[str])
        import inspect
        sig = inspect.signature(Datacheck.validate_method_prereq)
        params = list(sig.parameters.keys())
        assert 'method_name' in params
        assert 'prodata' in params
