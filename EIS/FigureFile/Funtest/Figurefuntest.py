# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""


import os
import sys
from numpy import log10,real,imag,array,angle,absolute,pi,sqrt,log,tanh,arctanh
import numpy as np
import pandas as pd
import xlsxwriter
from EIS.InputFile.Inputfun import readfile

from EIS.FigureFile.Figurefun import EISfiguremaker,writeanydata,creatanyfile,EPSfiguremaker,apply_paper_chart_maker,Anyplot,create_error_analysis_charts,create_statistical_charts,create_single_dataset_charts

from EIS.FigureFile.Error_stat import calculate_relative_errors,calculate_statistical_indicators,calculate_single_dataset_statistics
from EIS.Other.readdatafortest import get_project_root_path,get_files_and_read_data


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



proj_path = get_project_root_path()
print('proj_path:',proj_path)


pro_path = os.path.join(proj_path, 'testdata', 'error')
prodata, prodataname, profilepath = get_files_and_read_data(pro_path, read_mode=0)
outputlist=[1]

prodata2, prodataname2, profilepath2 = get_files_and_read_data(pro_path, read_mode=0)
outputlist2=[1,1,1]

error_df_list, error_stats = calculate_relative_errors(prodata, outputlist, prodataname)
stats_list, summary = calculate_statistical_indicators(prodata, outputlist, prodataname)

stats_dfs_list, single_stats_summary = calculate_single_dataset_statistics(prodata2, outputlist2, prodataname2)



wbname = 'Results/error_analysis_results.xlsx'

# 创建Excel文件，但不写入原始数据
workbook = xlsxwriter.Workbook(wbname)
worksheet = workbook.add_worksheet()

# 初始化写入信息
writeInfo = {'curvenamerow': 0, 'headingsrow': 1, 'datarow': 2}
current_col_offset = 0

# 写入误差分析数据
current_col_offset = write_error_analysis_data(worksheet, error_df_list, writeInfo, current_col_offset)

# 写入统计分析数据
current_col_offset = write_statistical_analysis_data(worksheet, stats_list, writeInfo, current_col_offset)

# 绘制误差分析图表
if error_df_list is not None and len(error_df_list) > 0:
    create_error_analysis_charts(workbook, worksheet, error_df_list, writeInfo)

# 绘制统计分析图表  
if stats_list is not None and len(stats_list) > 0:
    # 计算误差数据的列偏移量信息
    error_col_info = []
    if error_df_list is not None:
        for error_df in error_df_list:
            if error_df is not None and not error_df.empty:
                error_col_info.append(len(error_df.columns))
    
    create_statistical_charts(workbook, worksheet, stats_list, writeInfo, error_col_info)

workbook.close()






wbname = 'Results/single_dataset_statistics_results.xlsx'
# 创建Excel文件，但不写入原始数据
workbook = xlsxwriter.Workbook(wbname)
worksheet = workbook.add_worksheet()

# 初始化写入信息
writeInfo = {'curvenamerow': 0, 'headingsrow': 1, 'datarow': 2}
current_col_offset = 0

# 写入单数据集统计分析数据
current_col_offset = write_single_dataset_statistics_data(worksheet, stats_dfs_list, writeInfo, current_col_offset)

# 绘制单数据集统计分析图表
if stats_dfs_list is not None and len(stats_dfs_list) > 0:
    create_single_dataset_charts(workbook, worksheet, stats_dfs_list, writeInfo)



workbook.close()






















































