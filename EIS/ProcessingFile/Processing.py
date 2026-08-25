import sys
import os

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from EIS.ProcessingFile.ProcessingUI import DataprocessUI#, RefedataUI

from EIS.InputFile.Inputfun import readfile
from EIS.ProcessingFile.Processingfun import calibrate,paraplate,threesolutions,TLcalibrate,DieMat,TLcalculateEPS,TLcalculateEIS
from EIS.Other.Datacheck import check1,check2,check3,check4,check5

# 项目根目录（本文件位于 EIS/ProcessingFile/，向上 3 层即为项目根）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 参考文件对话框默认打开：TestData/Processing/DataProcess
_DEFAULT_REF_DIR = os.path.join(_PROJECT_ROOT, 'TestData', 'Processing', 'DataProcess')

"""
数据流动过程说明 (Data Flow Process):

1. 输入数据 (Input Data):
   - getsingal() 接收外部数据
   - 存储在: self.selectlist, self.prodataname, self.prodata, self.dataInfo

2. 参考数据 (Reference Data):
   - GetrefFiles() 读取参考文件
   - 存储在: self.refdata, self.refdataname

3. 数据处理 (Data Processing):
   - processdata() 根据 processCheckBox 状态决定处理方式
   - 未选中: 直接输出原始数据
   - 选中: 调用 processing() 进行数据处理

4. 输出数据 (Output Data):
   - 未处理: 直接输出输入数据
   - 已处理: 输出原始数据+处理数据，存储在 self.resultsselectlist, self.resultsdataname, self.resultsdata
   - sendsignal() 发送最终数据

5. 数据检查 (Data Validation):
   - check1(), check2(), check3(), check4() 验证数据完整性
   - check_data_status() 显示当前数据状态
"""


