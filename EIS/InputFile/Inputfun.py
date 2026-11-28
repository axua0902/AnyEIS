from numpy import size
from pandas import read_csv, read_excel, DataFrame

from EIS.Other.Datacheck import check7_phase_unit, check8_z_consistency


def readcsvfile(filepath):
    ###############参考名表############
    FREQnamelist = ['FREQ', 'FREQ[Hz]', 'FREQ[HZ]', 'FREQ', 'F', 'FR', 'Frequency[Hz]', 'f']
    Znamelist = ['Z', 'absZ', 'Z[ohm]', 'Z[OHM]', 'Z[Ω]']
    PHASEnamelist = ['PHASE', 'PHASE[deg]', 'PHASE[DEG]', 'ph']
    Rsnamelist = ['Rs', 'Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'R']
    Xnamelist = ['X', 'X[ohm]', 'X[OHM]', 'X[Ω]']

    namelist = ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']
    ###############参考名表############

    dataname = list()  ###s数据名
    data = list()  ####s全部数据

    filename = filepath[filepath.rfind('/') + 1:-4]  ########数据名就是文件名
    dataname.append(filename)

    for skiprowstemp in range(0, 100):  ##########通过列名，判断起始行的
        columnstemp = list(read_csv(filepath, skiprows=skiprowstemp, nrows=0))
        if 'FREQ[Hz]' in columnstemp or 'No.' in columnstemp or 'f' in columnstemp:
            # print(columnstemp)
            columns = columnstemp
            # print(skiprowstemp)
            startcol = skiprowstemp
            break
        else:
            pass

    df = read_csv(filepath, skiprows=startcol, index_col=None)  # Read data

    # 列名精确匹配(忽略大小写/首尾空格), 不再用子串匹配,
    # 避免 'Z' 命中 'Zreal'、'R' 命中 'RPM' 之类的误配。
    def _normcol(nametemp):
        return str(nametemp).strip().upper()

    def _pickcolumn(candidates):
        candkeys = {_normcol(c) for c in candidates}
        for usecolstemp in columns:
            if _normcol(usecolstemp) in candkeys:
                return usecolstemp
        return None

    freqcol = _pickcolumn(FREQnamelist)
    Zcol = _pickcolumn(Znamelist)
    phycol = _pickcolumn(PHASEnamelist)
    Rscol = _pickcolumn(Rsnamelist)
    Xcol = _pickcolumn(Xnamelist)

    colpairs = [(namelist[0], freqcol), (namelist[1], Zcol), (namelist[2], phycol),
                (namelist[3], Rscol), (namelist[4], Xcol)]
    missing = [nametemp for nametemp, coltemp in colpairs if coltemp is None]
    if missing:
        print('[readcsvfile] WARNING: "%s" 缺少列 %s' % (filename, missing))

    datadict = {nametemp: df.loc[:, coltemp] for nametemp, coltemp in colpairs
                if coltemp is not None}  #######组合生成数据
    data.append(DataFrame(datadict))

    # PHASE 单位自检: PHASE[deg] 列误存弧度时自动换算为度(check7)
    check7_phase_unit(data[0], dataname[0])
    # Z 列一致性自检: Z[ohm] 误存实部(real)而非幅值时告警(check8)
    check8_z_consistency(data[0], dataname[0])

    return dataname, data


def readexcelfile(filepath):
    ###############参考名表############
    FREQnamelist = ['FREQ', 'FREQ[Hz]', 'FREQ[HZ]', 'FREQ', 'F', 'FR', 'Frequency[Hz]', 'f']
    Znamelist = ['Z', 'absZ', 'Z[ohm]', 'Z[OHM]', 'Z[Ω]']
    PHASEnamelist = ['PHASE', 'PHASE[deg]', 'PHASE[DEG]', 'ph']
    Rsnamelist = ['Rs', 'Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'R']
    Xnamelist = ['X', 'X[ohm]', 'X[OHM]', 'X[Ω]']

    Impedancenamelist = ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']

    perREnamelist = ['PERMITTIVITY RE', 'EPSILON RE', 'EPS RE', 'PERMITTIVITYRE', 'EPSILONRE', 'EPSRE', 'epsRE[-]']
    perIMnamelist = ['PERMITTIVITY IM', 'EPSILON IM', 'EPS IM', 'PERMITTIVITYIM', 'EPSILONIM', 'EPSIM', 'epsIM[-]']
    conREnamelist = ['CONDUCTIVITY RE', 'SIGMA RE', 'SIG RE', 'CONDUCTIVITYRE', 'SIGMARE', 'SIGRE', 'sigmaRE[S/m]']
    conIMnamelist = ['CONDUCTIVITY IM', 'SIGMA IM', 'SIG IM', 'CONDUCTIVITYIM', 'SIGMAIM', 'SIGIM', 'sigmaIM[S/m]']

    Dielectricnamelist = ['FREQ[Hz]', 'epsRE[-]', 'epsIM[-]', 'sigmaRE[S/m]', 'sigmaIM[S/m]']
    ###############参考名表############
    emptycolnum = 2  # 数据间隔列数

    data = list()  ####s全部数据
    datanamelist = list()  ###s数据名
    # columnslist=list()###s数据列名

    ########## 获得数据名称 ##########
    datanamebase = read_excel(filepath, sheet_name=0, engine='openpyxl').iloc[:0]  #
    colnumtot = size(datanamebase.columns)  ##数据总列数

    for colstemp in range(colnumtot):
        t1 = 'Unnamed: ' not in datanamebase.columns[colstemp]
        t2 = '.csv' not in datanamebase.columns[colstemp]
        t3 = '.CSV' not in datanamebase.columns[colstemp]
        if t1 != 0 and t2 != 0 and t3 != 0:
            datanamelist.append(datanamebase.columns[colstemp])
        else:
            pass
    ########## 获得数据名称 ##########

    datanum = len(datanamelist)  ####数据数
    colnum = int((colnumtot - emptycolnum * (datanum - 1)) / datanum)  ###单一数据列数
    data = [0 for i in range(0, datanum)]

    for temdata in range(0, datanum):
        coltemp = [i + temdata * (emptycolnum + colnum) for i in range(0, colnum)]
        # sheetnamelist=['Sheet1','Experiment']
        # for sheetnametemp in range(0,len())
        # data[temdata]=read_excel(filepath,'Sheet1',engine='openpyxl',header=1,usecols=coltemp)
        data[temdata] = read_excel(filepath, sheet_name=0, engine='openpyxl', header=1, usecols=coltemp)
    ########## 读取数据 ##########

    ########## 读取数据列名 ##########
    # 仅对 EIS/DS 数据重命名: 以"能识别出频率列"为前提。
    # 一般数据(任意物理量, 如 v[mL] vs Z RE/IM)没有频率列, 原样保留列名。
    # 重命名按物理列位置写入 columnsname[j], 不再写语义下标, 避免列顺序非标准时错位。
    colnum = size(data[0].columns)
    # 同一 xlsx 的多个数据块共享第 1 行表头, 后续块表头可能为空(Unnamed),
    # 因此统一用 data[0] 的列名作母表头(与原实现一致), 再逐块按物理位置重命名。
    nametemp_list = [str(col) for col in data[0].columns]
    has_freq = any(
        nametemp.upper() in FREQnamelist or nametemp in FREQnamelist
        for nametemp in nametemp_list
    )
    for temnamelist in range(0, datanum):
        if not has_freq:  # 一般数据: 不改列名
            data[temnamelist].columns = nametemp_list
            continue
        columnsname = [0 for i in range(colnum)]
        for temcolumnsname in range(0, colnum):  #####命名数据列
            nametemp = nametemp_list[temcolumnsname]
            upname = nametemp.upper()
            #################impedance seies##########################
            if upname in FREQnamelist or nametemp in FREQnamelist:
                columnsname[temcolumnsname] = Impedancenamelist[0]
            elif upname in Znamelist or nametemp in Znamelist:
                columnsname[temcolumnsname] = Impedancenamelist[1]
            elif upname in PHASEnamelist or nametemp in PHASEnamelist:
                columnsname[temcolumnsname] = Impedancenamelist[2]
            elif upname in Rsnamelist or nametemp in Rsnamelist:
                columnsname[temcolumnsname] = Impedancenamelist[3]
            elif upname in Xnamelist or nametemp in Xnamelist:
                columnsname[temcolumnsname] = Impedancenamelist[4]
            ################impedance seies##########################
            ################Dielectric seies##########################
            elif upname in perREnamelist or nametemp in perREnamelist:
                columnsname[temcolumnsname] = Dielectricnamelist[1]
            elif upname in perIMnamelist or nametemp in perIMnamelist:
                columnsname[temcolumnsname] = Dielectricnamelist[2]
            elif upname in conREnamelist or nametemp in conREnamelist:
                columnsname[temcolumnsname] = Dielectricnamelist[3]
            elif upname in conIMnamelist or nametemp in conIMnamelist:
                columnsname[temcolumnsname] = Dielectricnamelist[4]
            ################Dielectricseies##########################
            else:
                columnsname[temcolumnsname] = nametemp
        data[temnamelist].columns = columnsname
        # 规整为标准列顺序: 下游绘图按位置取列(colname[0..4]), 仅改名不够
        targetcols = [nametemp for nametemp in Impedancenamelist if nametemp in columnsname]
        if len(targetcols) < 2:
            targetcols = [nametemp for nametemp in Dielectricnamelist if nametemp in columnsname]
        if len(targetcols) >= 2:
            data[temnamelist] = data[temnamelist][targetcols]
    ########## 读取数据列名 ##########

    # PHASE 单位自检: PHASE[deg] 列误存弧度时自动换算为度(check7)
    for temdata in range(0, datanum):
        check7_phase_unit(data[temdata], datanamelist[temdata])
        check8_z_consistency(data[temdata], datanamelist[temdata])

    return datanamelist, data


def readfile(filepath):
    if str(filepath[-3:]) == 'csv' or str(filepath[-3:]) == 'CSV':
        dataname, data = readcsvfile(filepath)
    elif str(filepath[-4:]) == 'xlsx':
        dataname, data = readexcelfile(filepath)
    else:
        return print('please check file type')
    return dataname, data


###########从输入的数字中获得用户选择的文件，数据序号
def extract_indices(text):
    teststr = str(text)  # 获得数据序号
    teststrtemp = teststr.replace("，", ",")  # 处理中文逗号
    teststrtemp = teststrtemp.replace(".", ",")  # 处理英文句号
    teststrtemp = teststrtemp.replace("。", ",")  # 处理中文句号
    chosedfiles = teststrtemp.split(",")  # 建立序号字符列表
    
    # Remove empty strings safely
    chosedfiles = [item.strip() for item in chosedfiles if item.strip()]
    
    testsorder = list()
    for tem in range(0, len(chosedfiles)):
        temstr1 = chosedfiles[tem]
        te = temstr1.find('-')
        if te == -1:
            try:
                testsorder.append(int(temstr1))
            except ValueError:
                print(f'Error: "{temstr1}" is not a valid number!')
                continue
        else:
            try:
                low = int(temstr1[0:te])
                up = int(temstr1[te + 1:])
                if low < up:
                    numstr = [i for i in range(low, up + 1)]
                    for nums in numstr:
                        testsorder.append(nums)
                else:
                    print(f'Error: Invalid range')
            except ValueError:
                print(f'Error: Invalid range format "{temstr1}"!')
                continue
    return testsorder


###########获得用户选择的文件，数据序号


def calculate(filepath):
    if filepath[-3:] == 'csv' or 'CSV':
        df = read_csv(filepath, skiprows=18, index_col=[0],
                      usecols=['No.', 'FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]'])  # Read data
        freq = df.loc[:, 'FREQ[Hz]']
        Z = df.loc[:, 'Z[ohm]']
        phy = df.loc[:, 'PHASE[deg]']
        Rs = df.loc[:, 'Rs[ohm]']
        X = df.loc[:, 'X[ohm]']
    else:
        if filepath[-3:] == 'xlsx' or 'xls':
            print('Waiting')
    return freq, Z, phy, Rs, X




def readCMSLdata(file,usecols,sr):
    # usecol1 = 'No'
    # usecol2 = 'FREQ'
    # usecol3 = 'Z0_RE'
    # usecol4 = 'Z0_IM'
    # usecol5 = 'gamma_RE'
    # usecol6 = 'gamma_IM'
    #
    # usecols = [usecol1, usecol2, usecol3, usecol4, usecol5, usecol6]
    n=size(file)
    db=[0 for i in range(n)]
    tem2=0
    for tem2 in range(0,n):
        df=read_csv(file[tem2],skiprows=sr,index_col=[0],usecols=usecols)#Read data
        db[tem2]=df
        data=db
    return data




















