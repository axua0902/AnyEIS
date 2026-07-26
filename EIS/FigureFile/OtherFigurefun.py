
import os
import numpy as np


import pandas as pd
import xlsxwriter

import sys
pwd = os.getcwd()
# proj_path = os.path.abspath(os.path.dirname(pwd) + os.path.sep + ".")
# Package_path = proj_path+'\programe'
# sys.path.append(Package_path)

import EIS.Other.EISplot as Ep
import EIS.Other.standard_parameter as Sp

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



def TIMEfiguremaker(workbook, worksheet, dataInfo, writeInfo):
    stratcol = writeInfo['datarow']
    datasize = dataInfo['datasize']
    endcol = stratcol + datasize
    datacol = [i for i in range(dataInfo['dataNum'] + 1)]
    curvenum = dataInfo['curveNum']
    datanum = dataInfo['dataNum']

    # 图表位置配置：每行2个图表，每个图表占用10行20列的空间
    chart_positions = []
    row_offset = 6  # 起始行
    col_positions = ['D', 'N']  # 每行的列位置
    
    # 生成图表位置
    for i in range(1, datanum):  # 从第1列开始（第0列是时间轴）
        row_index = (i - 1) // 2  # 计算行索引
        col_index = (i - 1) % 2   # 计算列索引
        chart_row = row_offset + row_index * 15  # 每个图表占用15行
        chart_pos = f"{col_positions[col_index]}{chart_row}"
        chart_positions.append(chart_pos)

    # 根据数据列数动态生成时序图表
    for i in range(1, datanum):  # 从第1列开始（第0列是时间轴）
        infoX = {'Xlabel': "Time", 'Axial': 'nonLog'}
        infoY = {'Ylabel': f"Data{i}", 'Axial': 'nonLog', 'Reverse': False}
        
        chart_position = chart_positions[i - 1] if i - 1 < len(chart_positions) else 'D6'
        
        Generalplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[i], 
                   stratcol, endcol, infoX, infoY, 0, 0, chart_position)

    return workbook


def Generalfiguremaker(workbook, worksheet, dataInfo, writeInfo):
    stratcol = writeInfo['datarow']
    datasize = dataInfo['datasize']
    endcol = stratcol + datasize
    datacol = [i for i in range(dataInfo['dataNum'] + 1)]
    curvenum = dataInfo['curveNum']
    datanum = dataInfo['dataNum']

    # 图表位置配置：每行2个图表，每个图表占用10行20列的空间
    chart_positions = []
    row_offset = 6  # 起始行
    col_positions = ['D', 'N']  # 每行的列位置
    
    # 生成图表位置
    for i in range(1, datanum):  # 从第1列开始（第0列是x轴）
        row_index = (i - 1) // 2  # 计算行索引
        col_index = (i - 1) % 2   # 计算列索引
        chart_row = row_offset + row_index * 15  # 每个图表占用15行
        chart_pos = f"{col_positions[col_index]}{chart_row}"
        chart_positions.append(chart_pos)

    # 根据数据列数动态生成图表
    for i in range(1, datanum):  # 从第1列开始（第0列是x轴）
        infoX = {'Xlabel': "X", 'Axial': 'nonLog'}
        infoY = {'Ylabel': f"Y{i}", 'Axial': 'nonLog', 'Reverse': False}
        
        chart_position = chart_positions[i - 1] if i - 1 < len(chart_positions) else 'D6'
        
        Generalplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[i], 
                   stratcol, endcol, infoX, infoY, 0, 0, chart_position)

    return workbook





