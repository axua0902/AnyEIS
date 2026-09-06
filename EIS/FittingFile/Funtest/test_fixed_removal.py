# -*- coding: utf-8 -*-
"""
test_fixed_removal.py
=====================

验证 Bug #006 Phase 2 修复:彻底删除 Fixed 死列。

设计目标:
  - `Fixed` 复选框在全工程都没有任何代码路径读取它(纯 UI 摆设)
  - 删除后:列数 8→7(fit),6→5(simu)
  - fit 模式列结构(7 列):Name, Comments, Initial_Value, Fitted_Value, Max, Min, Error [%]
  - simu 模式列结构(5 列):Name, Comments, Initial_Value, Max, Min

覆盖范围:
  1. ECUI.setECMTableHeader('fit' / 'simu') 输出列数与顺序
  2. MTMUI.setMTMTableHeader('fit' / 'simu') 输出列数与顺序
  3. ECMFunctions.py 不再含 'Fixed' 字符串与 fixed_checkbox 创建
  4. ECMFunctions.clearECMModel 不再硬编码 8 列
  5. Fitting.py processECMResults / processMTResults 写入 Error [%] 至 col 6
  6. Fitting.py 不再 setItem 到 col 7 (原 8 列表格 Fixed 后的位置)

策略:
  - 不实例化 ECUI / MTMUI / Fitting(避免触发重依赖)
  - 用 pytest 的 monkeypatch + 静态源码扫描验证

运行:
    pytest EIS/FittingFile/Funtest/test_fixed_removal.py -v
"""
import os
import sys
import pytest

# 让顶层 import 可用：EIS/FittingFile/Funtest/ -> AnyEIS/
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


@pytest.fixture(scope="module")
def ecm_ui(qapp):
    """构造真实的 ECUI.Tab1Content 实例(无外部依赖,直接可用)。"""
    from EIS.ModelFile.ECUI import Tab1Content
    return Tab1Content()


@pytest.fixture(scope="module")
def mtm_ui(qapp):
    """构造真实的 MTMUI.Tab2Content 实例。"""
    from EIS.ModelFile.MTMUI import Tab2Content
    return Tab2Content()


# ---------------------------------------------------------------------------
# 1. 列结构测试
# ---------------------------------------------------------------------------
class TestColumnStructure:
    """验证 fit/simu 模式列结构正确。"""

    def test_ECM_fit_mode_has_7_columns_in_order(self, ecm_ui):
        """fit 模式(7 列):Name, Comments, Initial_Value, Fitted_Value, Max, Min, Error [%]。"""
        ecm_ui.setECMTableHeader('fit')
        headers = [
            ecm_ui.ECMtable.horizontalHeaderItem(i).text()
            for i in range(ecm_ui.ECMtable.columnCount())
        ]
        assert headers == [
            'Name', 'Comments', 'Initial_Value', 'Fitted_Value',
            'Max', 'Min', 'Error [%]'
        ], f"ECMtable fit 模式表头不符,实际: {headers}"
        assert ecm_ui.ECMtable.columnCount() == 7
        # Fixed 不应再出现
        assert 'Fixed' not in headers, "Fixed 列不应再出现"

    def test_ECM_simu_mode_has_3_columns_in_order(self, ecm_ui):
        """simu 模式(Bug #006 Phase 2.5: 3 列):Name, Comments, Initial_Value。"""
        ecm_ui.setECMTableHeader('simu')
        headers = [
            ecm_ui.ECMtable.horizontalHeaderItem(i).text()
            for i in range(ecm_ui.ECMtable.columnCount())
        ]
        assert headers == [
            'Name', 'Comments', 'Initial_Value'
        ], f"ECMtable simu 模式表头不符,实际: {headers}"
        assert ecm_ui.ECMtable.columnCount() == 3
        # Fixed/Fitted/Error/Max/Min 均不应出现(Phase 2.5 移除 Max/Min)
        for forbidden in ('Fixed', 'Fitted_Value', 'Error [%]', 'Max', 'Min'):
            assert forbidden not in headers, (
                f"{forbidden} 列不应出现在 simu 模式"
            )

    def test_MTM_fit_mode_has_7_columns_in_order(self, mtm_ui):
        """fit 模式(7 列):与 ECMtable 对称。"""
        mtm_ui.setMTMTableHeader('fit')
        headers = [
            mtm_ui.MTtable.horizontalHeaderItem(i).text()
            for i in range(mtm_ui.MTtable.columnCount())
        ]
        assert headers == [
            'Name', 'Comments', 'Initial_Value', 'Fitted_Value',
            'Max', 'Min', 'Error [%]'
        ], f"MTtable fit 模式表头不符,实际: {headers}"
        assert mtm_ui.MTtable.columnCount() == 7
        assert 'Fixed' not in headers, "Fixed 列不应再出现"

    def test_MTM_simu_mode_has_3_columns_in_order(self, mtm_ui):
        """simu 模式(Bug #006 Phase 2.5: 3 列):与 ECMtable 对称。"""
        mtm_ui.setMTMTableHeader('simu')
        headers = [
            mtm_ui.MTtable.horizontalHeaderItem(i).text()
            for i in range(mtm_ui.MTtable.columnCount())
        ]
        assert headers == [
            'Name', 'Comments', 'Initial_Value'
        ], f"MTtable simu 模式表头不符,实际: {headers}"
        assert mtm_ui.MTtable.columnCount() == 3
        for forbidden in ('Fixed', 'Fitted_Value', 'Error [%]', 'Max', 'Min'):
            assert forbidden not in headers, (
                f"{forbidden} 列不应出现在 simu 模式"
            )


