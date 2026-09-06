# -*- coding: utf-8 -*-
"""
test_clear_calculation.py
=========================

验证 Fitting.py / simulation.py 中「计算行 Clear 按钮」槽函数的 B-1 行为合约：

  * `clearECCalculation`：清空 ECM 最近一次 Calculate 的输出，但保留模型结构
  * `clearMTCalculation`：清空 MT 最近一次 Calculate 的输出，但保留模型结构

B-1 合约(Fitting 路径,7 列表格 — Bug #006 Phase 2 移除 Fixed 死列后):
  ┌──────────────────────────────┬────────────┬────────────┐
  │ 对象                          │ B-1 是否清 │ 是否保留   │
  ├──────────────────────────────┼────────────┼────────────┤
  │ self.fitteddata / fittedresults│ ✓ 清空     │ -          │
  │ self.resultsdataInfo          │ ✓ 清空     │ -          │
  │ 全局 plotdata / plotdataname   │ ✓ 清空     │ -          │
  │ 全局 outputlist               │ ✓ 清空     │ -          │
  │ table col=3 (Fitted_Value)    │ ✓ 清空     │ -          │
  │ table col=6 (Error [%])       │ ✓ 清空     │ -          │
  │ table col=0,1,2,4,5           │ -          │ ✓ 保留     │
  │ (Name/Comments/Initial/Max/Min)              │        │
  │ self.circuit / self.params    │ -          │ ✓ 保留     │
  │ self.termnamelist / modelterm │ -          │ ✓ 保留     │
  │ connectionTextEdit /          │ -          │ ✓ 保留     │
  │ MTmultitermTextEdit           │            │            │
  │ EP / DC 勾选                   │ -          │ ✓ 保留     │
  └──────────────────────────────┴────────────┴────────────┘

Simulation 路径(5 列表格,无 Fitted_Value / Error [%] / Fixed 列):
  * 表格完全不动(所有列均为用户输入)
  * 只清空全局 plot 副本

策略：
  - 不实例化 Fitting / Simu 类（避免触发 PyTabWidget2 等重依赖）
  - 用 unittest.mock 构造一个最小 mock 对象
  - 将 `Fitting.clearECCalculation` / `Fitting.clearMTCalculation` 作为
    普通函数调用，传入 mock 对象作为 self
  - 验证对 mock 字段的访问路径与表格清空列

运行：
    pytest EIS/FittingFile/Funtest/test_clear_calculation.py -v
"""
import os
import sys
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

# 让顶层 import 可用：EIS/FittingFile/Funtest/ -> AnyEIS/
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Mock 工具
# ---------------------------------------------------------------------------
def _make_table_mock(num_rows=3):
    """构造一个 QTableWidget 风格的 mock。"""
    table = MagicMock()
    table.rowCount.return_value = num_rows
    return table


def _make_fitting_like_mock():
    """构造一个最小可用的「类 Fitting」对象，验证 B-1 合约。"""
    obj = SimpleNamespace()

    # 拟合输出缓存
    obj.fitteddata = [MagicMock(name='fit_data_1'), MagicMock(name='fit_data_2')]
    obj.fittedresults = [MagicMock(name='fit_result_1')]
    obj.resultsdataInfo = [MagicMock(name='info_1'), MagicMock(name='info_2')]

    # tab1 (ECM) / tab2 (MT) 表格
    obj.tab1 = SimpleNamespace(
        ECMtable=_make_table_mock(num_rows=3),
        connectionTextEdit=MagicMock(),
    )
    obj.tab2 = SimpleNamespace(
        MTtable=_make_table_mock(num_rows=3),
        MTmultitermTextEdit=MagicMock(),
        EPcheckBox=MagicMock(),
        DCcheckBox=MagicMock(),
    )

    # 模型结构（应被保留）
    obj.circuit = ['R1', 'C1']
    obj.params = MagicMock()
    obj.termnamelist = ['t1', 't2']
    obj.modelterm = ['R', 'C']
    obj.MTparams = MagicMock()
    obj.MTexpre = ['a+b']
    obj.option = {'EP': 1, 'DC Conductivity': 0}

    return obj


