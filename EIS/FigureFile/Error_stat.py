

import numpy as np
import pandas as pd


def calculate_relative_errors(plotdata, outputlist, plotdataname):
    """
    计算多数据集相对误差分析
    
    Parameters:
    plotdata: list - 数据列表
    outputlist: list - 选择列表 (1表示选中，0表示未选中)
    plotdataname: list - 数据名称列表
    
    Returns:
    tuple: (error_dfs_list, error_stats)
        - error_dfs_list: 相对误差DataFrame列表
        - error_stats: 误差统计信息字典
    """
    # 获取选中的数据索引
    selected_indices = [i for i, selected in enumerate(outputlist) if selected == 1]
    
    if len(selected_indices) <= 1:
        return None, None
    
    # 获取基准数据集（第一个选中的数据）
    base_data = plotdata[selected_indices[0]]
    
    if base_data is None or len(base_data) == 0:
        return None, None
    
    base_columns = list(base_data.columns)
    error_dfs_list = []
    error_stats = {}
    
    # 计算每个其他数据集与基准的相对误差
    for comp_idx in selected_indices[1:]:
        comp_data = plotdata[comp_idx]
        comp_name = plotdataname[comp_idx]
        
        if comp_data is None or len(comp_data) == 0:
            continue
        
        # 创建相对误差DataFrame
        current_error_df = pd.DataFrame()
        current_error_df[base_columns[0]] = base_data[base_columns[0]]
        
        comp_columns = list(comp_data.columns)
        min_length = min(len(base_data), len(comp_data))
        
        # 计算每列的相对误差
        for col_idx, base_col in enumerate(base_columns[1:], 1):
            if col_idx < len(comp_columns):
                comp_col = comp_columns[col_idx]
                
                # 截取相同长度的数据
                base_values = base_data[base_col].iloc[:min_length]
                comp_values = comp_data[comp_col].iloc[:min_length]
                
                # 计算相对误差 (%)，避免除零错误
                denominator = np.where(np.abs(base_values) < 1e-10, 1e-10, base_values)
                rel_error = ((comp_values - base_values) / denominator) * 100
                
                current_error_df[f'{base_col}_RelErr'] = rel_error
                
                # 统计信息
                if base_col not in error_stats:
                    error_stats[base_col] = []
                error_stats[base_col].append({
                    'mean_rel_error': np.mean(np.abs(rel_error)),
                    'max_rel_error': np.max(np.abs(rel_error)),
                    'comp_name': comp_name
                })
        
        error_dfs_list.append(current_error_df)
    
    return error_dfs_list, error_stats
    


def calculate_statistical_indicators(plotdata, outputlist, plotdataname):
    """
    计算多数据集统计指标（均值、方差、标准差、变异系数）
    
    Parameters:
    plotdata: list - 数据列表
    outputlist: list - 选择列表 (1表示选中，0表示未选中)
    plotdataname: list - 数据名称列表
    
    Returns:
    tuple: (stats_dfs_list, stats_summary)
        - stats_dfs_list: 包含各统计指标DataFrame的列表 [mean_df, variance_df, std_df, cv_df]
        - stats_summary: 统计摘要信息字典
    """
    # 获取选中的数据索引
    selected_indices = [i for i, selected in enumerate(outputlist) if selected == 1]
    
    if len(selected_indices) <= 1:
        return None, None
    
    # 获取基准数据
    base_data = plotdata[selected_indices[0]]
    base_columns = list(base_data.columns)
    
    # 收集所有比较数据集的值
    all_values = {col: [] for col in base_columns[1:]}
    
    for comp_idx in selected_indices[1:]:
        comp_data = plotdata[comp_idx]
        if comp_data is None or len(comp_data) == 0:
            continue
            
        comp_columns = list(comp_data.columns)
        min_length = min(len(base_data), len(comp_data))
        
        for col_idx, base_col in enumerate(base_columns[1:], 1):
            if col_idx < len(comp_columns):
                comp_col = comp_columns[col_idx]
                comp_values = comp_data[comp_col].iloc[:min_length]
                all_values[base_col].append(comp_values.values)
    
    # 初始化统计DataFrame
    mean_df = pd.DataFrame()
    variance_df = pd.DataFrame()
    std_df = pd.DataFrame()
    cv_df = pd.DataFrame()
    
    # 所有DataFrame都包含基准数据的第一列作为索引列
    for df in [mean_df, variance_df, std_df, cv_df]:
        df[base_columns[0]] = base_data[base_columns[0]]
    
    stats_summary = {}
    
    # 计算每列的统计指标
    for col in base_columns[1:]:
        if col in all_values and len(all_values[col]) > 0:
            # 合并基准数据和比较数据
            base_values = base_data[col].values
            all_col_values = [base_values] + all_values[col]
            
            # 转换为矩阵进行统计计算
            min_len = min(len(arr) for arr in all_col_values)
            col_matrix = np.array([arr[:min_len] for arr in all_col_values])
            
            # 计算统计指标
            col_mean = np.mean(col_matrix, axis=0)
            col_var = np.var(col_matrix, axis=0, ddof=1)
            col_std = np.std(col_matrix, axis=0, ddof=1)
            # 计算变异系数，避免除零错误
            col_cv = np.where(np.abs(col_mean) > 1e-10, (col_std / np.abs(col_mean)) * 100, 0)
            
            # 存储到对应DataFrame
            mean_df[f'{col}_Mean'] = col_mean
            variance_df[f'{col}_Variance'] = col_var
            std_df[f'{col}_StdDev'] = col_std
            cv_df[f'{col}_CV%'] = col_cv
            
            # 统计摘要
            stats_summary[col] = {
                'overall_mean_var': np.mean(col_var),
                'overall_mean_std': np.mean(col_std),
                'overall_mean_cv': np.mean(col_cv)
            }
    
    stats_list = [mean_df, variance_df, std_df, cv_df]
    return stats_list, stats_summary
    


