
import numpy as np
import pandas as pd
import xlsxwriter


def creatanyfile(wbname, dataname, data):  ########for creat excel file which data is from python calculate

    headings = list(data[0].columns)
    dataInfo = {'headingsNum': len(headings), 'curveNum': len(dataname), 'dataNum': len(headings)}
    writeInfo = {'curvenamerow': 0, 'headingsrow': 1, 'datarow': 2}
    name = [[i] for i in dataname]
    workbook = xlsxwriter.Workbook(wbname, {'nan_inf_to_errors': True})  # 创建一个excel
    worksheet = workbook.add_worksheet()  # 创建一个sheet
    tem1 = 0
    for tem1 in range(0, dataInfo['curveNum']):
        worksheet.write_row(writeInfo['curvenamerow'], tem1 * (2 + dataInfo['headingsNum']), name[tem1])
        worksheet.write_row(writeInfo['headingsrow'], tem1 * (2 + dataInfo['headingsNum']), headings)
    return workbook, worksheet, dataInfo, writeInfo


#######write data ################
def writeanydata(workbook, worksheet, dataname, data, dataInfo, writeInfo):
    headings = list(data[0].columns)
    curvenum = dataInfo['curveNum']
    datanum = dataInfo['dataNum']
    stratRow = writeInfo['datarow']

    tem2 = 0
    for tem2 in range(0, curvenum):
        tem1 = 0
        for tem1 in range(0, datanum):
            datanamewrite = headings[tem1]
            dff = data[tem2]
            col = dff.loc[:, datanamewrite]
            worksheet.write_column(stratRow, tem1 + tem2 * (datanum + 2), col)

        #########WRITE data#########

    dataInfo['datasize'] = np.size(col)
    dataInfo['startFreq'] = data[0][headings[0]][0]
    dataInfo['endFreq'] = data[0][headings[0]][dataInfo['datasize'] - 1]

    return workbook, worksheet, dataInfo, writeInfo




def get_color_schemes():
    """
    获取不同的配色方案
    Returns:
    - dict: 包含多种配色方案的字典
    """
    color_schemes = {
        'excel_basic': ['#5B9BD5', '#ED7D31', '#A5A5A5', '#FFC000', '#4472C4', '#70AD47'],  # Excel基础配色
        'classic': ['#000000', '#FF0000', '#0000FF', '#008000', '#800080', '#FFA500'],  # 经典配色
        'modern_blue': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],  # 现代蓝色系
        'nature': ['#2E8B57', '#FF6347', '#4682B4', '#DAA520', '#8B4513', '#9932CC'],  # 自然色系
        'professional': ['#2C3E50', '#E74C3C', '#3498DB', '#F39C12', '#9B59B6', '#1ABC9C'],  # 专业配色
        'warm': ['#D2691E', '#CD5C5C', '#B8860B', '#8B4513', '#A0522D', '#BC8F8F'],  # 暖色调
        'scientific': ['#1B4F72', '#C0392B', '#D68910', '#239B56', '#7D3C98', '#E67E22'],  # 科学期刊风格
    }
    return color_schemes
    

########write data ################
def EISfiguremaker(workbook, worksheet, dataInfo, writeInfo):
    stratcol = writeInfo['datarow']
    datasize = dataInfo['datasize']
    endcol = stratcol + datasize
    curvenum = dataInfo['curveNum']
    datanum = dataInfo['dataNum']
    datacol = [i for i in range(dataInfo['dataNum'] + 1)]
    startFreq = dataInfo['startFreq']
    endFreq = dataInfo['endFreq']

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': '|Z| [Ω]', 'Axial': 'nonLog', 'Reverse': False, 'startValue': 0, 'endValue': 400}
    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[1], stratcol, endcol, infoX, infoY, 'D6')

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': 'PHI [°] ', 'Axial': 'nonLog', 'Reverse': False, 'startValue': -180, 'endValue': 180}
    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[2], stratcol, endcol, infoX, infoY, 'N6')

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': 'Rs [Ω]', 'Axial': 'nonLog', 'Reverse': False, 'startValue': 60, 'endValue': 90}
    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[3], stratcol, endcol, infoX, infoY, 'D26')

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': 'X [Ω]', 'Axial': 'nonLog', 'Reverse': True, 'startValue': 0, 'endValue': 2.5}
    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[4], stratcol, endcol, infoX, infoY, 'N26')

    infoX = {'Xlabel': 'Rs [Ω]', 'Axial': 'nonLog'}  # ,'startValue':0,'endValue':200}
    infoY = {'Ylabel': 'X [Ω]', 'Axial': 'nonLog', 'Reverse': True}  # ,'startValue':-400,'endValue':0}
    Anyplot(workbook, worksheet, curvenum, datanum, datacol[3], datacol[4], stratcol, endcol, infoX, infoY, 'D46')

    return workbook