# ---------------------------------------------------------------------------
# 真实 QTableWidget 集成测试(覆盖关键 bug 场景)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def qapp():
    """Session-scoped QApplication,用于真实 QTableWidget 集成测试。"""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _build_7col_table(qapp, fitted_filled=True):
    """构造一个 7 列 MTtable(Fitting 路径,Bug #006 Phase 2 后无 Fixed),可选填充拟合结果列。"""
    from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
    mt = QTableWidget()
    mt.setColumnCount(7)
    mt.setHorizontalHeaderLabels(
        ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
    )
    mt.setRowCount(2)
    for row, (name, init_v, max_v, min_v) in enumerate(
        [('R1', '100.0', '1e6', '1e-9'),
         ('C1', '1e-6', '1e-3', '1e-15')]
    ):
        mt.setItem(row, 0, QTableWidgetItem(name))
        mt.setItem(row, 1, QTableWidgetItem('comment'))
        mt.setItem(row, 2, QTableWidgetItem(init_v))
        if fitted_filled:
            mt.setItem(row, 3, QTableWidgetItem('99.5'))   # 拟合结果
            mt.setItem(row, 6, QTableWidgetItem('0.5'))     # 误差
        mt.setItem(row, 4, QTableWidgetItem(max_v))
        mt.setItem(row, 5, QTableWidgetItem(min_v))
    return mt


# ---------------------------------------------------------------------------
# 测试 Fitting.clearECCalculation
# ---------------------------------------------------------------------------
class TestClearECCalculation:
    """验证 Fitting.clearECCalculation 行为符合 B-1 合约。"""

    def test_clears_fitteddata_fittedresults_datainfo(self):
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        Fitting.clearECCalculation(obj)

        assert obj.fitteddata == [], (
            "fitteddata 应被清空,实际: %r" % (obj.fitteddata,)
        )
        assert obj.fittedresults == [], (
            "fittedresults 应被清空,实际: %r" % (obj.fittedresults,)
        )
        assert obj.resultsdataInfo == [], (
            "resultsdataInfo 应被清空,实际: %r" % (obj.resultsdataInfo,)
        )

    def test_clears_global_plotdata(self):
        import EIS.FittingFile.Fitting as fitting_mod
        from EIS.FittingFile.Fitting import Fitting

        # 写入「脏」全局状态
        fitting_mod.plotdata = ['x']
        fitting_mod.plotdataname = ['n']
        fitting_mod.outputlist = [1]

        obj = _make_fitting_like_mock()
        Fitting.clearECCalculation(obj)

        assert fitting_mod.plotdata == []
        assert fitting_mod.plotdataname == []
        assert fitting_mod.outputlist == []

    def test_clears_ecm_table_columns_3_and_6_only(self):
        """Bug #006 Phase 2: 7 列表格,只清 Fitted_Value(3) / Error [%](6) 列。"""
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        # 记录每次 setItem(row, col, item) 的 col
        cleared_cols = []
        obj.tab1.ECMtable.setItem.side_effect = (
            lambda r, c, item: cleared_cols.append(c)
        )

        Fitting.clearECCalculation(obj)

        # 应只清 3/6 列;每个 row 调一次,所以 3 行 × 2 列 = 6 次
        assert sorted(set(cleared_cols)) == [3, 6], (
            "ECMtable 应只清 col 3(Fitted_Value)和 col 6(Error [%]),实际: %r"
            % (sorted(set(cleared_cols)),)
        )
        assert obj.tab1.ECMtable.setItem.call_count == 3 * 2, (
            "ECMtable 应清 3 行 × 2 列 = 6 次,实际: %d"
            % obj.tab1.ECMtable.setItem.call_count
        )

    def test_preserves_circuit_params_connection(self):
        """保留模型结构:circuit / params / connectionTextEdit 不应被修改。"""
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()
        circuit_before = list(obj.circuit)

        Fitting.clearECCalculation(obj)

        # 保留
        assert obj.circuit == circuit_before, "circuit 不应被清空"
        assert obj.params is not None, "params 不应被清空"
        # connectionTextEdit 不应被修改
        obj.tab1.connectionTextEdit.setText.assert_not_called()
        obj.tab1.connectionTextEdit.clear.assert_not_called()

    def test_preserves_ecm_table_all_user_input_columns(self):
        """Bug #006 Phase 2: Name(0)/Comments(1)/Initial_Value(2)/Max(4)/Min(5) 列不应被 setItem。"""
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        cleared_cols = []
        obj.tab1.ECMtable.setItem.side_effect = (
            lambda r, c, item: cleared_cols.append(c)
        )

        Fitting.clearECCalculation(obj)

        forbidden = {0, 1, 2, 4, 5}  # 用户输入列
        used = set(cleared_cols)
        assert used.isdisjoint(forbidden), (
            "不应清 Name/Comments/Initial_Value/Max/Min 列,实际访问: %r"
            % (sorted(used & forbidden),)
        )


