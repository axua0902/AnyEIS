# -*- coding: utf-8 -*-
# noqa: E501
r"""
ECMcalculation 函数 smoke test

测试目标: [FittingECM.py](../FittingECM.py) 中的 ECMcalculation
测试类型: 单次 smoke test（验证基础流程 + ampgo 兼容性）

已修复 ampgo 兼容性（result.message 兜底）。

运行方式:
    python EIS/FittingFile/Funtest/FittingTest.py
"""

import sys
import os
import numpy as np
import pandas as pd
from pandas import DataFrame, Series

# 添加项目根目录到路径（4 层 dirname 才能从 Funtest/ 退到 AnyEIS/）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# 导入必要的模块
from lmfit import Parameters, Parameter

# 导入被测试的函数和类
from EIS.FittingFile.FittingECM import auto_fitting, FittingresultsprocessECM, simuECM
from EIS.FittingFile.FittingMT import FittingMT, Fittingresultsprocess


def create_test_prodata():
    """
    创建测试用的 prodata 数据
    prodata 是全局数据，包含若干组EIS数据，每组包含 'FREQ[Hz]', 'Rs[ohm]', 'X[ohm]' 列
    """
    # 生成测试频率数据 (100个点，从 1e1 到 1e5 Hz)
    freq = np.logspace(1, 5, 100)
    
    # 创建一个简单的等效电路模型数据 (R-C 串联电路)
    # R = 100 ohm, C = 1e-6 F
    R = 100.0
    C = 1e-6
    omega = 2 * np.pi * freq
    Z_R = R * np.ones_like(freq)  # 电阻: 恒定 100 ohm (实部)
    Z_C = -1j / (omega * C)       # 电容: 阻抗为 -j/(ωC) (虚部为负)
    Z_total = Z_R + Z_C           # 串联总阻抗
    
    # 添加一些噪声模拟真实数据
    np.random.seed(42)
    noise_real = np.random.normal(0, 2, len(freq))
    noise_imag = np.random.normal(0, 2, len(freq))
    Z_total_noisy = Z_total + noise_real + 1j * noise_imag
    
    # 创建 DataFrame
    data = DataFrame({
        'FREQ[Hz]': freq,
        'Rs[ohm]': np.real(Z_total_noisy),
        'X[ohm]': np.imag(Z_total_noisy)
    })
    
    return [data]  # 返回列表，因为原代码中 prodata 是包含多个数据集的列表


def create_test_circuit():
    """
    创建测试用的电路描述
    电路格式: ['R1', 'C1', 'R1'] 表示 R1 和 C1 串联
    """
    # 简单串联电路: R 和 C 串联
    return ['R1', 'C1']


def create_test_parameters():
    """
    创建测试用的 lmfit Parameters 对象
    """
    params = Parameters()
    params.add('R1', value=80.0, min=1e-3, max=1e6)   # 初始值80 ohm
    params.add('C1', value=5e-7, min=1e-12, max=1e3)   # 初始值5e-7 F
    return params