class Dataprocess(QWidget, DataprocessUI):
    Apdatasignal = Signal(list, list, list, list)

    def __init__(self, parent=None):
        super(Dataprocess, self).__init__(parent)
        ########变量申明###############
        self.initdata()
        ########变量申明###############

        ###########初始化###################

        self.processui=DataprocessUI()
        self.processui.set_parent_processing_instance(self)  # 设置父实例引用
        self.processui.dataprocessUI(self)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 可选：移除边距
        self.main_layout.addWidget(self.processui.contents)  # 添加 UI 内容到布局
       ###########初始化###################

        # 连接信号和槽
        self.processui.processdataBtn.clicked.connect(self.processdata)
        self.processui.outputdataBtn2.clicked.connect(self.originaldata)
        self.processui.outputdataBtn3.clicked.connect(self.processeddata)
        self.processui.processmethodComboBox.currentIndexChanged.connect(self.processmethodselec)



    def initdata(self):
        # Input data (received from getsingal())
        self.selectlist = []           # 输入数据选择列表
        self.prodataname = []          # 输入数据名称列表
        self.prodata = []              # 输入数据列表
        self.dataInfo = []             # 输入数据信息
        
        # Processed/Output data
        self.resultsselectlist = []   # 输出数据选择列表
        self.resultsdata = []         # 输出数据列表
        self.resultsdataname = []     # 输出数据名称列表
        self.resultsdataInfo = []     # 输出数据信息

        # Reference data
        self.refdata = []             # 参考数据列表
        self.refdataname = []         # 参考数据名称列表



    #################################信号###########################
    def getsingal(self, inputselectlist, inputdataname, inputdata, inputmessage):  #####获得数据######
        """接收输入数据信号"""
        self.selectlist = inputselectlist.copy() if inputselectlist else []
        self.prodataname = inputdataname.copy() if inputdataname else []
        self.prodata = inputdata.copy() if inputdata else []
        self.dataInfo = inputmessage.copy() if inputmessage else []

        print('process get data',self.selectlist, self.prodataname, len(self.prodata), self.dataInfo)
        # print(self.prodata)

        self.auto_forward_data()

    def sendsignal(self, outputselectlist, outputdataname, outputdata, outputmessage):
        """发送输出数据信号"""
        self.Apdatasignal.emit(outputselectlist, outputdataname, outputdata, outputmessage)

        print('process emit data',outputselectlist, outputdataname, len(outputdata), outputmessage)
        # print(outputselectlist, outputdataname, len(outputdata))
        # print(self.outputdata)

    def auto_forward_data(self):
        """自动转发数据到下一个模块"""
        if len(self.prodata) > 0:
            if self.processui.processCheckBox.isChecked():
                # 如果启用了处理功能，等待用户手动处理
                pass
                print("Processing enabled - waiting for manual processing")
            else:
                # 如果未启用处理功能，自动转发原始数据
                self.sendsignal(self.selectlist.copy(), self.prodataname.copy(),
                            self.prodata.copy(), self.dataInfo.copy())
                print("Processing disabled - auto-forwarding original data")

    #################################信号###########################



    ##########################界面选择############################
    def processmethodselec(self):
        currentmethod = self.processui.processmethodComboBox.currentText()
        if currentmethod == 'System Calibration':
            self.processui.processing_method_uis.ui_calibration()
        elif currentmethod == 'Dielectric Material Method':
            self.processui.processing_method_uis.ui_DielectricMaterial()
        elif currentmethod == 'Parallel Plate Capacitor':
            self.processui.processing_method_uis.ui_ParallelPlate()
        elif currentmethod == 'RF Impedance Calibration':
            self.processui.processing_method_uis.ui_TransmissionLine()
        elif currentmethod == 'RF Dielectric Calculation':
            self.processui.processing_method_uis.ui_TransmissionLine_cal()

        elif currentmethod == 'RF Impedance Calculation':
            self.processui.processing_method_uis.ui_TransmissionLine_EIScal()
        elif currentmethod == 'Three-Solution Method':
            self.processui.processing_method_uis.ui_ThreeSolution()
        elif currentmethod == 'K-K for DS':
            self.processui.processing_method_uis.uiKKDS()
        elif currentmethod == 'K-K for EIS':
            self.processui.processing_method_uis.uiKKEIS()
        elif currentmethod == 'Other':
            self.processui.processing_method_uis.uiOther()
        else:
            self.processui.freshprocessUI()



    ###############################参考数据收集#############################

    def get_parameters_info(self):
        """获取当前处理方法的完整信息（包括处理参数和参考数据信息）"""
        current_method = self.processui.processmethodComboBox.currentText()
        parameters_info = {}

        if current_method == 'Parallel Plate Capacitor':            # 平行板电容方法需要几何常数参数，不需要参考数据
            parameters_info['processing_parameters'] = {
                'geometric_constant': getattr(self.processui, 'GeomconstantTextEdit', None).text() if hasattr(self.processui, 'GeomconstantTextEdit') else ''
            }

        elif current_method == 'System Calibration':            # 校准方法使用开路-短路-负载校准
            parameters_info['processing_parameters'] = {}
            solution_info = [
                {'solution_index': 0, 'name': 'open'},
                {'solution_index': 1, 'name': 'short'},
                {'solution_index': 2, 'name': 'load'}
            ]
            parameters_info['solution_parameters'] = solution_info

        elif current_method == 'Dielectric Material Method':            # 介电材料方法使用两种参考溶液
            parameters_info['processing_parameters'] = {}
            parameters_info['solution_parameters'] = self._collect_solution_info(2)

        elif current_method == 'RF Impedance Calibration':            # 传输线方法需要几何参数和一种参考溶液
            parameters_info['processing_parameters'] = {
                'geometric_constant': getattr(self.processui, 'GeomconstantTextEdit', None).text() if hasattr(self.processui, 'GeomconstantTextEdit') else '',
                'character_impedance': getattr(self.processui, 'CharaImpedanceTextEdit', None).text() if hasattr(self.processui, 'CharaImpedanceTextEdit') else '',
                'electrode_length': getattr(self.processui, 'ElectLengthTextEdit', None).text() if hasattr(self.processui, 'ElectLengthTextEdit') else '',
                'solution_length': getattr(self.processui, 'SoluLengtTextEdit', None).text() if hasattr(self.processui, 'SoluLengtTextEdit') else ''
            }
            parameters_info['solution_parameters'] = self._collect_solution_info(1)

        elif current_method == 'RF Dielectric Calculation':            # 传输线方法需要几何参数和一种参考溶液
            parameters_info['processing_parameters'] = {
                'geometric_constant': getattr(self.processui, 'GeomconstantTextEdit', None).text() if hasattr(self.processui, 'GeomconstantTextEdit') else '',
                'solution_length': getattr(self.processui, 'SoluLengtTextEdit', None).text() if hasattr(self.processui, 'SoluLengtTextEdit') else ''
            }
            parameters_info['solution_parameters'] = self._collect_solution_info(1)

        elif current_method == 'RF Impedance Calculation':            # 传输线方法需要几何参数和一种参考溶液
            parameters_info['processing_parameters'] = {
                'geometric_constant': getattr(self.processui, 'GeomconstantTextEdit', None).text() if hasattr(self.processui, 'GeomconstantTextEdit') else '',
                'solution_length': getattr(self.processui, 'SoluLengtTextEdit', None).text() if hasattr(self.processui, 'SoluLengtTextEdit') else ''
            }
            parameters_info['solution_parameters'] = self._collect_solution_info(1)


        elif current_method == 'Three-Solution Method':            # 三溶液方法使用三种参考溶液
            parameters_info['processing_parameters'] = {}
            parameters_info['solution_parameters'] = self._collect_solution_info(3)
            
        elif current_method == 'K-K for DS':            # K-K验证用于介电谱数据，不需要参考数据
            parameters_info['processing_parameters'] = {
                'validation_parameter': getattr(self.processui, 'kkdsParamEdit', None).text() if hasattr(self.processui, 'kkdsParamEdit') else ''
            }

        elif current_method == 'K-K for EIS':            # K-K验证用于EIS数据，不需要参考数据
            parameters_info['processing_parameters'] = {
                'validation_parameter': getattr(self.processui, 'kkeisParamEdit', None).text() if hasattr(self.processui, 'kkeisParamEdit') else ''
            }
           
        else:
            parameters_info['processing_parameters'] = {}            # 未选择方法或未知方法


        return parameters_info


    def _collect_solution_info(self, num_solutions):
        """收集溶液信息的辅助函数"""
        solution_info = []
        if hasattr(self.processui, 'refsoluionComboBox') and hasattr(self.processui, 'concentrationTextEdit') and hasattr(self.processui, 'temperatureTextEdit'):
            for i in range(min(num_solutions, len(self.processui.refsoluionComboBox))):
                if i < len(self.processui.concentrationTextEdit) and i < len(self.processui.temperatureTextEdit):
                    solution_info.append({
                        'solution_index': i,
                        'name': self.processui.refsoluionComboBox[i].currentText() if hasattr(self.processui.refsoluionComboBox[i], 'currentText') else '',
                        'concentration':  float(self.processui.concentrationTextEdit[i].text()) if hasattr(self.processui.concentrationTextEdit[i], 'text') else '',
                        'temperature':  float(self.processui.temperatureTextEdit[i].text()) if hasattr(self.processui.temperatureTextEdit[i], 'text') else ''
                    })
        return solution_info





    ###############################处理#############################

    def processdata(self):
        """主要的数据处理函数"""
        # 检查输入数据是否有效
        if len(self.prodata) == 0:
            print('No input data available')
            return
        if check1(self.selectlist, self.prodataname, self.prodata) == 0 or check2(self.prodata) == 0:
            print('Input data error - please check input data')
            return
        else:
            print('Processing enabled - processing data')
            self.processing()
            outputselectlist = self.resultsselectlist.copy()
            outputdataname = self.resultsdataname.copy()
            outputdata = self.resultsdata.copy()
            outputmessage = self.create_processed_datainfo()                # 创建包含处理信息的输出消息
            self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)


    def processing(self):
        currentmethod = self.processui.processmethodComboBox.currentText()
        
        if currentmethod == 'Parallel Plate Capacitor':  ####计算平行板电容的介电常数
            if check5(self.prodata) == 'EIS' or check5(self.prodata) == 'DS':
                params_info = self.get_parameters_info()  # 获取参数
                Gf = float(params_info['processing_parameters']['geometric_constant'])
                processresults = paraplate(self.prodata, Gf)           #数据处理
                self.databasecreat(processresults)                     #结果数据生成
            else:
                QMessageBox.warning(self, "Warning", f"Input data is not EIS or DS data")
                return


        elif currentmethod == 'System Calibration':  # open short load校准电极
            if check3(self.refdata, self.refdataname) == 1 and check5(self.refdata) == 'EIS':
                params_info = self.get_parameters_info()  # 获取参数
                print('params:',params_info)
                processresults = calibrate(self.refdata, self.prodata, params_info)
                self.databasecreat(processresults)
            else:
                QMessageBox.warning(self, "Warning", f"Reference data error")
                return


        elif currentmethod == 'Dielectric Material Method':  ###使用两种参考溶液计算介电常数
            if check3(self.refdata, self.refdataname) == 1 and check5(self.refdata) == 'EIS':
                params_info = self.get_parameters_info()  # 获取参数
                print('params:',params_info)
                processresults = DieMat(self.refdata, self.prodata, params_info)
                self.databasecreat(processresults)
            else:
                print('Reference data error')
                return

        elif currentmethod == 'Three-Solution Method':  ###使用三中参考溶液计算介电常数
            if check3(self.refdata, self.refdataname) == 1 and check5(self.refdata) == 'EIS':
                params_info = self.get_parameters_info()  # 获取参数
                print('params:',params_info)
                processresults = threesolutions(self.refdata, self.prodata, params_info)
                self.databasecreat(processresults)
            else:
                print('Reference data error')
                return


        elif currentmethod == 'RF Impedance Calibration':  ####基于传输线理论校准电极
            if check3(self.refdata, self.refdataname) == 1 and check5(self.refdata) == 'EIS':
                params_info = self.get_parameters_info()  # 获取参数
                print('params:',params_info)
                processresults = TLcalibrate(self.refdata, self.prodata, params_info)
                self.databasecreat(processresults)
            else:
                print('Reference data error')
                return

        elif currentmethod == 'RF Dielectric Calculation':  ####基于传输线理论计算复介电常数
            if check5(self.prodata) == 'EIS':
                params_info = self.get_parameters_info()  # 获取参数
                print('params:',params_info)
                processresults = TLcalculateEPS(self.prodata, params_info)
                self.databasecreat(processresults)
            else:
                print('Reference data error')
                return


        elif currentmethod == 'RF Impedance Calculation':  ####基于传输线理计算阻抗
            if check5(self.prodata) == 'DS':
                params_info = self.get_parameters_info()  # 获取参数
                print('params:',params_info)
                processresults = TLcalculateEIS(self.prodata, params_info)
                self.databasecreat(processresults)
            else:
                print('Reference data error')
                return







        elif currentmethod == 'K-K for EIS':
            parameters_info = self.get_parameters_info()  # 获取参数
            validation_param = parameters_info['processing_parameters']['validation_parameter']
            if validation_param:
                Gf = float(validation_param)
                processresults = paraplate(self.prodata, Gf)
                self.databasecreat(processresults)
            else:
                QMessageBox.warning(self, "Warning", "Validation parameter is required for K-K for EIS method")
                return
        else:
            return
        return
  
    ###############################处理#############################



    ##############################功能#############################
    def clearrefdata(self, num):
        """清除参考数据"""
        self.refdata = ['empty' for i in range(0, num)]
        self.refdataname = ['empty' for i in range(0, num)]
        print(f'Cleared reference data: {num} slots initialized')



    def databasecreat(self, processresults):
        """创建输出数据库：将原始数据和处理结果组合"""
                # 清空输出数据（但不清空输入数据和参考数据）
        self.resultsdata = []
        self.resultsdataname = []
        self.resultsselectlist = []
        
        # 组合原始数据和处理结果
        for i in range(0, len(self.prodata)):
            # 添加原始数据
            self.resultsdata.append(self.prodata[i])
            self.resultsdataname.append('Origin_' + self.prodataname[i])
            self.resultsselectlist.append(self.selectlist[i])
            
            # 添加处理后的数据
            self.resultsdata.append(processresults[i])
            self.resultsdataname.append('Processed_' + self.prodataname[i])
            self.resultsselectlist.append(self.selectlist[i])
        
        print(f'Database created: {len(self.resultsdata)} datasets (original + processed)')
        return



    def create_processed_datainfo(self):
        """创建包含处理信息的数据信息"""
        processed_datainfo = []
        current_method = self.processui.processmethodComboBox.currentText()
        
        # 为每个输出数据集创建对应的信息
        for i in range(len(self.resultsdataname)):
            if 'Origin_' in self.resultsdataname[i]:
                # 原始数据，使用原始信息
                original_index = i // 2  # 每两个输出对应一个输入
                if original_index < len(self.dataInfo):
                    processed_datainfo.append(self.dataInfo[original_index].copy())
                else:
                    processed_datainfo.append({})
            else:
                # 处理数据，添加处理信息
                original_index = i // 2
                if original_index < len(self.dataInfo):
                    info = self.dataInfo[original_index].copy()
                else:
                    info = {}
                       
        return processed_datainfo


    def ClearrefFiles(self, ComboBoxNum):  ##清除输入的参考数据
        """清除指定位置的参考文件"""
        if self.processui.refdataComboBox[ComboBoxNum - 1].count() != 0:
            self.processui.refdataComboBox[ComboBoxNum - 1].clear()  ##清除原有数据
            self.refdataname[ComboBoxNum - 1] = 'empty'
            self.refdata[ComboBoxNum - 1] = 'empty'
            print(f'Cleared reference file {ComboBoxNum}: {self.refdataname}')
            return
        else:
            print(f'No reference file to clear at position {ComboBoxNum}')
            return

    def GetrefFiles(self, ComboBoxNum):  ##inputdataButton输入新数据
        """获取参考文件"""
        reffilename, _ = QFileDialog.getOpenFileName(self, 'Open File', _DEFAULT_REF_DIR,
                                                     "Data Files (*.xlsx *.xls *.csv);;Text Files (*.txt);;All Files (*)")
        print(f'Selected reference file: {reffilename}')
        
        if not reffilename:  # Exit when no choice (empty string when cancelled)
            print("No file selected")
            return
        else:
            itemname = str(reffilename)
            if self.processui.refdataComboBox[ComboBoxNum - 1].count() != 0:
                self.processui.refdataComboBox[ComboBoxNum - 1].clear()  ##清除原有数据
                self.processui.refdataComboBox[ComboBoxNum - 1].addItem(itemname)
            else:
                self.processui.refdataComboBox[ComboBoxNum - 1].addItem(itemname)

            result = readfile(itemname)
            if result is not None:
                refdatanametemp, refdatatemp = result
                self.refdataname[ComboBoxNum - 1] = refdatanametemp
                self.refdata[ComboBoxNum - 1] = refdatatemp[0]
                print(f'Successfully loaded reference file {ComboBoxNum}: {refdatanametemp}')
            else:
                print(f"Failed to read reference file {ComboBoxNum}")
        return

    def OpenFiles(self, CobomBoxNum):  ###用外部工具打开文件
        """用外部工具打开参考文件"""
        if self.processui.refdataComboBox[CobomBoxNum - 1].currentIndex() == -1:
            print(f'No reference file selected at position {CobomBoxNum}')
            return
        else:
            filepath = self.processui.refdataComboBox[CobomBoxNum - 1].currentText()
            print(f'Opening reference file {CobomBoxNum}: {filepath}')
            os.startfile(filepath)
            return

    ##############################功能#############################



    def get_current_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")





    def originaldata(self):  # 'orignal date'
        outputselectlist = self.selectlist
        outputdataname = self.prodataname
        outputdata = self.prodata
        outputmessage = self.dataInfo
        self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)  # 输出信号
        return

    def processeddata(self):  # 'processed date'
        for i in range(0, len(self.resultsselectlist)):
            if i % 2 == 0:
                self.resultsselectlist[i] = 0
            else:
                pass
        outputselectlist = self.resultsselectlist
        outputdataname = self.resultsdataname
        outputdata = self.resultsdata
        # 创建包含处理信息的输出消息
        outputmessage = self.create_processed_datainfo()
        self.sendsignal(outputselectlist, outputdataname, outputdata, outputmessage)  # 输出信号
        return









# class Refedata(QWidget, RefedataUI):
#
#     global selectlist
#     global prodataname
#     global prodata
#
#     # datasignal=pyqtSignal(list,list,list)
#
#     def __init__(self, parent=None):
#         super(Refedata, self).__init__(parent)
#
#         self.refedataUI()

        # def sendsignal(self):
        #     outputselectlist=self.resultsselectlist
        #     outputdataname=self.resultsdataname
        #     outputdata=self.resultsdata
        #     outputmessage=self.dataInfo
        #     self.Apdatasignal.emit(outputselectlist,outputdataname,outputdata,outputmessage)####发送数据
        #     print('Data emitted in Processing')###输出到状态栏
        #     print(outputselectlist,outputdataname,len(outputdata))