# ---------------------------------------------------------------------------
# 2. ECMFunctions 源码扫描
# ---------------------------------------------------------------------------
class TestECMFunctionsSource:
    """验证 ECMFunctions.py 不再含 Fixed 列处理。"""

    def test_no_Fixed_in_table_headers(self):
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        # 任何 setHorizontalHeaderLabels 调用都不应再含 'Fixed'
        import re
        label_calls = re.findall(
            r"setHorizontalHeaderLabels\s*\(\s*\[([^\]]+)\]\s*\)", src
        )
        for call in label_calls:
            assert "'Fixed'" not in call and '"Fixed"' not in call, (
                f"setHorizontalHeaderLabels 中不应含 'Fixed',实际: {call}"
            )

    def test_no_setColumnCount_8(self):
        """不应再硬编码 setColumnCount(8) —— 7 列表格才对。"""
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        assert 'setColumnCount(8)' not in src, (
            "ECMFunctions.py 仍硬编码 setColumnCount(8),应改为 setECMTableHeader('fit')"
        )

    def test_no_fixed_checkbox_creation(self):
        """不应再创建 fixed_checkbox QTableWidgetItem。"""
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        assert 'fixed_checkbox' not in src, (
            "ECMFunctions.py 仍创建 fixed_checkbox,Fixed 死列应已删除"
        )

    def test_no_checkState_access(self):
        """不应再调用 .checkState()(原 Fixed 复选框用)。"""
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        assert '.checkState()' not in src, (
            "ECMFunctions.py 仍调用 .checkState(),Fixed 死列应已删除"
        )

    def test_no_Qt_Import(self):
        """Fixed 删除后,Qt import 不再被 ECMFunctions.py 使用,应可移除(回归保护)。"""
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        # 若 ECMFunctions.py 真的不再用 Qt,import 应已被删除
        # 仍允许保留(因为 import 不会被静态检查),但如果已删除则是好的
        # 这里只检查不再使用 Qt.*,而 Qt 的 import 可有可无
        # 留作可选清理,不强制
        pass


