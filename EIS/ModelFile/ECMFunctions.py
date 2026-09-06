# -*- coding: utf-8 -*-
"""
ECM.py - ECM模型的业务逻辑和JSON序列化

包含ECM模型的业务逻辑（按钮处理、文件保存/加载）和JSON序列化和反序列化功能
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from lmfit import Parameters


def parse_circuit_string_to_list(circuit_string):
    """
    将电路字符串解析为标记列表

    参数:
        circuit_string: 电路字符串，如 "R1+p(R2,C2)"

    返回:
        circuit_list: 标记列表，如 ['R1', '+', 'p(', 'R2', ',', 'C2', ')']
    """
    if not circuit_string:
        return []

    circuit_list = []
    i = 0
    while i < len(circuit_string):
        char = circuit_string[i]
        if char in '(),+':
            circuit_list.append(char)
            i += 1
        elif char == 'p':
            # 并联符号 p(
            circuit_list.append('p(')
            i += 2  # 跳过 'p('
        elif char.isalpha():
            # 元件名称 (R, C, L 等开头的标识符)
            j = i
            while j < len(circuit_string) and (circuit_string[j].isalnum() or circuit_string[j] == '_'):
                j += 1
            circuit_list.append(circuit_string[i:j])
            i = j
        elif circuit_string[i:i+1] in [' ', '\t', '\n']:
            # 跳过空白字符
            i += 1
        else:
            i += 1
    return circuit_list


# =============================================================================
# Handler Functions - JSON序列化/反序列化
# =============================================================================

def create_ecm_model_json(obj):
    """
    从UI对象创建ECM模型的JSON数据

    参数:
        obj: 包含以下属性的对象:
            - tab1: ECUI.Tab1Content 实例
            - current_model_path: 当前模型文件路径
            - circuit: 电路元件列表
            - ECMparams: lmfit Parameters 对象
            - _ecm_param_bounds: (可选) Bug #006 Phase 2.5 simu 隐藏持久化字典

    返回:
        dict: ECM模型的JSON数据

    说明(Bug #006 Phase 2.5):
        根据当前 ECMtable 的列数自适应读取:
        - 7 列 (fit 模式): 从 col 4/5 读 min/max
        - 3 列 (simu 模式): 表内无 min/max, 从 `obj._ecm_param_bounds` 隐藏字典取
    """
    model_name = "Untitled Model"
    if hasattr(obj, 'current_model_path') and obj.current_model_path:
        model_name = os.path.splitext(os.path.basename(obj.current_model_path))[0]

    model_data = {
        "version": "1.0",
        "model_type": "ECM",
        "model_name": model_name,
        "file_path": getattr(obj, 'current_model_path', "") or "",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "frequency": {
            "min": float(obj.tab1.ECMlowfreqTextEdit.text()) if obj.tab1.ECMlowfreqTextEdit.text() else 0.1,
            "max": float(obj.tab1.ECMupfreqTextEdit.text()) if obj.tab1.ECMupfreqTextEdit.text() else 1e9,
            "points": 50,
            "unit": "Hz"
        },
        "circuit_string": obj.tab1.connectionTextEdit.text() or "",
        "parameters": []
    }

    table = obj.tab1.ECMtable
    ncols = table.columnCount()
    is_full = ncols >= 7
    hidden = getattr(obj, '_ecm_param_bounds', None) or {}

    for row in range(table.rowCount()):
        # col 0: Name (必有)
        name_item = table.item(row, 0)
        name = name_item.text() if name_item else ""
        if not name:
            continue

        # col 1: Comments
        comments_item = table.item(row, 1)
        display_name = comments_item.text() if comments_item else ""

        # col 2: Initial_Value
        value_item = table.item(row, 2)
        try:
            value = float(value_item.text()) if value_item and value_item.text() else 0.0
        except ValueError:
            value = 0.0

        param = {
            "name": name,
            "display_name": display_name,
            "value": value,
            "unit": "",
        }

        if is_full:
            # 7 列 fit 模式: 从 col 4/5 读 min/max
            max_item = table.item(row, 4)
            min_item = table.item(row, 5)
            try:
                param["max"] = float(max_item.text()) if max_item and max_item.text() else 0.0
            except ValueError:
                param["max"] = 0.0
            try:
                param["min"] = float(min_item.text()) if min_item and min_item.text() else 0.0
            except ValueError:
                param["min"] = 0.0
        else:
            # 3 列 simu 模式: 从隐藏字典取 min/max/unit
            bound = hidden.get(name, {})
            try:
                param["min"] = float(bound.get('min', 0)) if bound.get('min') not in (None, "") else 0.0
            except (TypeError, ValueError):
                param["min"] = 0.0
            try:
                param["max"] = float(bound.get('max', 0)) if bound.get('max') not in (None, "") else 0.0
            except (TypeError, ValueError):
                param["max"] = 0.0
            param["unit"] = bound.get('unit', "")

        model_data["parameters"].append(param)

    return model_data


def load_ecm_model_to_ui(obj, model_data):
    """
    将ECM模型JSON数据加载到UI

    参数:
        obj: UI对象
        model_data: dict, ECM模型的JSON数据

    说明(Bug #006 Phase 2.5):
        根据当前 ECMtable 的列数自适应写入:
        - 7 列 (fit 模式): 写入全部 7 列(Name/Comments/Initial/Fitted/Max/Min/Error)
        - 3 列 (simu 模式): 只写入前 3 列(Name/Comments/Initial);min/max 持久化到
          `obj._ecm_param_bounds` 隐藏字典,这样在 simu 模式下加载一个含 min/max 的
          JSON 模型时,虽然表内不显示,但仍能在 roundtrip 时保留边界信息。
    """
    circuit_string = model_data.get("circuit_string", "")
    obj.tab1.connectionTextEdit.setText(circuit_string)

    # 解析电路字符串并填充 circuit 列表
    obj.circuit = parse_circuit_string_to_list(circuit_string)

    freq = model_data.get("frequency", {})
    obj.tab1.ECMlowfreqTextEdit.setText(str(freq.get("min", "1e1")))
    obj.tab1.ECMupfreqTextEdit.setText(str(freq.get("max", "1e9")))

    table = obj.tab1.ECMtable
    table.setRowCount(0)

    # Bug #006 Phase 2.5: 根据当前表头列数决定写入策略
    # 7 列 (fit) = 完整加载; 3 列 (simu) = 隐藏持久化 min/max
    ncols = table.columnCount()
    is_full = ncols >= 7
    # 初始化隐藏持久化字典
    if not hasattr(obj, '_ecm_param_bounds') or obj._ecm_param_bounds is None:
        obj._ecm_param_bounds = {}

    for param in model_data.get("parameters", []):
        row = table.rowCount()
        table.insertRow(row)

        name = param.get("name", "")
        display_name = param.get("display_name", "")
        value = param.get("value", "")
        max_v = param.get("max", "")
        min_v = param.get("min", "")

        # col 0: Name (必有)
        table.setItem(row, 0, QTableWidgetItem(name))
        # col 1: Comments (必有)
        table.setItem(row, 1, QTableWidgetItem(display_name))
        # col 2: Initial_Value (必有)
        table.setItem(row, 2, QTableWidgetItem(str(value)))

        if is_full:
            # 7 列 fit 模式: 写入 Fitted_Value(3)/Max(4)/Min(5)/Error(6)
            table.setItem(row, 3, QTableWidgetItem(""))  # Fitted_Value - 初始空
            table.setItem(row, 4, QTableWidgetItem(str(max_v)))
            table.setItem(row, 5, QTableWidgetItem(str(min_v)))
            table.setItem(row, 6, QTableWidgetItem(""))  # Error - 初始空
        else:
            # 3 列 simu 模式: 把 min/max 存入隐藏字典, 不在表内显示
            obj._ecm_param_bounds[name] = {
                'min': min_v,
                'max': max_v,
                'unit': param.get("unit", ""),
            }


# =============================================================================
# ECMFunction Class - 业务逻辑
# =============================================================================

class ECMFunction:
    """ECM模型业务逻辑Mixin类"""

    def newECMModel(self):
        """新建空白ECM模型，按时间+类型生成文件名，自动保存基础JSON数据"""
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_folder = os.path.join(current_dir, 'ModelFileExamples', 'ECM')
        os.makedirs(model_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"ECM_{timestamp}.json"
        file_path = os.path.join(model_folder, file_name)

        model_data = {
            "version": "1.0",
            "model_type": "ECM",
            "model_name": f"New ECM Model {timestamp}",
            "file_path": file_path,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "frequency": {
                "min": 1e1,
                "max": 1e9,
                "points": 50,
                "unit": "Hz"
            },
            "circuit_string": "",
            "parameters": []
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=4, ensure_ascii=False)
            print(f"New model created: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to create model file:\n{str(e)}')
            return

        self.current_model_path = file_path

        if file_path not in self.modelfilesnamelist:
            model_index = len(self.modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.modelfilesnamelist.append(file_path)
            self.modelitemsnamelist.append(model_display_name)
            self.tab1.inputdataComboBox.clear()
            self.tab1.inputdataComboBox.addItems(self.modelitemsnamelist)

        self.clearECMModel()

    def openECMModel(self):
        """打开ECM模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Model File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)

            if model_data.get('model_type') != 'ECM':
                QMessageBox.warning(self, 'Warning', 'This function only supports ECM model files.')
                return

            self._load_ecm_model_to_ui(model_data)
            self.current_model_path = file_path

            model_index = len(self.modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.modelfilesnamelist.append(file_path)
            self.modelitemsnamelist.append(model_display_name)

            self.tab1.inputdataComboBox.clear()
            self.tab1.inputdataComboBox.addItems(self.modelitemsnamelist)

            print(f"Model loaded from: {file_path}")

        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Error', 'Invalid JSON file format.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open model file:\n{str(e)}')

    def saveECMModel(self):
        """保存ECM模型到已有文件"""
        if self.current_model_path is None:
            self.saveasECMModel()
            return
        self._save_ecm_model_to_file(self.current_model_path)

    def saveasECMModel(self):
        """另存为ECM模型文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Model As",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.endswith('.json'):
            file_path += '.json'

        self._save_ecm_model_to_file(file_path)
        self.current_model_path = file_path

        if file_path not in self.modelfilesnamelist:
            model_index = len(self.modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.modelfilesnamelist.append(file_path)
            self.modelitemsnamelist.append(model_display_name)
            self.tab1.inputdataComboBox.clear()
            self.tab1.inputdataComboBox.addItems(self.modelitemsnamelist)

    def _save_ecm_model_to_file(self, file_path):
        """将ECM模型保存到指定文件"""
        try:
            model_data = self._create_ecm_model_json()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=4, ensure_ascii=False)
            print(f"Model saved to: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save model file:\n{str(e)}')

    def _create_ecm_model_json(self):
        """从当前UI创建ECM模型的JSON数据"""
        return create_ecm_model_json(self)

    def _load_ecm_model_to_ui(self, model_data):
        """将ECM模型JSON数据加载到UI"""
        load_ecm_model_to_ui(self, model_data)

    def clearECMModel(self):
        """清空ECM模型数据"""
        self.circuit = list()
        self.termnamelist = list()
        self.modelterm = list()
        self.MTexpre = list()
        self.params = Parameters()
        self.option = {'EP': 0, 'DC Conductivity': 0}
        self.tab1.connectionTextEdit.setText('')
        self.tab1.ECMtable.setRowCount(0)
        # Bug #006 Phase 2: 移除 Fixed 死列,通过 setECMTableHeader('fit') 统一重置为 7 列
        self.tab1.setECMTableHeader('fit')
        self.tab1.ECMtable.setShowGrid(True)

    def _get_model_folder(self):
        """获取ECM模型文件夹路径"""
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(current_dir, 'ModelFileExamples', 'ECM')

    def _update_model_files_list(self, file_path):
        """更新ECM模型文件列表"""
        if file_path not in self.modelfilesnamelist:
            model_index = len(self.modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.modelfilesnamelist.append(file_path)
            self.modelitemsnamelist.append(model_display_name)
            self.tab1.inputdataComboBox.clear()
            self.tab1.inputdataComboBox.addItems(self.modelitemsnamelist)

    def addelement(self):
        """添加元件到电路"""
        if self.tab1.elementnameTextEdit.text() != '':
            elementtype = self.tab1.elementComboBox.currentText()
            elementname = self.tab1.elementnameTextEdit.text()
            element = elementtype + elementname
        else:
            QMessageBox.information(self, 'Information', 'please input a name')
            return
        ######编辑电路信息列表######
        ########保证存在连接关系#########
        checklist = ['+', 'p(', ',']
        if len(self.circuit) != 0:
            if self.circuit[-1] not in checklist:
                QMessageBox.information(self, 'Information', 'please input a connection')
                return
        ########保证存在连接关系#########
        # check repeat
        if element not in self.circuit:
            self.circuit.append(element)
            #####表格添加元件########
            row = self.tab1.ECMtable.rowCount()
            self.tab1.ECMtable.setRowCount(row + 1)
            newitem = QTableWidgetItem(str(element))
            self.tab1.ECMtable.setItem(row, 0, newitem)
            init_val = QTableWidgetItem(str(1))
            self.tab1.ECMtable.setItem(row, 2, init_val)
            #####表格添加元件########
            ###在对话框中展示电路#########
            circuitname = ''.join(self.circuit)
            self.tab1.connectionTextEdit.setText(circuitname)
            ###在对话框中展示电路#########
        else:
            QMessageBox.information(self, 'Information', 'same name exist')
            return
        print(self.circuit)

    def undo(self):
        """撤销上一个操作"""
        if len(self.circuit) != 0:
            row = self.tab1.ECMtable.rowCount()
            obj = self.circuit[-1]
            if self.tab1.ECMtable.item(row - 1, 0).text() == obj:
                print(self.tab1.ECMtable.item(row - 1, 0).text())
                self.tab1.ECMtable.removeRow(row - 1)
            self.circuit.pop()
            circuitname = ''.join(self.circuit)
            self.tab1.connectionTextEdit.setText(circuitname)
        else:
            print('Empty')
        print(self.circuit)

    def addconnection(self):
        """添加连接符"""
        connectiontype = self.tab1.connectionComboBox.currentText()
        if connectiontype == 'Series':
            if len(self.circuit) != 0:
                if self.circuit[-1] in ['p(', ',', '+']:
                    return
                else:
                    self.circuit.append('+')
                    circuitname = ''.join(self.circuit)
                    self.tab1.connectionTextEdit.setText(circuitname)
            else:
                return
        if connectiontype == 'Parallel':
            if len(self.circuit) != 0:
                if self.circuit[-1] in ['+', ',']:
                    self.circuit.append('p(')
                    circuitname = ''.join(self.circuit)
                    self.tab1.connectionTextEdit.setText(circuitname)
                else:
                    return
            else:
                self.circuit.append('p(')
                circuitname = ''.join(self.circuit)
                self.tab1.connectionTextEdit.setText(circuitname)
        if connectiontype == ',':
            if len(self.circuit) != 0:
                if self.circuit[-1] not in ['+', ',', 'p(']:
                    self.circuit.append(',')
                    circuitname = ''.join(self.circuit)
                    self.tab1.connectionTextEdit.setText(circuitname)
                else:
                    return
            else:
                return
        if connectiontype == ')':
            if len(self.circuit) != 0:
                if self.circuit[-1] not in ['+', ',', 'p(']:
                    self.circuit.append(')')
                    circuitname = ''.join(self.circuit)
                    self.tab1.connectionTextEdit.setText(circuitname)
                else:
                    return
            else:
                return