def EPSfiguremaker(workbook, worksheet, dataInfo, writeInfo):
    stratcol = writeInfo['datarow']
    datasize = dataInfo['datasize']
    endcol = stratcol + datasize

    curvenum = dataInfo['curveNum']
    datanum = dataInfo['dataNum']

    datacol = [i for i in range(dataInfo['dataNum'] + 1)]

    startFreq = dataInfo['startFreq']
    endFreq = dataInfo['endFreq']

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': "ε [-]", 'Axial': 'nonLog', 'Reverse': False, 'startValue': 0, 'endValue': 100}
    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[1], stratcol, endcol, infoX, infoY, 'D6')

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': "ε'' [-]", 'Axial': 'nonLog', 'Reverse': False, 'startValue': 0, 'endValue': 180}

    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[2], stratcol, endcol, infoX, infoY,"N6")

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': "σ [S/m]", 'Axial': 'nonLog', 'Reverse': False, 'startValue': 60, 'endValue': 90}

    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[3], stratcol, endcol, infoX, infoY, "D26")

    infoX = {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq}
    infoY = {'Ylabel': "σ'' [S/m]", 'Axial': 'nonLog', 'Reverse': False, 'startValue': 60, 'endValue': 90}

    Anyplot(workbook, worksheet, curvenum, datanum, datacol[0], datacol[4], stratcol, endcol, infoX, infoY, "N26")

    infoX = {'Xlabel': "ε [-]", 'Axial': 'nonLog'}  # ,'startValue':60,'endValue':90}
    infoY = {'Ylabel': "ε'' [-]", 'Axial': 'nonLog', 'Reverse': False, 'startValue': 60, 'endValue': 90}

    Anyplot(workbook, worksheet, curvenum, datanum, datacol[1], datacol[2], stratcol, endcol, infoX, infoY, 'D46')

    return workbook





