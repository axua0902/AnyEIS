"""
Data Validation Functions for EIS/DS Analysis
EIS/DS分析数据验证函数

Data Structure Analysis / 数据结构分析:
Based on the validation functions, the expected data structures are:
根据验证函数分析，预期的数据结构如下：

1. Main Data Lists / 主要数据列表:
   - selectlist: List of selection flags/indices (1=selected, 0=not selected) / 选择标志/索引列表(1=已选择,0=未选择）
     Example / 示例: [1, 1, 1, 1, 1]
   
   - prodataname: List of processing data names / 处理数据名称列表  
     Example / 示例: ['name1', 'name2', 'name3', 'name4', 'name5']
   
   - prodata: List of pandas DataFrames containing processing data / 包含处理数据的pandas DataFrame列表
     Example / 示例: Each DataFrame contains EIS measurement data with columns:
     每个DataFrame包含EIS/DS测量数据,列包括：
     * FREQ[Hz]: Frequency in Hz / 频率（赫兹）
     * Z[ohm]: Impedance magnitude in ohms / 阻抗幅值（欧姆）
     * PHASE[deg]: Phase angle in degrees / 相位角（度）
     * Rs[ohm]: Series resistance in ohms / 串联电阻（欧姆）
     * X[ohm]: Reactance in ohms / 电抗（欧姆）
     Typical size: 200 rows x 5 columns / 典型尺寸:200行x5列
   
   - refdata: List of pandas DataFrames containing reference data / 包含参考数据的pandas DataFrame列表
     Same structure as prodata, used for comparison / 与prodata结构相同,用于比较
   
   - dataInfo: Additional data information list (can be empty) / 附加数据信息列表（可为空）
     Example / 示例: []
     
        print(self.selectlist)
        [1, 1, 1, 1, 1]

        print(self.prodataname)
        ['name1', 'name2', 'name3', 'name4', 'name5']

        print(self.prodata)
        [       FREQ[Hz]    Z[ohm]  PHASE[deg]   Rs[ohm]    X[ohm]
        0       1000000  131.3670      -6.152  130.6110  -14.0793
        1       1000000  131.3790      -6.145  130.6240  -14.0628
        2       1100000  130.4170      -6.520  129.5740  -14.8085
        ..          ...       ...         ...       ...       ...
        198  2881700000  115.5250     -77.610   24.7885 -112.8340
        199  3000000000  126.9770     -78.427   25.4741 -124.3950
            [200 rows x 5 columns],

        print(self.refdata)
        [       FREQ[Hz]    Z[ohm]  PHASE[deg]   Rs[ohm]    X[ohm]
        0       1000000  138.3640      -8.027  137.0080  -19.3210
        1       1000000  138.3790      -8.016  137.0270  -19.2976
        2       1100000  136.9670      -8.388  135.5020  -19.9791
        ..          ...       ...         ...       ...       ...
        198  2881700000  116.7160     -77.330   25.5997 -113.8740
        199  3000000000  128.3470     -78.126   26.4084 -125.6010
            [200 rows x 5 columns],

        print(self.dataInfo)
        []  

2. Data Format / 数据格式:
   - Each DataFrame has .shape attribute (rows, columns) / 每个DataFrame具有.shape属性(行数,列数）
     Example / 示例: (200, 5) - 200 data points with 5 measurement parameters
   - Each DataFrame has .columns attribute for column names / 每个DataFrame具有.columns属性用于列名
     Example / 示例: ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']
   - All DataFrames in the same list should have consistent dimensions / 同一列表中的所有DataFrame应具有一致的维度
   - Frequency range typically spans from 1MHz to 3GHz / 频率范围通常从1MHz到3GHz
   - Data contains both low and high frequency measurements / 数据包含低频和高频测量

3. EIS Data Columns / EIS数据列:
   - Frequency: FREQ[Hz] - Measurement frequency / 测量频率
   - Impedance: Z, absZ, Z[ohm], Z[OHM], Z[Ω] - Impedance magnitude / 阻抗幅值
   - Phase: PHASE, PHASE[deg], PHASE[DEG], ph - Phase angle (typically negative) / 相位角（通常为负值）
   - Resistance: Rs, Rs[ohm], RS[OHM], Rs[Ω], R -  resistance / 阻抗实部，电阻
   - Reactance: X, X[ohm], X[OHM], X[Ω] - Reactance (typically negative for capacitive) /阻抗虚部， 电抗（电容性通常为负值）

4. DS (Dielectric Spectroscopy) Data Columns / DS(介电谱)数据列:
   - Real Permittivity: PERMITTIVITY RE, EPSILON RE, EPS RE, epsRE[-] / 实部介电常数
   - Imaginary Permittivity: PERMITTIVITY IM, EPSILON IM, EPS IM, epsIM[-] / 虚部介电常数  
   - Real Conductivity: CONDUCTIVITY RE, SIGMA RE, SIG RE, sigmaRE[S/m] / 实部电导率
   - Imaginary Conductivity: CONDUCTIVITY IM, SIGMA IM, SIG IM, sigmaIM[S/m] / 虚部电导率

5. Validation Rules / 验证规则:
   - All related lists must have equal lengths / 所有相关列表必须具有相等的长度
     Example / 示例: len(selectlist) = len(prodataname) = len(prodata) = 5
   - All DataFrames in a list must have same row count / 列表中所有DataFrame必须具有相同的行数
     Example / 示例: All DataFrames have 200 rows / 所有DataFrame都有200行
   - All DataFrames in a list must have same column count / 列表中所有DataFrame必须具有相同的列数
     Example / 示例: All DataFrames have 5 columns / 所有DataFrame都有5列
   - Processing data and reference data must have compatible dimensions / 处理数据和参考数据必须具有兼容的维度

"""

