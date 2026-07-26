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
from EIS.ProcessingFile.Processingfun import calibrate, paraplate, TLcalibrate, DieMat, threesolutions

from EIS.Other.standard_parameter import paraNaCl, paraWater, paraEthanol

##############constant##############
eps0 = 8.854187817e-12  # F/m Vacuum permittivity
mu0 = 4 * np.pi * 1e-7  # H/m  Permeability
##############constant##############


# 获取当前文件的绝对路径，然后向上三级目录到达项目根目录
current_file_path = os.path.abspath(__file__)
proj_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))

# 验证项目根目录文件夹名字中是否包含"AnyEIS"（不区分大小写）
proj_folder_name = os.path.basename(proj_path)
if "anyeis" not in proj_folder_name.lower():
    print(f"错误：项目根目录文件夹名字 '{proj_folder_name}' 中不包含 'AnyEIS'")
    print(f"当前项目路径：{proj_path}")
    print("请确保项目位于包含'AnyEIS'的文件夹中")
    import sys
    sys.exit(1)
else:
    pass

# path = os.path.join(proj_path, 'testdata', 'process', 'Three solution','ref')
# fileslist = sorted(os.listdir(path), reverse=False)

# path = os.path.join(proj_path, 'testdata', 'process', 'Dielectric material','ref')
# fileslist = sorted(os.listdir(path), reverse=False)

path = os.path.join(proj_path, 'testdataprocess',  'Transmission line','ref')
fileslist = sorted(os.listdir(path), reverse=False)

# 过滤掉文件夹，只保留文件
fileslist_filtered = []
for item in fileslist:
    item_path = os.path.join(path, item)
    if os.path.isfile(item_path):  # 检查是否为文件
        fileslist_filtered.append(item)

fileslist = fileslist_filtered
filepath = [os.path.join(path, i) for i in fileslist]






# propath = proj_path + '\\testdata\\process\\Parallel plate'
# profileslist = sorted(os.listdir(propath), reverse=False)
# profilepath = [propath + "\\" + i for i in profileslist]


# propath = proj_path + '\\testdata\\process\\Dielectric material\\pro'
# profileslist = sorted(os.listdir(propath), reverse=False)
# profilepath = [propath + "\\" + i for i in profileslist]


# propath = proj_path + '\\testdata\\process\\Three solution\\pro'
# profileslist = sorted(os.listdir(propath), reverse=False)
# profilepath = [propath + "\\" + i for i in profileslist]

propath = proj_path + '\\testdataprocess\\Transmission line\\pro'
profileslist = sorted(os.listdir(propath), reverse=False)
profilepath = [propath + "\\" + i for i in profileslist]

# ################读取数据######################
# data=list()
# dataname=list()

# datanametemp,datatemp=readfile(filepath[0])
# data.append(datatemp[0])
# dataname.append(datanametemp[0])


# datanametemp,datatemp=readfile(filepath[1])
# data.append(datatemp[0])
# dataname.append(datanametemp[0])

# datanametemp,datatemp=readfile(filepath[2])
# data.append(datatemp[0])
# dataname.append(datanametemp[0])
# ################读取数据######################


################读取参考数据######################
refdata = list()
refdataname = list()

refdatanametemp, refdatatemp = readfile(filepath[0])
refdata.append(refdatatemp[0])
refdataname.append(refdatanametemp[0])

# refdatanametemp, refdatatemp = readfile(filepath[1])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])

# refdatanametemp, refdatatemp = readfile(filepath[2])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])
################读取参考数据######################




##################循环读取数据########################
prodata = list()
prodataname = list()

for i in range(0, len(profilepath)):
    prodatanametemp, prodatatemp = readfile(profilepath[i])
    prodata.append(prodatatemp[0])
    prodataname.append(prodatanametemp[0])
##################循环读取数据########################









# Parallel Plate method parameters
# parallel_plate_parameters_info = {
#     'processing_parameters': {
#         'geometric_constant': '0.00255'
#     }
# }
# Gf=float(parallel_plate_parameters_info['processing_parameters']['geometric_constant'])


# Calibration method parameters
# calibration_parameters_info = {
#     'processing_parameters': {},
#     'solution_parameters': [
#         {'solution_index': 1, 'name': 'open'},
#         {'solution_index': 2, 'name': 'short'},
#         {'solution_index': 3, 'name': 'load'}
#     ]
# }
# open_idx = calibration_parameters_info.get('open_index', 0)
# short_idx = calibration_parameters_info.get('short_index', 1)
# load_idx = calibration_parameters_info.get('load_index', 2)


# ################Calibration method parameters读取参考数据######################
# refdata = list()
# refdataname = list()

# refdatanametemp, refdatatemp = readfile(filepath[load_idx-1])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])

# refdatanametemp, refdatatemp = readfile(filepath[open_idx-1])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])

# refdatanametemp, refdatatemp = readfile(filepath[short_idx-1])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])
# ################Calibration读取参考数据######################


# Dielectric Material method parameters
# dielectric_material_parameters_info = {
#     'processing_parameters': {},
#     'solution_parameters': [
#         {
#             'solution_index': 0,
#             'name': 'Air',
#             'concentration': 0.0,
#             'temperature': 25.0
#         },
#         {
#             'solution_index': 1,
#             'name': 'Water',
#             'concentration': 0.01,
#             'temperature': 25.0
#         }
#     ]
# }
# Air_idx = dielectric_material_parameters_info.get('Air', 0)
# Water_idx = dielectric_material_parameters_info.get('Water', 1)