def Anyplot(workbook, worksheet, n, num, x, y, stratcol, endcol, infoX, infoY, chartposition='D6'):
    chart_Anyplot = workbook.add_chart({
        'type': 'scatter',
        'subtype': 'straight'
    })

    chart_Anyplot.set_size({'width': 454, 'height': 314,})

    chart_Anyplot.set_title({
        'overlay': True,
        'name_font': {'name': 'Arial', 'size': 20},
        'layout': {'x': 0.37, 'y': 0.01, }
    })

    temZ = 0
    for temZ in range(0, n):
        chart_Anyplot.add_series({
            'categories': ['Sheet1', stratcol, x + (num + 2) * temZ, endcol, x + (num + 2) * temZ],
            # '=Sheet1!$D$2:$D$201',# X axis
            'values': ['Sheet1', stratcol, y + (num + 2) * temZ, endcol, y + (num + 2) * temZ],
            # '=Sheet1!$E$2:$E$201',# Y axis
            #    'marker': {
            #            'type': 'circle',
            #            'size': 5,
            #               },
            'line': {'width': 3},
            'name': ['Sheet1', 0, 0 + (num + 2) * temZ]
        })

    chart_Anyplot.set_plotarea({
        'layout': {'x': 0.20, 'y': 0.13, 'width': 0.72, 'height': 0.68, }
    })

    # chart_Anyplot.set_x_axis({'label_position': 'high'})

    if infoX['Axial'] == 'Log':
        chart_Anyplot.set_x_axis({
            'name': infoX['Xlabel'],  # x axil
            'name_font': {'size': 18},
            'num_font': {'size': 18},
            'num_format': '0E+0',  # 使用科学计数法格式 0E+0
            'label_position': 'low',
            'name_layout': {'x': 0.52, 'y': 1},
            'major_gridlines': {'visible': True, 'line': {'width': 0.5}},
            'minor_gridlines': {'visible': True, 'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',
            'min': infoX['startValue'],  # x min
            'max': infoX['endValue'],  # x max
            'minor_unit':10,
            'major_unit':10,
            'log_base': 10,  #
        })

    else:
        chart_Anyplot.set_x_axis({
            'name': infoX['Xlabel'],  # x axil
            'name_font': {'size': 18},
            'num_font': {'size': 18},
            'num_format': 'General',
            'label_position': 'low',
            'name_layout': {'x': 0.52, 'y': 1},
            'major_gridlines': {'visible': True, 'line': {'width': 0.5}},
            'minor_gridlines': {'visible': True, 'line': {'width': 0.2, 'dash_type': 'dash'}},
            'major_tick_mark': 'none',
            'minor_tick_mark': 'outside',
            # 'min':infoX['startValue'],# x min
            # 'max':infoX['endValue'],#x max
        })

    if infoY['Reverse'] == True:
        if infoY['Axial'] == 'Log':
            chart_Anyplot.set_y_axis({
                'name': infoY['Ylabel'],  # y axil
                'name_font': {'size': 18},
                'num_font': {'size': 18},
                'log_base': 10,
                'reverse': True,
            })


        else:
            chart_Anyplot.set_y_axis({
                'name': infoY['Ylabel'],  # y axil
                'name_font': {'size': 18},
                'num_font': {'size': 18},
                'reverse': True,
                #         'log_base': 10,
            })
    else:
        if infoY['Axial'] == 'Log':
            chart_Anyplot.set_y_axis({
                'name': infoY['Ylabel'],  # y axil
                'name_font': {'size': 18},
                'num_font': {'size': 18},
                'log_base': 10,
            })
        else:
            chart_Anyplot.set_y_axis({
                'name': infoY['Ylabel'],  # y axil
                'name_font': {'size': 18},
                'num_font': {'size': 18},
                #         'log_base': 10,
            })

    chart_Anyplot.set_legend({
        'position': 'right',
        'font': {'size': 18, 'color': 'black'},
        #        'layout': {'x':0.95,'y':0.40,'width':0.2,'height': 0.4,}
    })

    worksheet.insert_chart(chartposition, chart_Anyplot)
    ########creat Nyquist line chart ################






def apply_paper_chart_maker(workbook, worksheet, dataInfo, writeInfo, color_scheme):
    """
    读取workbook中的图表样式，并修改为符合学术论文要求的样式
    
    Parameters:
    - workbook: xlsxwriter workbook对象
    - worksheet: xlsxwriter worksheet对象  
    - dataInfo: 数据信息字典
    - writeInfo: 写入信息字典
    - color_scheme: 配色方案名称 (默认: 'classic')
    
    Returns:
    - workbook: 修改后的workbook对象
    """
    
    # 获取配色方案
    color_schemes = get_color_schemes()
    selected_colors = color_schemes.get(color_scheme, color_schemes['classic'])
    
    # 学术论文图表样式配置
    academic_style = {
        'chart_size': {'width': 265, 'height': 215},  # 进一步缩小图表尺寸
        'dpi':300,
        'title_font': {'name': 'Times New Roman', 'size': 10, 'bold': True},
        'axis_font': {'name': 'Times New Roman', 'size': 10},
        'legend_font': {'name': 'Times New Roman', 'size': 10},
        'line_width': 1.25,  # 适中的线条宽度
        'marker_size': 2,  # 数据点大小
        'gridlines': {
            'major': {'visible': True, 'line': {'width': 0.75, 'color': '#D3D3D3'}},
            'minor': {'visible': False}  # 学术论文通常不显示次要网格线
        },
        'plot_area': {'x': 0.18, 'y': 0.12, 'width': 0.70, 'height': 0.75},
        'colors': selected_colors  # 使用选定的配色方案
    }
    
    # 重新创建符合学术要求的图表
    stratcol = writeInfo['datarow']
    datasize = dataInfo['datasize']
    endcol = stratcol + datasize
    curvenum = dataInfo['curveNum']
    datanum = dataInfo['dataNum']
    datacol = [i for i in range(dataInfo['dataNum'] + 1)]
    startFreq = dataInfo['startFreq']
    endFreq = dataInfo['endFreq']

    # 创建学术风格的EIS图表
    # 添加 f vs Rs 图表 
    create_paper_chart(workbook, worksheet, curvenum, datanum, datacol[0], datacol[3], 
                         stratcol, endcol,
                         {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq},
                         {'Ylabel': 'Rs [Ω]', 'Axial': 'nonLog', 'Reverse': False, 'startValue': 0},
                         'D6', academic_style)

    # 添加 f vs X 图表 (横轴标签位置设置为high)
    create_paper_chart(workbook, worksheet, curvenum, datanum, datacol[0], datacol[4], 
                         stratcol, endcol,
                         {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq},
                         {'Ylabel': 'X [Ω]', 'Axial': 'nonLog', 'Reverse': True, 'endValue': 0},
                         'N6', academic_style, 'high')

    # Nyquist图 (横轴标签位置设置为high)
    create_paper_chart(workbook, worksheet, curvenum, datanum, datacol[3], datacol[4], 
                         stratcol, endcol,
                         {'Xlabel': 'Rs [Ω]', 'Axial': 'nonLog'},
                         {'Ylabel': 'X [Ω]', 'Axial': 'nonLog', 'Reverse': True,'endValue': 0},
                         'D20', academic_style, 'high')

    create_paper_chart(workbook, worksheet, curvenum, datanum, datacol[0], datacol[2], 
                         stratcol, endcol,
                         {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq},
                         {'Ylabel': 'φ [°]', 'Axial': 'nonLog', 'Reverse': False, 'startValue': -180, 'endValue': 180},
                         'N20', academic_style)


    # 添加 f vs |Z| 图表 
    create_paper_chart(workbook, worksheet, curvenum, datanum, datacol[0], datacol[1], 
                         stratcol, endcol, 
                         {'Xlabel': 'f [Hz]', 'Axial': 'Log', 'startValue': startFreq, 'endValue': endFreq},
                         {'Ylabel': '|Z| [Ω]', 'Axial': 'nonLog', 'Reverse': False, 'startValue': 0},
                         'D35', academic_style)
    return workbook


def create_paper_chart(workbook, worksheet, n, num, x, y, stratcol, endcol, 
                         infoX, infoY, chartposition, style, x_label_position='low'):
    """
    创建符合学术论文要求的图表
    
    Parameters:
    - workbook: xlsxwriter workbook对象
    - worksheet: xlsxwriter worksheet对象
    - n: 曲线数量
    - num: 数据列数
    - x, y: x轴和y轴数据列索引
    - stratcol, endcol: 数据起始和结束行
    - infoX, infoY: x轴和y轴信息
    - chartposition: 图表位置
    - style: 学术样式配置
    - x_label_position: X轴标签位置 ('low' 或 'high')，默认为 'low'
    """
    
    chart = workbook.add_chart({
        'type': 'scatter',
        'subtype': 'straight_with_markers'  # 学术论文常用带标记的线图
    })

    # 设置图表尺寸
    chart.set_size(style['chart_size'])

    # 不设置标题，避免与图例冲突

    # 添加数据系列
    for temZ in range(n):
        chart.add_series({
            'categories': ['Sheet1', stratcol, x + (num + 2) * temZ, endcol, x + (num + 2) * temZ],
            'values': ['Sheet1', stratcol, y + (num + 2) * temZ, endcol, y + (num + 2) * temZ],
            'line': {
                'width': style['line_width'],
                'color': style['colors'][temZ % len(style['colors'])]
            },
            'marker': {
                'type': 'circle',
                'size': style['marker_size'],
                'border': {'color': style['colors'][temZ % len(style['colors'])]},
                'fill': {'color': style['colors'][temZ % len(style['colors'])]}
            },
            'name': ['Sheet1', 0, 0 + (num + 2) * temZ]
        })

    # 设置绘图区域，添加黑色实线边框
    chart.set_plotarea({
        'layout': style['plot_area'],
        'border': {'color': '#000000', 'width': 0.75}  # 黑色实线边框
    })

    # 设置X轴
    # 创建X轴标题字体配置（如果包含f则设为斜体）
    x_axis_font = style['axis_font'].copy()
    if infoX.get('italic_f', False):
        x_axis_font['italic'] = True
    
    x_axis_config = {
        'name': infoX['Xlabel'],
        'name_font': x_axis_font,
        'num_font': style['axis_font'],
        'label_position': x_label_position,
        'name_layout': {'x': 0.5, 'y': 0.95},  # 将X轴标题放在图的底部
        'major_gridlines': style['gridlines']['major'],
        'minor_gridlines': style['gridlines']['minor'],
        'major_tick_mark': 'outside',
        'minor_tick_mark': 'none',
    }
    
    if infoX['Axial'] == 'Log':
        # 使用科学计数法格式 0E+0
        x_axis_config.update({
            'num_format': '0E+0',  # 使用科学计数法格式
            'log_base': 10,
            'min': infoX.get('startValue'),
            'max': infoX.get('endValue'),
            'major_unit': 10,

        })
    
    chart.set_x_axis(x_axis_config)

    # 设置Y轴
    y_axis_config = {
        'name': infoY['Ylabel'],
        'name_font': style['axis_font'],
        'num_font': style['axis_font'],
        'major_gridlines': style['gridlines']['major'],
        'minor_gridlines': style['gridlines']['minor'],
        'major_tick_mark': 'outside',
        'minor_tick_mark': 'none',
    }
    
    # 虚部图表使用逆序刻度
    if infoY.get('Reverse'):
        y_axis_config['reverse'] = True
    
    if infoY['Axial'] == 'Log':
        y_axis_config['log_base'] = 10
        
    # 设置Y轴范围
    if 'startValue' in infoY:
        y_axis_config['min'] = infoY['startValue']
    if 'endValue' in infoY:
        y_axis_config['max'] = infoY['endValue']
    
    chart.set_y_axis(y_axis_config)

    # 设置图例
    chart.set_legend({
        'position': 'top',  # 学术论文图例通常在顶部
        'font': style['legend_font'],
        'layout': {'x': 0.13, 'y': 0.02, 'width': 0.70, 'height': 0.08}
    })

    # 插入图表
    worksheet.insert_chart(chartposition, chart)


def create_error_analysis_charts(workbook, worksheet, error_df_list, writeInfo):
    """
    为误差分析数据创建图表
    以第一个df的第一列数据为横轴，每一个df中相同列标题的数据放入同一个图
    
    Parameters:
    - workbook: xlsxwriter workbook对象
    - worksheet: xlsxwriter worksheet对象
    - error_df_list: 误差分析DataFrame列表
    - writeInfo: 写入信息字典
    """
    if not error_df_list or len(error_df_list) == 0:
        return
    
    # 获取第一个df的第一列作为横轴
    first_df = error_df_list[0]
    x_column = first_df.columns[0]
    
    # 收集所有唯一的列标题（除了第一列）
    all_columns = set()
    for df in error_df_list:
        for col in df.columns[1:]:  # 跳过第一列
            # 提取基础列名（去掉_RelErr后缀）
            base_col = col.replace('_RelErr', '')
            all_columns.add(base_col)
    
    all_columns = sorted(list(all_columns))
    
    # 为每个基础列名创建一个图表
    chart_positions = ['D10', 'N10', 'D30', 'N30', 'D50', 'N50']
    
    for idx, base_col in enumerate(all_columns):
        if idx >= len(chart_positions):
            break
            
        chart_position = chart_positions[idx]
        
        # 创建图表
        chart = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight_with_markers'
        })
        
        chart.set_size({'width': 454, 'height': 314})
        chart.set_title({
            'name': f'Relative Error Analysis - {base_col}',
            'name_font': {'name': 'Arial', 'size': 14, 'bold': True}
        })
        
        # 添加数据系列
        current_col_offset = 0
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for df_idx, error_df in enumerate(error_df_list):
            # 查找匹配的列
            matching_col = None
            for col in error_df.columns[1:]:
                if base_col in col and '_RelErr' in col:
                    matching_col = col
                    break
            
            if matching_col is not None:
                # 计算数据范围
                data_size = len(error_df)
                start_row = writeInfo['datarow']
                end_row = start_row + data_size - 1
                
                # X轴数据（第一列）
                x_col_idx = current_col_offset
                # Y轴数据（匹配的误差列）
                y_col_idx = current_col_offset + list(error_df.columns).index(matching_col)
                
                chart.add_series({
                    'categories': ['Sheet1', start_row, x_col_idx, end_row, x_col_idx],
                    'values': ['Sheet1', start_row, y_col_idx, end_row, y_col_idx],
                    'line': {
                        'width': 2,
                        'color': colors[df_idx % len(colors)]
                    },
                    'marker': {
                        'type': 'circle',
                        'size': 4,
                        'border': {'color': colors[df_idx % len(colors)]},
                        'fill': {'color': colors[df_idx % len(colors)]}
                    },
                    'name': f'Dataset_{df_idx+1}'
                })
            
            # 更新列偏移量
            current_col_offset += len(error_df.columns) + 2
        
        # 设置坐标轴
        chart.set_x_axis({
            'name': x_column,
            'name_font': {'size': 12},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True}
        })
        
        chart.set_y_axis({
            'name': f'{base_col} Relative Error (%)',
            'name_font': {'size': 12},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True}
        })
        
        # 设置图例
        chart.set_legend({
            'position': 'top',
            'font': {'size': 10}
        })
        
        # 插入图表
        worksheet.insert_chart(chart_position, chart)


