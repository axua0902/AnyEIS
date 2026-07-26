import os

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal

from EIS.InputFile.ui_Input import InputdataUI
from EIS.InputFile.Inputfun import readfile,extract_indices
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
        self.datasignal.emit(self.selectlist, self.plotdataname, self.plotdata, self.dataInfo)  ####发送数据
        # column_headers = self.plotdata[0].columns.tolist() if self.plotdata else "No data available"
        # print('Inputdata emitted', self.selectlist, self.plotdataname, column_headers, self.dataInfo)

        print('Inputdata emitted',self.selectlist, self.plotdataname, len(self.plotdata), self.dataInfo)
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
        # 使用Settings中的working_path获取Data文件夹路径
        settings = Settings()
        working_path = settings.get_working_path()
        data_folder = os.path.join(working_path, 'Data')
        
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
        self.selectfiles()  ##########选择文件



    def deleteFiles(self):  ##删除导入的文件
        if self.inputui.inputdataComboBox.currentIndex() == -1:
            self.cleartable()
            self.filesnamelist = list()
            print('DeleteFiles No input data')
            return
        else:
            index = self.inputui.inputdataComboBox.currentIndex()
            self.inputui.inputdataComboBox.removeItem(index)  ########删除下拉列表中的文件
            self.filesnamelist.pop(index)                     ########删除文件列表中文件
            if len(self.filesnamelist) > 0:                   ##文件列表不为空时
                self.selectfiles()                            ##########选择文件
            else:                                             ###文件列表为空，删除表格
                self.cleartable()


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
                # 检查所有索引是否有效，而不只是最后一个
                if any(index >= len(self.filesnamelist) for index in self.nondash):
                    print('Please check selection')  ###输出到状态栏
                    self.inputui.allCheckBox.setChecked(True)  # 回退到全选
                    return
                else:
                    self.selectedfileslist = [self.filesnamelist[temp] for temp in self.nondash]
        else:  #########无选择
            print('Please select one')  ###输出到状态栏
            return

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
        self.inputui.allCheckBox.setChecked(True)
        self.inputui.selectallBtn.setChecked(True)
        #########清空输入的文件###############

        self.cleartable()           # 清空表格 

        ########清空变量###############
        self.plotdata = list()      # 所有数据 
        self.plotdataname = list()  # 被选中的数据名 
        self.selectlist = list()    # 被选中的数据 
        self.dataInfo = list()      # 数据信息 
        self.filesnamelist = list() # 打开的文件名列表 
        ########清空变量###############

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
        if column == 0:  # 检查框列
            lastState = item.data(Qt.ItemDataRole.UserRole)
            currentState = item.checkState()
            if currentState != lastState:
                self.fresh()
                item.setData(Qt.ItemDataRole.UserRole, currentState)
        elif column == 1:  # 数据名称列
            if row < len(self.plotdataname):
                self.plotdataname[row] = item.text()
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