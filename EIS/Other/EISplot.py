# -*- coding: utf-8 -*-
"""
Created on Wed May  2 19:49:21 2018

@author: zhang
"""


import numpy as np
import xlsxwriter
import pandas as pd
import matplotlib.pyplot as plt 




def readexceldata(file):
    emptycol=2#数据间隔列数
    n=np.size(file)#文件数
    
    namelist=[0 for i in range(n)]
    columnslist=[0 for i in range(n)]
    datalist=[0 for i in range(n)]
    
    for temfile in range(n):
        ########## 获得数据名称 ##########
        dataname=[0 for i in range(200)]
        datanamebase=pd.read_excel(file[temfile],'Sheet1').iloc[:0]#
        colnumtot=np.size(datanamebase.columns)##数据总列数

        tem=0
        for temcolnumtot in range(colnumtot):
            temstr=str(temcolnumtot)
            ctemstr='Unnamed: '+temstr
            if ctemstr!=datanamebase.columns[temcolnumtot]:
                if '.csv' not in datanamebase.columns[temcolnumtot]:
                    dataname[tem]=datanamebase.columns[temcolnumtot]
                    tem=tem+1  
                    
        while 0 in dataname:
            dataname.remove(0)       
        namelist[temfile]=dataname
        datanum=np.size(dataname)####数据数
        colnum=int((colnumtot-emptycol*(datanum-1))/datanum)###单一数据列数
            ########## 获得数据名称 ########## 
            
            ########## 读取数据 ##########   
        db=[0 for i in range(np.size(dataname))]
        for temdata in range(np.size(dataname)):
            db[temdata]=pd.read_excel(file[temfile],'Sheet1',header=1,usecols=[i+temdata*(emptycol+colnum) for i in range(colnum)])#
        datalist[temfile]=db
            ########## 读取数据 ##########

            ########## 读取数据列名 ##########
        colnum=np.size(db[0].columns)
        columnsname=[0 for i in range(colnum)]
        for temnamelist in range(datanum):
            for temcolumnsname in range(colnum):
                columnsname[temcolumnsname]=db[0].columns[temcolumnsname]
            datalist[temfile][temnamelist].columns=columnsname
            ########## 读取数据列名 ##########
        columnslist=columnsname

    return namelist,columnslist,datalist

def readanydata(dataname,database,curvenum,datanum):
    inputdata=[0 for i in range(curvenum)]
    tem=0
    for tem in range(0,curvenum):
        datadict={}
        indatadict={}
        tem1=0
        for tem1 in range(0,datanum):
            dicttemp={dataname[tem1]:database[datanum*tem+tem1]}
            indatadict=dict(datadict,**dicttemp) 
            datadict=indatadict 
        inputdata[tem]=pd.DataFrame(datadict)
    return inputdata

#################### Read data database  #######################   
def creatdataformat(dataname,database,curvenum,datanum):
    inputdata=[0 for i in range(curvenum)]
    tem=0
    for tem in range(0,curvenum):
        datadict={}
        indatadict={}
        tem1=0
        for tem1 in range(0,datanum):
            dicttemp={dataname[tem1]:database[datanum*tem+tem1]}
            indatadict=dict(datadict,**dicttemp) 
            datadict=indatadict 
        inputdata[tem]=pd.DataFrame(datadict)
    return inputdata
#################### Read data database  #######################

def creatanyfile(wbname,name,headings):########for creat excel file which data is from python calculate
    num=np.size(headings)
    n=np.size(name)
    workbook = xlsxwriter.Workbook(wbname)# 创建一个excel
    worksheet=workbook.add_worksheet()# 创建一个sheet
    tem1=0
    for tem1 in range(0,n):
        worksheet.write_row(0,tem1*(2+num),name[tem1])
        worksheet.write_row(1,tem1*(2+num),headings)
    return workbook,worksheet,n,num
########creat Nyquist line chart ################


#######write data ################
def writeanydata(workbook,worksheet,inputdata,dataname,curvenum,datanum):   
    tem2=0
    for tem2 in range(0,curvenum):
        tem1=0
        for tem1 in range(0,datanum):
             datanamewrite=dataname[tem1]
             dff=inputdata[tem2]
             col=dff.loc[:,datanamewrite]
             worksheet.write_column(2,tem1+tem2*(datanum+2), col)#0