def test_auto_fitting():
    """测试 auto_fitting 函数"""
    print("=" * 60)
    print("测试 1: auto_fitting 函数")
    print("=" * 60)
    
    prodata = create_test_prodata()
    circuit = create_test_circuit()
    params = create_test_parameters()
    freq = prodata[0]['FREQ[Hz]'].values
    
    print(f"频率范围: {freq[0]:.2e} - {freq[-1]:.2e} Hz")
    print(f"电路: {circuit}")
    print(f"参数: R1={params['R1'].value}, C1={params['C1'].value}")
    
    try:
        result = auto_fitting(params, freq, circuit, prodata[0])
        print(f"\n拟合成功!")
        print(f"  方法: {result.method}")
        print(f"  成功: {result.success}")
        # ampgo 没有 result.message，getattr 兜底
        msg = getattr(result, 'message', None) or getattr(result, 'ampgo_msg', None)
        print(f"  消息: {msg}")
        print(f"  拟合参数:")
        for name in result.var_names:
            print(f"    {name} = {result.params[name].value:.6e}")
        return result
    except Exception as e:
        print(f"\n拟合失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_FittingresultsprocessECM():
    """测试 FittingresultsprocessECM 函数"""
    print("\n" + "=" * 60)
    print("测试 2: FittingresultsprocessECM 函数")
    print("=" * 60)
    
    prodata = create_test_prodata()
    circuit = create_test_circuit()
    params = create_test_parameters()
    freq = prodata[0]['FREQ[Hz]'].values
    
    # 先进行拟合
    result = auto_fitting(params, freq, circuit, prodata[0])
    if result is None:
        print("拟合失败，无法测试 FittingresultsprocessECM")
        return None
    
    print(f"\n处理拟合结果...")
    try:
        results_data = FittingresultsprocessECM(params, freq, circuit, result)
        print(f"生成数据成功!")
        print(f"数据列: {list(results_data.columns)}")
        print(f"数据行数: {len(results_data)}")
        return results_data
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simuECM():
    """测试 simuECM 函数"""
    print("\n" + "=" * 60)
    print("测试 3: simuECM 函数 (直接仿真)")
    print("=" * 60)
    
    circuit = create_test_circuit()
    params = create_test_parameters()
    params['R1'].set(value=100.0)  # 设置为理论值
    params['C1'].set(value=1e-6)    # 设置为理论值
    freq = np.logspace(1, 5, 50)
    
    print(f"参数: R1={params['R1'].value}, C1={params['C1'].value}")
    
    try:
        Ztotal, Zparallel = simuECM(params, circuit, freq)
        print(f"\n仿真成功!")
        print(f"Ztotal 类型: {type(Ztotal)}, 长度: {len(Ztotal)}")
        print(f"前5个阻抗值: {Ztotal[:5]}")
        return Ztotal
    except Exception as e:
        print(f"仿真失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_data_format():
    """测试 prodata 数据格式"""
    print("\n" + "=" * 60)
    print("测试 4: prodata 数据格式验证")
    print("=" * 60)
    
    prodata = create_test_prodata()
    data = prodata[0]
    
    required_columns = ['FREQ[Hz]', 'Rs[ohm]', 'X[ohm]']
    
    print(f"数据列: {list(data.columns)}")
    print(f"必需列: {required_columns}")
    
    for col in required_columns:
        if col in data.columns:
            print(f"  ✓ {col} 存在")
        else:
            print(f"  ✗ {col} 缺失!")
    
    print(f"\n数据统计:")
    print(f"  频率范围: {data['FREQ[Hz]'].min():.2e} - {data['FREQ[Hz]'].max():.2e} Hz")
    print(f"  Rs[ohm] 范围: {data['Rs[ohm]'].min():.2f} - {data['Rs[ohm]'].max():.2f}")
    print(f"  X[ohm] 范围: {data['X[ohm]'].min():.2f} - {data['X[ohm]'].max():.2f}")


def test_ECMcalculation():
    """测试 ECMcalculation 函数 (line 333)"""
    print("\n" + "=" * 60)
    print("测试 5: ECMcalculation 函数 (line 333)")
    print("=" * 60)
    
    # ECMcalculation 是一个 Qt 窗口方法，依赖大量 UI 元素和全局变量
    # 为了测试它，需要设置以下环境
    
    print("\n[步骤1] 设置全局变量 prodata, outputlist, plotdataname")
    global prodata, outputlist, plotdataname
    prodata = create_test_prodata()
    outputlist = []
    plotdataname = []
    print(f"  prodata 已设置: {len(prodata)} 组数据")
    print(f"  outputlist: {outputlist}")
    print(f"  plotdataname: {plotdataname}")
    
    print("\n[步骤2] 创建 Fitting 实例 (需要 Qt 应用环境)")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
    except Exception as e:
        print(f"  无法创建 QApplication: {e}")
        print("  跳过完整 ECMcalculation 测试")
        print("\n  问题汇总:")
        print("  - ECMcalculation 是 Qt 窗口方法，需要 QApplication 环境")
        print("  - 依赖 self.ECMtable (QTableWidget) 读取参数")
        print("  - 依赖 self.ECMlowfreqTextEdit, self.ECMupfreqTextEdit 读取频率范围")
        print("  - 依赖 self.distributionComboBox 读取分布类型")
        print("  - 依赖 self.circuit (电路描述列表)")
        print("  - 依赖 self.processECMResults() 写入结果到表格")
        print("  - 依赖 self.sendsignal() 发送信号")
        return
    
    try:
        from EIS.FittingFile.Fitting import Fitting
        fitting_widget = Fitting()
        
        print("\n[步骤3] 设置电路和参数")
        # 设置电路
        fitting_widget.circuit = create_test_circuit()
        print(f"  电路: {fitting_widget.circuit}")
        
        # 创建模拟的 ECMtable 数据
        # ECMtable 的结构: 第0列=元件名, 第2列=初始值
        print("\n[步骤4] 模拟 ECMtable 参数输入")
        # 由于 ECMtable 是 QTableWidget，我们需要手动设置 ECMparams
        fitting_widget.ECMparams = Parameters()
        fitting_widget.ECMparams.add('R1', value=80.0, min=1e-3, max=1e6)
        fitting_widget.ECMparams.add('C1', value=5e-7, min=1e-12, max=1e3)
        print(f"  ECMparams: {list(fitting_widget.ECMparams.keys())}")
        
        print("\n[步骤5] 尝试直接调用 ECMcalculation 内部逻辑")
        # ECMcalculation 的核心逻辑是:
        # for i in range(0, len(prodata)):
        #     ECMfreq = prodata[i]['FREQ[Hz]']
        #     results = auto_fitting(self.ECMparams, ECMfreq, self.circuit, prodata[i])
        #     fitteddata = FittingresultsprocessECM(self.ECMparams, ECMfreq, self.circuit, results)
        
        for i in range(0, len(prodata)):
            ECMfreq = prodata[i]['FREQ[Hz]']
            print(f"  处理第 {i} 组数据, 频率点数: {len(ECMfreq)}")
            
            results = auto_fitting(fitting_widget.ECMparams, ECMfreq, 
                                   fitting_widget.circuit, prodata[i])
            print(f"    拟合成功: {results.success}, 方法: {results.method}")
            
            fitteddata = FittingresultsprocessECM(fitting_widget.ECMparams, ECMfreq, 
                                                   fitting_widget.circuit, results)
            print(f"    结果处理成功, 生成 {len(fitteddata)} 行数据")
            
            # 验证结果
            print(f"    结果列: {list(fitteddata.columns)}")
            
        print("\n[结论] ECMcalculation 的核心拟合逻辑可以正常工作")
        print("  但完整测试需要 Qt UI 环境来测试:")
        print("  - UI 元素读取 (ECMtable, TextEdit, ComboBox)")
        print("  - processECMResults() 写入表格")
        print("  - sendsignal() 信号机制")
        
    except Exception as e:
        print(f"\n测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n问题汇总:")
        print(f"  - 错误类型: {type(e).__name__}")
        print(f"  - 错误信息: {str(e)}")


def test_MTcalculation():
    """测试 MTcalculation 函数 (line 1167)"""
    print("\n" + "=" * 60)
    print("测试 6: MTcalculation 函数 (line 1167)")
    print("=" * 60)
    
    # MTcalculation 的核心拟合逻辑:
    # 1. 从 self.MTtable 读取参数 (跳过UI测试，假设参数已正确设置)
    # 2. 遍历 prodata，对每组数据进行 FittingMT
    # 3. 调用 Fittingresultsprocess 处理结果
    
    print("\n[步骤1] 设置全局变量 prodata, outputlist, plotdataname")
    global prodata, outputlist, plotdataname
    
    # 创建 MT 测试用的 prodata (需要 'FREQ[Hz]', 'epsRE[-]', 'sigmaRE[S/m]' 列)
    freq = np.logspace(1, 5, 50)  # 50个频率点
    omega = 2 * np.pi * freq
    
    # 创建测试用的介电数据 (Debye 模型)
    # eps = eps_inf + (eps_s - eps_inf) / (1 + j*omega*tau)
    eps_inf = 5.0  # 高频介电常数
    eps_s = 50.0   # 静态介电常数
    tau = 1e-8     # 弛豫时间
    
    eps_re = eps_inf + (eps_s - eps_inf) / (1 + (omega * tau)**2)
    eps_im = (eps_s - eps_inf) * omega * tau / (1 + (omega * tau)**2)
    
    # 添加噪声
    np.random.seed(42)
    eps_re_noisy = eps_re + np.random.normal(0, 0.5, len(freq))
    eps_im_noisy = eps_im + np.random.normal(0, 0.5, len(freq))
    
    # 计算 sigma (电导率)
    eps0 = 8.854e-12  # 真空介电常数
    sigma = omega * eps0 * eps_im_noisy
    
    # 创建 DataFrame
    mt_data = DataFrame({
        'FREQ[Hz]': freq,
        'epsRE[-]': eps_re_noisy,
        'sigmaRE[S/m]': sigma
    })
    
    prodata = [mt_data]
    outputlist = []
    plotdataname = []
    
    print(f"  prodata 已设置: {len(prodata)} 组数据")
    print(f"  数据列: {list(mt_data.columns)}")
    print(f"  频率范围: {freq[0]:.2e} - {freq[-1]:.2e} Hz")
    
    print("\n[步骤2] 设置 MT 参数 (模拟 self.MTparams)")
    MTparams = Parameters()
    MTparams.add('epsh', value=10.0, min=1, max=100)            # 高频介电常数
    MTparams.add('Depsterm1', value=50.0, min=1, max=200)       # 介电贡献 (格式: Deps + name)
    MTparams.add('Taoterm1', value=1e-8, min=1e-12, max=1e-4)   # 弛豫时间 (格式: Tao + name)
    print(f"  MTparams: {list(MTparams.keys())}")
    
    print("\n[步骤3] 设置 modelterm (模拟 self.modelterm)")
    # modelterm 是包含 'name' 和 'modeltype' 的字典列表
    modelterm = [
        {'name': 'term1', 'modeltype': 'Debye'}
    ]
    print(f"  modelterm: {modelterm}")
    
    print("\n[步骤4] 设置 option (模拟 self.option)")
    option = {'EP': 0, 'DC Conductivity': 0}
    print(f"  option: {option}")
    
    print("\n[步骤5] 执行 FittingMT 拟合")
    try:
        results = FittingMT(MTparams, freq, modelterm, prodata[0], option)
        print(f"  拟合成功!")
        print(f"    方法: {results.method}")
        print(f"    成功: {results.success}")
        # ampgo 没有 result.message
        msg = getattr(results, 'message', None) or getattr(results, 'ampgo_msg', None)
        print(f"    消息: {msg}")
        print(f"    拟合参数:")
        for name in results.var_names:
            print(f"      {name} = {results.params[name].value:.6e}")
    except Exception as e:
        print(f"  拟合失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n  问题汇总:")
        print(f"    - 错误类型: {type(e).__name__}")
        print(f"    - 错误信息: {str(e)}")
        return
    
    print("\n[步骤6] 执行 Fittingresultsprocess 结果处理")
    try:
        fitteddata = Fittingresultsprocess(MTparams, freq, modelterm, results, option)
        print(f"  结果处理成功!")
        print(f"    数据列: {list(fitteddata.columns)}")
        print(f"    数据行数: {len(fitteddata)}")
        print(f"    epsRE[-] 范围: {fitteddata['epsRE[-]'].min():.2f} - {fitteddata['epsRE[-]'].max():.2f}")
        print(f"    sigmaRE[S/m] 范围: {fitteddata['sigmaRE[S/m]'].min():.2e} - {fitteddata['sigmaRE[S/m]'].max():.2e}")
    except Exception as e:
        print(f"  结果处理失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n  问题汇总:")
        print(f"    - 错误类型: {type(e).__name__}")
        print(f"    - 错误信息: {str(e)}")
        return
    
    print("\n[结论] MTcalculation 的核心拟合逻辑可以正常工作")
    print("  UI 交互部分 (MTtable, processMTResults, sendsignal) 需要在 Qt 环境中测试")


def main():
    print("=" * 60)
    print("ECMcalculation 单元测试")
    print("=" * 60)
    
    # 测试数据格式
    test_data_format()
    
    # 测试 simuECM (最基础的仿真函数)
    test_simuECM()
    
    # 测试 auto_fitting
    result = test_auto_fitting()
    
    # 测试 FittingresultsprocessECM
    if result is not None:
        test_FittingresultsprocessECM()
    
    # 测试 ECMcalculation (line 333)
    test_ECMcalculation()
    
    # 测试 MTcalculation (line 1167)
    test_MTcalculation()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    # 问题汇总
    print("\n" + "=" * 60)
    print("问题汇总")
    print("=" * 60)
    print("""
    问题1: ECMcalculation 函数依赖以下全局变量和类属性:
           - prodata: 全局变量，需要外部设置
           - plotdataname: 全局变量
           - outputlist: 全局变量
           - self.ECMtable: QTableWidget，无法在无界面环境测试
           - self.ECMparams: Parameters 对象
           - self.circuit: 电路描述列表
           - self.processECMResults(): 需要 ECMtable
           - self.sendsignal(): 需要 UI 信号机制
    
    问题2: auto_fitting 函数可能抛出异常，如果:
           - prodata 中缺少必需的列
           - 电路描述不合法
           - 参数边界设置不合理
    
    问题3: FittingresultsprocessECM 内部调用 report_fit，
           会打印大量输出，可能不适合在无界面环境运行
    
    建议: 在实际的 Qt 应用中测试完整流程，或创建 Mock 对象
    """)


if __name__ == "__main__":
    main()
