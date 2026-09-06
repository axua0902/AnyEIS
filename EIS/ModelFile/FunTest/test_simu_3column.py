# -*- coding: utf-8 -*-
"""
测试 Bug #006 Phase 2.5: Simulation 模式表格列结构为 3 列
验证 Max/Min 列在 simu 模式下已移除,只保留 Name/Comments/Initial_Value

Created: 2026-09-06
Related: update.md "关于 simulation 模式表头的修改"
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication
    from EIS.ModelFile.ECUI import Tab1Content
    from EIS.ModelFile.MTMUI import Tab2Content
except ImportError as e:
    pytest.skip(f"Cannot import required modules: {e}", allow_module_level=True)


class TestSimulationTableStructure:
    """测试 Simulation 模式下表格列结构"""

    @pytest.fixture(scope="class")
    def qapp(self):
        """创建 QApplication 实例供所有测试共享"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
        # 不调用 app.quit(),避免影响后续测试

    def test_ECM_simu_mode_has_3_columns(self, qapp):
        """验证 ECM 表格在 simu 模式下有且仅有 3 列"""
        tab1 = Tab1Content()
        tab1.setECMTableHeader('simu')
        
        assert tab1.ECMtable.columnCount() == 3, \
            f"ECMtable in simu mode should have 3 columns, got {tab1.ECMtable.columnCount()}"
        
        # 验证列标题
        expected_labels = ['Name', 'Comments', 'Initial_Value']
        for col in range(3):
            actual_label = tab1.ECMtable.horizontalHeaderItem(col).text()
            assert actual_label == expected_labels[col], \
                f"ECMtable simu col {col}: expected '{expected_labels[col]}', got '{actual_label}'"

    def test_ECM_fit_mode_has_7_columns(self, qapp):
        """验证 ECM 表格在 fit 模式下有 7 列"""
        tab1 = Tab1Content()
        tab1.setECMTableHeader('fit')
        
        assert tab1.ECMtable.columnCount() == 7, \
            f"ECMtable in fit mode should have 7 columns, got {tab1.ECMtable.columnCount()}"
        
        # 验证列标题
        expected_labels = ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
        for col in range(7):
            actual_label = tab1.ECMtable.horizontalHeaderItem(col).text()
            assert actual_label == expected_labels[col], \
                f"ECMtable fit col {col}: expected '{expected_labels[col]}', got '{actual_label}'"

    def test_MT_simu_mode_has_3_columns(self, qapp):
        """验证 MT 表格在 simu 模式下有且仅有 3 列"""
        tab2 = Tab2Content()
        tab2.setMTMTableHeader('simu')
        
        assert tab2.MTtable.columnCount() == 3, \
            f"MTtable in simu mode should have 3 columns, got {tab2.MTtable.columnCount()}"
        
        # 验证列标题
        expected_labels = ['Name', 'Comments', 'Initial_Value']
        for col in range(3):
            actual_label = tab2.MTtable.horizontalHeaderItem(col).text()
            assert actual_label == expected_labels[col], \
                f"MTtable simu col {col}: expected '{expected_labels[col]}', got '{actual_label}'"

    def test_MT_fit_mode_has_7_columns(self, qapp):
        """验证 MT 表格在 fit 模式下有 7 列"""
        tab2 = Tab2Content()
        tab2.setMTMTableHeader('fit')
        
        assert tab2.MTtable.columnCount() == 7, \
            f"MTtable in fit mode should have 7 columns, got {tab2.MTtable.columnCount()}"
        
        # 验证列标题
        expected_labels = ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
        for col in range(7):
            actual_label = tab2.MTtable.horizontalHeaderItem(col).text()
            assert actual_label == expected_labels[col], \
                f"MTtable fit col {col}: expected '{expected_labels[col]}', got '{actual_label}'"