# ---------------------------------------------------------------------------
# 3. ECUI/MTMUI 源码扫描
# ---------------------------------------------------------------------------
class TestUISource:
    """验证 ECUI/MTMUI 不再有 8 列表格硬编码。"""

    def test_ECUI_no_Fixed_in_init(self):
        from EIS.ModelFile import ECUI
        src = open(ECUI.__file__, 'r', encoding='utf-8').read()
        # ECUI.__init__ 内的 ECMtable 初始化不应再硬编码 8 列含 Fixed
        # 已统一通过 setECMTableHeader('fit') 调用
        # 检查没有 8 列硬编码
        assert 'setColumnCount(8)' not in src, (
            "ECUI.py 仍硬编码 setColumnCount(8),应使用 setECMTableHeader('fit')"
        )
        # 应通过 setECMTableHeader('fit') 初始化
        assert "self.setECMTableHeader('fit')" in src, (
            "ECUI.py 应通过 setECMTableHeader('fit') 初始化表头"
        )

    def test_MTMUI_no_Fixed_in_init(self):
        from EIS.ModelFile import MTMUI
        src = open(MTMUI.__file__, 'r', encoding='utf-8').read()
        assert 'setColumnCount(8)' not in src, (
            "MTMUI.py 仍硬编码 setColumnCount(8),应使用 setMTMTableHeader('fit')"
        )
        assert "self.setMTMTableHeader('fit')" in src, (
            "MTMUI.py 应通过 setMTMTableHeader('fit') 初始化表头"
        )


# ---------------------------------------------------------------------------
# 4. Fitting.py 源码扫描
# ---------------------------------------------------------------------------
class TestFittingSource:
    """验证 Fitting.py 写入 Error [%] 至 col 6 (7 列表格位置)。"""

    def test_processECMResults_writes_Error_to_col_6(self):
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        # processECMResults 应在 7 列表格下写入 col=6
        assert 'self.ECMtableWrite(paramsname, err_str, 6)' in src or \
               'self.ECMtableWrite(paramsname, errbartemp, 6)' in src, (
            "Fitting.py processECMResults 应将 Error [%] 写入 col 6(7 列表格)"
        )
        # 不应再写入 col 7 (原 8 列表格位置)
        assert 'self.ECMtableWrite(paramsname, errbartemp, 7)' not in src, (
            "Fitting.py processECMResults 仍写入 col 7,应改为 col 6"
        )
        assert 'self.ECMtableWrite(paramsname, err_str, 7)' not in src, (
            "Fitting.py processECMResults 仍写入 col 7,应改为 col 6"
        )

    def test_processMTResults_writes_Error_to_col_6(self):
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        assert 'self.MTtableWrite(paramsname, err_str, 6)' in src or \
               'self.MTtableWrite(paramsname, errbartemp, 6)' in src, (
            "Fitting.py processMTResults 应将 Error [%] 写入 col 6(7 列表格)"
        )
        assert 'self.MTtableWrite(paramsname, errbartemp, 7)' not in src, (
            "Fitting.py processMTResults 仍写入 col 7,应改为 col 6"
        )
        assert 'self.MTtableWrite(paramsname, err_str, 7)' not in src, (
            "Fitting.py processMTResults 仍写入 col 7,应改为 col 6"
        )

    def test_clear_uses_cols_3_6(self):
        from EIS.FittingFile import Fitting
        src = open(Fitting.__file__, 'r', encoding='utf-8').read()
        # 7 列表格,clearECCalculation / clearMTCalculation 应使用 (3, 6)
        assert 'cleared_cols = (3, 6)' in src, (
            "Fitting.py clear 槽应使用 cleared_cols=(3, 6) 清 7 列表格"
        )


