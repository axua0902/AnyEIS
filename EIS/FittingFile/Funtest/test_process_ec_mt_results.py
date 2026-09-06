# -*- coding: utf-8 -*-
"""
test_process_ec_mt_results.py
=============================

验证 Bug #006 Phase 3 修复:`Fitting.py:processECMResults` / `processMTResults`
在 `param.stderr is None` 时(Error [%] 列)写入字符串 `'N/A'`,而非 `NaN`。

设计目标:
  - `param.stderr` 只在 `least_squares` (LM) 算法下由协方差矩阵算出
  - 其它 9 种算法(全局/启发式)在 lmfit 中 stderr 为 None
  - 旧实现:写入 `float('nan')`,显示 'nan' 字串,无意义且易误导
  - 新实现:写入字符串 `'N/A'`,明确告知用户该算法不提供 stderr 估计

覆盖范围:
  1. `processECMResults` 静态源码:不存在 `float('nan')` 写 Error 列
  2. `processMTResults` 静态源码:不存在 `float('nan')` 写 Error 列
  3. `processECMResults` / `processMTResults` 包含 `'N/A'` 字符串分支
  4. 行为级:mock 拟合结果,验证当 stderr=None 时,表格 Error [%] 单元为 'N/A'

策略:
  - 不实例化 Fitting 类(避免触发 PyTabWidget2 重依赖)
  - 用 monkeypatch + MagicMock 构造最小依赖
  - 静态源码扫描保证不被回归

运行:
    pytest EIS/FittingFile/Funtest/test_process_ec_mt_results.py -v
"""
import os
import sys
import math
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# 共享 fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _build_ecm_table(qapp, num_rows=2):
    """构造 7 列 ECMtable(Bug #006 Phase 2 后),用于行为级测试。"""
    from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
    ecm = QTableWidget()
    ecm.setColumnCount(7)
    ecm.setHorizontalHeaderLabels(
        ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
    )
    ecm.setRowCount(num_rows)
    for row, name in enumerate(['R1', 'C1'][:num_rows]):
        ecm.setItem(row, 0, QTableWidgetItem(name))
        ecm.setItem(row, 1, QTableWidgetItem('comment'))
        ecm.setItem(row, 2, QTableWidgetItem('100.0'))
        ecm.setItem(row, 3, QTableWidgetItem(''))   # Fitted (空)
        ecm.setItem(row, 4, QTableWidgetItem('1e6'))
        ecm.setItem(row, 5, QTableWidgetItem('1e-9'))
        ecm.setItem(row, 6, QTableWidgetItem(''))   # Error (空)
    return ecm


def _build_mt_table(qapp, num_rows=2):
    """构造 7 列 MTtable。"""
    from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
    mt = QTableWidget()
    mt.setColumnCount(7)
    mt.setHorizontalHeaderLabels(
        ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
    )
    mt.setRowCount(num_rows)
    for row, name in enumerate(['epsh', 'Deps1'][:num_rows]):
        mt.setItem(row, 0, QTableWidgetItem(name))
        mt.setItem(row, 1, QTableWidgetItem('comment'))
        mt.setItem(row, 2, QTableWidgetItem('5.0'))
        mt.setItem(row, 3, QTableWidgetItem(''))
        mt.setItem(row, 4, QTableWidgetItem('50.0'))
        mt.setItem(row, 5, QTableWidgetItem('0.0'))
        mt.setItem(row, 6, QTableWidgetItem(''))
    return mt


# ---------------------------------------------------------------------------
# 1. 静态源码扫描
# ---------------------------------------------------------------------------
class TestSourceCode:
    """静态扫描 Fitting.py,确保 Bug #006 Phase 3 修复不被回归。"""

    def _get_function_body(self, src, method_name):
        start = src.find(f'def {method_name}')
        assert start != -1, f"未找到 {method_name} 定义"
        end = src.find('\n    def ', start + 1)
        if end == -1:
            end = len(src)
        return src[start:end]

    def test_processECMResults_no_nan_write(self):
        """processECMResults 不应再写 float('nan') 到 Error [%] 列。"""
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        body = self._get_function_body(src, 'processECMResults')
        assert "float('nan')" not in body, (
            "processECMResults 仍含 float('nan') 写入,应改为 'N/A' 字符串"
        )

    def test_processECMResults_uses_NA_string(self):
        """processECMResults 应使用 'N/A' 字符串替代 nan。"""
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        body = self._get_function_body(src, 'processECMResults')
        assert "'N/A'" in body, (
            "processECMResults 应使用 'N/A' 字符串替代 NaN"
        )

    def test_processMTResults_no_nan_write(self):
        """processMTResults 不应再写 float('nan') 到 Error [%] 列。"""
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        body = self._get_function_body(src, 'processMTResults')
        assert "float('nan')" not in body, (
            "processMTResults 仍含 float('nan') 写入,应改为 'N/A' 字符串"
        )

    def test_processMTResults_uses_NA_string(self):
        """processMTResults 应使用 'N/A' 字符串替代 nan。"""
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        body = self._get_function_body(src, 'processMTResults')
        assert "'N/A'" in body, (
            "processMTResults 应使用 'N/A' 字符串替代 NaN"
        )