class TestSimulationColumnReadLogic:
    """验证 simulation.py 只读 col 0 和 col 2"""

    def test_ECM_simulation_reads_only_col_0_and_2(self):
        """静态验证:simulation.py ECMcalculation 只访问 col 0 (Name) 和 col 2 (Initial_Value)"""
        simulation_file = project_root / "EIS" / "SimulationFile" / "simulation.py"
        assert simulation_file.exists(), f"simulation.py not found at {simulation_file}"
        
        with open(simulation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定位到 ECMcalculation 方法(约 L170-L190)
        # 验证只有 .item(temp - 1, 0) 和 .item(temp - 1, 2) 被访问
        assert "self.tab1.ECMtable.item(temp - 1, 0).text()" in content, \
            "ECMcalculation should read col 0 (Name)"
        assert "self.tab1.ECMtable.item(temp - 1, 2).text()" in content, \
            "ECMcalculation should read col 2 (Initial_Value)"
        
        # 确保不读 col 3, 4 (在旧 5 列布局中是 Max/Min)
        # 注意:在新 3 列布局中,col 3/4 根本不存在
        forbidden_patterns = [
            "self.tab1.ECMtable.item(temp - 1, 3)",
            "self.tab1.ECMtable.item(temp - 1, 4)",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in content, \
                f"ECMcalculation should NOT read {pattern} (Max/Min are not used in simulation)"

    def test_MT_simulation_reads_only_col_0_and_2(self):
        """静态验证:simulation.py MTcalculation 只访问 col 0 (Name) 和 col 2 (Initial_Value)"""
        simulation_file = project_root / "EIS" / "SimulationFile" / "simulation.py"
        
        with open(simulation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定位到 MTcalculation 方法(约 L310-L320)
        assert "self.tab2.MTtable.item(temp - 1, 0).text()" in content, \
            "MTcalculation should read col 0 (Name)"
        assert "self.tab2.MTtable.item(temp - 1, 2).text()" in content, \
            "MTcalculation should read col 2 (Initial_Value)"
        
        # 确保不读 col 3, 4
        forbidden_patterns = [
            "self.tab2.MTtable.item(temp - 1, 3)",
            "self.tab2.MTtable.item(temp - 1, 4)",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in content, \
                f"MTcalculation should NOT read {pattern} (Max/Min are not used in simulation)"


class TestDocstringConsistency:
    """验证文档字符串与实际列数一致"""

    def test_clearECCalculation_docstring_mentions_3_columns(self):
        """验证 clearECCalculation 文档说明 ECMtable 为 3 列"""
        simulation_file = project_root / "EIS" / "SimulationFile" / "simulation.py"
        
        with open(simulation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证 clearECCalculation 的 docstring 提到 "3 列"
        assert "setECMTableHeader('simu') 初始化为 3 列" in content, \
            "clearECCalculation docstring should mention 3 columns"
        assert "(Name/Comments/Initial_Value)" in content, \
            "clearECCalculation docstring should list the 3 column names"

    def test_clearMTCalculation_docstring_mentions_3_columns(self):
        """验证 clearMTCalculation 文档说明 MTtable 为 3 列"""
        simulation_file = project_root / "EIS" / "SimulationFile" / "simulation.py"
        
        with open(simulation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证 clearMTCalculation 的 docstring 提到 "3 列"(已在本次会话中修复)
        assert "setMTMTableHeader('simu') 初始化为 3 列" in content, \
            "clearMTCalculation docstring should mention 3 columns"
        
        # 确保不再说 "5 列"
        # 注意:这个检查可能误伤其它上下文中合法的 "5 列",所以只在 clearMTCalculation 附近搜索
        lines = content.splitlines()
        in_clearMT = False
        for i, line in enumerate(lines):
            if "def clearMTCalculation(self):" in line:
                in_clearMT = True
            elif in_clearMT and line.strip().startswith("def "):
                in_clearMT = False
            
            if in_clearMT and "5 列" in line and "MTtable" in line:
                pytest.fail(f"Line {i+1} in clearMTCalculation still mentions '5 列': {line.strip()}")


class TestSetHeaderMethodsExist:
    """验证 setECMTableHeader 和 setMTMTableHeader 方法存在且被正确调用"""

    def test_ECUI_has_setECMTableHeader_method(self):
        """验证 ECUI.py 包含 setECMTableHeader 方法"""
        ecui_file = project_root / "EIS" / "ModelFile" / "ECUI.py"
        assert ecui_file.exists(), f"ECUI.py not found at {ecui_file}"
        
        with open(ecui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "def setECMTableHeader(self, mode='fit'):" in content, \
            "ECUI.py should have setECMTableHeader method"

    def test_MTMUI_has_setMTMTableHeader_method(self):
        """验证 MTMUI.py 包含 setMTMTableHeader 方法"""
        mtmui_file = project_root / "EIS" / "ModelFile" / "MTMUI.py"
        assert mtmui_file.exists(), f"MTMUI.py not found at {mtmui_file}"
        
        with open(mtmui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "def setMTMTableHeader(self, mode='fit'):" in content, \
            "MTMUI.py should have setMTMTableHeader method"

    def test_simulation_calls_setECMTableHeader_with_simu(self):
        """验证 simulation.py 使用 'simu' 参数调用 setECMTableHeader"""
        simulation_file = project_root / "EIS" / "SimulationFile" / "simulation.py"
        
        with open(simulation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "self.tab1.setECMTableHeader('simu')" in content, \
            "simulation.py should call setECMTableHeader('simu')"

    def test_simulation_calls_setMTMTableHeader_with_simu(self):
        """验证 simulation.py 使用 'simu' 参数调用 setMTMTableHeader"""
        simulation_file = project_root / "EIS" / "SimulationFile" / "simulation.py"
        
        with open(simulation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "self.tab2.setMTMTableHeader('simu')" in content, \
            "simulation.py should call setMTMTableHeader('simu')"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