# Three Solution method parameters
# three_solution_parameters_info = {
#     'processing_parameters': {},
#     'solution_parameters': [
#         {
#             'solution_index': 0,
#             'name': 'Ethanol',
#             'concentration': 0.0,
#             'temperature': 25.0
#         },
#         {
#             'solution_index': 1,
#             'name': 'NaCl',
#             'concentration': 0.01,
#             'temperature': 25.0
#         },
#         {
#             'solution_index': 2,
#             'name': 'NaCl',
#             'concentration': 0.1,
#             'temperature': 25.0
#         }
#     ]
# }

# Transmission Line method parameters
transmission_line_parameters_info = {
    'processing_parameters': {
        'geometric_constant': '3.874702216993875',
        'character_impedance': '50',
        'electrode_length': '0.0164',
        'solution_length': '0.00255'
    },
    'solution_parameters': [
        {
            'solution_index': 0,
            'name': 'NaCl',
            'concentration': 0.01,
            'temperature': 25.0
        }
    ]
}



# # K-K for DS method parameters
# kk_ds_parameters_info = {
#     'processing_parameters': {
#         'validation_parameter': '1.0'
#     }
# }

# # K-K for EIS method parameters
# kk_eis_parameters_info = {
#     'processing_parameters': {
#         'validation_parameter': '0.00255'
#     }
# }

# # Other method parameters (empty)
# other_parameters_info = {
#     'processing_parameters': {}
# }



################# Calbrate #########
# result1 = paraplate(prodata, Gf)           #数据处理
# result2 = calibrate(refdata, prodata,calibration_parameters_info)
# result3=DieMat(refdata,prodata,dielectric_material_parameters_info)
# result5=threesolutions(refdata,prodata,three_solution_parameters_info)

result4 = TLcalibrate(refdata, prodata, transmission_line_parameters_info)
# result7=twosolutions(refdata,prodata,solutioninfolist)
# ################## Calbrate #########


















##############subplot#############

# plt.figure(2, figsize=(16, 9))

# # 绘制result1处理后的数据
# for i, data_df in enumerate(result4):
#     # 从DataFrame中提取数据
#     freq = data_df['FREQ[Hz]']
#     eps_re = data_df['EpsRE[-]']
#     eps_im = data_df['EpsIM[-]']
#     sigma_re = data_df['SigmaRE[S/m]']
#     sigma_im = data_df['SigmaIM[S/m]']
    
#     # 获取标签名称
#     label = prodataname[i] if i < len(prodataname) else f'Data {i+1}'
    
#     # 子图1: 频率 vs 介电常数实部
#     ax1 = plt.subplot(221)
#     plt.plot(log10(freq), eps_re, linewidth=2, label=label)
#     plt.xlabel("Log Frequency [Hz]")
#     plt.ylabel("Dielectric Constant Real Part")
    
#     # 子图2: 频率 vs 介电常数虚部
#     ax2 = plt.subplot(222)
#     plt.plot(log10(freq), eps_im, linewidth=2, label=label)
#     plt.xlabel("Log Frequency [Hz]")
#     plt.ylabel("Dielectric Constant Imaginary Part")
    
#     # 子图3: 介电常数复平面图 (实部 vs 虚部)
#     ax3 = plt.subplot(223)
#     plt.plot(eps_re, eps_im, linewidth=2, label=label)
#     plt.xlabel("Dielectric Constant Real Part")
#     plt.ylabel("Dielectric Constant Imaginary Part")
    
#     # 子图4: 频率 vs 电导率实部
#     ax4 = plt.subplot(224)
#     plt.plot(log10(freq), sigma_re, linewidth=2, label=label)
#     plt.xlabel("Log Frequency [Hz]")
#     plt.ylabel("Conductivity Real Part [S/m]")

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
# ##############subplot##############


# ##############subplot for result2#############

plt.figure(3, figsize=(16, 9))

# 绘制result2处理后的阻抗谱数据
for i, data_df in enumerate(result4):
    # 从DataFrame中提取阻抗谱数据
    freq = data_df['FREQ[Hz]']
    z_re = data_df['Rs[ohm]']
    z_im = data_df['X[ohm]']
    z_mag = np.sqrt(z_re**2 + z_im**2)  # 阻抗幅值
    z_phase = data_df['PHASE[deg]']
    
    # 获取标签名称
    label = prodataname[i] if i < len(prodataname) else f'Data {i+1}'
    
    # 子图1: 频率 vs 阻抗实部
    ax1 = plt.subplot(221)
    plt.plot(log10(freq), z_re, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Resistance [Ω]")
    
    # 子图2: 频率 vs 阻抗虚部
    ax2 = plt.subplot(222)
    plt.plot(log10(freq), -z_im, linewidth=2, label=label)  # 负号使虚部为正值显示
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("-Reactance [Ω]")
    
    # 子图3: Nyquist图 (阻抗实部 vs 阻抗虚部)
    ax3 = plt.subplot(223)
    plt.plot(z_re, -z_im, linewidth=2, label=label)  # 负号使虚部为正值显示
    plt.xlabel("Resistance [Ω]")
    plt.ylabel("-Reactance [Ω]")
    
    # 子图4: 频率 vs 阻抗幅值
    ax4 = plt.subplot(224)
    plt.plot(log10(freq), log10(z_mag), linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Log |Z| [Ω]")

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
##############subplot for result2##############


