# ---------------------------------------------------------------------------
# 2. 行为级测试:stderr=None 时表格 Error [%] 列写入 'N/A'
# ---------------------------------------------------------------------------
def _make_fit_result(param_names, param_values, stderr_values):
    """构造一个 lmfit.MinimizerResult 风格的 mock。"""
    fit_result = MagicMock()
    fit_result.var_names = list(param_names)

    # x 属性:对全局/启发式算法可能为 None,故用 getattr 兜底
    fit_result.x = list(param_values)

    # params 字典:每个 name -> {value, stderr}
    params_dict = {}
    for name, value, stderr in zip(param_names, param_values, stderr_values):
        p = MagicMock()
        p.value = value
        p.stderr = stderr  # None 触发 'N/A' 路径
        params_dict[name] = p
    fit_result.params = params_dict
    return fit_result


class TestProcessECMResultsBehavior:
    """行为级:用真实 QTableWidget 验证 processECMResults 写入 'N/A'。"""

    def test_stderr_none_writes_NA_string(self, qapp):
        """非 LS 算法:stderr=None,Error [%] 列应写入 'N/A' 字符串。"""
        from EIS.FittingFile.Fitting import Fitting

        # 构造表格 + mock self
        ecm = _build_ecm_table(qapp, num_rows=2)
        self_mock = SimpleNamespace(
            fittedresults=[
                _make_fit_result(['R1', 'C1'], [99.5, 1e-6], [None, None])
            ],
            current_fitting_dataset=0,
            tab1=SimpleNamespace(
                ECMtable=ecm,
                setECMTableHeader=MagicMock(),
            ),
            ECMtableWrite=MagicMock(),
        )

        # 调用 processECMResults
        Fitting.processECMResults(self_mock, dataset_index=0)

        # 收集所有调用,筛选 col=6(Error [%])的调用
        err_calls = [
            c for c in self_mock.ECMtableWrite.call_args_list
            if c.args[2] == 6
        ]
        assert len(err_calls) == 2, (
            f"ECMtableWrite 应被调 2 次到 col 6(2 个参数),实际 {len(err_calls)}"
        )

        # 每次调用 Error [%] 的值应为 'N/A'
        for call in err_calls:
            err_value = call.args[1]
            assert err_value == 'N/A', (
                f"Error [%] 单元值应为 'N/A' 字符串,实际: {err_value!r}"
            )

    def test_stderr_value_writes_percentage(self, qapp):
        """LS 算法:stderr 有值,Error [%] 列应写入百分比数字。"""
        from EIS.FittingFile.Fitting import Fitting

        ecm = _build_ecm_table(qapp, num_rows=1)
        # R1 value=100, stderr=0.5 → 0.5%
        self_mock = SimpleNamespace(
            fittedresults=[
                _make_fit_result(['R1'], [100.0], [0.5])
            ],
            current_fitting_dataset=0,
            tab1=SimpleNamespace(
                ECMtable=ecm,
                setECMTableHeader=MagicMock(),
            ),
            ECMtableWrite=MagicMock(),
        )

        Fitting.processECMResults(self_mock, dataset_index=0)

        # 收集所有调用,筛选 col=6(Error [%])的调用
        err_calls = [
            c for c in self_mock.ECMtableWrite.call_args_list
            if c.args[2] == 6
        ]
        assert len(err_calls) == 1
        err_value = err_calls[0].args[1]
        # 期望 0.5(100 * round(0.5/100, 4) = 0.5)
        assert err_value == 0.5, f"Error [%] 应为 0.5,实际: {err_value!r}"


class TestProcessMTResultsBehavior:
    """行为级:用真实 QTableWidget 验证 processMTResults 写入 'N/A'。"""

    def test_stderr_none_writes_NA_string(self, qapp):
        """非 LS 算法:stderr=None,Error [%] 列应写入 'N/A' 字符串。"""
        from EIS.FittingFile.Fitting import Fitting

        mt = _build_mt_table(qapp, num_rows=2)
        self_mock = SimpleNamespace(
            fittedresults=[
                _make_fit_result(['epsh', 'Deps1'], [5.5, 2.1], [None, None])
            ],
            current_fitting_dataset=0,
            tab2=SimpleNamespace(
                MTtable=mt,
            ),
            MTtableWrite=MagicMock(),
        )

        Fitting.processMTResults(self_mock, dataset_index=0)

        # 收集所有调用,筛选 col=6(Error [%])的调用
        err_calls = [
            c for c in self_mock.MTtableWrite.call_args_list
            if c.args[2] == 6
        ]
        assert len(err_calls) == 2, (
            f"MTtableWrite 应被调 2 次到 col 6(2 个参数),实际 {len(err_calls)}"
        )

        for call in err_calls:
            err_value = call.args[1]
            assert err_value == 'N/A', (
                f"Error [%] 单元值应为 'N/A' 字符串,实际: {err_value!r}"
            )

    def test_stderr_value_writes_percentage(self, qapp):
        """LS 算法:stderr 有值,Error [%] 列应写入百分比数字。"""
        from EIS.FittingFile.Fitting import Fitting

        mt = _build_mt_table(qapp, num_rows=1)
        # epsh value=5, stderr=0.05 → 1.0%
        self_mock = SimpleNamespace(
            fittedresults=[
                _make_fit_result(['epsh'], [5.0], [0.05])
            ],
            current_fitting_dataset=0,
            tab2=SimpleNamespace(
                MTtable=mt,
            ),
            MTtableWrite=MagicMock(),
        )

        Fitting.processMTResults(self_mock, dataset_index=0)

        err_calls = [
            c for c in self_mock.MTtableWrite.call_args_list
            if c.args[2] == 6
        ]
        assert len(err_calls) == 1
        err_value = err_calls[0].args[1]
        assert err_value == 1.0, f"Error [%] 应为 1.0,实际: {err_value!r}"