def create_statistical_charts(workbook, worksheet, stats_list, writeInfo, error_col_info=None):
    """
    为统计分析数据创建图表
    每一个df做一幅图
    
    Parameters:
    - workbook: xlsxwriter workbook对象
    - worksheet: xlsxwriter worksheet对象
    - stats_list: 统计分析DataFrame列表
    - writeInfo: 写入信息字典
    - error_col_info: 误差数据的列数信息列表
    """
    if not stats_list or len(stats_list) == 0:
        return
    
    stats_names = ['Mean Values', 'Variance Values', 'Standard Deviation', 'Coefficient of Variation (%)']
    chart_positions = ['AA10', 'AI10', 'AA30', 'AI30']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # 计算每个统计DataFrame的列偏移量
    col_offsets = []
    current_offset = 0
    
    # 先计算误差分析数据的偏移量
    if error_col_info:
        for error_cols in error_col_info:
            current_offset += error_cols + 2
    
    # 计算统计数据的偏移量
    for stats_df in stats_list:
        col_offsets.append(current_offset)
        current_offset += len(stats_df.columns) + 2
    
    for idx, stats_df in enumerate(stats_list):
        if idx >= len(chart_positions) or stats_df is None or stats_df.empty:
            continue
            
        chart_position = chart_positions[idx]
        stats_name = stats_names[idx] if idx < len(stats_names) else f'Statistics_{idx+1}'
        
        # 创建图表
        chart = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight_with_markers'
        })
        
        chart.set_size({'width': 454, 'height': 314})
        chart.set_title({
            'name': stats_name,
            'name_font': {'name': 'Arial', 'size': 14, 'bold': True}
        })
        
        # 获取X轴列（第一列）和数据列
        x_column = stats_df.columns[0]
        data_columns = stats_df.columns[1:]
        
        # 计算数据范围
        data_size = len(stats_df)
        start_row = writeInfo['datarow']
        end_row = start_row + data_size - 1
        col_offset = col_offsets[idx]
        
        # 添加数据系列
        for col_idx, col_name in enumerate(data_columns):
            x_col_idx = col_offset  # X轴列索引
            y_col_idx = col_offset + col_idx + 1  # Y轴列索引
            
            chart.add_series({
                'categories': ['Sheet1', start_row, x_col_idx, end_row, x_col_idx],
                'values': ['Sheet1', start_row, y_col_idx, end_row, y_col_idx],
                'line': {
                    'width': 2,
                    'color': colors[col_idx % len(colors)]
                },
                'marker': {
                    'type': 'circle',
                    'size': 4,
                    'border': {'color': colors[col_idx % len(colors)]},
                    'fill': {'color': colors[col_idx % len(colors)]}
                },
                'name': col_name
            })
        
        # 设置坐标轴
        chart.set_x_axis({
            'name': x_column,
            'name_font': {'size': 12},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True}
        })
        
        # 根据统计类型设置Y轴标签
        y_labels = {
            0: 'Mean Value',
            1: 'Variance',
            2: 'Standard Deviation', 
            3: 'CV (%)'
        }
        y_label = y_labels.get(idx, 'Statistical Value')
        
        chart.set_y_axis({
            'name': y_label,
            'name_font': {'size': 12},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True}
        })
        
        # 设置图例
        chart.set_legend({
            'position': 'right',
            'font': {'size': 10}
        })
        
        # 插入图表
        worksheet.insert_chart(chart_position, chart)





