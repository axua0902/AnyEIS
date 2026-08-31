# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 10:45:26 2020

@author: zhang
"""


import os
import sys
sys.path.append('..')

import pandas as pd
import numpy as np
import mpmath as mp
from numpy import real,imag,angle,absolute,pi,log,sqrt,tanh,arctanh,array,abs
from pandas import DataFrame,Series
from scipy.optimize import fsolve, root_scalar, brentq
from EIS.Other.standard_parameter import paraNaCl,paraWater,paraEthanol


##############constant##############
eps0=8.854187817e-12 #F/m Vacuum permittivity
mu0=4*pi*1e-7# H/m  Permeability
##############constant##############



def paraplate(prodata, Gf):
    """
    平行板电容器法 (Parallel Plate Capacitor) — 由测得阻抗计算 MUT (被测材料) 的介电常数与电导率。

    适用场景:
        - 已知电极几何因子 Gf (单位: m),由用户根据电极尺寸/间距手动填入
        - 适用于以平行板电极测得的阻抗数据,直接换算为 ε 和 σ

    计算公式:
        ε_MUT = 1 / (jω·ε_0·Gf·Z)
        σ_MUT = j·ω·ε_0·ε_MUT

    参数:
        prodata (list[DataFrame]): 测得的各样本阻抗数据,每条含 'FREQ[Hz]','Rs[ohm]','X[ohm]'
        Gf (float): 几何因子 (电极面积 / 间距, 单位: m)

    返回:
        list[DataFrame]: 每条样本的 ε 和 σ,字段为 'FREQ[Hz]','EpsRE[-]','EpsIM[-]','SigmaRE[S/m]','SigmaIM[S/m]'
    """
    print("Gf", Gf)
    Reffreq1=prodata[0]['FREQ[Hz]']
    Refomega1=array(list(2*pi*Reffreq1))
    
    resultsdata=list()
    for temp in range(0,len(prodata)):
        ZREmeasrued=prodata[temp]['Rs[ohm]']
        ZIMmeasrued=prodata[temp]['X[ohm]']
        Zmeasrued=ZREmeasrued+1.j*ZIMmeasrued
        Zexptest=array(Zmeasrued)


        with np.errstate(divide='ignore', invalid='ignore'):
            omega_safe = np.where(Refomega1 == 0, 1e-30, Refomega1)
            epsMUT = 1.0 / (1j * omega_safe * eps0 * Gf * Zexptest)
            epsMUT = np.where(np.abs(Zexptest) < 1e-30,
                              np.inf + 0j,
                              epsMUT)
        sigmaMUT=1j*Refomega1*epsMUT*eps0

        Freq=prodata[temp]['FREQ[Hz]']
        resu=creatdatabaseEPS(Freq,epsMUT,sigmaMUT)
        resultsdata.append(resu)

    print('paraplate Processed')#输出到状态栏
    return resultsdata



#############################################calibrate##########################################################################
def calibrate(refdata, prodata, params_info):
    """
    三步校准法 (Open/Short/Load Calibration) — 去除测试夹具和电缆的寄生阻抗,得到 MUT 真实阻抗。

    适用场景:
        - 同轴/夹具测量中,夹具和电缆的寄生阻抗影响不能忽略
        - 通过三组参考测量 (开路 Open, 短路 Short, 负载 Load=50Ω) 求解 MUT 阻抗

    计算公式 (传输/反射式双端口校准):
        Z_MUT = Z_std · (Z_short − Z_meas) · (Z_load − Z_open) / [(Z_meas − Z_open) · (Z_short − Z_load)]

    参数:
        refdata (list[DataFrame]): 三组校准数据,索引由 params_info 指定
        prodata (list[DataFrame]): 待测 MUT 的阻抗数据
        params_info (dict): 需含
            - 'open_index' (int): refdata 中开路参考的索引
            - 'short_index' (int): refdata 中短路参考的索引
            - 'load_index' (int): refdata 中负载参考的索引 (默认 Z_std=50Ω)

    返回:
        list[DataFrame]: 校准后 MUT 阻抗,字段 'FREQ[Hz]','Z[ohm]','PHASE[deg]','Rs[ohm]','X[ohm]'
    """
    ############   get data ############
    # Use params_info to get the correct indices for open, short, and load
    open_idx = params_info.get('open_index', 0)
    short_idx = params_info.get('short_index', 1)
    load_idx = params_info.get('load_index', 2)
    
    ZREopen=refdata[open_idx]['Rs[ohm]']
    ZIMopen=refdata[open_idx]['X[ohm]']
    Zopen=ZREopen+1.j*ZIMopen

    ZREshort=refdata[short_idx]['Rs[ohm]']
    ZIMshort=refdata[short_idx]['X[ohm]']
    Zshort=ZREshort+1.j*ZIMshort
    
    ZREload=refdata[load_idx]['Rs[ohm]']
    ZIMload=refdata[load_idx]['X[ohm]']
    Zload=ZREload+1.j*ZIMload
    
    Zstd=50+0j
    resultsdata=list()
    for i in range(0,len(prodata)):
        Freq=prodata[i]['FREQ[Hz]']
        ZREmeasrued=prodata[i]['Rs[ohm]']
        ZIMmeasrued=prodata[i]['X[ohm]']
        Zmeasrued=ZREmeasrued+1.j*ZIMmeasrued
        ############   get data ############

        # 修复: 当 Zmeas ≈ Zopen 时, 公式分母趋近 0 -> 物理意义 ZMUT=∞
        # 之前直接产生 NaN, 现改用 np.where 避免 NaN
        ZMUT_num = Zstd * (Zshort - Zmeasrued) * (Zload - Zopen)
        ZMUT_den = (Zmeasrued - Zopen) * (Zshort - Zload)
        # 使用 np.where: 分母为 0 时返回 inf (数学上的正确值)
        # 阈值 1e-30 远小于实际物理阻抗, 仅用于浮点除零保护
        with np.errstate(divide='ignore', invalid='ignore'):
            ZMUT = np.where(np.abs(ZMUT_den) < 1e-30,
                            np.inf * np.sign(ZMUT_num + 1e-300),  # 保持符号
                            ZMUT_num / ZMUT_den)

        resu=creatdatabase(Freq,ZMUT)
        resultsdata.append(resu)

    print('calibrate Processed')#输出到状态栏
    return resultsdata
      


#############################################permittivity calculate###########################################################################
def DieMat(refdata, prodata, params_info):
    """
    介电材料法 (Dielectric Material Method) — 用 Air + Water 两种参考溶液,反求电极等效电路参数 (C0, Cr),进而计算 MUT 介电常数与电导率。

    适用场景:
        - 圆柱形/平行板电极(几何因子未知),通过两种已知介电常数的参考液校准
        - 当前仅支持 Air (ε=1) + Water (ε 由 paraWater 计算) 组合
        - 参考: Schwan H P 电气化学生物阻抗方法

    计算思路:
        1. 由 Air/Water 阻抗分别求出两参考液下的等效电容 C_air、C_water
        2. 由 C_air、C_water 和 ε_air=1、ε_water 解线性方程组,得到 C0 (空载电容) 和 Cr (杂散电容)
        3. 用 C0、Cr 反演 MUT 的 ε_MUT、σ_MUT

    参数:
        refdata (list[DataFrame]): 包含 Air 和 Water 两组参考阻抗
        prodata (list[DataFrame]): 待测 MUT 阻抗数据
        params_info (dict): 需含
            - 'solution_parameters' (list[dict]): 长度 2,
                [0]: Air 溶液信息 (含 'solution_index','name','temperature')
                [1]: Water 溶液信息 (同上)

    返回:
        list[DataFrame]: MUT 介电常数/电导率,字段 'FREQ[Hz]','EpsRE[-]','EpsIM[-]','SigmaRE[S/m]','SigmaIM[S/m]'

    异常:
        当 air_name != 'Air' 或 water_name != 'Water' 时,静默打印 'DM wrong' 并返回 None。
    """
    # 从params_info获取溶液信息
    solution_params = params_info['solution_parameters']
    
    # 获取Air和Water的索引和信息
    air_info = solution_params[0]  # Air solution
    water_info = solution_params[1]  # Water solution
    
    Air_idx = air_info['solution_index']
    Water_idx = water_info['solution_index']
    
    ##################循环读取数据########################
    ZairRs=array(refdata[Air_idx]['Rs[ohm]'])
    ZairX=array(refdata[Air_idx]['X[ohm]'])
    Zairabs=abs(ZairRs+1j*ZairX)
    
    ZwaterRs=array(refdata[Water_idx]['Rs[ohm]'])
    ZwaterX=array(refdata[Water_idx]['X[ohm]'])
    Zwaterabs=abs(ZwaterRs+1j*ZwaterX)
    
         
    colname=list(prodata[0].columns)
    freq=array(refdata[0][colname[0]])
    omega=2*pi*freq
    
      #######################################
    Cair=ZairX/(omega*Zairabs**2)
    Cwater=ZwaterX/(omega*Zwaterabs**2)
    
    
    # 从params_info获取溶液名称和参数
    air_name = air_info['name']
    water_name = water_info['name']
    air_temp = air_info['temperature']
    water_temp = water_info['temperature']
    
    if air_name == 'Air' and water_name == 'Water':
        epswater,sigmawater=paraWater(omega)
        epsair=1
        epswater=real(epswater)
    else:
        return print('DM wrong')
    C0=(-Cwater-Cair)/(epswater-epsair)  
    Cr=Cair-C0
    #######################################

    
    resultsdata=list()
    for temp in range(0,len(prodata)):
        L=0
        R=0 
        omega=2*pi*freq
        Freq=prodata[temp]['FREQ[Hz]']       
        ZREmeasrued=array(prodata[temp]['Rs[ohm]'])
        ZIMmeasrued=array(prodata[temp]['X[ohm]'])
       
        epsp1=(ZREmeasrued-R)**2+(ZIMmeasrued-omega*L)**2
        epsMUT=(1/C0)*((omega*L-ZIMmeasrued)/(omega*epsp1))-(Cr/C0)
        sigmaMUT=(eps0/C0)*((ZREmeasrued-R)/epsp1)
        
        resu=creatdatabaseEPS(Freq,epsMUT,sigmaMUT)
        resultsdata.append(resu)

    print('DieMat Processed')#输出到状态栏
    return resultsdata






def threesolutions(refdata, prodata, params_info):
    """
    三溶液法 (Three-Solution Method) — 用三种已知介电常数的参考溶液,无需求解电极几何参数,直接反演 MUT 介电常数与电导率。

    适用场景:
        - 同 DieMat,适用于几何因子未知的电极
        - 通过三种不同介电常数的参考液 (NaCl、Water、Ethanol/Alcohol、Air 任选三种),利用线性插值关系求 ε_MUT
        - 当电极几何/杂散无法用 2 种参考精确求解时,3 种参考可提供过约束,提高鲁棒性

    计算思路 (基于双截距线性插值):
        D = (Z_meas − Z_ref1)·(Z_ref2 − Z_ref3)·(ε_ref1 − ε_ref3)
            / [(Z_meas − Z_ref2)·(Z_ref1 − Z_ref3)·(ε_ref2 − ε_ref3)]
        ε_MUT = (ε_ref1 − D·ε_ref2) / (1 − D)

    参数:
        refdata (list[DataFrame]): 三种参考溶液的阻抗数据
        prodata (list[DataFrame]): 待测 MUT 阻抗数据
        params_info (dict): 需含
            - 'solution_parameters' (list[dict]): 长度 3,每个含
                - 'solution_index' (int): refdata 索引
                - 'name' (str): 'NaCl' / 'Water' / 'Ethanol' / 'Alcohol' / 'Air'
                - 'temperature' (float)
                - 'concentration' (float, NaCl 时使用,mol/L)

    返回:
        list[DataFrame]: MUT 介电常数/电导率,字段 'FREQ[Hz]','EpsRE[-]','EpsIM[-]','SigmaRE[S/m]','SigmaIM[S/m]'
    """
    CalSoleps1=list()
    CalSoleps2=list()
    CalSoleps3=list()
    
    # 从params_info获取溶液参数
    solution_params = params_info['solution_parameters']
    
    # 处理第一个溶液 (NaCl)
    sol1_info = solution_params[0]
    sol1_idx = sol1_info['solution_index']
    Reffreq1=refdata[sol1_idx]['FREQ[Hz]']
    Refomega1=array(list(2*pi*Reffreq1))
    ZREref1=refdata[sol1_idx]['Rs[ohm]']
    ZIMref1=refdata[sol1_idx]['X[ohm]']
    Zref1=ZREref1+1.j*ZIMref1
    Zref1=array(Zref1)
    
    
    temperature1=float(sol1_info['temperature'])
    concentration1=float(sol1_info['concentration'])
    # print(concentration1)
    if sol1_info['name']=='NaCl':
        CalSoleps1,msigmaNaCl1=paraNaCl(Refomega1,temperature1,concentration1)
    elif sol1_info['name']=='Ethanol' or sol1_info['name']=='Alcohol':
        mepsEthanol,msigmaEthanol=paraEthanol(Refomega1)
        CalSoleps1=mepsEthanol
    elif sol1_info['name']=='Water':
        mepsWater,msigmaWater=paraWater(Refomega1)
        CalSoleps1=mepsWater
    elif sol1_info['name']=='Air':
        CalSoleps1=array([1.0]*len(Refomega1))  # Air的介电常数为1
        CalSoleps1=CalSoleps1
    else:
        print('Unknown solution type for solution 1')
  
    
    
    # 处理第二个溶液 (Water)
    sol2_info = solution_params[1]
    sol2_idx = sol2_info['solution_index']
    Reffreq2=refdata[sol2_idx]['FREQ[Hz]']
    Refomega2=array(list(2*pi*Reffreq2))
    ZREref2=refdata[sol2_idx]['Rs[ohm]']
    ZIMref2=refdata[sol2_idx]['X[ohm]']
    Zref2=ZREref2+1.j*ZIMref2
    Zref2=array(Zref2)    
    temperature2=float(sol2_info['temperature'])
    concentration2=float(sol2_info['concentration'])
    # print(concentration2)
    if sol2_info['name']=='NaCl':
        CalSoleps2,msigmaNaCl2=paraNaCl(Refomega2,temperature2,concentration2)
    elif sol2_info['name']=='Ethanol' or sol2_info['name']== 'Alcohol':
        mepsEthanol,msigmaEthanol=paraEthanol(Refomega2)
        CalSoleps2=mepsEthanol
    elif sol2_info['name']=='Water':
        mepsWater,msigmaWater=paraWater(Refomega2)
        CalSoleps2=mepsWater
    elif sol2_info['name']=='Air':
        CalSoleps2=array([1.0]*len(Refomega2))  # Air的介电常数为1
    else:
        print('Unknown solution type for solution 2')



    # 处理第三个溶液 (NaCl)
    sol3_info = solution_params[2]
    sol3_idx = sol3_info['solution_index']
    Reffreq3=refdata[sol3_idx]['FREQ[Hz]']
    Refomega3=array(list(2*pi*Reffreq3))
    ZREref3=refdata[sol3_idx]['Rs[ohm]']
    ZIMref3=refdata[sol3_idx]['X[ohm]']
    Zref3=ZREref3+1.j*ZIMref3 
    Zref3=array(Zref3)
    temperature3=float(sol3_info['temperature'])
    concentration3=float(sol3_info['concentration'])
    if sol3_info['name']=='NaCl':
        CalSoleps3,msigmaNaCl3=paraNaCl(Refomega3,temperature3,concentration3)
    elif sol3_info['name']=='Ethanol' or sol3_info['name']== 'Alcohol':
        mepsEthanol,msigmaEthanol=paraEthanol(Refomega3)
        CalSoleps3=mepsEthanol
    elif sol3_info['name']=='Water':
        mepsWater,msigmaWater=paraWater(Refomega3)
        CalSoleps3=mepsWater
    elif sol3_info['name']=='Air':
        CalSoleps3=array([1.0]*len(Refomega3))  # Air的介电常数为1
    else:
        print('Unknown solution type for solution 3')

    resultsdata=list()
    
    for temp in range(0,len(prodata)):
        ZREmeasrued=prodata[temp]['Rs[ohm]']
        ZIMmeasrued=prodata[temp]['X[ohm]']  # 修正这里，应该是X[ohm]而不是Rs[ohm]
        Zmeasrued=ZREmeasrued+1.j*ZIMmeasrued
        Zexptest=array(Zmeasrued)
        D=(Zexptest-Zref1)*(Zref2-Zref3)*(CalSoleps1-CalSoleps3)/((Zexptest-Zref2)*(Zref1-Zref3)*(CalSoleps2-CalSoleps3))
        epsMUT=(CalSoleps1-D*CalSoleps2)/(1-D)
        sigmaMUT=1j*Refomega1*epsMUT*eps0
        Freq=prodata[temp]['FREQ[Hz]']
        resu=creatdatabaseEPS(Freq,epsMUT,sigmaMUT)
        resultsdata.append(resu)
    
    print('threesolutions Processed')#输出到状态栏
    return resultsdata





def TLcalibrate(refdata, prodata, params_info):
    """
    传输线校准 (Transmission Line Calibration) — 求解同轴/传输线夹具的传播常数 γ,然后将 MUT 测量阻抗换算为溶液段真实阻抗。

    适用场景:
        - 同轴传输线型电解池(已知几何常数 Gf、测量段长度 ls、电极段长度 l2、特征阻抗 Z0)
        - 通过测量一段已知溶液 (NaCl) 的阻抗,反推传输线寄生参数 γCable
        - 然后用 γCable 校正所有 MUT 测量,得到 MUT 段真实阻抗

    计算思路:
        1. 由已知 NaCl 浓度/温度求 ε_NaCl,σ_NaCl
        2. 由 ε、σ 推算 NaCl 段理论阻抗 CalZsol = Z0_sol / tanh(γ_sol·ls)
        3. 由 Z_meas 求解 γCable (传输线校正传播常数)
        4. 用 γCable 反演 MUT 段阻抗: Z_MUT = Z0·(Z0·tanh(γ·l2) − Z_meas) / (Z_meas·tanh(γ·l2) − Z0)

    参数:
        refdata (list[DataFrame]): NaCl 参考溶液的阻抗数据
        prodata (list[DataFrame]): 待测 MUT 阻抗数据
        params_info (dict): 需含
            - 'processing_parameters' (dict):
                - 'geometric_constant' (str→float): Gf
                - 'solution_length' (str→float): ls
                - 'electrode_length' (str→float): l2
                - 'character_impedance' (str→float): Z0
            - 'solution_parameters' (list[dict]): 长度 1,NaCl 溶液信息
                (含 'name'='NaCl','temperature','concentration','solution_index')

    返回:
        list[DataFrame]: 校正后 MUT 阻抗,字段 'FREQ[Hz]','Z[ohm]','PHASE[deg]','Rs[ohm]','X[ohm]'

    限制:
        当前实现仅支持 NaCl 作为参考溶液;其他溶液会打印错误并直接返回。
    """
    resultsdata=list()
    
    # 从params_info获取处理参数
    processing_params = params_info['processing_parameters']

    # 将字符串参数转换为float
    Gf1 = float(processing_params['geometric_constant'])  # 3.95
    ls = float(processing_params['solution_length'])  # 0.00255 测量段长度
    l2 = float(processing_params['electrode_length'])  # 0.0164
    Z0 = float(processing_params['character_impedance'])  # 50
    # ri1=0.8e-3/2#m
    # ro1=4.5e-3/2#m
    # rs1=ro1-ri1#/2#0.0025
    # p1=1.1
    # Gf1=p1*(2*np.pi)/(np.log(ro1/ri1))
    # ls=0.00255#测量段长度
    # l2=0.00168
    mu1=1
    Calsigma=0

    # 获取溶液信息
    solution_params = params_info['solution_parameters']
    sol_info = solution_params[0]  # NaCl solution
    sol_idx = sol_info['solution_index']
    
    Reffreq=refdata[sol_idx]['FREQ[Hz]']
    Refomega=array(list(2*pi*Reffreq))
    
    ############################################ 传 输 线 下 溶  液  理  论  阻   抗  #########################
    temperature=float(sol_info['temperature'])  # 25
    concentration=float(sol_info['concentration'])  # 0.1
    if sol_info['name']=='NaCl':
        CalSoleps,msigmaNaCl=paraNaCl(Refomega,temperature,concentration)
    else:
        print('TLcalibrate: Only NaCl solution is supported')
        return
    
    ZREref=refdata[sol_idx]['Rs[ohm]']
    ZIMref=refdata[sol_idx]['X[ohm]']
    Zref=ZREref+1.j*ZIMref
    CalZexp=array(Zref)
    
    gammaCalSol=sqrt((Calsigma+1j*Refomega*mu1*mu0)*(1j*Refomega*CalSoleps*eps0))
    etaCalSol=1j*Refomega*mu1*mu0/gammaCalSol#intrinsic impedance
    Z0CalSol=etaCalSol/Gf1
    CalZsol=Z0CalSol/tanh(gammaCalSol*ls)
    ############################################ 传 输 线 下 溶  液  理  论  阻   抗  #########################
    
    ############################## 传输线参数###############################
    gammaCable=arctanh((CalZsol-CalZexp)/(CalZsol*CalZexp/Z0-Z0))/l2

    SolZThe=[0 for i in range(0,len(prodata))]
    for temp in range(0,len(prodata)):
        Freq=prodata[temp]['FREQ[Hz]']
        ZREmeasrued=prodata[temp]['Rs[ohm]']
        ZIMmeasrued=prodata[temp]['X[ohm]']
        Zmeasrued=ZREmeasrued+1.j*ZIMmeasrued
        Zexptest=array(Zmeasrued)
        
        SolZThe[temp]=Z0*(Z0*tanh(gammaCable*l2)-Zexptest)/(Zexptest*tanh(gammaCable*l2)-Z0)
    
        resu=creatdatabase(Freq,SolZThe[temp])
        resultsdata.append(resu)
        
    print('TLcalibrate Processed')#输出到状态栏
    return resultsdata
############################################# Calbrate ###########################################################################






def TLcalculateEPS(prodata, params_info):
    """
    传输线介电常数反演 (mpmath 实现) — 由 MUT 测量阻抗,数值反求 MUT 复介电常数 ε_MUT。

    适用场景:
        - 已用 TLcalibrate 得到 MUT 真实阻抗 SolZThe
        - 由 SolZThe 数值求解每个频率点的复介电常数 ε(ω) = ε' − jε''
        - 与 paraplate/DieMat 互补:paraplate 已知 Gf,TLcalculateEPS 已知 Gf+ls

    计算公式 (传输线输入阻抗):
        Z_meas = √((μ·μ0)/(ε·ε0)) / Gf / tanh(jω·√(μ·μ0·ε·ε0)·ls)

    对每个频率点用 mpmath.findroot 数值求根,初值 ε=30。

    参数:
        prodata (list[DataFrame]): MUT 阻抗数据,字段 'FREQ[Hz]','Rs[ohm]','X[ohm]'
        params_info (dict): 需含
            - 'processing_parameters' (dict):
                - 'geometric_constant' (str→float): Gf
                - 'solution_length' (str→float): ls

    返回:
        list[DataFrame]: MUT 介电常数/电导率,字段 'FREQ[Hz]','EpsRE[-]','EpsIM[-]','SigmaRE[S/m]','SigmaIM[S/m]'

    备注:
        使用 mpmath 高精度求根,速度较慢但精度高;批量场景可改用 TLcalculateEPS_JAX 加速版。
    """
    # 延迟导入: 仅在调用本函数时才加载 mpmath（避免 gmpy2 后端加载失败）
    # 注: 模块顶部已有 import mpmath as mp (line 15), 此处 import 为冗余保留以防万一
    mu1 = 1  # 相对磁导率
    mu0 = 4*np.pi*1e-7  # 真空磁导率
    eps0 = 8.854187817e-12    # 真空介电常数
    Calsigma = 0  # 电导率初始值

    resultsdata=list()
    
    processing_params = params_info['processing_parameters']    # 从params_info获取处理参数
    
    # 将字符串参数转换为float
    Gf1 = float(processing_params['geometric_constant'])  # 3.95
    ls = float(processing_params['solution_length'])  # 0.00255 测量段长度

    # 处理每个测试样品数据
    SolZThe = [0 for i in range(0, len(prodata))]
    for temp in range(0, len(prodata)):

        ZREmeasured = prodata[temp]['Rs[ohm]']
        ZIMmeasured = prodata[temp]['X[ohm]']
        Zmeasured = ZREmeasured + 1.j*ZIMmeasured
        SolZThe[temp] = array(Zmeasured)
        
    # 计算介电常数
    Solepsnamelistnum = len(SolZThe)
    SolepsThe = [0 for i in range(0, Solepsnamelistnum)]
    omega = 2 * np.pi * prodata[0]['FREQ[Hz]']

    for temp in range(0, Solepsnamelistnum):
        freq = prodata[temp]['FREQ[Hz]']
        tempepsdata = [0 for i in range(np.size(freq))]

        for mptemp in range(0, np.size(freq)):
            anstemp = mp.findroot(
                lambda eps: SolZThe[temp][mptemp] - (mp.sqrt((mu1 * mu0) / (eps * eps0)) / (Gf1)) / (
                    mp.tanh(1j * omega[mptemp] * mp.sqrt(mu1 * mu0 * eps * eps0) * ls)), 30)
            re = float(mp.nstr(mp.re(anstemp), 15))
            im = float(mp.nstr(mp.im(anstemp), 15))
            tempepsdata[mptemp] = re + im * 1j

        
        SolepsThe[temp] = pd.Series(tempepsdata)
        sigmaMUT = 1j*omega*SolepsThe[temp]*eps0        # 计算电导率
       
        # 创建结果数据
        resu = creatdatabaseEPS(freq, SolepsThe[temp], sigmaMUT)
        resultsdata.append(resu)

    print('TLcalculateEPS Processed')
    return resultsdata


def TLcalculateEPS_JAX(prodata, params_info):
    """
    传输线介电常数反演 (JAX 加速版) — 与 TLcalculateEPS 计算逻辑相同,但用 JAX 进行向量化与 JIT 加速,适合大批量数据。

    适用场景:
        - 同 TLcalculateEPS,但样本数多、频率点多时显著加速
        - 需安装 jax、jaxlib

    实现要点:
        - 复数介电常数拆为 (real, imag) 两路实数优化变量
        - 使用 BFGS 算法向量化 (vmap) 处理所有频率点
        - 自定义 stable_tanh 防止 tanh 在大参数下数值溢出
        - 添加正则化项防止除零
        - 目标函数: 100·|Z_meas − Z_theory|² / |Z_meas|² (相对误差平方)

    参数/返回: 同 TLcalculateEPS
    """
    import jax
    import jax.numpy as jnp
    from jax.scipy.optimize import minimize
    from jax import vmap, jit
    jax.config.update("jax_enable_x64", True)  # 在代码开头添加此行

    # 使用双精度常数
    mu1 = jnp.float64(1.0)  # 相对磁导率
    mu0 = jnp.float64(4.0 * np.pi * 1e-7)  # 真空磁导率
    eps0 = jnp.float64(8.854187817e-12)    # 真空介电常数
    
    # 正则化项防止除零错误
    eps_regularization = jnp.float64(1e-15)
    
    resultsdata = list()
    
    processing_params = params_info['processing_parameters']
    
    # 将字符串参数转换为双精度float
    Gf1 = jnp.float64(float(processing_params['geometric_constant']))  # 3.95
    ls = jnp.float64(float(processing_params['solution_length']))  # 0.00255 测量段长度
    
    @jit
    def stable_tanh(x):
        """数值稳定的tanh函数实现，避免大参数时的数值问题"""
        # 对于大参数使用渐近展开，避免数值溢出
        abs_x = jnp.abs(x)
        threshold = jnp.float64(700.0)  # tanh函数稳定化阈值
        return jnp.where(
            abs_x > threshold,
            jnp.sign(x) * (jnp.float64(1.0) - jnp.float64(2.0) * jnp.exp(-jnp.float64(2.0) * abs_x)),
            jnp.tanh(x)
        )
    
    @jit
    def equation_single(eps_complex, omega_val, SolZThe_val):
        # 使用双精度复数
        eps_real = jnp.float64(eps_complex[0])
        eps_imag = jnp.float64(eps_complex[1])
        eps = eps_real + 1j * eps_imag
        
        # 添加正则化项防止除零
        eps_regularized = eps + eps_regularization * (jnp.float64(1.0) + 1j)
        
        # 使用稳定化的tanh函数
        tanh_arg = 1j * omega_val * jnp.sqrt(mu1 * mu0 * eps_regularized * eps0) * ls
        tanh_result = stable_tanh(tanh_arg)
        
        # 防止tanh结果接近零
        tanh_result = jnp.where(
            jnp.abs(tanh_result) < eps_regularization,
            eps_regularization,
            tanh_result
        )
        
        theory = (jnp.sqrt((mu1 * mu0) / (eps_regularized * eps0)) / Gf1) / tanh_result
        return 100*(jnp.abs(SolZThe_val - theory)/jnp.abs(SolZThe_val))**2
    
    # 向量化处理所有频率点，使用Newton-CG算法获得更高精度
    solve_vectorized = vmap(lambda omega_val, sol_val: minimize(
        lambda x: equation_single(x, omega_val, sol_val), 
        jnp.array([30.0, 0.0], dtype=jnp.float64),
        method='BFGS',
        options={
            'gtol': 1e-15,      # 更严格的梯度容差
            'maxiter': 5000,    # 增加最大迭代次数
        }
    ).x)
    
    # 处理每个测试样品数据
    for temp in range(0, len(prodata)):
        freq = prodata[temp]['FREQ[Hz]']
        omega = 2 * np.pi * freq
        
        ZREmeasured = prodata[temp]['Rs[ohm]']
        ZIMmeasured = prodata[temp]['X[ohm]']
        Zmeasured = ZREmeasured + 1.j*ZIMmeasured
        SolZThe_temp = array(Zmeasured)
        
        # 转换为JAX双精度数组
        omega_jax = jnp.array(omega, dtype=jnp.float64)
        SolZThe_jax = jnp.array(SolZThe_temp, dtype=jnp.complex128)
        
        # 使用JAX优化求解
        results = solve_vectorized(omega_jax, SolZThe_jax)
        # 构建复数介电常数，使用双精度
        tempepsdata = results[:, 0].astype(np.float64) + 1j * results[:, 1].astype(np.float64)
        
        # 转换回numpy数组和pandas Series，保持双精度
        tempepsdata = np.array(tempepsdata, dtype=np.complex128)
        SolepsThe_temp = pd.Series(tempepsdata)
        # 计算电导率，使用双精度
        omega_np = np.array(omega, dtype=np.float64)
        sigmaMUT = 1j * omega_np * SolepsThe_temp * float(eps0)
        
        # 创建结果数据
        resu = creatdatabaseEPS(freq, SolepsThe_temp, sigmaMUT)
        resultsdata.append(resu)
    
    print('TLcalculateEPS_JAX Processed')
    return resultsdata






def TLcalculateEIS(prodata, params_info):
    """
    传输线正演 (EIS) — 由 MUT 已知复介电常数 ε(ω),正向计算传输线输入阻抗 Z(ω)。

    适用场景:
        - 与 TLcalculateEPS 互为正/反问题
        - 用于验证材料模型、生成合成数据、或在拟合流程中作为正演模型
        - 输入需含 EpsRE/EpsIM 字段 (一般来自 TLcalculateEPS 输出)

    计算公式:
        η = √(μ·μ0 / (ε·ε0))    本征阻抗
        z0 = η / Gf                特征阻抗
        γ = j·ω·√(μ·μ0·ε·ε0)     传播常数
        Z = z0 / tanh(γ·ls)        传输线输入阻抗

    使用 mpmath 高精度计算(每个频率点),保证 tanh 在大参数下不溢出。

    参数:
        prodata (list[DataFrame]): MUT 介电常数数据,字段 'FREQ[Hz]','EpsRE[-]','EpsIM[-]'
        params_info (dict): 需含
            - 'processing_parameters' (dict):
                - 'geometric_constant' (str→float): Gf
                - 'solution_length' (str→float): ls

    返回:
        list[DataFrame]: MUT 阻抗,字段 'FREQ[Hz]','Z[ohm]','PHASE[deg]','Rs[ohm]','X[ohm]'
    """
    # 注: 模块顶部已有 import mpmath as mp (line 15)
    mu1 = 1  # 相对磁导率
    mu0 = 4*pi*1e-7  # 真空磁导率
    eps0 = 8.854187817e-12    # 真空介电常数

    resultsdata=list()
    
    processing_params = params_info['processing_parameters']    # 从params_info获取处理参数
    
    # 将字符串参数转换为float
    Gf1 = float(processing_params['geometric_constant'])  # 3.95
    ls = float(processing_params['solution_length'])  # 0.00255 测量段长度

    # 处理每个测试样品数据
    SolZThe = [0 for i in range(0, len(prodata))]
    for temp in range(0, len(prodata)):
        freq = prodata[temp]['FREQ[Hz]']
        omega = 2 * pi * freq
        
        # 从prodata中读取介电常数数据
        epsRE = prodata[temp]['EpsRE[-]']
        epsIM = prodata[temp]['EpsIM[-]']
        eps = epsRE + 1j*epsIM
        eps = array(eps)
        
        # 使用传输线理论计算阻抗
        tempZdata = [0 for i in range(np.size(freq))]
        for mptemp in range(0, np.size(freq)):
            # 第一部分：计算特征阻抗z0
            eta = mp.sqrt((mu1 * mu0) / (eps[mptemp] * eps0))  # 本征阻抗
            z0 = eta / Gf1  # 特征阻抗
            
            # 第二部分：计算传播常数gamma
            gamma = 1j * omega[mptemp] * mp.sqrt(mu1 * mu0 * eps[mptemp] * eps0)
            
            # 第三部分：通过z0和gamma计算传输线理论的阻抗
            Z_calculated = z0 / mp.tanh(gamma * ls)
            
            re = float(mp.nstr(mp.re(Z_calculated), 15))
            im = float(mp.nstr(mp.im(Z_calculated), 15))
            tempZdata[mptemp] = re + 1j * im
        
        SolZThe[temp] = array(tempZdata)
        
        # 创建结果数据
        resu = creatdatabase(freq, SolZThe[temp])
        resultsdata.append(resu)

    print('TLcalculateEIS Processed')
    return resultsdata

















#########################################################other#######################################


# def KKZlink():
#
#     # Remove the series resistor (here it does not alter realZ)
#     realZ_RemovedSeries = realZ
#
#     # Calculate the imaginary part using Kramers-Kronig (KK) relations
#     NumFreq = len(freq)
#     FreqKK = freq[2:-2]
#     KKimagZ = np.zeros(len(FreqKK))
#
#     for nn in range(2, NumFreq-2):
#         integrand = realZ_RemovedSeries / (freq**2 - freq[nn]**2)
#         KKimagZ[nn - 2] = (2 * freq[nn] / np.pi) * (np.trapz(integrand[:nn], freq[:nn]) + np.trapz(integrand[nn+1:], freq[nn+1:]))
#
#     # Plotting measured and KK-calculated imaginary impedance
#     plt.figure(figsize=(8, 6))
#     plt.semilogx(freq, imagZ, 'r--', linewidth=2, label='Measured Imag Z')
#     plt.semilogx(FreqKK, KKimagZ, 'g-', linewidth=2, label='KK Imag Z')
#     plt.title('Impedance Spectroscopy (Imaginary Part)')
#     plt.xlabel('Frequency [Hz]')
#     plt.ylabel('Reactance [Ω]')
#     plt.legend()
#     plt.grid(True, which="both")
#     plt.xlim([1, max(freq)])
#     plt.show()
#
#     # Calculate the real part using KK relations
#     imagZ_RemovedSeries = imagZ
#     KKrealZ = np.zeros(len(FreqKK))
#
#     for nn in range(2, NumFreq-2):
#         integrand = imagZ_RemovedSeries * freq / (freq**2 - freq[nn]**2)
#         KKrealZ[nn - 2] = -(2 / np.pi) * (np.trapz(integrand[:nn], freq[:nn]) + np.trapz(integrand[nn+1:], freq[nn+1:]))
#
#
#     return
#########################################################other#######################################




# def KKDSlink():
#
#     # Calculate real and imaginary parts of dielectric constant using Debye model
#     def debye_model(w, epsilon_0, epsilon_infinity, tau):
#         # Debye model for dielectric constant
#         return epsilon_infinity + (epsilon_0 - epsilon_infinity) / (1 + 1j * w * tau)
#
#     epsilon_complex = debye_model(omega, epsilon_0, epsilon_infinity, tau)
#     real_epsilon = np.real(epsilon_complex)
#     imag_epsilon = np.imag(epsilon_complex)
#
#     # Plot original Debye model results
#     plt.figure('Dielectric Function from Debye Model')
#     plt.semilogx(freq, real_epsilon, 'b', linewidth=2)
#     plt.semilogx(freq, imag_epsilon, 'r', linewidth=2)
#     plt.xlabel('Frequency [Hz]')
#     plt.ylabel('Dielectric Constant')
#     plt.legend(['Real ε', 'Imag ε'])
#     plt.grid(True)
#     plt.title('Debye Model Dielectric Function')
#
#     # Kramers-Kronig Relation: Real to Imaginary
#     NumFreq = len(freq)
#     FreqKK = freq[2:NumFreq-2]  # Adjusted range to prevent boundary issues
#     KKimag_epsilon = np.zeros(len(FreqKK))
#
#     for nn in range(2, NumFreq-2):  # Change this line
#         integrand = real_epsilon / (omega**2 - omega[nn]**2)
#         integrand[nn] = 0  # To avoid division by zero and the Cauchy principal value
#         KKimag_epsilon[nn-2] = (2 * omega[nn] / np.pi) * \
#             (np.trapz(integrand[:nn], omega[:nn]) + np.trapz(integrand[nn+1:], omega[nn+1:]))
#
#     # Kramers-Kronig Relation: Imaginary to Real
#     KKreal_epsilon = np.zeros(len(FreqKK))
#
#     for nn in range(2, NumFreq-2):  # Change this line
#         integrand = imag_epsilon * omega / (omega**2 - omega[nn]**2)
#         integrand[nn] = 0  # To avoid division by zero and the Cauchy principal value
#         KKreal_epsilon[nn-2] = -(2 / np.pi) * \
#             (np.trapz(integrand[:nn], omega[:nn]) + np.trapz(integrand[nn+1:], omega[nn+1:]))
#
#
#     return



def DRT():
    """
    弛豫时间分布 (Distribution of Relaxation Times, DRT) — 占位函数,待实现。

    计划功能:
        - 由测得阻抗谱 Z(ω) 反演连续的弛豫时间分布函数 γ(τ)
        - 揭示被测体系的多物理过程 (电荷转移、扩散、双电层等),等价于无模型阻抗拟合
        - 常用算法: Tikhonov 正则化、Maxwell 拟合、贝叶斯等
    """
    pass

    return


def creatdatabase(freq, Z):
    """
    由频域复阻抗 Z 创建结果 DataFrame (用于 paraplate/calibrate/TLcalibrate/TLcalculateEIS 等输出)。

    字段:
        - 'FREQ[Hz]': 频率
        - 'Z[ohm]': 阻抗幅值 |Z|
        - 'PHASE[deg]': 相位角 (°)
        - 'Rs[ohm]': 实部 Re(Z)
        - 'X[ohm]': 虚部 Im(Z)
    """
    data = DataFrame()
    Z = Series(Z)
    data['FREQ[Hz]'] = freq
    data['Z[ohm]'] = Series(absolute(Z))  # BUG 修复: 原 real(Z) → absolute(Z)
    Phase = Series(angle(Z))
    data['PHASE[deg]'] = Series(Phase * 180 / pi)
    data['Rs[ohm]'] = Series(real(Z))
    data['X[ohm]'] = Series(imag(Z))
    return data


def creatdatabaseEPS(freq, epsMUT, sigmaMUT):
    """
    由复介电常数 ε_MUT 和复电导率 σ_MUT 创建结果 DataFrame (用于 DieMat/threesolutions/TLcalculateEPS 等输出)。

    字段:
        - 'FREQ[Hz]': 频率
        - 'EpsRE[-]': ε 实部
        - 'EpsIM[-]': ε 虚部
        - 'SigmaRE[S/m]': σ 实部
        - 'SigmaIM[S/m]': σ 虚部
    """
    RE = pd.Series(real(epsMUT))
    IM = pd.Series(imag(epsMUT))
    sigmaRE = pd.Series(real(sigmaMUT))
    sigmaIM = pd.Series(imag(sigmaMUT))

    result = pd.DataFrame(
        {'FREQ[Hz]': freq, 'EpsRE[-]': RE, 'EpsIM[-]': IM, 'SigmaRE[S/m]': sigmaRE, 'SigmaIM[S/m]': sigmaIM})
    return result




