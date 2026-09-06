# -*- coding: utf-8 -*-
"""
MTM.py - MT (Multi-Term)模型的业务逻辑和JSON序列化

包含MT模型的业务逻辑（按钮处理、文件保存/加载）和JSON序列化和反序列化功能
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from lmfit import Parameters


# =============================================================================
# Handler Functions - JSON序列化/反序列化
# =============================================================================

def create_mt_model_json(obj):
    """
    从UI对象创建MT模型的JSON数据

    参数:
        obj: 包含以下属性的对象:
            - tab2: MTMUI.Tab2Content 实例
            - current_mt_model_path: 当前模型文件路径
            - modelterm: 模型项列表
            - MTexpre: 表达式列表
            - MTparams: lmfit Parameters 对象
            - option: 选项字典

    返回:
        dict: MT模型的JSON数据
    """
    model_name = "Untitled MT Model"
    if hasattr(obj, 'current_mt_model_path') and obj.current_mt_model_path:
        model_name = os.path.splitext(os.path.basename(obj.current_mt_model_path))[0]

    # 获取频率设置
    try:
        freq_min = float(obj.tab2.MTlowfreqTextEdit.text())
        freq_max = float(obj.tab2.MTupfreqTextEdit.text())
    except:
        freq_min = 1e1
        freq_max = 1e9
    freq_distribution = obj.tab2.MTdistributionComboBox.currentText()

    # 获取选项设置
    option = getattr(obj, 'option', {'EP': 0, 'DC Conductivity': 0})

    # 构建model_terms列表
    model_terms = []
    if hasattr(obj, 'modelterm') and hasattr(obj, 'MTexpre'):
        for i, term_info in enumerate(obj.modelterm):
            if i < len(obj.MTexpre):
                model_terms.append({
                    "name": term_info.get('name', ''),
                    "modeltype": term_info.get('modeltype', ''),
                    "expression": obj.MTexpre[i]
                })

    # 构建parameters列表，直接从表格读取，保证未拟合时也能保存当前参数
    parameters = []
    table = obj.tab2.MTtable
    # Bug #006 Phase 2.5: 根据 MTtable 列数自适应读取
    # 7 列 (fit): 读 col 4 (Max) / col 5 (Min)
    # 3 列 (simu): 表内无 Min/Max, 从 obj._mt_param_bounds 隐藏字典取
    ncols = table.columnCount()
    is_full = ncols >= 7
    hidden = getattr(obj, '_mt_param_bounds', None) or {}
    for row in range(table.rowCount()):
        name_item = table.item(row, 0)
        if not name_item or not name_item.text():
            continue
        name = name_item.text()
        init_item = table.item(row, 2)
        try:
            init_val = float(init_item.text()) if init_item and init_item.text() else 0.0
        except ValueError:
            init_val = 0.0
        if is_full:
            max_item = table.item(row, 4)
            min_item = table.item(row, 5)
            try:
                max_val = float(max_item.text()) if max_item and max_item.text() else None
            except ValueError:
                max_val = None
            try:
                min_val = float(min_item.text()) if min_item and min_item.text() else None
            except ValueError:
                min_val = None
        else:
            # 3 列 simu 模式: 表内无 min/max, 从隐藏字典取
            bound = hidden.get(name, {})
            min_val = bound.get('min', None)
            max_val = bound.get('max', None)
        parameters.append({
            "name": name,
            "init": init_val,
            "min": min_val,
            "max": max_val
        })

    return {
        "version": "1.0",
        "model_type": "MT",
        "model_name": model_name,
        "file_path": getattr(obj, 'current_mt_model_path', "") or "",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "frequency": {
            "min": freq_min,
            "max": freq_max,
            "distribution": freq_distribution,
            "unit": "Hz"
        },
        "option": option,
        "model_terms": model_terms,
        "parameters": parameters
    }


def load_mt_model_to_ui(obj, model_data):
    """
    将MT模型JSON数据加载到UI

    参数:
        obj: 包含以下属性的对象:
            - tab2: MTMUI.Tab2Content 实例
            - termnamelist: 项名称列表 (会被修改)
            - modelterm: 模型项列表 (会被修改)
            - MTexpre: 表达式列表 (会被修改)
            - MTparams: lmfit Parameters 对象 (会被修改)
            - option: 选项字典 (会被修改)
            - _mt_param_bounds: (可选) Bug #006 Phase 2.5 simu 隐藏持久化字典
        model_data: dict, MT模型的JSON数据

    说明(Bug #006 Phase 2.5):
        根据当前 MTtable 的列数自适应写入:
        - 7 列 (fit 模式): 写入全部 7 列(Name/Comments/Initial/Fitted/Max/Min/Error)
        - 3 列 (simu 模式): 只写入前 3 列(Name/Comments/Initial);min/max 持久化到
          `obj._mt_param_bounds` 隐藏字典
    """
    try:
        # 1. 清空当前模型数据
        obj.termnamelist = []
        obj.modelterm = []
        obj.MTexpre = []
        obj.MTparams = Parameters()
        obj.option = {'EP': 0, 'DC Conductivity': 0}

        # 2. 加载频率设置
        if 'frequency' in model_data:
            freq = model_data['frequency']
            obj.tab2.MTlowfreqTextEdit.setText(str(freq.get('min', 1e1)))
            obj.tab2.MTupfreqTextEdit.setText(str(freq.get('max', 1e9)))
            dist = freq.get('distribution', 'log')
            if obj.tab2.MTdistributionComboBox.findText(dist) >= 0:
                obj.tab2.MTdistributionComboBox.setCurrentText(dist)

        # 3. 加载选项设置
        if 'option' in model_data:
            obj.option = model_data['option']

        # 4. 清空表格
        obj.tab2.MTtable.setRowCount(0)

        # Bug #006 Phase 2.5: 初始化隐藏持久化字典
        if not hasattr(obj, '_mt_param_bounds') or obj._mt_param_bounds is None:
            obj._mt_param_bounds = {}
        ncols = obj.tab2.MTtable.columnCount()
        is_full = ncols >= 7

        # 5. 加载parameters到MTparams和表格
        if 'parameters' in model_data:
            for param in model_data['parameters']:
                name = param['name']
                init_val = param.get('init', 0)
                max_val = param.get('max', 1e15)
                min_val = param.get('min', 1e-15)

                # 添加到MTparams(始终保留 min/max, 因为 lmfit Parameter 需要)
                obj.MTparams.add(name, value=init_val, min=min_val, max=max_val)

                # 添加到表格
                currentRow = obj.tab2.MTtable.rowCount()
                obj.tab2.MTtable.setRowCount(currentRow + 1)
                obj.tab2.MTtable.setItem(currentRow, 0, QTableWidgetItem(name))
                obj.tab2.MTtable.setItem(currentRow, 2, QTableWidgetItem(str(init_val)))
                if is_full:
                    # 7 列 fit 模式: 写入 Fitted(3)/Max(4)/Min(5)/Error(6)
                    obj.tab2.MTtable.setItem(currentRow, 3, QTableWidgetItem(""))
                    obj.tab2.MTtable.setItem(currentRow, 4, QTableWidgetItem(str(max_val)))
                    obj.tab2.MTtable.setItem(currentRow, 5, QTableWidgetItem(str(min_val)))
                    obj.tab2.MTtable.setItem(currentRow, 6, QTableWidgetItem(""))
                else:
                    # 3 列 simu 模式: 把 min/max 存入隐藏字典
                    obj._mt_param_bounds[name] = {
                        'min': min_val,
                        'max': max_val,
                    }

        # 6. 加载model_terms
        if 'model_terms' in model_data:
            for term in model_data['model_terms']:
                name = term.get('name', '')
                modeltype = term.get('modeltype', '')
                expression = term.get('expression', '')

                if not name:
                    continue

                # 添加到列表
                obj.termnamelist.append(name)
                obj.modelterm.append({'name': name, 'modeltype': modeltype})
                obj.MTexpre.append(expression)

            # 更新表达式文本框
            if obj.MTexpre:
                mt_expression = 'epsh+' + '+'.join(obj.MTexpre)
                obj.tab2.MTmultitermTextEdit.setText(mt_expression)

        print(f"MT Model loaded to UI: {model_data.get('model_name', 'Unknown')}")

    except Exception as e:
        QMessageBox.critical(None, 'Error', f'Failed to load MT model to UI:\n{str(e)}')


# =============================================================================
# MTMFunction Class - 业务逻辑
# =============================================================================

class MTMFunction:
    """MTM模型业务逻辑Mixin类"""

    def newMTModel(self):
        """新建空白MT模型，按时间+类型生成文件名，自动保存基础JSON数据"""
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_folder = os.path.join(current_dir, 'ModelFileExamples', 'MT')
        os.makedirs(model_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"MT_{timestamp}.json"
        file_path = os.path.join(model_folder, file_name)

        model_data = {
            "version": "1.0",
            "model_type": "MT",
            "model_name": f"New MT Model {timestamp}",
            "file_path": file_path,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "frequency": {
                "min": 1e6,
                "max": 1e10,
                "points": 100,
                "unit": "Hz"
            },
            "model_terms": []
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=4, ensure_ascii=False)
            print(f"New MT model created: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to create MT model file:\n{str(e)}')
            return

        self.current_mt_model_path = file_path

        if file_path not in self.mt_modelfilesnamelist:
            model_index = len(self.mt_modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.mt_modelfilesnamelist.append(file_path)
            self.mt_modelitemsnamelist.append(model_display_name)
            self.tab2.inputdataComboBox.clear()
            self.tab2.inputdataComboBox.addItems(self.mt_modelitemsnamelist)

        self.clearMTModel()

    def openMTModel(self):
        """打开MT模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open MT Model File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)

            if model_data.get('model_type') != 'MT':
                QMessageBox.warning(self, 'Warning', 'This function only supports MT model files.')
                return

            self._load_mt_model_to_ui(model_data)
            self.current_mt_model_path = file_path

            if file_path not in self.mt_modelfilesnamelist:
                model_index = len(self.mt_modelfilesnamelist) + 1
                model_display_name = f"{model_index}...{file_path}"
                self.mt_modelfilesnamelist.append(file_path)
                self.mt_modelitemsnamelist.append(model_display_name)

                self.tab2.inputdataComboBox.clear()
                self.tab2.inputdataComboBox.addItems(self.mt_modelitemsnamelist)

            print(f"MT Model loaded from: {file_path}")

        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Error', 'Invalid JSON file format.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open MT model file:\n{str(e)}')

    def saveMTModel(self):
        """保存MT模型到已有文件"""
        if self.current_mt_model_path is None:
            self.saveasMTModel()
            return
        self._save_mt_model_to_file(self.current_mt_model_path)

    def saveasMTModel(self):
        """另存为MT模型文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save MT Model As",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.endswith('.json'):
            file_path += '.json'

        self._save_mt_model_to_file(file_path)
        self.current_mt_model_path = file_path

        if file_path not in self.mt_modelfilesnamelist:
            model_index = len(self.mt_modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.mt_modelfilesnamelist.append(file_path)
            self.mt_modelitemsnamelist.append(model_display_name)
            self.tab2.inputdataComboBox.clear()
            self.tab2.inputdataComboBox.addItems(self.mt_modelitemsnamelist)

    def _save_mt_model_to_file(self, file_path):
        """将MT模型保存到指定文件"""
        try:
            model_data = self._create_mt_model_json()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=4, ensure_ascii=False)
            print(f"MT Model saved to: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save MT model file:\n{str(e)}')

    def _create_mt_model_json(self):
        """从当前UI创建MT模型的JSON数据"""
        return create_mt_model_json(self)

    def _load_mt_model_to_ui(self, model_data):
        """将MT模型JSON数据加载到UI"""
        load_mt_model_to_ui(self, model_data)

    def clearMTModel(self):
        """清空MT模型数据"""
        self.termnamelist = []
        self.modelterm = []
        self.MTexpre = []
        self.MTparams = Parameters()
        self.option = {'EP': 0, 'DC Conductivity': 0}
        self.tab2.MTmultitermTextEdit.setText('')
        self.tab2.MTtable.setRowCount(0)
        self.tab2.EPcheckBox.setChecked(False)
        self.tab2.DCcheckBox.setChecked(False)

    def _get_mt_model_folder(self):
        """获取MT模型文件夹路径"""
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(current_dir, 'ModelFileExamples', 'MT')

    def _update_mt_model_files_list(self, file_path):
        """更新MT模型文件列表"""
        if file_path not in self.mt_modelfilesnamelist:
            model_index = len(self.mt_modelfilesnamelist) + 1
            model_display_name = f"{model_index}...{file_path}"
            self.mt_modelfilesnamelist.append(file_path)
            self.mt_modelitemsnamelist.append(model_display_name)
            self.tab2.inputdataComboBox.clear()
            self.tab2.inputdataComboBox.addItems(self.mt_modelitemsnamelist)

    def addterm(self):
        """添加MT模型项"""
        if self.tab2.termnameTextEdit.text() == '' or self.tab2.termnameTextEdit.text() in self.termnamelist:
            print('please input a name')
            return
        else:
            self.termnamelist.append(self.tab2.termnameTextEdit.text())
            modeltypetemp = {'name': self.tab2.termnameTextEdit.text(),
                             'modeltype': self.tab2.termComboBox.currentText()}
            self.modelterm.append(modeltypetemp)

        MTexpressionpart1 = 'epsh+'

        if modeltypetemp['modeltype'] == 'Debye':
            part2 = 'Deps' + str(self.tab2.termnameTextEdit.text()) + '/' + '(1+' + 'j*omega*Tao' + str(
                self.tab2.termnameTextEdit.text()) + ')'
            self.MTexpre.append(part2)
            MTexpression = MTexpressionpart1 + '+'.join(self.MTexpre)
            self.tab2.MTmultitermTextEdit.setText(MTexpression)

            if len(self.modelterm) <= 1:
                self.tableAdd('epsh', 6, 50, 0)
            self.tableAdd('Deps' + str(self.tab2.termnameTextEdit.text()), 72, 100, 0)
            self.tableAdd('Tao' + str(self.tab2.termnameTextEdit.text()), 8.38E-12, 1e-6, 0)

        elif modeltypetemp['modeltype'] == 'Cole-Cole':
            part2 = 'Deps' + str(self.tab2.termnameTextEdit.text()) + '/' + '(1+' + '(j*omega*Tao' + str(
                self.tab2.termnameTextEdit.text()) + ')^(1-Alpha' + str(self.tab2.termnameTextEdit.text()) + ')' + ')'
            self.MTexpre.append(part2)
            MTexpression = MTexpressionpart1 + '+'.join(self.MTexpre)
            self.tab2.MTmultitermTextEdit.setText(MTexpression)

            if len(self.modelterm) <= 1:
                self.tableAdd('epsh', 6, 50, 0)
            self.tableAdd('Deps' + str(self.tab2.termnameTextEdit.text()), 1.9, 500, 0)
            self.tableAdd('Tao' + str(self.tab2.termnameTextEdit.text()), 2.63, 20, 0)
            self.tableAdd('Alpha' + str(self.tab2.termnameTextEdit.text()), 0.67, 1, 0)

        elif modeltypetemp['modeltype'] == 'Davidson-Cole':
            part2 = 'Deps' + str(self.tab2.termnameTextEdit.text()) + '/' + '((1+' + 'j*omega*Tao' + str(
                self.tab2.termnameTextEdit.text()) + ')^Beta' + str(self.tab2.termnameTextEdit.text()) + ')'
            self.MTexpre.append(part2)
            MTexpression = MTexpressionpart1 + '+'.join(self.MTexpre)
            self.tab2.MTmultitermTextEdit.setText(MTexpression)

            if len(self.modelterm) <= 1:
                self.tableAdd('epsh', 6, 50, 0)
            self.tableAdd('Deps' + str(self.tab2.termnameTextEdit.text()), 1.9, 500, 0)
            self.tableAdd('Tao' + str(self.tab2.termnameTextEdit.text()), 2.63, 20, 0)
            self.tableAdd('Beta' + str(self.tab2.termnameTextEdit.text()), 0.9, 1, 0)

        elif modeltypetemp['modeltype'] == 'Havriliak-Negami':
            part2 = 'Deps' + str(self.tab2.termnameTextEdit.text()) + '/' + '((1+' + '(j*omega*Tao' + str(
                self.tab2.termnameTextEdit.text()) + ')^(1-Alpha' + str(self.tab2.termnameTextEdit.text()) + ')' + ')^Beta' + str(
                self.tab2.termnameTextEdit.text()) + ')'
            self.MTexpre.append(part2)
            MTexpression = MTexpressionpart1 + '+'.join(self.MTexpre)
            self.tab2.MTmultitermTextEdit.setText(MTexpression)

            if len(self.modelterm) <= 1:
                self.tableAdd('epsh', 6, 50, 0)
            self.tableAdd('Deps' + str(self.tab2.termnameTextEdit.text()), 1.9, 500, 0)
            self.tableAdd('Tao' + str(self.tab2.termnameTextEdit.text()), 2.63, 20, 0)
            self.tableAdd('Beta' + str(self.tab2.termnameTextEdit.text()), 0.9, 1, 0)
        else:
            return

    def deleteterm(self):
        """删除MT模型项"""
        if len(self.termnamelist) != 0:
            self.tableDelete(self.MTexpre[-1])
            self.MTexpre.pop()
            self.termnamelist.pop()
            self.modelterm.pop()
            MTexpression = 'epsh+' + '+'.join(self.MTexpre)
            self.tab2.MTmultitermTextEdit.setText(MTexpression)
        else:
            print('Empty')
            self.tableDelete(['epsh'])
            self.tab2.MTmultitermTextEdit.setText('')

    def tableAdd(self, name, init_val, max_val, min_val):
        """表格添加行(Bug #006 Phase 2.5: 自适应 3/7 列表)"""
        currentRow = self.tab2.MTtable.rowCount()
        self.tab2.MTtable.setRowCount(currentRow + 1)
        MTnewitem = QTableWidgetItem(name)
        self.tab2.MTtable.setItem(currentRow, 0, MTnewitem)
        MTinit_val = QTableWidgetItem(str(init_val))
        self.tab2.MTtable.setItem(currentRow, 2, MTinit_val)
        # Bug #006 Phase 2.5: 根据当前表头列数决定 max/min 写入策略
        ncols = self.tab2.MTtable.columnCount()
        if ncols >= 7:
            # 7 列 fit 模式: 写入 Max(4)/Min(5)
            MTmax_val = QTableWidgetItem(str(max_val))
            self.tab2.MTtable.setItem(currentRow, 4, MTmax_val)
            MTmin_val = QTableWidgetItem(str(min_val))
            self.tab2.MTtable.setItem(currentRow, 5, MTmin_val)
        else:
            # 3 列 simu 模式: max/min 存入隐藏字典
            if not hasattr(self, '_mt_param_bounds') or self._mt_param_bounds is None:
                self._mt_param_bounds = {}
            self._mt_param_bounds[name] = {'min': min_val, 'max': max_val}

    def tableDelete(self, namelist):
        """表格删除行"""
        currentRow = self.tab2.MTtable.rowCount()
        while currentRow > 0:
            if self.tab2.MTtable.item(currentRow - 1, 0).text() in namelist:
                self.tab2.MTtable.removeRow(currentRow - 1)
                currentRow = currentRow - 1
            else:
                currentRow = currentRow - 1

    def EPconfirm(self):
        """电极极化选项确认"""
        if self.tab2.EPcheckBox.isChecked() == 1:
            if self.tab2.EPComboBox.currentText() == 'CPE':
                self.tableAdd('A', 2.59, 1e5, 0)
                self.tableAdd('alphaCPE', 0.94, 1, 0)
                self.option['EP'] = 1
        elif self.tab2.EPcheckBox.isChecked() == 0:
            self.tableDelete(['A'])
            self.tableDelete(['alphaCPE'])
            self.option['EP'] = 0

    def DCconfirm(self):
        """DC电导率选项确认"""
        if self.tab2.DCcheckBox.isChecked() == 1:
            self.tableAdd('sigmaDC', 4, 100, 0)
            self.option['DC Conductivity'] = 1
        elif self.tab2.DCcheckBox.isChecked() == 0:
            self.tableDelete(['sigmaDC'])
            self.option['DC Conductivity'] = 0
