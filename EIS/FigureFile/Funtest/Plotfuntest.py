# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""


import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import matplotlib.pyplot as plt

from numpy import log10,real,imag,array,angle,absolute,pi,sqrt,log,tanh,arctanh
import pandas as pd
from EIS.InputFile.Inputfun import readfile

from EIS.FigureFile.Figurefun import EISfiguremaker,writeanydata,creatanyfile,EPSfiguremaker


import sys
# from Plottest_pyqt5 import MyMplCanvasPyQt5, create_academic_canvas, save_publication_figure, setup_academic_style




# 获取当前文件的绝对路径，然后向上两级目录到达项目根目录
current_file_path = os.path.abspath(__file__)
proj_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))

# 验证项目根目录文件夹名字中是否包含"AnyEIS"（不区分大小写）
proj_folder_name = os.path.basename(proj_path)
if "anyeis" not in proj_folder_name.lower():
    print(f"错误：项目根目录文件夹名字 '{proj_folder_name}' 中不包含 'AnyEIS'")
    print(f"当前项目路径：{proj_path}")
    print("请确保项目位于包含'AnyEIS'的文件夹中")
    sys.exit(1)
else:
    pass


##############constant##############
eps0=8.854187817e-12 #F/m Vacuum permittivity
mu0=4*pi*1e-7# H/m  Permeability
##############constant##############


path=proj_path+'\\testdata\\process\\Transmission line'
fileslist=sorted(os.listdir(path),reverse=False)

# 过滤掉文件夹，只保留文件
fileslist_filtered = []
for item in fileslist:
    item_path = os.path.join(path, item)
    if os.path.isfile(item_path):  # 检查是否为文件
        fileslist_filtered.append(item)

fileslist = fileslist_filtered
filepath = [path + "\\" + i for i in fileslist]


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






##################测试绘图函数########################
# 确保QApplication实例存在
if QApplication.instance() is None:
    app = QApplication(sys.argv)
else:
    app = QApplication.instance()

# 创建输出列表，选择要绘制的数据（1表示绘制，0表示不绘制）
# 这里选择前3个数据进行测试
num_datasets = min(3, len(prodata))  # 最多选择3个数据集
outputlist = [1] * num_datasets + [0] * (len(prodata) - num_datasets)

print(f"测试数据集数量: {len(prodata)}")
print(f"选择绘制的数据集: {num_datasets}")
print(f"输出列表: {outputlist[:5]}...")  # 显示前5个元素

# 测试1: 创建学术风格画布并测试单个图形
print("\n=== 测试1: 单个图形绘制 ===")
canvas1 = create_academic_canvas(width=10, height=6, dpi=150)

# 创建主窗口1
main_window1 = QMainWindow()
main_window1.setWindowTitle('EIS Plot Test - Single Plot')
main_window1.setGeometry(100, 100, 1000, 600)
central_widget1 = QWidget()
main_window1.setCentralWidget(central_widget1)
layout1 = QVBoxLayout()
layout1.addWidget(canvas1)
central_widget1.setLayout(layout1)

# 测试单个图形绘制
canvas1.fig.clear()
canvas1.plotX(outputlist, prodataname, prodata, 111)  # 绘制X图

# 保存单个图形
save_publication_figure(canvas1, "EIS_X_plot_test", format='png', dpi=300, save_mode='direct')

main_window1.show()

# 测试2: 创建完整的4图布局
print("\n=== 测试2: 完整4图布局 ===")
canvas2 = create_academic_canvas(width=12, height=10, dpi=150)

# 创建主窗口2
main_window2 = QMainWindow()
main_window2.setWindowTitle('EIS Plot Test - Complete Layout')
main_window2.setGeometry(150, 150, 1200, 800)
central_widget2 = QWidget()
main_window2.setCentralWidget(central_widget2)
layout2 = QVBoxLayout()
layout2.addWidget(canvas2)
central_widget2.setLayout(layout2)

# 使用plotZall方法绘制完整布局
canvas2.plotZall(outputlist, prodataname, prodata)

# 保存完整图形
save_publication_figure(canvas2, "EIS_complete_analysis", format='tiff', dpi=300, save_mode='direct')

main_window2.show()

# 测试3: 测试介电常数相关图形
print("\n=== 测试3: 介电常数图形 ===")
canvas3 = create_academic_canvas(width=10, height=8, dpi=150)

# 创建主窗口3
main_window3 = QMainWindow()
main_window3.setWindowTitle('EIS Plot Test - Permittivity')
main_window3.setGeometry(200, 200, 1000, 700)
central_widget3 = QWidget()
main_window3.setCentralWidget(central_widget3)
layout3 = QVBoxLayout()
layout3.addWidget(canvas3)
central_widget3.setLayout(layout3)

# 测试介电常数图形（如果数据支持）
try:
    canvas3.plotEpsall(outputlist, prodataname, prodata)
    save_publication_figure(canvas3, "EIS_permittivity_analysis", format='png', dpi=300, save_mode='direct')
    main_window3.show()
    print("介电常数图形绘制成功")
except Exception as e:
    print(f"介电常数图形绘制失败: {e}")
    # 如果失败，绘制Nyquist图作为替代
    canvas3.fig.clear()
    canvas3.plotNyquist(outputlist, prodataname, prodata, 111)
    save_publication_figure(canvas3, "EIS_nyquist_plot", format='png', dpi=300, save_mode='direct')
    main_window3.show()

# 测试4: 测试个别图形方法
print("\n=== 测试4: 个别图形方法测试 ===")
canvas4 = MyMplCanvasPyQt5(width=8, height=6, dpi=100)

# 创建主窗口4
main_window4 = QMainWindow()
main_window4.setWindowTitle('EIS Plot Test - Individual Methods')
main_window4.setGeometry(250, 250, 800, 600)
central_widget4 = QWidget()
main_window4.setCentralWidget(central_widget4)
layout4 = QVBoxLayout()
layout4.addWidget(canvas4)
central_widget4.setLayout(layout4)

# 测试Rs图
canvas4.fig.clear()
canvas4.plotRs(outputlist, prodataname, prodata, 111)
save_publication_figure(canvas4, "EIS_Rs_plot", format='png', dpi=300, save_mode='direct')

main_window4.show()

print("\n=== 所有测试完成 ===")
print("已创建4个测试窗口，图形已保存到Results文件夹")

# 运行应用程序
app.exec_()

##################测试绘图函数########################


















