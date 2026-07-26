# -*- coding: utf-8 -*-
"""
ECM.py - ECM模型的业务逻辑和JSON序列化

包含ECM模型的业务逻辑（按钮处理、文件保存/加载）和JSON序列化和反序列化功能
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from PySide6.QtCore import Qt
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

    返回:
        dict: ECM模型的JSON数据
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
    for row in range(table.rowCount()):
        param = {}
        for col, header in enumerate(['name', 'display_name', 'value', 'unit', 'min', 'max', 'fixed']):
            item = table.item(row, col)
            if header == 'fixed':
                param[header] = (item.checkState() == Qt.CheckState.Checked) if item else False
            elif header == 'value' or header == 'min' or header == 'max':
                try:
                    param[header] = float(item.text()) if item and item.text() else 0.0
                except ValueError:
                    param[header] = 0.0
            else:
                param[header] = item.text() if item else ""
        if 'name' in param and param['name']:
            model_data["parameters"].append(param)

    return model_data


def load_ecm_model_to_ui(obj, model_data):
    """
    将ECM模型JSON数据加载到UI

    参数:
        obj: UI对象
        model_data: dict, ECM模型的JSON数据
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
    headers = ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Fixed', 'Error [%]']
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)

    for param in model_data.get("parameters", []):
        row = table.rowCount()
        table.insertRow(row)

        name_item = QTableWidgetItem(param.get("name", ""))
        comments_item = QTableWidgetItem(param.get("display_name", ""))
        value_item = QTableWidgetItem(str(param.get("value", "")))
        unit_item = QTableWidgetItem(param.get("unit", ""))
        max_item = QTableWidgetItem(str(param.get("max", "")))
        min_item = QTableWidgetItem(str(param.get("min", "")))
        fixed_checkbox = QTableWidgetItem()
        fixed_checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        fixed_checkbox.setCheckState(Qt.CheckState.Checked if param.get("fixed", False) else Qt.CheckState.Unchecked)
        error_item = QTableWidgetItem("")

        table.setItem(row, 0, name_item)
        table.setItem(row, 1, comments_item)
        table.setItem(row, 2, value_item)
        table.setItem(row, 3, QTableWidgetItem(""))
        table.setItem(row, 4, max_item)
        table.setItem(row, 5, min_item)
        table.setItem(row, 6, fixed_checkbox)
        table.setItem(row, 7, error_item)


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
        self.tab1.ECMtable.setColumnCount(8)
        self.tab1.ECMtable.setHorizontalHeaderLabels(['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Fixed', 'Error [%]'])
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