#            worksheet.write_column(2,1+tem2*(num+2), y)#0
        #########WRITE data#########
    nu=[i for i in range(datanum+1)]
    stratcol=2
    datasize=np.size(col)
    return nu,stratcol,datasize
########write data ################
    

def Anyplot(workbook,worksheet,n,num,x,y,stratcol,endcol,infoX,infoY):

    chart_Anyplot = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight'
            })
    
    chart_Anyplot.set_size({'width': 454, 'height': 314,})
        
    chart_Anyplot.set_title({
        'overlay': True,
        'name_font':{'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37,'y': 0.01,}
        })
        
    temZ=0
    for temZ in  range(0,n):
        chart_Anyplot.add_series({
         'categories': ['Sheet1', stratcol, x+(num+2)*temZ, endcol, x+(num+2)*temZ],#'=Sheet1!$D$2:$D$201',# X axis 
         'values':     ['Sheet1', stratcol, y+(num+2)*temZ, endcol, y+(num+2)*temZ],#'=Sheet1!$E$2:$E$201',# Y axis 
    #    'marker': {
    #            'type': 'circle',
    #            'size': 5,
    #               },
        'line':{'width': 3},
         'name':['Sheet1', 0, 0+(num+2)*temZ]
        }) 
    
    
    chart_Anyplot.set_plotarea({
        'layout': {'x': 0.20,'y': 0.13,'width': 0.75, 'height': 0.68,}
        })
    
    if infoX[1]=='log':
        chart_Anyplot.set_x_axis({
                'name': infoX[0],# x axil 
                'name_font': {'size': 18},
                'num_font':{'size': 18},
                'num_format': '0E+0',
                'label_position': 'low',
                'name_layout': {'x': 0.52,'y': 1},
                'major_gridlines': {'visible': True,'line': {'width': 0.5}},
                'minor_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
                'major_tick_mark': 'none',
                'minor_tick_mark': 'outside',
                'min':infoX[2],# x min
                'max':infoX[3],#x max
                'minor_unit':10,
                'major_unit':10,
                'log_base': 10,#
                })
    else:
        chart_Anyplot.set_x_axis({
                'name': infoX[0],# x axil 
                'name_font': {'size': 18},
                'num_font':{'size': 18},
                'num_format': 'General',
                'label_position': 'low',
                'name_layout': {'x': 0.52,'y': 1},
                'major_gridlines': {'visible': True,'line': {'width': 0.5}},
                'minor_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
                'major_tick_mark': 'none',
                'minor_tick_mark': 'outside',
                # 'min':infoX[2],# x min
                # 'max':infoX[3],#x max
                })
        
    
    if infoY.get('Reverse') == True:
        if infoY[1]=='log':
            chart_Anyplot.set_y_axis({
                    'name': infoY[0],#y axil
                    'name_font': {'size': 18},
                    'num_font':{'size': 18},
                    'log_base': 10,
                    'reverse': True,
                    })
        else:
            chart_Anyplot.set_y_axis({
                    'name': infoY[0],#y axil
                    'name_font': {'size': 18},
                    'num_font':{'size': 18},
                    'reverse': True,
            #         'log_base': 10,
                    })
    else:
        if infoY[1]=='log':
            chart_Anyplot.set_y_axis({
                    'name': infoY[0],#y axil
                    'name_font': {'size': 18},
                    'num_font':{'size': 18},
                    'log_base': 10,
                    })
        else:
            chart_Anyplot.set_y_axis({
                    'name': infoY[0],#y axil
                    'name_font': {'size': 18},
                    'num_font':{'size': 18},
            #         'log_base': 10,
                    })
    
    
    chart_Anyplot.set_legend({
            'position': 'right',
            'font': {'size': 18,'color': 'black'},          
    #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}        
                      })
      
    worksheet.insert_chart('D6', chart_Anyplot)   
    ########creat Nyquist line chart ################  



########creat  chart ################
def creatEISfile(wbname,name,filerecord,headings):########for process the data from Impedance analyser
    datanum=np.size(headings)
    curvenum=np.size(name)
    workbook = xlsxwriter.Workbook(wbname)# 创建一个excel
    worksheet=workbook.add_worksheet()# 创建一个sheet
    tem1=0
    for tem1 in range(0,curvenum):
        worksheet.write_row(0,tem1*(2+datanum),name[tem1])
        worksheet.write_row(0,2+tem1*(2+datanum),filerecord[tem1])
        worksheet.write_row(1,tem1*(2+datanum),headings)
    return workbook,worksheet,curvenum,datanum
########creat  chart ################



def readEISdata(file):
    n=np.size(file)
    db=[0 for i in range(n)]
    tem2=0
    for tem2 in range(0,n):
        df=pd.read_csv(file[tem2],skiprows=18,index_col=[0],usecols=['No.','FREQ[Hz]','Z[ohm]','PHASE[deg]','Rs[ohm]','X[ohm]'])#Read data    
        db[tem2]=df
        data=db
    return data

########write data ################
def writeEISdata(workbook,worksheet,file,data):
    n=np.size(file)
    tem2=0
    for tem2 in range(0,n):
        df=data[tem2]
        freq=df.loc[:,'FREQ[Hz]']
        Z=df.loc[:,'Z[ohm]']
        phy=df.loc[:,'PHASE[deg]']
        Rs=df.loc[:,'Rs[ohm]']
        X=df.loc[:,'X[ohm]']
        #########WRITE data#########
        worksheet.write_column(2,0+tem2*7, freq)#0
        worksheet.write_column(2,1+tem2*7, Z)#1
        worksheet.write_column(2,2+tem2*7, phy)#2
        worksheet.write_column(2,3+tem2*7, Rs)#3
        worksheet.write_column(2,4+tem2*7, X)#4
        #########WRITE data#########
        nu=[0,1,2,3,4]
        stratcol=2
        freqsize=np.size(freq)
    return nu,stratcol,freqsize
########write data ################




def Nyquist(workbook,worksheet,n,x,y,stratcol,endcol):
    chart_Nyquist = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight'
            })
    
    chart_Nyquist.set_size({'width': 624, 'height': 326})
    
    
    chart_Nyquist.set_title({
    #    'name': 'Nyquist Plot',
        'overlay': True,
        'name_font':{'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37,'y': 0.01,}
        })
    
    temN=0
    for temN in range(0,n):
        chart_Nyquist.add_series({
        'categories': ['Sheet1', stratcol, x+7*temN, endcol, x+7*temN],#'=Sheet1!$D$2:$D$201',# X axis 
        'values':     ['Sheet1', stratcol, y+7*temN, endcol, y+7*temN],#'=Sheet1!$E$2:$E$201',# Y axis 
    #    'marker': {
    #            'type': 'circle',
    #            'size': 3,
    #               },
        'line':{'width': 3},
        'name':['Sheet1', 0, 0+7*temN]
        }) 
     
    
    chart_Nyquist.set_plotarea({
        'layout': {'x': 0.20,'y': 0.13,'width': 0.75, 'height': 0.68,}
        })
    
    
    chart_Nyquist.set_x_axis({
            'name': "Z' [Ω]",
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'label_position': 'high',
            'name_layout': {'x': 0.52,'y': 1},
            'major_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside'
            })
    
    
    chart_Nyquist.set_y_axis({
            'name': "Z'' [Ω]",
            'name_font': {'size': 18},
            'reverse': True,
            'num_font':{'size': 18},
            'crossing': 'max',
            })
    
    
    chart_Nyquist.set_legend({
            'position': 'right',
            'font': {'size': 18,'color': 'black'},          
    #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}        
                      })

    worksheet.insert_chart('G2', chart_Nyquist)

    ########creat Nyquist line chart ################
    
    ########creat BodeZ plot ################   
def BodeZ(workbook,worksheet,n,x,y,stratcol,endcol):

    chart_BodeZ = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight'
            })
    
    chart_BodeZ.set_size({'width': 624, 'height': 326})
        
    chart_BodeZ.set_title({
    #    'name': 'Bode Plot',    
        'overlay': True,
        'name_font':{'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37,'y': 0.01,}
        })
        
    temZ=0
    for temZ in  range(0,n):
        chart_BodeZ.add_series({
         'categories': ['Sheet1', stratcol, x+7*temZ, endcol, x+7*temZ],#'=Sheet1!$D$2:$D$201',# X axis 
         'values':     ['Sheet1', stratcol, y+7*temZ, endcol, y+7*temZ],#'=Sheet1!$E$2:$E$201',# Y axis 
    #    'marker': {
    #            'type': 'circle',
    #            'size': 5,
    #               },
        'line':{'width': 3},
         'name':['Sheet1', 0, 0+7*temZ]
        }) 
    
    
    chart_BodeZ.set_plotarea({
        'layout': {'x': 0.20,'y': 0.13,'width': 0.75, 'height': 0.68,}
        })
    
    
    chart_BodeZ.set_x_axis({
            'name': 'f [Hz]',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'num_format': '#.0E+0',
            'label_position': 'low',
            'name_layout': {'x': 0.52,'y': 1},
            'major_gridlines': {'visible': True,'line': {'width': 0.5}},
            'minor_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',
            'min':1E6,
            'max':1E9,
            'log_base': 10,
            })
    
    
    chart_BodeZ.set_y_axis({
            'name': '|Z| [Ω]',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
    #         'log_base': 10,
            })
    
    
    chart_BodeZ.set_legend({
            'position': 'right',
            'font': {'size': 18,'color': 'black'},          
    #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}        
                      })
      
    worksheet.insert_chart('R42', chart_BodeZ)   
    ########creat Nyquist line chart ################  
  
def BodeRs(workbook,worksheet,n,x,y,stratcol,endcol):
    ########creat BodeZ plot ################
    chart_BodeR = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight'
            })
    
    chart_BodeR.set_size({'width': 624, 'height': 326})
        
    chart_BodeR.set_title({
    #    'name': 'Bode Plot',    
        'overlay': True,
        'name_font':{'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37,'y': 0.01,}
        })
        
    temZ=0
    for temZ in  range(0,n):
        chart_BodeR.add_series({
         'categories': ['Sheet1', stratcol, x+7*temZ, endcol, x+7*temZ],#'=Sheet1!$D$2:$D$201',# X axis 
         'values':     ['Sheet1', stratcol, y+7*temZ, endcol, y+7*temZ],#'=Sheet1!$E$2:$E$201',# Y axis 
    #    'marker': {
    #            'type': 'circle',
    #            'size': 5,
    #               },
        'line':{'width': 3},
         'name':['Sheet1', 0, 0+7*temZ]
        }) 
    
    
    chart_BodeR.set_plotarea({
        'layout': {'x': 0.20,'y': 0.13,'width': 0.75, 'height': 0.68,}
        })
    
    
    chart_BodeR.set_x_axis({
            'name': 'f [Hz]',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'num_format': '#.0E+0',
            'label_position': 'low',
            'name_layout': {'x': 0.52,'y': 1},
            'major_gridlines': {'visible': True,'line': {'width': 0.5}},
            'minor_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',
            'min':1E6,
            'max':1E9,
            'log_base': 10,
            })
    
    
    chart_BodeR.set_y_axis({
            'name': 'Rs (Ω)',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
    #         'log_base': 10,
            })
    
    
    chart_BodeR.set_legend({
            'position': 'right',
            'font': {'size': 18,'color': 'black'},          
    #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}        
                      })
      
    worksheet.insert_chart('R2', chart_BodeR)   
    ########creat Nyquist line chart ################  
    
def BodeX(workbook,worksheet,n,x,y,stratcol,endcol):   
    ########creat Bode plot ################
    chart_BodeX = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight'
            })
    
    chart_BodeX.set_size({'width': 624, 'height': 326})
    
    chart_BodeX.set_title({
    #    'name': 'Bode Plot',
        'overlay': True,
        'name_font':{'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37,'y': 0.01,}
        })
    
    temX=0
    for temX in  range(0,n):
        chart_BodeX.add_series({
         'categories': ['Sheet1', stratcol, x+7*temX, endcol, x+7*temX],#'=Sheet1!$D$2:$D$201',# X axis 
         'values':     ['Sheet1', stratcol, y+7*temX, endcol, y+7*temX],#'=Sheet1!$E$2:$E$201',# Y axis 
    #     'marker': {
    #            'type': 'circle',
    #            'size': 5,
    #               },
        'line':{'width': 3},
         'name':['Sheet1', 0, 0+7*temX]
        }) 
    
    
    chart_BodeX.set_plotarea({
        'layout': {'x': 0.20,'y': 0.13,'width': 0.75, 'height': 0.68,}
        })
    
    
    chart_BodeX.set_x_axis({
            'name': 'f [Hz]',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'num_format': '#.0E+0',
            'label_position': 'high',
            'name_layout': {'x': 0.52,'y': 1},
            'major_gridlines': {'visible': True,'line': {'width': 0.5}},
            'minor_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',
            'min':1E6,
            'max':1E9,
            'log_base': 10,
            })
    
    
    chart_BodeX.set_y_axis({
            'name': "Z'' (Ω)",
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'reverse': True,
            'crossing': 'max',
            })
    
    
    chart_BodeX.set_legend({
            'position': 'right',
            'font': {'size': 18,'color': 'black'},          
    #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}        
                      })
    
    
    worksheet.insert_chart('G22', chart_BodeX)   
    ########creat BodeX line chart ################
    
def BodeP(workbook,worksheet,n,x,y,stratcol,endcol):
    ########creat BodeP plot ################
    chart_BodeP = workbook.add_chart({'type': 'scatter',
                                 'subtype': 'straight'})
    chart_BodeP.set_size({'width': 624, 'height': 326})
    
    
    chart_BodeP.set_title({
    #    'name': 'Bode Plot',
        'overlay': True,
        'name_font':{'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37,'y': 0.01,}
        })
    
        
    temP=0
    for temP in  range(0,n):
        chart_BodeP.add_series({
         'categories': ['Sheet1', stratcol, x+7*temP, endcol, x+7*temP],#'=Sheet1!$D$2:$D$201',# X axis 
         'values':     ['Sheet1', stratcol, y+7*temP, endcol, y+7*temP],#'=Sheet1!$E$2:$E$201',# Y axis 
    #     'marker': {
    #            'type': 'circle',
    #            'size': 5,
    #               },
         'line':{'width': 3},
         'name':['Sheet1', 0, 0+7*temP]
        }) 
    
    chart_BodeP.set_plotarea({
        'layout': {'x': 0.20,'y': 0.13,'width': 0.75, 'height': 0.68,}
        })
    
    
    chart_BodeP.set_x_axis({
            'name': 'f [Hz]',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'num_format': '#.0E+0',
            'label_position': 'low',
            'name_layout': {'x': 0.52,'y': 1},
            'major_gridlines': {'visible': True,'line': {'width': 0.5}},
            'minor_gridlines': {'visible': True,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',
            'min':1E6,
            'max':1E9,
            'log_base': 10,
            })
    
    
    chart_BodeP.set_y_axis({
            'name': 'θ [deg]',
            'name_font': {'size': 18},
            'num_font':{'size': 18},
            'crossing': -100,
            })
    
    
    chart_BodeP.set_legend({
            'position': 'right',
            'font': {'size': 18, 'color': 'black'},          
    #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}        
                      })
    
    
    worksheet.insert_chart('R22', chart_BodeP) 
    ########creat BodeP plot ################

##########  pairplot #####################
def pairplot(database,label):
    x1=database[0]
    y1=database[1]
    x2=database[2]
    y2=database[3]
    
    plt.figure(1,figsize=(16,9))  
    
    plt.subplot(121)  
    plt.plot(x1,y1,linewidth=4) 
    plt.xlabel(label[0]) 
    plt.ylabel(label[1]) 
    
    plt.subplot(122)  
    plt.plot(x2,y2,linewidth=4) 
     
    plt.xlabel(label[2]) 
    plt.ylabel(label[3]) 
########## pairplot #####################
    


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



def write_error_analysis_data(worksheet, error_df_list, writeInfo, current_col_offset):
    """
    写入误差分析数据到Excel工作表
    
    Args:
        worksheet: xlsxwriter工作表对象
        error_df_list: 误差数据DataFrame列表
        writeInfo: 写入信息字典，包含行位置信息
        current_col_offset: 当前列偏移量
    
    Returns:
        int: 更新后的列偏移量
    """
    if error_df_list is not None and len(error_df_list) > 0:
        for idx, error_df in enumerate(error_df_list):
            if error_df is not None and not error_df.empty:
                # 写入误差数据标题和列名
                error_name = f'Relative_Errors_{idx+1}'
                error_headings = list(error_df.columns)
                error_datanum = len(error_headings)
                
                worksheet.write_row(writeInfo['curvenamerow'], current_col_offset, [error_name])
                worksheet.write_row(writeInfo['headingsrow'], current_col_offset, error_headings)
                
                # 写入误差数据
                for col_idx, col_name in enumerate(error_headings):
                    col_data = error_df[col_name].values
                    worksheet.write_column(writeInfo['datarow'], current_col_offset + col_idx, col_data)
                
                # 更新列偏移量
                current_col_offset += error_datanum + 2
    
    return current_col_offset


def write_statistical_analysis_data(worksheet, stats_list, writeInfo, current_col_offset):
    """
    写入统计分析数据到Excel工作表
    
    Args:
        worksheet: xlsxwriter工作表对象
        stats_list: 统计数据DataFrame列表
        writeInfo: 写入信息字典，包含行位置信息
        current_col_offset: 当前列偏移量
    
    Returns:
        int: 更新后的列偏移量
    """
    if stats_list is not None and len(stats_list) > 0:
        stats_names = ['Mean_Values', 'Variance_Values', 'StdDev_Values', 'CV_Values']
        
        for idx, stats_df in enumerate(stats_list):
            if stats_df is not None and not stats_df.empty:
                # 写入统计数据标题和列名
                stats_name = stats_names[idx] if idx < len(stats_names) else f'Stats_{idx+1}'
                stats_headings = list(stats_df.columns)
                stats_datanum = len(stats_headings)
                
                worksheet.write_row(writeInfo['curvenamerow'], current_col_offset, [stats_name])
                worksheet.write_row(writeInfo['headingsrow'], current_col_offset, stats_headings)
                
                # 写入统计数据
                for col_idx, col_name in enumerate(stats_headings):
                    col_data = stats_df[col_name].values
                    worksheet.write_column(writeInfo['datarow'], current_col_offset + col_idx, col_data)
                
                # 更新列偏移量
                current_col_offset += stats_datanum + 2
    
    return current_col_offset


def write_single_dataset_statistics_data(worksheet, stats_dfs_list, writeInfo, current_col_offset):
    """
    写入单数据集统计分析数据到Excel工作表
    
    Args:
        worksheet: xlsxwriter工作表对象
        stats_dfs_list: 单数据集统计数据DataFrame列表
        writeInfo: 写入信息字典，包含行位置信息
        current_col_offset: 当前列偏移量
    
    Returns:
        int: 更新后的列偏移量
    """
    if stats_dfs_list is not None and len(stats_dfs_list) > 0:
        stats_names = ['Rolling_Std_Errors', 'Relative_Deviation_Percent']
        
        for idx, stats_df in enumerate(stats_dfs_list):
            if stats_df is not None and not stats_df.empty:
                # 写入统计数据标题和列名
                stats_name = stats_names[idx] if idx < len(stats_names) else f'Single_Stats_{idx+1}'
                stats_headings = list(stats_df.columns)
                stats_datanum = len(stats_headings)
                
                worksheet.write_row(writeInfo['curvenamerow'], current_col_offset, [stats_name])
                worksheet.write_row(writeInfo['headingsrow'], current_col_offset, stats_headings)
                
                # 写入统计数据
                for col_idx, col_name in enumerate(stats_headings):
                    col_data = stats_df[col_name].values
                    worksheet.write_column(writeInfo['datarow'], current_col_offset + col_idx, col_data)
                
                # 更新列偏移量
                current_col_offset += stats_datanum + 2
    
    return current_col_offset