# ---------------------------------------------------------------------------
# 测试 Fitting.clearMTCalculation
# ---------------------------------------------------------------------------
class TestClearMTCalculation:
    """验证 Fitting.clearMTCalculation 行为符合 B-1 合约。"""

    def test_clears_fitteddata_fittedresults_datainfo(self):
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        Fitting.clearMTCalculation(obj)

        assert obj.fitteddata == []
        assert obj.fittedresults == []
        assert obj.resultsdataInfo == []

    def test_clears_global_plotdata(self):
        import EIS.FittingFile.Fitting as fitting_mod
        from EIS.FittingFile.Fitting import Fitting

        fitting_mod.plotdata = ['x']
        fitting_mod.plotdataname = ['n']
        fitting_mod.outputlist = [1]

        obj = _make_fitting_like_mock()
        Fitting.clearMTCalculation(obj)

        assert fitting_mod.plotdata == []
        assert fitting_mod.plotdataname == []
        assert fitting_mod.outputlist == []

    def test_clears_mt_table_columns_3_and_6_only(self):
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        cleared_cols = []
        obj.tab2.MTtable.setItem.side_effect = (
            lambda r, c, item: cleared_cols.append(c)
        )

        Fitting.clearMTCalculation(obj)

        assert sorted(set(cleared_cols)) == [3, 6], (
            "MTtable 应只清 col 3(Fitted_Value)和 col 6(Error [%]),"
            "实际: %r" % (sorted(set(cleared_cols)),)
        )
        assert obj.tab2.MTtable.setItem.call_count == 3 * 2

    def test_preserves_mt_model_structure(self):
        """termnamelist / modelterm / MTexpre / MTmultitermTextEdit / EP&DC 勾选 全部保留。"""
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        term_before = list(obj.termnamelist)
        modelterm_before = list(obj.modelterm)
        expre_before = list(obj.MTexpre)
        option_before = dict(obj.option)

        Fitting.clearMTCalculation(obj)

        assert obj.termnamelist == term_before
        assert obj.modelterm == modelterm_before
        assert obj.MTexpre == expre_before
        assert obj.option == option_before
        obj.tab2.MTmultitermTextEdit.setText.assert_not_called()
        obj.tab2.EPcheckBox.setChecked.assert_not_called()
        obj.tab2.DCcheckBox.setChecked.assert_not_called()

    def test_preserves_mt_table_all_user_input_columns(self):
        """Name(0)/Comments(1)/Initial_Value(2)/Max(4)/Min(5) 列不应被 setItem。"""
        from EIS.FittingFile.Fitting import Fitting
        obj = _make_fitting_like_mock()

        cleared_cols = []
        obj.tab2.MTtable.setItem.side_effect = (
            lambda r, c, item: cleared_cols.append(c)
        )

        Fitting.clearMTCalculation(obj)

        forbidden = {0, 1, 2, 4, 5}
        used = set(cleared_cols)
        assert used.isdisjoint(forbidden), (
            "不应清 Name/Comments/Initial_Value/Max/Min 列,实际访问: %r"
            % (sorted(used & forbidden),)
        )


