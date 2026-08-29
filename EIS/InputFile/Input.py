import os

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal

from EIS.InputFile.ui_Input import InputdataUI
from EIS.InputFile.Inputfun import readfile,extract_indices
from EIS.Other.Datacheck import ensure_paired_form
from setting import Settings

class inputWidget(QWidget):
    datasignal = Signal(list, list, list, list)

    def __init__(self, parent=None):
        super(inputWidget, self).__init__(parent)
        ########变量申明###############
        self.plotdata = list()      # 所有数据 
        self.plotdataname = list()  # 被选中的数据名 
        self.selectlist = list()    # 被选中的数据 
        self.dataInfo = list()      # 数据信息 

        self.filesnamelist = list() # 打开的文件名列表 
        self._signal_connected = False  # 添加信号连接状态标志


        ###########初始化###################
        self.inputui = InputdataUI()
        self.inputui.init_ui(self)        # 设置 UI

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 可选：移除边距
        self.main_layout.addWidget(self.inputui.contents)  # 添加 UI 内容到布局


        ###########初始化###################
        self.inputui.inputdataBtn.clicked.connect(lambda: self.GetInputFiles())
        self.inputui.openexfilebtn.clicked.connect(lambda: self.OpenFiles())
        self.inputui.deletexfilebtn.clicked.connect(lambda: self.deleteFiles())
        self.inputui.clearinputbtn.clicked.connect(lambda: self.clearinput())
        self.inputui.freshbtn.clicked.connect(lambda: self.fresh())
        self.inputui.selection_files_group.buttonClicked.connect(lambda button: self.selectfiles())
        self.inputui.selection_data_group.buttonClicked.connect(lambda button: self.handle_data_selection(button))
       
        self._connect_cell_changed()        # 使用统一的信号连接方法



    def sendsignal(self):
        # 空数据保护:没有数据时不发射信号,避免下游 Figure 模块被空数据覆盖
        if not self.plotdata:
            # print('[Input.sendsignal] plotdata 为空, 跳过发射')
            return
        # 将单条数据成对化,让下游 selectsavedata 的 i%2 逻辑可工作
        self.selectlist, self.plotdataname, self.plotdata, self.dataInfo = ensure_paired_form(
            self.selectlist,
            self.plotdataname,
            self.plotdata,
            self.dataInfo,
        )
        self.datasignal.emit(self.selectlist, self.plotdataname, self.plotdata, self.dataInfo)  ####发送数据
        # column_headers = self.plotdata[0].columns.tolist() if self.plotdata else "No data available"
        # print('Inputdata emitted', self.selectlist, self.plotdataname, column_headers, self.dataInfo)

        # print('Inputdata emitted',self.selectlist, self.plotdataname, len(self.plotdata), self.dataInfo)
        # print(self.selectlist)
        # print(self.plotdataname)
        # print(self.plotdata)
        # print(self.dataInfo)


    def cleardata(self):
        ################清除旧数据###################
        self.selectlist = list()  #############被选中的数据###########
        self.plotdata = list()  #############所有数据###########
        self.plotdataname = list()  #############被选中的数据名###########
        self.dataInfo=list()########数据信息
        ################清除旧数据###################

    def GetInputFiles(self):  ##inputdataButton输入新数据文件
        # 默认打开项目根目录下的 Data 文件夹
        # 不再依赖 base_settings.json 中的 working_path(避免绝对路径耦合)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        data_folder = os.path.join(project_root, 'Data')

        # 如果 Data 文件夹不存在,自动创建(可选,提升用户体验)
        if not os.path.exists(data_folder):
            try:
                os.makedirs(data_folder, exist_ok=True)
                print(f'Created data folder: {data_folder}')
            except Exception as e:
                print(f'Failed to create data folder {data_folder}: {e}')
                data_folder = project_root  # 回退到项目根目录

        filesname, filetype = QFileDialog.getOpenFileNames(self, 'Open File', data_folder,
                                                           "Data Files (*.xlsx *.xls *.csv);;Text Files (*.txt);;All Files (*)")
        if filesname == []:  # Exit when no choice
            print("No choice")  ###输出到状态栏
            return
        else:  # 比较新输入的数据列表
            filesnametemp = [tem for tem in filesname if tem not in self.filesnamelist]  # 比较新输入的数据列表
            self.filesnamelist.extend(filesnametemp)  ###只加入新数据在列表最后
            self.itemsnamelist = [str(self.filesnamelist.index(itemtem) + 1) + '...' + itemtem for itemtem in
                                  self.filesnamelist]  ##为数据添加序号
            if self.inputui.inputdataComboBox.count() != 0:
                self.inputui.inputdataComboBox.clear()  ##清除原有数据
                self.inputui.inputdataComboBox.addItems(self.itemsnamelist)
            else:
                self.inputui.inputdataComboBox.addItems(self.itemsnamelist)

        self.inputui.allCheckBox.setChecked(True)  ####默认选中全部文件
        self.inputui.selectallBtn.setChecked(True)  ####默认选中全部数据
        # 调试:文件获取结果
        # print(f'[Input.GetInputFiles] 本次新增 {len(filesnametemp)} 个文件, 累计 {len(self.filesnamelist)} 个文件')
        self.selectfiles()  ##########选择文件



    def deleteFiles(self):  ##删除导入的文件
        if self.inputui.inputdataComboBox.currentIndex() == -1:
            self.cleardata()
            self.filesnamelist = list()
            self._disconnect_cell_changed()
            self.inputui.tableWidget.clearContents()
            # 保留空表格结构(至少 10 行),避免表格被完全删除
            while self.inputui.tableWidget.rowCount() < 10:
                self.inputui.tableWidget.insertRow(self.inputui.tableWidget.rowCount())
            self._connect_cell_changed()
            print('DeleteFiles No input data')
            return
        else:
            index = self.inputui.inputdataComboBox.currentIndex()
            self.inputui.inputdataComboBox.removeItem(index)  ########删除下拉列表中的文件
            self.filesnamelist.pop(index)                     ########删除文件列表中文件
            if len(self.filesnamelist) > 0:                   ##文件列表不为空时
                self.selectfiles()                            ##########选择文件
            else:                                             ###文件列表为空,清空数据但保留空表格
                self.cleardata()
                self._disconnect_cell_changed()
                self.inputui.tableWidget.clearContents()
                # 保留空表格结构(至少 10 行)
                while self.inputui.tableWidget.rowCount() < 10:
                    self.inputui.tableWidget.insertRow(self.inputui.tableWidget.rowCount())
                self._connect_cell_changed()


    def selectfiles(self):
        if self.inputui.allCheckBox.isChecked() :#####全选
            self.nondash = [i for i in range(0, len(self.filesnamelist))]
            if self.nondash == []:
                print('Please input files')  ###输出到状态栏
                return
            else:
                self.selectedfileslist = []
                self.selectedfileslist = self.filesnamelist
        elif self.inputui.selectedCheckBox.isChecked():#######部分选
            self.nondash = list()
            self.nondash = extract_indices(self.inputui.plotTextEdit.text())  ####寻找选中的文件
            if self.nondash == []:
                print(' No selection, Please input files')  ###输出到状态栏
                self.inputui.allCheckBox.setChecked(True)  ####默认选中全部文件
                return
            else:
                self.selectedfileslist = []
                # 检查所有索引是否有效(1-based,与 combo box 显示一致)
                if any(index < 1 or index > len(self.filesnamelist) for index in self.nondash):
                    print('Please check selection')  ###输出到状态栏
                    self.inputui.allCheckBox.setChecked(True)  # 回退到全选
                    return
                else:
                    # 1-based 输入转为 0-based 访问 filesnamelist
                    self.selectedfileslist = [self.filesnamelist[temp - 1] for temp in self.nondash]
        else:  #########无选择
            print('Please select one')  ###输出到状态栏
            return

        # 调试:文件选择结果
        # print(f'[Input.selectfiles] 选中 {len(self.selectedfileslist)} 个文件, allCheckBox={self.inputui.allCheckBox.isChecked()}, selectedCheckBox={self.inputui.selectedCheckBox.isChecked()}')
        self.cleartable()
        self.adddataTotable()
        self.fresh()




    def fresh(self):  ###获得当前选中的数据
        # 计算有数据的行数（检查第1列是否有数据名称）
        data_rows = 0
        for row in range(self.inputui.tableWidget.rowCount()):
            item = self.inputui.tableWidget.item(row, 1)  # 第1列是数据名称
            if item is not None and item.text().strip():  # 检查是否有数据名称
                data_rows += 1
            else:
                break  # 遇到空行就停止计数

        self.selectlist = [i for i in range(0, data_rows)]

        ###########################获得当前选中的数据############
        if data_rows > 0:
            for rowtemp in range(0, data_rows):
                item = self.inputui.tableWidget.item(rowtemp, 0)
                if item is None:  # 检查item是否为None
                    self.selectlist[rowtemp] = 0
                elif item.checkState() != Qt.CheckState.Checked:
                    self.selectlist[rowtemp] = 0
                else:
                    self.selectlist[rowtemp] = 1
        else:
            print('No data')
        ##########################获得当前选中的数据############

        # 确保表格至少有10行
        current_total_rows = self.inputui.tableWidget.rowCount()
        if current_total_rows < 10:
            rows_to_add = 10 - current_total_rows
            for i in range(rows_to_add):
                row_number = self.inputui.tableWidget.rowCount()
                self.inputui.tableWidget.insertRow(row_number)

        # 调试:fresh 结果
        # print(f'[Input.fresh] data_rows={data_rows}, selectlist={self.selectlist}, plotdata 长度={len(self.plotdata)}')
        self.sendsignal()


    def handle_data_selection(self, button):
        """处理数据选择按钮组的点击事件"""
        if button == self.inputui.selectallBtn:
            self.selectall()
        elif button == self.inputui.selectdataBtn:
            self.selectdata()

            
    def selectall(self):  ####选中全部的数据
        self._disconnect_cell_changed()        # 安全断开信号避免批量操作时重复触发

        # 计算有数据的行数（检查第1列是否有数据名称）
        data_rows = 0
        for row in range(self.inputui.tableWidget.rowCount()):
            item = self.inputui.tableWidget.item(row, 1)  # 第1列是数据名称
            if item is not None and item.text().strip():  # 检查是否有数据名称
                data_rows += 1
            else:
                break  # 遇到空行就停止计数
        
        # 只为有数据的行添加选择框
        for temrow in range(0, data_rows):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, Qt.CheckState.Checked)
            self.inputui.tableWidget.setItem(temrow, 0, item)
        
        self._connect_cell_changed()        # 重新连接信号
        self.fresh()


    def selectdata(self):  ##选择部分数据
        if len(self.inputui.dataTextEdit.text()) == 0:
            print('No input data')
            self.inputui.selectallBtn.setChecked(True)
            return
        else:
            self._disconnect_cell_changed()            # 安全断开信号避免批量操作时重复触发
            
            selecedtdata = extract_indices(self.inputui.dataTextEdit.text())
            
            # 计算有数据的行数（检查第1列是否有数据名称）
            data_rows = 0
            for row in range(self.inputui.tableWidget.rowCount()):
                item = self.inputui.tableWidget.item(row, 1)  # 第1列是数据名称
                if item is not None and item.text().strip():  # 检查是否有数据名称
                    data_rows += 1
                else:
                    break  # 遇到空行就停止计数
            
            # 只为有数据的行创建选择框
            ref = [i for i in range(1, data_rows + 1)]

            for tem1 in ref:  ####让选中的文件选中
                if tem1 in selecedtdata:
                    item = QTableWidgetItem()
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    item.setCheckState(Qt.CheckState.Checked)
                    item.setData(Qt.ItemDataRole.UserRole, Qt.CheckState.Checked)
                    self.inputui.tableWidget.setItem(tem1 - 1, 0, item)
                else:
                    item = QTableWidgetItem()
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    item.setData(Qt.ItemDataRole.UserRole, Qt.CheckState.Unchecked)
                    self.inputui.tableWidget.setItem(tem1 - 1, 0, item)

            self._connect_cell_changed()            # 重新连接信号
        self.fresh()






    def clearinput(self):  ##清除全部输入的数据
        ########清空输入的文件################
        self.inputui.inputdataComboBox.clear()
        self.inputui.plotTextEdit.clear()
        self.inputui.dataTextEdit.clear()
        # 清除后无文件,回到默认不选择状态
        self.inputui.allCheckBox.setChecked(False)
        self.inputui.selectedCheckBox.setChecked(False)
        self.inputui.selectallBtn.setChecked(False)
        self.inputui.selectdataBtn.setChecked(False)
        #########清空输入的文件###############

        # 清空数据但保留空表格结构(至少 10 行)
        self._disconnect_cell_changed()
        self.inputui.tableWidget.clearContents()
        while self.inputui.tableWidget.rowCount() < 10:
            self.inputui.tableWidget.insertRow(self.inputui.tableWidget.rowCount())
        self._connect_cell_changed()

        ########清空变量###############
        self.plotdata = list()      # 所有数据
        self.plotdataname = list()  # 被选中的数据名
        self.selectlist = list()    # 被选中的数据
        self.dataInfo = list()      # 数据信息
        self.filesnamelist = list() # 打开的文件名列表
        ########清空变量###############

        # 调试:清除所有数据
        # print('[Input.clearinput] 已清除所有数据')
        self.sendsignal()


    def OpenFiles(self):  ###用外部工具打开当前文件
        if self.inputui.inputdataComboBox.currentIndex() == -1:
            print('No input data')
            return
        else:
            index = self.inputui.inputdataComboBox.currentIndex()
            os.startfile(self.filesnamelist[index])


    def adddataTotable(self):
        self.cleardata()

        self._disconnect_cell_changed()        # 安全断开信号

        datanum = 0  # 数据总数计数器
        for tem in range(0, len(self.selectedfileslist)):
            filestemp = self.selectedfileslist[tem]
            dataname, data = readfile(filestemp)
            # 调试:单个文件读取结果
            # print(f'[Input.adddataTotable] 文件 "{os.path.basename(filestemp)}" 读取到 {len(dataname)} 条数据, dataname={dataname}')
            for i in range(0, len(dataname)):
                self.plotdataname.append(dataname[i])
                self.plotdata.append(data[i])

                row = self.inputui.tableWidget.rowCount()
                self.inputui.tableWidget.insertRow(row)

                # 创建并设置复选框项
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsEnabled)  # 添加这行
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, Qt.CheckState.Checked)  # 保存初始状态
                self.inputui.tableWidget.setItem(datanum, 0, item)

                # 设置路径和文件名（跨平台兼容）
                path = os.path.dirname(filestemp) + os.sep
                filename = os.path.basename(filestemp)

                # 设置各列数据
                self.inputui.tableWidget.setItem(datanum, 1, QTableWidgetItem(str(dataname[i])))
                self.inputui.tableWidget.setItem(datanum, 2, QTableWidgetItem(str(filename)))
                self.inputui.tableWidget.setItem(datanum, 3, QTableWidgetItem(''))  # comments
                self.inputui.tableWidget.setItem(datanum, 4, QTableWidgetItem(str(path)))

                datanum += 1

        # 调试:全部数据加载完成
        # print(f'[Input.adddataTotable] 加载完成, plotdataname={self.plotdataname}, plotdata 长度={len(self.plotdata)}')

        # 重新连接信号
        self._connect_cell_changed()


    def cleartable(self):  ##清除表格中输入的数据
            # 安全断开信号
        self._disconnect_cell_changed()

        self.inputui.tableWidget.clearContents()
        rows = self.inputui.tableWidget.rowCount()
        for row in range(rows, -1, -1):
            self.inputui.tableWidget.removeRow(row)

        # 重新连接信号
        self._connect_cell_changed()


    def onCellChanged(self, row, column):
        item = self.inputui.tableWidget.item(row, column)
        if not item:
            return
        # 调试:cell 变化
        # if column == 0:
        #     print(f'[Input.onCellChanged] 复选框变化 row={row}, currentState={item.checkState()}')
        # elif column == 1:
        #     print(f'[Input.onCellChanged] 数据名变化 row={row}, text={item.text()}')
        if column == 0:  # 检查框列
            lastState = item.data(Qt.ItemDataRole.UserRole)
            currentState = item.checkState()
            if currentState != lastState:
                self.fresh()
                item.setData(Qt.ItemDataRole.UserRole, currentState)
        elif column == 1:  # 数据名称列
            new_name = item.text()
            # 关键修复:plotdataname 已被 ensure_paired_form 成对化(每条数据 2 项)
            # 表格行 N 对应成对化后的 2N (原始) 和 2N+1 (合成) 两个位置
            # 必须同时更新,否则 Figure 过滤 synthetic 后只能看到一半的修改
            paired_idx_original = 2 * row
            paired_idx_synthetic = 2 * row + 1
            if paired_idx_original < len(self.plotdataname):
                self.plotdataname[paired_idx_original] = new_name
            if paired_idx_synthetic < len(self.plotdataname):
                self.plotdataname[paired_idx_synthetic] = new_name
        self.sendsignal()


    def _disconnect_cell_changed(self):
        """安全地断开 cellChanged 信号"""
        if self._signal_connected:
            try:
                self.inputui.tableWidget.cellChanged.disconnect(self.onCellChanged)
                self._signal_connected = False
            except Exception as e:
                print(f"Warning: Failed to disconnect signal: {e}")

    def _connect_cell_changed(self):
        """安全地连接 cellChanged 信号"""
        if not self._signal_connected:
            self.inputui.tableWidget.cellChanged.connect(self.onCellChanged)
            self._signal_connected = True