def create_single_dataset_charts(workbook, worksheet, stats_dfs_list, writeInfo):
    """
    为单数据集统计分析数据创建图表
    以第一个df的第一列数据为横轴，每一个df中相同列标题的数据放入同一个图
    
    Parameters:
    - workbook: xlsxwriter workbook对象
    - worksheet: xlsxwriter worksheet对象
    - stats_dfs_list: 单数据集统计分析DataFrame列表 [rolling_std_df, relative_deviation_df]
    - writeInfo: 写入信息字典
    """
    if not stats_dfs_list or len(stats_dfs_list) == 0:
        return
    
    # 获取第一个df的第一列作为横轴
    first_df = stats_dfs_list[0]
    x_column = first_df.columns[0]
    
    # 收集所有唯一的基础列标题（去掉后缀）
    all_base_columns = set()
    for df in stats_dfs_list:
        for col in df.columns[1:]:  # 跳过第一列
            # 提取基础列名（去掉_RollingStd和_RelDeviation%后缀）
            if '_RollingStd' in col:
                base_col = col.replace('_RollingStd', '')
            elif '_RelDeviation%' in col:
                base_col = col.replace('_RelDeviation%', '')
            else:
                base_col = col
            all_base_columns.add(base_col)
    
    all_base_columns = sorted(list(all_base_columns))
    
    # 为每个基础列名创建一个图表
    chart_positions = ['D10', 'N10', 'D30', 'N30', 'D50', 'N50']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for idx, base_col in enumerate(all_base_columns):
        if idx >= len(chart_positions):
            break
            
        chart_position = chart_positions[idx]
        
        # 创建图表
        chart = workbook.add_chart({
            'type': 'scatter',
            'subtype': 'straight_with_markers'
        })
        
        chart.set_size({'width': 454, 'height': 314})
        chart.set_title({
            'name': f'Single Dataset Statistics - {base_col}',
            'name_font': {'name': 'Arial', 'size': 14, 'bold': True}
        })
        
        # 添加数据系列
        current_col_offset = 0
        series_names = ['Rolling Std', 'Relative Deviation (%)']
        
        for df_idx, stats_df in enumerate(stats_dfs_list):
            # 查找匹配的列
            matching_col = None
            for col in stats_df.columns[1:]:
                if base_col in col:
                    matching_col = col
                    break
            
            if matching_col is not None:
                # 计算数据范围
                data_size = len(stats_df)
                start_row = writeInfo['datarow']
                end_row = start_row + data_size - 1
                
                # X轴数据（第一列）
                x_col_idx = current_col_offset
                # Y轴数据（匹配的统计列）
                y_col_idx = current_col_offset + list(stats_df.columns).index(matching_col)
                
                chart.add_series({
                    'categories': ['Sheet1', start_row, x_col_idx, end_row, x_col_idx],
                    'values': ['Sheet1', start_row, y_col_idx, end_row, y_col_idx],
                    'line': {
                        'width': 2,
                        'color': colors[df_idx % len(colors)]
                    },
                    'marker': {
                        'type': 'circle',
                        'size': 4,
                        'border': {'color': colors[df_idx % len(colors)]},
                        'fill': {'color': colors[df_idx % len(colors)]}
                    },
                    'name': series_names[df_idx] if df_idx < len(series_names) else f'Series_{df_idx+1}'
                })
            
            # 更新列偏移量
            current_col_offset += len(stats_df.columns) + 2
        
        # 设置坐标轴
        chart.set_x_axis({
            'name': x_column,
            'name_font': {'size': 12},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True}
        })
        
        chart.set_y_axis({
            'name': f'{base_col} Statistical Values',
            'name_font': {'size': 12},
            'num_font': {'size': 10},
            'major_gridlines': {'visible': True}
        })
        
        # 设置图例
        chart.set_legend({
            'position': 'top',
            'font': {'size': 10}
        })
        
        # 插入图表
        worksheet.insert_chart(chart_position, chart)




