# ---------------------------------------------------------------------------
# 5. ECMFunctions.py: clearECMModel 通过 setECMTableHeader('fit') 重置
# ---------------------------------------------------------------------------
class TestClearECMModel:
    """验证 clearECMModel 不再硬编码 8 列。"""

    def test_clearECMModel_uses_setECMTableHeader(self):
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        # clearECMModel 中应通过 setECMTableHeader('fit') 统一重置
        # 找到 def clearECMModel 函数体
        start = src.find('def clearECMModel')
        assert start != -1, "未找到 clearECMModel 定义"
        end = src.find('\n    def ', start + 1)
        if end == -1:
            end = len(src)
        body = src[start:end]
        assert "setECMTableHeader('fit')" in body, (
            "clearECMModel 应通过 setECMTableHeader('fit') 统一重置表头"
        )
        assert 'setColumnCount(8)' not in body, (
            "clearECMModel 仍硬编码 setColumnCount(8)"
        )
        assert "'Fixed'" not in body, (
            "clearECMModel 函数体不应再含 'Fixed'"
        )


# ---------------------------------------------------------------------------
# 6. ECMFunctions: load_ecm_model_to_ui 不再创建 Fixed 复选框
# ---------------------------------------------------------------------------
class TestLoadECMModelToUI:
    """验证 load_ecm_model_to_ui 不再创建 Fixed 复选框。"""

    def test_load_ecm_model_to_ui_creates_7_columns(self):
        """模型加载时应根据当前 ECMtable 列数自适应(Bug #006 Phase 2.5)。"""
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        start = src.find('def load_ecm_model_to_ui')
        assert start != -1
        end = src.find('\n\n\n', start + 1)
        if end == -1:
            end = len(src)
        body = src[start:end]

        # Phase 2.5: 不再硬编码 headers,而是根据 table.columnCount() 判断
        assert "ncols = table.columnCount()" in body, (
            "load_ecm_model_to_ui 应根据 columnCount() 自适应"
        )
        assert "is_full = ncols >= 7" in body, (
            "load_ecm_model_to_ui 应判断 is_full 来区分 fit/simu 模式"
        )
        # 不应再含 Fixed 列
        assert "'Fixed'" not in body, (
            "load_ecm_model_to_ui 不应再含 'Fixed' 列"
        )
        assert "fixed_checkbox" not in body, (
            "load_ecm_model_to_ui 不应再创建 fixed_checkbox"
        )
        # 应包含 simu 模式的隐藏持久化逻辑
        assert "_ecm_param_bounds" in body, (
            "load_ecm_model_to_ui 应在 simu 模式下持久化 min/max 到隐藏字典"
        )


# ---------------------------------------------------------------------------
# 7. create_ecm_model_json 不再写 'fixed' 字段,且根据列数自适应读取 min/max
# ---------------------------------------------------------------------------
class TestCreateECMModelJson:
    """验证 create_ecm_model_json 自适应读取 min/max(Bug #006 Phase 2.5)。"""

    def test_create_ecm_model_json_adaptive_read(self):
        from EIS.ModelFile import ECMFunctions
        src = open(ECMFunctions.__file__, 'r', encoding='utf-8').read()
        start = src.find('def create_ecm_model_json')
        assert start != -1
        end = src.find('\n\n\n', start + 1)
        if end == -1:
            end = len(src)
        body = src[start:end]

        # Phase 2.5: 根据 table.columnCount() 判断
        assert "ncols = table.columnCount()" in body, (
            "create_ecm_model_json 应根据 columnCount() 自适应"
        )
        assert "is_full = ncols >= 7" in body, (
            "create_ecm_model_json 应判断 is_full 来区分 fit/simu 模式"
        )
        # 不应再含 'fixed' 字段
        assert "'fixed'" not in body, (
            "create_ecm_model_json 不应再含 'fixed' header"
        )
        # 也不应有 header == 'fixed' 条件分支
        assert "header == 'fixed'" not in body, (
            "create_ecm_model_json 不应再有 'fixed' 分支"
        )
        # 应包含 simu 模式从隐藏字典读取的逻辑
        assert "_ecm_param_bounds" in body, (
            "create_ecm_model_json 应在 simu 模式下从隐藏字典读 min/max"
        )