##################################数据检查#############################
def check1(selectlist, prodataname, prodata):  # 全部输入数据检查
    if len(selectlist) == len(prodataname) and len(prodataname) == len(prodata):
        return 1
    else:
        print('Data Check Error')  ##输出到状态栏
        return 0

def check2(prodata):  # 输入数据内部检查
    if len(prodata) > 0:
        rownumtot = prodata[0].shape[0]  ##数据总行数
        colnumtot = prodata[0].shape[1]  ##数据总列数
        for numtemp in range(1, len(prodata)):
            if rownumtot != prodata[numtemp].shape[0]:  ##数据总行数
                print('Data Error please check row number of data')  ##输出到状态栏
                return 0
            else:
                print('check2 pass')
                return 1
        for numtemp in range(1, len(prodata)):
            if colnumtot != prodata[numtemp].shape[1]:  ##数据总列数
                print('Data Error please check colnum number of data')  ##输出到状态栏
                return 0
            else:
                print('check2 pass')
                return 1
    else:
        print('No data Input')
        return 1

def check3(data, namelist):  # 参考数据之间检查
    print(namelist, len(data))
    if namelist[0] == 'empty':
        return 1
    else:
        if len(data) > 0:
            rownumtot = data[0].shape[0]  ##数据总行数
            colnumtot = data[0].shape[1]  ##数据总列数
            for numtemp in range(0, len(data)):
                if rownumtot != data[numtemp].shape[0]:  ##数据总行数
                    print('Data Error please check row number of data')  ##输出到状态栏
                    return 0
                else:
                    print('check3 pass')
                    return 1
            for numtemp in range(1, len(data)):
                if colnumtot != data[numtemp].shape[1]:  ##数据总列数
                    print('Data Error please check colnum number of data')  ##输出到状态栏
                    return 0
                else:
                    print('check3 pass')
                    return 1
        else:
            print('No data Input')
            return 1

def check4(prodata, refdata):  # 参考数据与输入数据比较检查
    prodataRownumtot = list()
    refdataRownumtot = list()
    prodataColnumtot = list()
    refdataColnumtot = list()

    for i in range(0, len(prodata)):
        prodataRownumtot.append(prodata[i].shape[0])
        prodataColnumtot.append(prodata[i].shape[1])

    for i in range(0, len(refdata)):
        refdataRownumtot.append(refdata[i].shape[0])
        refdataColnumtot.append(refdata[i].shape[1])

    a = [x for x in prodataRownumtot if x in refdataRownumtot]
    b = [y for y in (prodataRownumtot + refdataRownumtot) if y not in a]

    a1 = [x for x in prodataColnumtot if x in refdataColnumtot]
    b1 = [y for y in (prodataColnumtot + refdataColnumtot) if y not in a1]

    if len(b) != 0:
        print('prodata and refdata error please check colnum number of data')
        return 0
    elif len(b1) != 0:
        print('prodata and refdata error please check colnum number of data')
        return 0
    else:
        print('check4 pass')
        return 1


def check5(data):  #判断数据类型
    """判断输入数据是EIS数据还是DS数据"""
    if not data or len(data) == 0:
        return 'UNKNOWN'
    
    # EIS和DS数据的特征列名
    eis_columns = {
        'Z': ['Z', 'absZ', 'Z[ohm]', 'Z[OHM]', 'Z[Ω]'],
        'PHASE': ['PHASE', 'PHASE[deg]', 'PHASE[DEG]', 'ph'],
        'Rs': ['Rs', 'Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'R'],
        'X': ['X', 'X[ohm]', 'X[OHM]', 'X[Ω]']
    }
    
    ds_columns = {
        'epsRE': ['PERMITTIVITY RE', 'EPSILON RE', 'EPS RE','EPS RE[-]', 'PERMITTIVITYRE', 'EPSILONRE', 'EPSRE', 'epsRE[-]'],
        'epsIM': ['PERMITTIVITY IM', 'EPSILON IM', 'EPS IM','EPS IM[-]', 'PERMITTIVITYIM', 'EPSILONIM', 'EPSIM', 'epsIM[-]'],
        'sigmaRE': ['CONDUCTIVITY RE', 'SIGMA RE', 'SIG RE','SIGMA RE[S/m]', 'CONDUCTIVITYRE', 'SIGMARE', 'SIGRE', 'sigmaRE[S/m]'],
        'sigmaIM': ['CONDUCTIVITY IM', 'SIGMA IM', 'SIG IM','SIGMA IM[S/m]', 'CONDUCTIVITYIM', 'SIGMAIM', 'SIGIM', 'sigmaIM[S/m]']
    }
    
    # 获取列名
    if not hasattr(data[0], 'columns'):
        return 'UNKNOWN'
    column_names = [str(col).strip() for col in data[0].columns]
    
    # 检查匹配的特征列
    def check_match(col_name, name_list):
        return col_name in name_list or col_name.upper() in [name.upper() for name in name_list]
    
    eis_matches = sum(1 for key, names in eis_columns.items() 
                        if any(check_match(col, names) for col in column_names))
    
    ds_matches = sum(1 for key, names in ds_columns.items() 
                    if any(check_match(col, names) for col in column_names))
    
    # 判断数据类型
    if eis_matches >= 2:
        return 'EIS'
    elif ds_matches >= 2:
        return 'DS'
    else:
        return 'UNKNOWN'
    
##################################数据检查#############################