# wbname = 'error_analysis_results.xlsx'

# # 创建Excel文件，但不写入原始数据
# workbook = xlsxwriter.Workbook(wbname)
# worksheet = workbook.add_worksheet()

# # 初始化写入信息
# writeInfo = {'curvenamerow': 0, 'headingsrow': 1, 'datarow': 2}
# current_col_offset = 0

# # 写入误差分析数据
# if error_df_list is not None and len(error_df_list) > 0:
#     for idx, error_df in enumerate(error_df_list):
#         if error_df is not None and not error_df.empty:
#             # 写入误差数据标题和列名
#             error_name = f'Relative_Errors_{idx+1}'
#             error_headings = list(error_df.columns)
#             error_datanum = len(error_headings)
            
#             worksheet.write_row(writeInfo['curvenamerow'], current_col_offset, [error_name])
#             worksheet.write_row(writeInfo['headingsrow'], current_col_offset, error_headings)
            
#             # 写入误差数据
#             for col_idx, col_name in enumerate(error_headings):
#                 col_data = error_df[col_name].values
#                 worksheet.write_column(writeInfo['datarow'], current_col_offset + col_idx, col_data)
            
#             # 更新列偏移量
#             current_col_offset += error_datanum + 2

# # 写入统计分析数据
# if stats_list is not None and len(stats_list) > 0:
#     stats_names = ['Mean_Values', 'Variance_Values', 'StdDev_Values', 'CV_Values']
    
