# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""

import os
import sys


from numpy import log10, real, imag, array, angle, absolute, pi, sqrt, log, tanh, arctanh
import numpy as np

import pandas as pd
import matplotlib.pyplot as plt

from EIS.InputFile.Inputfun import readfile


from EIS.ProcessingFile.Filterfun import (
    savgol, median, wiener, butterworth, cspline,
    arithmeticAverage, slidingAverage, medianAverage, 
    amplitudeLimitingAverage, firstOrderLag, weightedAverage,
    shakeOff, amplitudeLimitingShakeOff,calculate_multi_filter_comparison_data
)
from EIS.Other.standard_parameter import paraNaCl, paraWater, paraEthanol




# 获取当前文件的绝对路径，然后向上三级目录到达项目根目录
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



propath = proj_path + '\\testdata\\process\\Three solution\\pro'
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


##################循环读取数据########################
prodata = list()
prodataname = list()

for i in range(0, len(profilepath)):
    prodatanametemp, prodatatemp = readfile(profilepath[i])
    prodata.append(prodatatemp[0])
    prodataname.append(prodatanametemp[0])
##################循环读取数据########################



###########################################savgol###############################
print("Testing Savitzky-Golay Filter...")
parameter = {'a': '17', 'b': '1'}
result_savgol = savgol(prodata, parameter)
print(f"Savgol result length: {len(result_savgol)}")
###########################################savgol###############################

###########################################median###############################
print("Testing Median Filter...")
parameter = {'kernel_size': '5'}
result_median = median(prodata, parameter)
print(f"Median result length: {len(result_median)}")
###########################################median###############################

###########################################wiener###############################
print("Testing Wiener Filter...")
parameter = {'noise': None}
result_wiener = wiener(prodata, parameter)
print(f"Wiener result length: {len(result_wiener)}")
###########################################wiener###############################

###########################################butterworth###############################
print("Testing Butterworth Filter...")
parameter = {'order': '2', 'cutoff': '0.1', 'filter_type': 'filtfilt'}
result_butterworth = butterworth(prodata, parameter)
print(f"Butterworth result length: {len(result_butterworth)}")
###########################################butterworth###############################

###########################################cspline###############################
print("Testing Cubic Spline Filter...")
parameter = {'lamb': '50.0'}
result_cspline = cspline(prodata, parameter)
print(f"Cubic Spline result length: {len(result_cspline)}")
###########################################cspline###############################

###########################################arithmeticAverage###############################
print("Testing Arithmetic Average Filter...")
parameter = {'window_size': '5'}
result_arithmetic = arithmeticAverage(prodata, parameter)
print(f"Arithmetic Average result length: {len(result_arithmetic)}")
###########################################arithmeticAverage###############################

###########################################slidingAverage###############################
print("Testing Sliding Average Filter...")
parameter = {'window_size': '7'}
result_sliding = slidingAverage(prodata, parameter)
print(f"Sliding Average result length: {len(result_sliding)}")
###########################################slidingAverage###############################

###########################################medianAverage###############################
print("Testing Median Average Filter...")
parameter = {'window_size': '5'}
result_median_avg = medianAverage(prodata, parameter)
print(f"Median Average result length: {len(result_median_avg)}")
###########################################medianAverage###############################

###########################################amplitudeLimitingAverage###############################
print("Testing Amplitude Limiting Average Filter...")
parameter = {'window_size': '5', 'amplitude_limit': '10.0'}
result_amp_limit = amplitudeLimitingAverage(prodata, parameter)
print(f"Amplitude Limiting Average result length: {len(result_amp_limit)}")
###########################################amplitudeLimitingAverage###############################

###########################################firstOrderLag###############################
print("Testing First Order Lag Filter...")
parameter = {'alpha': '0.3'}
result_lag = firstOrderLag(prodata, parameter)
print(f"First Order Lag result length: {len(result_lag)}")
###########################################firstOrderLag###############################

###########################################weightedAverage###############################
print("Testing Weighted Average Filter...")
parameter = {'window_size': '6'}
result_weighted = weightedAverage(prodata, parameter)
print(f"Weighted Average result length: {len(result_weighted)}")
###########################################weightedAverage###############################

