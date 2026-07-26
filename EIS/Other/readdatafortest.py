# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""

import os
import sys
sys.path.append('..')



from EIS.InputFile.Inputfun import readfile




def get_project_root_path(current_file=__file__):
    """
    获取项目根目录路径并验证项目名称
    
    Args:
        current_file (str): 当前文件路径，默认为调用文件的路径
        
    Returns:
        str: 项目根目录路径
        
    Raises:
        SystemExit: 当项目根目录名称不包含'AnyEIS'时退出程序
    """
    # 1. 获取当前文件的绝对路径
    current_file_path = os.path.abspath(current_file)
    proj_path = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    
    # 2. 验证项目根目录文件夹名字中是否包含"AnyEIS"（不区分大小写）
    proj_folder_name = os.path.basename(proj_path)
    if "anyeis" not in proj_folder_name.lower():
        print(f"错误：项目根目录文件夹名字 '{proj_folder_name}' 中不包含 'AnyEIS'")
        sys.exit(1)
    
    return proj_path




def get_files_and_read_data(folder_path, read_mode="all"):
    """
    过滤掉文件夹只保留文件，并读取文件数据
    
    Args:
        folder_path (str): 文件夹路径
        read_mode (str or int): "all"读取所有文件，整数指定读取第几个文件（从0开始）
        
    Returns:
        tuple: (数据列表, 数据名称列表, 文件路径列表)
    """
    # 过滤掉文件夹，只保留文件
    items = sorted(os.listdir(folder_path))
    filepaths = [os.path.join(folder_path, item) for item in items if os.path.isfile(os.path.join(folder_path, item))]
    
    # 读取文件
    data_list = []
    dataname_list = []
    
    if read_mode == "all":
        # 读取所有文件的所有数据
        for filepath in filepaths:
            datanametemp, datatemp = readfile(filepath)
            # 读取文件中的所有数据集，而不只是第一个
            for i in range(len(datatemp)):
                data_list.append(datatemp[i])
                dataname_list.append(datanametemp[i])

    elif isinstance(read_mode, int):
        # 读取指定索引的文件的所有数据
        if 0 <= read_mode < len(filepaths):
            datanametemp, datatemp = readfile(filepaths[read_mode])
            # 读取该文件中的所有数据集
            for i in range(len(datatemp)):
                data_list.append(datatemp[i])
                dataname_list.append(datanametemp[i])
    
    return data_list, dataname_list, filepaths




# 获取项目根目录路径
proj_path = get_project_root_path()

# 3、4. 过滤并读取ref文件（读取第一个文件）
ref_path = os.path.join(proj_path, 'testdataprocess', 'Three solution', 'ref')
refdata, refdataname, filepath = get_files_and_read_data(ref_path, read_mode='all')

# 5、6. 过滤并读取pro文件（读取所有文件）
pro_path = os.path.join(proj_path, 'testdataprocess', 'Three solution', 'pro')
prodata, prodataname, profilepath = get_files_and_read_data(pro_path, read_mode='all')


