# ---------------------------------------------------------------------------
# 测试 simulation.py 中的同名方法
# ---------------------------------------------------------------------------
class TestSimulationClearMethods:
    """simulation.py 没有 fitteddata/fittedresults,只清全局 plot 副本,不动 5 列表。"""

    def test_simulation_clearECCalculation_preserves_model(self):
        from EIS.SimulationFile.simulation import Simu
        obj = _make_fitting_like_mock()
        circuit_before = list(obj.circuit)
        params = obj.params

        Simu.clearECCalculation(obj)

        # 保留模型结构
        assert obj.circuit == circuit_before
        assert obj.params is params  # 同一对象,未重新赋值
        obj.tab1.connectionTextEdit.setText.assert_not_called()

    def test_simulation_clearECCalculation_does_not_touch_ecm_table(self):
        """Simulation 路径下 ECMtable 5 列无计算结果列,完全不动。"""
        from EIS.SimulationFile.simulation import Simu
        obj = _make_fitting_like_mock()

        Simu.clearECCalculation(obj)

        # ECMtable.setItem 不应被调用
        obj.tab1.ECMtable.setItem.assert_not_called()
        obj.tab1.ECMtable.clearContents.assert_not_called()
        obj.tab1.ECMtable.setRowCount.assert_not_called()

    def test_simulation_clearMTCalculation_preserves_model(self):
        from EIS.SimulationFile.simulation import Simu
        obj = _make_fitting_like_mock()
        MTparams = obj.MTparams
        option_before = dict(obj.option)

        Simu.clearMTCalculation(obj)

        assert obj.MTparams is MTparams
        assert obj.option == option_before
        obj.tab2.MTmultitermTextEdit.setText.assert_not_called()
        obj.tab2.EPcheckBox.setChecked.assert_not_called()
        obj.tab2.DCcheckBox.setChecked.assert_not_called()

    def test_simulation_clearMTCalculation_does_not_touch_mt_table(self):
        """Simulation 路径下 MTtable 5 列无计算结果列,完全不动。"""
        from EIS.SimulationFile.simulation import Simu
        obj = _make_fitting_like_mock()

        Simu.clearMTCalculation(obj)

        # MTtable 完全不动
        obj.tab2.MTtable.setItem.assert_not_called()
        obj.tab2.MTtable.clearContents.assert_not_called()
        obj.tab2.MTtable.setRowCount.assert_not_called()