###########################################shakeOff###############################
print("Testing Shake Off Filter...")
parameter = {'threshold_count': '3'}
result_shake = shakeOff(prodata, parameter)
print(f"Shake Off result length: {len(result_shake)}")
###########################################shakeOff###############################

###########################################amplitudeLimitingShakeOff###############################
print("Testing Amplitude Limiting Shake Off Filter...")
parameter = {'amplitude_limit': '5.0', 'threshold_count': '3'}
result_amp_shake = amplitudeLimitingShakeOff(prodata, parameter)
print(f"Amplitude Limiting Shake Off result length: {len(result_amp_shake)}")
###########################################amplitudeLimitingShakeOff###############################

print("\nAll filter tests completed successfully!")




###########################################测试calculate_multi_filter_comparison_data函数###############################
print("\n" + "="*80)
print("TESTING calculate_multi_filter_comparison_data FUNCTION")
print("="*80)

def plot_multi_filter_comparison(prodata, prodataname):
    """
    绘图函数，用于测试calculate_multi_filter_comparison_data函数
    """
    # 调用calculate_multi_filter_comparison_data函数获取数据
    comparison_data = calculate_multi_filter_comparison_data(prodata, prodataname)
    
    if comparison_data is None:
        print("No comparison data available for plotting")
        return
    
    # 提取数据
    original_data = comparison_data['original_data']
    original_name = comparison_data['original_name']
    filtered_results = comparison_data['filtered_results']
    filter_stats = comparison_data['filter_stats']
    filters_config = comparison_data['filters_config']
    performance_scores = comparison_data['performance_scores']
    
    # 创建图形
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Multi-Filter Comparison Analysis - {original_name}', fontsize=16, fontweight='bold')
    
    # 获取原始数据
    freq_orig = original_data['FREQ[Hz]']
    Rs_orig = original_data['Rs[ohm]']
    X_orig = original_data['X[ohm]']
    phy_orig = original_data['PHASE[deg]']
    
    # 子图1: Nyquist图对比
    ax1 = axes[0, 0]
    ax1.plot(Rs_orig, -X_orig, 'ko-', markersize=3, linewidth=1, label='Original', alpha=0.7)
    
    for filter_name, result_data in filtered_results.items():
        Rs_filt = result_data['Rs[ohm]']
        X_filt = result_data['X[ohm]']
        color = filters_config[filter_name]['color']
        ax1.plot(Rs_filt, -X_filt, color=color, linewidth=2, label=filter_name, alpha=0.8)
    
    ax1.set_xlabel('Rs [Ω]')
    ax1.set_ylabel('-X [Ω]')
    ax1.set_title('Nyquist Plot Comparison')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')
    
    # 子图2: Bode图 - 幅值对比
    ax2 = axes[0, 1]
    Z_orig = np.sqrt(Rs_orig**2 + X_orig**2)
    ax2.loglog(freq_orig, Z_orig, 'ko-', markersize=3, linewidth=1, label='Original', alpha=0.7)
    
    for filter_name, result_data in filtered_results.items():
        Rs_filt = result_data['Rs[ohm]']
        X_filt = result_data['X[ohm]']
        Z_filt = np.sqrt(Rs_filt**2 + X_filt**2)
        color = filters_config[filter_name]['color']
        ax2.loglog(freq_orig, Z_filt, color=color, linewidth=2, label=filter_name, alpha=0.8)
    
    ax2.set_xlabel('Frequency [Hz]')
    ax2.set_ylabel('|Z| [Ω]')
    ax2.set_title('Bode Plot - Magnitude')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 子图3: Bode图 - 相位对比
    ax3 = axes[0, 2]
    ax3.semilogx(freq_orig, phy_orig, 'ko-', markersize=3, linewidth=1, label='Original', alpha=0.7)
    
    for filter_name, result_data in filtered_results.items():
        phy_filt = result_data['PHASE[deg]']
        color = filters_config[filter_name]['color']
        ax3.semilogx(freq_orig, phy_filt, color=color, linewidth=2, label=filter_name, alpha=0.8)
    
    ax3.set_xlabel('Frequency [Hz]')
    ax3.set_ylabel('Phase [°]')
    ax3.set_title('Bode Plot - Phase')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 子图4: 噪声减少效果对比
    ax4 = axes[1, 0]
    filter_names = list(filter_stats.keys())
    noise_reduction_Rs = [filter_stats[name]['noise_reduction']['Rs'] for name in filter_names]
    noise_reduction_X = [filter_stats[name]['noise_reduction']['X'] for name in filter_names]
    
    x_pos = np.arange(len(filter_names))
    width = 0.35
    
    bars1 = ax4.bar(x_pos - width/2, noise_reduction_Rs, width, label='Rs Noise Reduction', alpha=0.8)
    bars2 = ax4.bar(x_pos + width/2, noise_reduction_X, width, label='X Noise Reduction', alpha=0.8)
    
    ax4.set_xlabel('Filter Methods')
    ax4.set_ylabel('Noise Reduction [%]')
    ax4.set_title('Noise Reduction Comparison')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(filter_names, rotation=45, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # 子图5: 信号保真度对比
    ax5 = axes[1, 1]
    correlation_Rs = [filter_stats[name]['correlation']['Rs'] for name in filter_names]
    correlation_X = [filter_stats[name]['correlation']['X'] for name in filter_names]
    correlation_Phase = [filter_stats[name]['correlation']['Phase'] for name in filter_names]
    
    bars1 = ax5.bar(x_pos - width/3, correlation_Rs, width/1.5, label='Rs Correlation', alpha=0.8)
    bars2 = ax5.bar(x_pos, correlation_X, width/1.5, label='X Correlation', alpha=0.8)
    bars3 = ax5.bar(x_pos + width/3, correlation_Phase, width/1.5, label='Phase Correlation', alpha=0.8)
    
    ax5.set_xlabel('Filter Methods')
    ax5.set_ylabel('Correlation Coefficient')
    ax5.set_title('Signal Fidelity Comparison')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(filter_names, rotation=45, ha='right')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    ax5.set_ylim([0.95, 1.0])  # 放大显示相关性差异
    
    # 子图6: 综合性能评分
    ax6 = axes[1, 2]
    overall_scores = [performance_scores[name]['overall'] for name in filter_names]
    colors = [filters_config[name]['color'] for name in filter_names]
    
    bars = ax6.bar(filter_names, overall_scores, color=colors, alpha=0.7)
    ax6.set_xlabel('Filter Methods')
    ax6.set_ylabel('Overall Performance Score')
    ax6.set_title('Overall Performance Ranking')
    ax6.tick_params(axis='x', rotation=45)
    ax6.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, score in zip(bars, overall_scores):
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{score:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    # 打印统计信息
    print("\n" + "="*60)
    print("FILTER PERFORMANCE STATISTICS")
    print("="*60)
    
    for filter_name in filter_names:
        stats = filter_stats[filter_name]
        scores = performance_scores[filter_name]
        print(f"\n{filter_name} Filter:")
        print(f"  Noise Reduction - Rs: {stats['noise_reduction']['Rs']:.2f}%, X: {stats['noise_reduction']['X']:.2f}%")
        print(f"  Signal Fidelity - Rs: {stats['correlation']['Rs']:.4f}, X: {stats['correlation']['X']:.4f}, Phase: {stats['correlation']['Phase']:.4f}")
        print(f"  Overall Score: {scores['overall']:.2f}")
    
    # 找出最佳滤波器
    best_filter = max(performance_scores.keys(), key=lambda x: performance_scores[x]['overall'])
    print(f"\n🏆 Best Overall Filter: {best_filter} (Score: {performance_scores[best_filter]['overall']:.2f})")
    
    return comparison_data

# 调用绘图函数测试calculate_multi_filter_comparison_data
try:
    print("Calling plot_multi_filter_comparison function...")
    comparison_result = plot_multi_filter_comparison(prodata, prodataname)
    print("✅ Multi-filter comparison plotting completed successfully!")
    
    if comparison_result:
        print(f"✅ Function returned data for {len(comparison_result['filtered_results'])} filters")
        print(f"✅ Original data shape: {comparison_result['original_data'].shape}")
        print(f"✅ Performance scores calculated for all filters")
    
except Exception as e:
    print(f"❌ Error in multi-filter comparison: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("ALL TESTS COMPLETED!")
print("="*80)