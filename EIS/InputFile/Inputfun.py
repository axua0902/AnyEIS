from numpy import size
from pandas import read_csv, read_excel, DataFrame


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
    columslist = list()  ###s数据列名
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

    refecolomns = FREQnamelist + Znamelist + PHASEnamelist + Rsnamelist + Xnamelist
    for refecolsttemp in refecolomns:
        for usecolstemp in columns:
            if refecolsttemp in usecolstemp:
                # print(usecolstemp)
                columslist.append(usecolstemp)
            else:
                pass

    for i in range(0, len(columslist)):  # 分配数据
        if columslist[i].upper() in FREQnamelist or columslist[i] in FREQnamelist:
            freq = df.loc[:, columslist[i]]
        elif columslist[i].upper() in Znamelist or columslist[i] in Znamelist:
            Z = df.loc[:, columslist[i]]
        elif columslist[i].upper() in PHASEnamelist or columslist[i] in PHASEnamelist:
            phy = df.loc[:, columslist[i]]
        elif columslist[i].upper() in Rsnamelist or columslist[i] in Rsnamelist:
            Rs = df.loc[:, columslist[i]]
        elif columslist[i].upper() in Xnamelist or columslist[i] in Xnamelist:
            X = df.loc[:, columslist[i]]
        else:
            pass

    datadict = {namelist[0]: freq, namelist[1]: Z, namelist[2]: phy, namelist[3]: Rs, namelist[4]: X}  #######组合生成数据
    data.append(DataFrame(datadict))

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
    colnum = size(data[0].columns)
    columnsname = [0 for i in range(colnum)]
    for temnamelist in range(0, datanum):
        for temcolumnsname in range(0, colnum):  #####命名数据列
            nametemp = str(data[0].columns[temcolumnsname])
            #################impedance seies##########################
            if nametemp.upper() in FREQnamelist or nametemp in FREQnamelist:
                columnsname[0] = Impedancenamelist[0]
            elif nametemp.upper() in Znamelist or nametemp in Znamelist:
                columnsname[1] = Impedancenamelist[1]
            elif nametemp.upper() in PHASEnamelist or nametemp in PHASEnamelist:
                columnsname[2] = Impedancenamelist[2]
            elif nametemp.upper() in Rsnamelist or nametemp in Rsnamelist:
                columnsname[3] = Impedancenamelist[3]
            elif nametemp.upper() in Xnamelist or nametemp in Xnamelist:
                columnsname[4] = Impedancenamelist[4]
            ################impedance seies##########################
            ################Dielectric seies##########################
            elif nametemp.upper() in perREnamelist or nametemp in perREnamelist:
                columnsname[1] = Dielectricnamelist[1]
            elif nametemp.upper() in perIMnamelist or nametemp in perIMnamelist:
                columnsname[2] = Dielectricnamelist[2]
            elif nametemp.upper() in conREnamelist or nametemp in conREnamelist:
                columnsname[3] = Dielectricnamelist[3]
            elif nametemp.upper() in conIMnamelist or nametemp in conIMnamelist:
                columnsname[4] = Dielectricnamelist[4]
            ################Dielectricseies##########################
            else:
                columnsname[temcolumnsname] = nametemp
        data[temnamelist].columns = columnsname
    ########## 读取数据列名 ##########
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




















