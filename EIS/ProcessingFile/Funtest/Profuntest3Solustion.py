# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""

import os
import sys

sys.path.append('..')

from numpy import log10, real, imag, array, angle, absolute, pi, sqrt, log, tanh, arctanh
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd

from EIS.InputFile.Inputfun import readfile
from EIS.ProcessingFile.Processingfun import calibrate, paraplate, TLcalibrate, DieMat, threesolutions,TLcalculateEPS_JAX,TLcalculateEPS

from EIS.Other.standard_parameter import paraNaCl, paraWater, paraEthanol

##############constant##############
eps0 = 8.854187817e-12  # F/m Vacuum permittivity
mu0 = 4 * np.pi * 1e-7  # H/m  Permeability
##############constant##############


# 1. 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
proj_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))

# 2. 验证项目根目录文件夹名字中是否包含"AnyEIS"（不区分大小写）
proj_folder_name = os.path.basename(proj_path)
if "anyeis" not in proj_folder_name.lower():
    print(f"错误：项目根目录文件夹名字 '{proj_folder_name}' 中不包含 'AnyEIS'")
    sys.exit(1)


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
        # 读取所有文件
        for filepath in filepaths:
            datanametemp, datatemp = readfile(filepath)
            data_list.append(datatemp[0])
            dataname_list.append(datanametemp[0])

    elif isinstance(read_mode, int):
        # 读取指定索引的文件
        if 0 <= read_mode < len(filepaths):
            datanametemp, datatemp = readfile(filepaths[read_mode])
            data_list.append(datatemp[0])
            dataname_list.append(datanametemp[0])
    
    return data_list, dataname_list, filepaths

# 3、4. 过滤并读取ref文件（读取第一个文件）
ref_path = os.path.join(proj_path, 'testdataprocess', 'Three solution', 'ref')
refdata, refdataname, filepath = get_files_and_read_data(ref_path, read_mode='all')

# 5、6. 过滤并读取pro文件（读取所有文件）
pro_path = os.path.join(proj_path, 'testdataprocess', 'Three solution', 'pro')
prodata, prodataname, profilepath = get_files_and_read_data(pro_path, read_mode='all')



# Three Solution method parameters
three_solution_parameters_info = {
    'processing_parameters': {},
    'solution_parameters': [
        {
            'solution_index': 0,
            'name': 'NaCl',
            'concentration': 0.01,
            'temperature': 25.0
        },
        {
            'solution_index': 1,
            'name': 'NaCl',
            'concentration': 0.05,
            'temperature': 25.0
        },
        {
            'solution_index': 2,
            'name': 'NaCl',
            'concentration': 0.5,
            'temperature': 25.0
        }
    ]
}

omega=refdata[1]['FREQ[Hz]']
eps1,sigma1=paraWater(omega)

result5=threesolutions(refdata,prodata,three_solution_parameters_info)







# #############subplot#############

plt.figure(2, figsize=(16, 9))

# 绘制result1处理后的数据
for i, data_df in enumerate(result5):
    # 从DataFrame中提取数据
    freq = data_df['FREQ[Hz]']
    eps_re = data_df['EpsRE[-]']
    eps_im = data_df['EpsIM[-]']
    sigma_re = data_df['SigmaRE[S/m]']
    sigma_im = data_df['SigmaIM[S/m]']
    
    # 获取标签名称
    label = prodataname[i] if i < len(prodataname) else f'Data {i+1}'
    
    # 子图1: 频率 vs 介电常数实部
    ax1 = plt.subplot(221)
    plt.plot(log10(freq), eps_re, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Dielectric Constant ")

    # 子图2: 频率 vs 电导率实部
    ax2 = plt.subplot(222)
    plt.plot(log10(freq), sigma_re, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Conductivity [S/m]")
        
        
    # 子图3: 导电率复平面图 (实部 vs 虚部)
    ax3 = plt.subplot(223)
    plt.plot(sigma_re, sigma_im, linewidth=2, label=label)
    plt.xlabel("Dielectric Constant Real Part")
    plt.ylabel("Dielectric Constant Imaginary Part")

    # 子图4: 频率 vs 介电常数虚部
    ax4 = plt.subplot(224)
    plt.plot(log10(freq), eps_im, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Dielectric Constant Imaginary Part")
    

    


# 为每个子图添加图例
plt.subplot(221)
plt.legend()
plt.subplot(222)
plt.legend()
plt.subplot(223)
plt.legend()
plt.subplot(224)
plt.legend()

plt.tight_layout()
plt.show()
##############subplot##############


##############subplot for result2#############

# plt.figure(3, figsize=(16, 9))

# # 绘制result2处理后的阻抗谱数据
# for i, data_df in enumerate(result5):
#     # 从DataFrame中提取阻抗谱数据
#     freq = data_df['FREQ[Hz]']
#     z_re = data_df['Rs[ohm]']
#     z_im = data_df['X[ohm]']
#     z_mag = np.sqrt(z_re**2 + z_im**2)  # 阻抗幅值
#     z_phase = data_df['PHASE[deg]']
    
#     # 获取标签名称
#     label = prodataname[i] if i < len(prodataname) else f'Data {i+1}'
    
#     # 子图1: 频率 vs 阻抗实部
#     ax1 = plt.subplot(221)
#     plt.plot(log10(freq), z_re, linewidth=2, label=label)
#     plt.xlabel("Log Frequency [Hz]")
#     plt.ylabel("Resistance [Ω]")
    
#     # 子图2: 频率 vs 阻抗虚部
#     ax2 = plt.subplot(222)
#     plt.plot(log10(freq), -z_im, linewidth=2, label=label)  # 负号使虚部为正值显示
#     plt.xlabel("Log Frequency [Hz]")
#     plt.ylabel("-Reactance [Ω]")
    
#     # 子图3: Nyquist图 (阻抗实部 vs 阻抗虚部)
#     ax3 = plt.subplot(223)
#     plt.plot(z_re, -z_im, linewidth=2, label=label)  # 负号使虚部为正值显示
#     plt.xlabel("Resistance [Ω]")
#     plt.ylabel("-Reactance [Ω]")
    
#     # 子图4: 频率 vs 阻抗幅值
#     ax4 = plt.subplot(224)
#     plt.plot(log10(freq), log10(z_mag), linewidth=2, label=label)
#     plt.xlabel("Log Frequency [Hz]")
#     plt.ylabel("Log |Z| [Ω]")

# # 为每个子图添加图例
# plt.subplot(221)
# plt.legend()
# plt.subplot(222)
# plt.legend()
# plt.subplot(223)
# plt.legend()
# plt.subplot(224)
# plt.legend()

# plt.tight_layout()
# plt.show()
##############subplot for result2##############


