# ---------------------------------------------------------------------------
# 真实 QTableWidget 集成测试
# ---------------------------------------------------------------------------
class TestRealTableIntegration:
    """用真实 QTableWidget 验证 clear 后能再次 Calculate(关键回归场景)。"""

    def test_Fitting_clearMTCalculation_on_7col_preserves_all_user_input(self, qapp):
        """Fitting 路径 7 列 MTtable(Bug #006 Phase 2 后):clear 后 Name/Comments/Initial/Max/Min 全保留。"""
        from EIS.FittingFile.Fitting import Fitting
        from types import SimpleNamespace

        mt = _build_7col_table(qapp, fitted_filled=True)
        obj = SimpleNamespace(
            fitteddata=['x'], fittedresults=['y'], resultsdataInfo=['z'],
            tab2=SimpleNamespace(MTtable=mt),
        )

        Fitting.clearMTCalculation(obj)

        # 验证 7 列结构未变
        assert mt.columnCount() == 7, f"columnCount 应保持 7,实际 {mt.columnCount()}"
        assert mt.rowCount() == 2, f"rowCount 应保持 2,实际 {mt.rowCount()}"

        # 保留所有用户输入列
        for row in range(2):
            assert mt.item(row, 0).text() in ('R1', 'C1'), f"row{row} Name 被误清"
            assert mt.item(row, 1).text() == 'comment', f"row{row} Comments 被误清"
            assert mt.item(row, 2).text() in ('100.0', '1e-6'), f"row{row} Initial_Value 被误清"
            assert mt.item(row, 4).text() in ('1e6', '1e-3'), f"row{row} Max 被误清"
            assert mt.item(row, 5).text() in ('1e-9', '1e-15'), f"row{row} Min 被误清"

        # 清空计算结果列
        for row in range(2):
            assert mt.item(row, 3).text() == '', f"row{row} Fitted_Value 应清空"
            assert mt.item(row, 6).text() == '', f"row{row} Error [%] 应清空"

    def test_Fitting_clearECCalculation_on_7col_preserves_user_input(self, qapp):
        """Fitting 路径 7 列 ECMtable(Bug #006 Phase 2 后):clear 后用户输入列保留(回归保护)。"""
        from EIS.FittingFile.Fitting import Fitting
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
        from types import SimpleNamespace

        # 构造 7 列 ECMtable
        ecm = QTableWidget()
        ecm.setColumnCount(7)
        ecm.setHorizontalHeaderLabels(
            ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
        )
        ecm.setRowCount(1)
        ecm.setItem(0, 0, QTableWidgetItem('R1'))
        ecm.setItem(0, 1, QTableWidgetItem('comment'))
        ecm.setItem(0, 2, QTableWidgetItem('100.0'))
        ecm.setItem(0, 3, QTableWidgetItem('99.5'))   # 拟合结果
        ecm.setItem(0, 4, QTableWidgetItem('1e6'))
        ecm.setItem(0, 5, QTableWidgetItem('1e-9'))
        ecm.setItem(0, 6, QTableWidgetItem('0.5'))     # Error

        obj = SimpleNamespace(
            fitteddata=['x'], fittedresults=['y'], resultsdataInfo=['z'],
            tab1=SimpleNamespace(ECMtable=ecm),
        )

        Fitting.clearECCalculation(obj)

        # 用户输入列必须保留
        assert ecm.item(0, 0).text() == 'R1', "Name 列被误清"
        assert ecm.item(0, 1).text() == 'comment', "Comments 列被误清"
        assert ecm.item(0, 2).text() == '100.0', "Initial_Value 列被误清"
        assert ecm.item(0, 4).text() == '1e6', "Max 列被误清"
        assert ecm.item(0, 5).text() == '1e-9', "Min 列被误清"
        # 拟合结果列已清空
        assert ecm.item(0, 3).text() == '', "Fitted_Value 应清空"
        assert ecm.item(0, 6).text() == '', "Error [%] 应清空"

    def test_simulation_clearMTCalculation_on_3col_does_nothing_to_table(self, qapp):
        """Simulation 路径 3 列 MTtable(Bug #006 Phase 2.5 后):clear 完全不动表格(所有列都是用户输入)。"""
        from EIS.SimulationFile.simulation import Simu
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
        from types import SimpleNamespace

        # 构造 3 列 MTtable(simulation 路径,Phase 2.5 移除 Max/Min)
        mt = QTableWidget()
        mt.setColumnCount(3)
        mt.setHorizontalHeaderLabels(['Name', 'Comments', 'Initial_Value'])
        mt.setRowCount(2)
        for row, (name, init_v) in enumerate(
            [('R1', '100.0'),
             ('C1', '1e-6')]
        ):
            mt.setItem(row, 0, QTableWidgetItem(name))
            mt.setItem(row, 1, QTableWidgetItem('comment'))
            mt.setItem(row, 2, QTableWidgetItem(init_v))

        # 记录 clear 前状态
        before = [[mt.item(r, c).text() if mt.item(r, c) else '' for c in range(3)]
                  for r in range(2)]

        obj = SimpleNamespace(
            tab2=SimpleNamespace(MTtable=mt),
        )

        Simu.clearMTCalculation(obj)

        # 表格完全不变
        after = [[mt.item(r, c).text() if mt.item(r, c) else '' for c in range(3)]
                 for r in range(2)]
        assert before == after, (
            "Simulation 路径 clearMTCalculation 不应改动 3 列 MTtable.\n"
            f"before={before}\nafter={after}"
        )
        # 关键:列数保持 3(不能因 setItem 越界而自动扩展)
        assert mt.columnCount() == 3, f"columnCount 应保持 3,实际 {mt.columnCount()}"