######## creat line chart ################
def Generalplot(workbook, worksheet, n, num, x, y, stratcol, endcol, infoX, infoY, infoY2, y2, chartposition='D6'):
    chart_Anyplot = workbook.add_chart({
        'type': 'scatter',
        'subtype': 'straight'
    })

    chart_Anyplot.set_size({'width': 280, 'height': 180})  ######图表尺寸

    chart_Anyplot.set_plotarea({
        'border': {'color': 'black', 'width': 1.25, },  ######线框
        'layout': {'x': 0.18, 'y': 0.13, 'width': 0.76, 'height': 0.70, }  #####绘图区尺寸
    })

    chart_Anyplot.set_legend({
        'position': 'right',
        'border': {'color': 'black', 'width': 0.75, },  ######线框
        'fill': {'color': 'white'},
        'font': {'size': 10, 'color': 'black', 'bold': True, 'name': 'Times New Roman'},
        #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}
    })

    temZ = 0
    for temZ in range(0, n):
        chart_Anyplot.add_series({
            'categories': ['Sheet1', stratcol, x + (num + 2) * temZ, endcol, x + (num + 2) * temZ],
            # '=Sheet1!$D$2:$D$201',# X axis
            'values': ['Sheet1', stratcol, y + (num + 2) * temZ, endcol, y + (num + 2) * temZ],
            # '=Sheet1!$E$2:$E$201',# Y axis
            'marker': {
                'type': 'automatic',
                # 'type': 'circle',
                'size': 5,
            },
            'line': {'width': 2},
            'name': ['Sheet1', 0, 0 + (num + 2) * temZ]
        })

    if infoX.get('Axial') == 'Log':
        chart_Anyplot.set_x_axis({
            'name': infoX.get('Xlabel', 'X'),  # x axil
            'name_font': {'size': 10, 'bold': True, 'italic': True, 'name': 'Times New Roman'},
            'name_layout': {'x': 0.85, 'y': 0.89, },

            'num_font': {'size': 10, 'bold': True, 'name': 'Times New Roman'},
            'num_format': '#.0E+0',

            'label_position': 'low',

            'major_gridlines': {'visible': True, 'line': {'width': 0.25}},
            'minor_gridlines': {'visible': False},  # ,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',

            'min': infoX.get('startValue'),  # x min
            'max': infoX.get('endValue'),  # x max
            'log_base': 10,  #
        })
    else:
        chart_Anyplot.set_x_axis({
            'name': infoX.get('Xlabel', 'X'),  # x axil
            'name_font': {'size': 10, 'bold': True, 'italic': True, 'name': 'Times New Roman'},
            'name_layout': {'x': 0.85, 'y': 0.89, },

            'num_font': {'size': 10, 'name': 'Times New Roman'},

            'label_position': 'low',

            'major_gridlines': {'visible': True, 'line': {'width': 0.5}},
            'minor_gridlines': {'visible': False},  # ,'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',

            'min': infoX.get('startValue'),  # x min
            'max': infoX.get('endValue'),  # x max
        })

    if infoY.get('Axial') == 'Log':
        chart_Anyplot.set_y_axis({
            'name': infoY.get('Ylabel', 'Y'),  # y axil
            'name_font': {'size': 10, 'bold': True, 'italic': True, 'name': 'Times New Roman', 'rotation': 0},
            'name_layout': {'x': 0.01, 'y': 0.01, },

            'num_font': {'size': 10, 'bold': True, 'name': 'Times New Roman'},

            'major_gridlines': {'visible': True, 'line': {'width': 0.25, 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',

            'log_base': 10,
        })
    else:
        y_axis_config = {
            'name': infoY.get('Ylabel', 'Y'),  # y axil
            'name_font': {'size': 10, 'bold': True, 'italic': True, 'name': 'Times New Roman', 'rotation': 0},
            'name_layout': {'x': 0.01, 'y': 0.01, },

            'num_font': {'size': 10, 'bold': True, 'name': 'Times New Roman'},

            'major_gridlines': {'visible': True, 'line': {'width': 0.25, 'dash_type': 'dash'}},
            'major_tick_mark': 'outside',
        }
        
        # 只在有值时设置范围
        if 'startValue' in infoY:
            y_axis_config['min'] = infoY['startValue']
        if 'endValue' in infoY:
            y_axis_config['max'] = infoY['endValue']
            
        chart_Anyplot.set_y_axis(y_axis_config)

    if infoY2 != 0:
        temZ = 0
        for temZ in range(0, n):
            chart_Anyplot.add_series({
                'categories': ['Sheet1', stratcol, x + (num + 2) * temZ, endcol, x + (num + 2) * temZ],
                # '=Sheet1!$D$2:$D$201',# X axis
                'values': ['Sheet1', stratcol, y2 + (num + 2) * temZ, endcol, y2 + (num + 2) * temZ],
                # '=Sheet1!$E$2:$E$201',# Y axis
                'y2_axis': True,
                'marker': {
                    'type': 'automatic',
                    # 'type': 'circle',
                    'size': 5,
                },
                'line': {'width': 2},
                'name': ['Sheet1', 0, 0 + (num + 2) * temZ]
            })

        if infoY2.get('Axial') == 'Log':
            chart_Anyplot.set_y2_axis({
                'name': infoY2.get('Ylabel', 'Y2'),  # y axil
                'name_font': {'size': 10, 'bold': True, 'italic': True, 'name': 'Times New Roman', 'rotation': 0},
                'name_layout': {'x': 0.91, 'y': 0.01, },

                'num_font': {'size': 10, 'bold': True, 'name': 'Times New Roman'},

                'major_gridlines': {'visible': True, 'line': {'width': 0.25, 'dash_type': 'dash'}},
                'major_tick_mark': 'outside',

                'log_base': 10,
            })
        else:
            y2_axis_config = {
                'name': infoY2.get('Ylabel', 'Y2'),  # y axil
                'name_font': {'size': 10, 'bold': True, 'italic': True, 'name': 'Times New Roman', 'rotation': 0},
                'name_layout': {'x': 0.91, 'y': 0.01, },

                'num_font': {'size': 10, 'bold': True, 'name': 'Times New Roman'},

                'major_gridlines': {'visible': True, 'line': {'width': 0.25, 'dash_type': 'dash'}},
                'major_tick_mark': 'outside',
            }
            
            # 只在有值时设置范围
            if 'startValue' in infoY2:
                y2_axis_config['min'] = infoY2['startValue']
            if 'endValue' in infoY2:
                y2_axis_config['max'] = infoY2['endValue']
                
            chart_Anyplot.set_y2_axis(y2_axis_config)

    worksheet.insert_chart(chartposition, chart_Anyplot)
########creat line chart ################
