# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""
########数据输入窗口功能测试#######

import os


from numpy import log10,real,imag,array,angle,absolute,pi,sqrt,log,tanh,arctanh,exp,cos,sin
import pandas as pd
import matplotlib.pyplot as plt
from EIS.InputFile.Inputfun import readfile,readcsvfile,readexcelfile


##############constant##############
eps0=8.854187817e-12 #F/m Vacuum permittivity
mu0=4*pi*1e-7# H/m  Permeability
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




path = os.path.join(proj_path, 'testdata', 'process', 'Three solution')
fileslist = sorted(os.listdir(path), reverse=False)

# 过滤掉文件夹，只保留文件
fileslist_filtered = []
for item in fileslist:
    item_path = os.path.join(path, item)
    if os.path.isfile(item_path):  # 检查是否为文件
        fileslist_filtered.append(item)

fileslist = fileslist_filtered
filepath = [os.path.join(path, i) for i in fileslist]



# ################读取参考数据######################
# refdata=list()
# refdataname=list()

# refdatanametemp,refdatatemp=readfile(filepath[0])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])

# refdatanametemp,refdatatemp=readfile(filepath[15])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])

# refdatanametemp,refdatatemp=readfile(filepath[17])
# refdata.append(refdatatemp[0])
# refdataname.append(refdatanametemp[0])
# ################读取参考数据######################

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


##################循环读取数据########################
prodata=list()
prodataname=list()

for i in range(0,len(filepath)):
    prodatanametemp,prodatatemp=readfile(filepath[i])
    prodata.append(prodatatemp[0])
    prodataname.append(prodatanametemp[0])
##################循环读取数据########################








##############subplot#############

plt.figure(2, figsize=(16, 9))

# 绘制所有数据
for i, data_df in enumerate(prodata):
    # 从DataFrame中提取数据
    freq = data_df['FREQ[Hz]']
    Z = data_df['Z[ohm]']
    phy = data_df['PHASE[deg]']
    Rs = data_df['Rs[ohm]']
    X = data_df['X[ohm]']
    
    # 获取标签名称
    label = prodataname[i] if i < len(prodataname) else f'Data {i+1}'
    
    # 子图1: 频率 vs 实部
    ax1 = plt.subplot(221)
    plt.plot(log10(freq), Rs, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Rs [Ohm]")
    
    # 子图2: 频率 vs 虚部
    ax2 = plt.subplot(222)
    plt.plot(log10(freq), X, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("x [Ohm]")
    plt.gca().invert_yaxis()
    
    # 子图3: Nyquist图 (实部 vs 虚部)
    ax3 = plt.subplot(223)
    plt.plot(Rs, X, linewidth=2, label=label)
    plt.gca().invert_yaxis()
    plt.xlabel("Rs [Ohm]")
    plt.ylabel("X [Ohm]")
    
    # 子图4: 频率 vs 相位
    ax4 = plt.subplot(224)
    plt.plot(log10(freq), phy, linewidth=2, label=label)
    plt.xlabel("Log Frequency [Hz]")
    plt.ylabel("Phase [deg]")

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











