def calculate_single_dataset_statistics(plotdata, outputlist, plotdataname):
    """
    计算单数据集内部统计误差
    
    Parameters:
    plotdata: list - 数据列表
    outputlist: list - 选择列表 (1表示选中，0表示未选中)
    plotdataname: list - 数据名称列表
    
    Returns:
    tuple: (stats_dfs_list, single_stats_summary)
        - stats_dfs_list: 包含两个DataFrame的列表 [rolling_std_df, relative_deviation_df]
        - single_stats_summary: 单数据集统计摘要
    """
    # 获取选中的数据索引
    selected_indices = [i for i, selected in enumerate(outputlist) if selected == 1]
    
    if len(selected_indices) == 0:
        return None, None
    
    data = plotdata[selected_indices[0]]
    
    if data is None or len(data) <= 1:
        return None, None
    
    columns = list(data.columns)
    
    # 创建两个独立的DataFrame
    rolling_std_df = pd.DataFrame()
    relative_deviation_df = pd.DataFrame()
    
    # 两个DataFrame都包含横轴数据
    rolling_std_df[columns[0]] = data[columns[0]]
    relative_deviation_df[columns[0]] = data[columns[0]]
    
    single_stats_summary = {}
    
    # 计算移动窗口大小（数据长度的10%，最小为3）
    window_size = max(3, len(data) // 10)
    
    for col in columns[1:]:
        if data[col].dtype in ['float64', 'int64']:
            values = data[col].values
            
            # 计算基本统计量
            mean_val = np.mean(values)
            std_val = np.std(values, ddof=1)
            var_val = np.var(values, ddof=1)
            cv_val = (std_val / np.abs(mean_val)) * 100 if np.abs(mean_val) > 1e-10 else 0
            
            # 计算移动统计误差
            rolling_std = data[col].rolling(window=window_size, center=True, min_periods=1).std()
            rolling_mean = data[col].rolling(window=window_size, center=True, min_periods=1).mean()
            
            # 相对于移动平均的偏差 (%)
            denominator = np.where(np.abs(rolling_mean) > 1e-10, rolling_mean, 1e-10)
            relative_deviation = np.abs((values - rolling_mean) / denominator) * 100
            
            # 分别存储到两个DataFrame
            rolling_std_df[f'{col}_RollingStd'] = rolling_std
            relative_deviation_df[f'{col}_RelDeviation%'] = relative_deviation
            
            # 统计摘要
            single_stats_summary[col] = {
                'mean_val': mean_val,
                'std_val': std_val,
                'var_val': var_val,
                'cv_val': cv_val,
                'mean_relative_deviation': np.mean(relative_deviation)
            }
    
    # 返回包含两个DataFrame的列表
    stats_dfs_list = [rolling_std_df, relative_deviation_df]
    return stats_dfs_list, single_stats_summary