# ---------------------------------------------------------------------------
# Connect 绑定检查：确保 Fitting / Simu 把对应按钮连到对应槽
# ---------------------------------------------------------------------------
class TestSignalConnections:
    """静态校验 connect 语句中按钮→槽的映射。"""

    def test_fitting_tab1_clearBtn_connects_to_clearECCalculation(self):
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        assert 'self.tab1.clearBtn.clicked.connect(self.clearECCalculation)' in src, (
            "Fitting.py 缺少: self.tab1.clearBtn.clicked.connect(self.clearECCalculation)"
        )
        # 不应再 connect 到旧的 clearCalculation
        assert 'self.tab1.clearBtn.clicked.connect(self.clearCalculation)' not in src, (
            "Fitting.py 不应再 connect 到已删除的 clearCalculation"
        )

    def test_fitting_tab2_clearBtn_connects_to_clearMTCalculation(self):
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        assert 'self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)' in src, (
            "Fitting.py 缺少: self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)"
        )

    def test_simulation_tab1_clearBtn_connects_to_clearECCalculation(self):
        from EIS.SimulationFile import simulation
        src = open(simulation.__file__, 'r', encoding='utf-8').read()
        assert 'self.tab1.clearBtn.clicked.connect(self.clearECCalculation)' in src
        assert 'self.tab1.clearBtn.clicked.connect(self.clearCalculation)' not in src

    def test_simulation_tab2_clearBtn_connects_to_clearMTCalculation(self):
        from EIS.SimulationFile import simulation
        src = open(simulation.__file__, 'r', encoding='utf-8').read()
        assert 'self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)' in src

    def test_old_clearCalculation_removed_from_fitting(self):
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        # 旧的空函数 `def clearCalculation(self): return` 应被清除
        assert 'def clearCalculation(self):' not in src, (
            "Fitting.py 仍残留旧的 clearCalculation 定义,应已替换为 clearECCalculation"
        )

    def test_clear_uses_cleared_cols_3_6(self):
        """Bug #006 Phase 2 回归保护:Fitting 路径 clear 槽应清 col=3,6(7 列表格)。"""
        from EIS.FittingFile import Fitting
        from EIS.SimulationFile import simulation

        # Fitting 路径:7 列表格,应清 (3, 6) 列
        fitting_src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        for method in ('clearECCalculation', 'clearMTCalculation'):
            start = fitting_src.find(f'def {method}')
            if start == -1:
                continue
            end = fitting_src.find('\n    def ', start + 1)
            if end == -1:
                end = len(fitting_src)
            body = fitting_src[start:end]
            assert '(3, 6)' in body, (
                f"Fitting.{method} 应使用 cleared_cols=(3, 6) 清 7 列表格"
            )
            # 不应再含 (3, 7)(原 8 列表格假设)
            assert '(3, 7)' not in body, (
                f"Fitting.{method} 仍含 (3, 7) — 已切换为 7 列表格,应改为 (3, 6)"
            )

        # Simulation 路径:5 列表格,clear 方法不应动表(本就不写 cleared_cols)
        simu_src = open(simulation.__file__, 'r', encoding='utf-8').read()
        for method in ('clearECCalculation', 'clearMTCalculation'):
            start = simu_src.find(f'def {method}')
            if start == -1:
                continue
            end = simu_src.find('\n    def ', start + 1)
            if end == -1:
                end = len(simu_src)
            body = simu_src[start:end]
            # 5 列 simu 模式:不应含 cleared_cols(原 6/8 列表格遗留)
            assert 'cleared_cols' not in body, (
                f"Simulation.{method} 仍含 cleared_cols — 5 列表格无需清列"
            )
            # 不应再含 (3, 7)(原 8 列表格假设)
            assert '(3, 7)' not in body, (
                f"Simulation.{method} 仍含 (3, 7) — 应已删除"
            )