#     for idx, stats_df in enumerate(stats_list):
#         if stats_df is not None and not stats_df.empty:
#             # 写入统计数据标题和列名
#             stats_name = stats_names[idx] if idx < len(stats_names) else f'Stats_{idx+1}'
#             stats_headings = list(stats_df.columns)
#             stats_datanum = len(stats_headings)
            
#             worksheet.write_row(writeInfo['curvenamerow'], current_col_offset, [stats_name])
#             worksheet.write_row(writeInfo['headingsrow'], current_col_offset, stats_headings)
            
#             # 写入统计数据
#             for col_idx, col_name in enumerate(stats_headings):
#                 col_data = stats_df[col_name].values
#                 worksheet.write_column(writeInfo['datarow'], current_col_offset + col_idx, col_data)
            
#             # 更新列偏移量
#             current_col_offset += stats_datanum + 2

# # 绘制误差分析图表
# if error_df_list is not None and len(error_df_list) > 0:
#     create_error_analysis_charts(workbook, worksheet, error_df_list, writeInfo)

# # 绘制统计分析图表  
# if stats_list is not None and len(stats_list) > 0:
#     # 计算误差数据的列偏移量信息
#     error_col_info = []
#     if error_df_list is not None:
#         for error_df in error_df_list:
#             if error_df is not None and not error_df.empty:
#                 error_col_info.append(len(error_df.columns))
    
#     create_statistical_charts(workbook, worksheet, stats_list, writeInfo, error_col_info)





