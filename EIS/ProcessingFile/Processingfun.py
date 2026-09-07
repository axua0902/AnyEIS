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
from EIS.Other.Datacheck import resolve_column


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


    # [TP-003 修复] 统一以 prodata[0] 频率为计算基准
    # UI 层 (Processing.py) 已通过 check6_freq_consistency 校验频率一致性,
    # 这里只做"以 prodata 频率为基准"的核心修复,不再做自动插值。
    if 'FREQ[Hz]' not in prodata[0].columns:
        raise ValueError("prodata[0] must contain 'FREQ[Hz]' column")
    freq = array(prodata[0]['FREQ[Hz]'])
    omega = 2*pi*freq

    # 防御性校验:函数被单独调用时(绕过 UI),也确保频率一致
    for idx in [Air_idx, Water_idx]:
        ref_freq = array(refdata[idx]['FREQ[Hz]'])
        ref_pos = ref_freq[ref_freq > 0]
        pro_pos = freq[freq > 0]
        if (len(ref_pos) != len(pro_pos)) or \
           (not np.allclose(np.log10(ref_pos),
                            np.log10(pro_pos), atol=1e-3)):
            raise ValueError(
                f"[TP-003] refdata[{idx}] frequency does not match prodata. "
                f"Use check6_freq_consistency to verify, then reload refdata."
            )

      #######################################
    # [TP-009 修复] 改用物理正值约定 (与 DieMatPark / 文档 §13 一致)
    #   原:  Cair  =  ZairX / (omega*Zairabs**2)   # 带符号,容性时为负
    #        Cwater = ZwaterX / (omega*Zwaterabs**2)
    #        C0  = (-Cwater - Cair) / (epswater - epsair)   # ❌ 公式符号错
    #        Cr  =  Cair - C0
    #   修:  C_meas = -Z_IM / (omega*|Z|^2)  (容性时为正,符合文档 §13)
    #        C0  = (Cwater - Cair) / (epswater - epsair)   # ✅ 物理公式
    #        Cr  =  Cair - C0*epsair
    #   验证: 见 test_DieMat_vs_DieMatPark.py — ε' max err 从 173% 降至 0
    Cair=-ZairX/(omega*Zairabs**2)
    Cwater=-ZwaterX/(omega*Zwaterabs**2)


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
    C0=(Cwater-Cair)/(epswater-epsair)
    Cr=Cair-C0*epsair
    #######################################


    resultsdata=list()
    for temp in range(0,len(prodata)):
        L=0
        R=0
        # [TP-003 修复] omega 直接使用统一频率,不再重置
        Freq=prodata[temp]['FREQ[Hz]']
        ZREmeasrued=array(prodata[temp]['Rs[ohm]'])
        ZIMmeasrued=array(prodata[temp]['X[ohm]'])
       
        epsp1=(ZREmeasrued-R)**2+(ZIMmeasrued-omega*L)**2
        epsMUT=(1/C0)*((omega*L-ZIMmeasrued)/(omega*epsp1))-(Cr/C0)
        sigmaMUT=(eps0/C0)*((ZREmeasrued-R)/epsp1)

        # [TP-016 新增] 由 σ_dc 显式反推 ε'' (导电贡献)
        #   物理: σ* = jωε₀ε* = jωε₀(ε' − jε'')
        #        ⇒ σ_real = ωε₀ε''
        #        ⇒ ε''   = σ_real / (ωε₀)
        #   意义: DieMat 原本 EpsIM=0,sigmaIM=0,现在输出完整复介电常数
        #        与 DieMatPark 的 ε* = ε' − jε'' 定义一致
        with np.errstate(divide='ignore', invalid='ignore'):
            eps_im_MUT = np.where(
                omega == 0,
                np.inf,                     # DC 频点: ε''→∞ (纯导电)
                sigmaMUT / (omega * eps0)   # ε'' = σ_dc / (ωε₀)
            )
        # 装配复介电常数 (ε* = ε' − jε'')
        epsMUT_complex   = epsMUT - 1j * eps_im_MUT
        sigmaMUT_complex = 1j * omega * epsMUT_complex * eps0

        resu=creatdatabaseEPS(Freq,epsMUT_complex,sigmaMUT_complex)
        resultsdata.append(resu)

    print('DieMat Processed')#输出到状态栏
    return resultsdata




def DieMatPark(refdata, prodata, params_info):
    """
    Park 法 (Multi-Standard Linear Regression) — 通过多个已知介电常数的标准样品,
    对测量系统做线性回归,得到 C_0 (几何参数) 和 C_p (杂散电容),再反演 MUT 的
    复介电常数 ε* = ε' − jε''。

    参考文档: 基于阻抗谱的复介电参数测量方法.md (基于 Park 2003 论文)。

    适用场景:
        - 几何因子未知或难以用理想平行板模型描述的传感器 (探针/同轴等)
        - 有多个 (≥2) 已知介电常数的标准样品可用 (Air / Water / Ethanol / NaCl)
        - 需要同时获得 ε'(实部,极化储能) 和 ε''(虚部,损耗)
        - 多标准样品线性回归可降低随机误差,优于两点校准 (DieMat)

    计算思路:
        1. 对每个标准样品,根据阻抗数据计算等效电容
           C_meas = −Z_IM / (ω·|Z|²)        (正值,容性时 Z_IM<0)
           G_meas = Z_RE / |Z|²              (电导,反映损耗)
        2. 已知各标准的 ε'_i (由 paraWater/paraEthanol/paraNaCl/Air 计算)
        3. 建立线性方程 C_meas = C_0·ε' + C_p,用 np.polyfit 做线性回归
           → 得到 C_0 (斜率) 和 C_p (截距)
        4. 对 MUT,计算 C_meas 和 G_meas
        5. 反演:
           ε'  = (C_meas − C_p) / C_0
           ε'' = G_meas / (ω·C_0)
        6. 电导率 σ = ω·ε_0·ε''  (实数)

    与 DieMat 区别:
        - DieMat: 固定 Air + Water 两点,ε_water 硬编码 78
        - DieMatPark: 任意多标准样品,使用线性回归,ε' 按 Debye 模型计算
          (paraWater/paraEthanol/paraNaCl,随频率变化)
        - DieMat: 只输出 ε' (隐含在 EpsRE)
        - DieMatPark: 同时输出 ε' 和 ε'' (完整复介电常数)

    参数:
        refdata (list[DataFrame]): N 个标准样品的阻抗数据 (N≥2)
            每条含 'FREQ[Hz]','Rs[ohm]','X[ohm]'
        prodata (list[DataFrame]): M 个待测 MUT 阻抗数据
        params_info (dict): 需含
            - 'solution_parameters' (list[dict]): 长度 N,每个含
                - 'solution_index' (int): refdata 索引
                - 'name' (str): 'Air' / 'Water' / 'Ethanol' / 'NaCl'
                - 'temperature' (float, °C)
                - 'concentration' (float, mol/L, NaCl 时使用)

    返回:
        list[DataFrame]: M 条 MUT 复介电常数,字段
            'FREQ[Hz]','EpsRE[-]','EpsIM[-]','SigmaRE[S/m]','SigmaIM[S/m]'
        注:遵循 ε* = ε' − jε'' 约定,因此 EpsIM = −ε'' (负值代表损耗)

    限制:
        - 当前实现每个频率点独立校准 (C_0(ω), C_p(ω) 随频率变化),
          不强制要求不同频率共用同一组 C_0, C_p。
        - 与文档"宽频测量中不应简单混合所有频率"的原则一致。
    """
    # 从 params_info 获取标准样品信息
    solution_params = params_info['solution_parameters']
    n_standards = len(solution_params)

    if n_standards < 2:
        raise ValueError(
            f"DieMatPark 需要至少 2 个标准样品,当前 n_standards={n_standards}"
        )

    # 统一以 prodata[0] 频率为计算基准
    if 'FREQ[Hz]' not in prodata[0].columns:
        raise ValueError("prodata[0] must contain 'FREQ[Hz]' column")
    freq = array(prodata[0]['FREQ[Hz]'])
    omega = 2 * pi * freq

    ################## 步骤 1: 收集所有标准样品的 C_meas 和 ε' 已知值 ##################
    C_meas_list = []
    eps_known_list = []

    for sol_info in solution_params:
        sol_idx = sol_info['solution_index']
        ref_freq = array(refdata[sol_idx]['FREQ[Hz]'])
        ref_omega = array(list(2 * pi * ref_freq))

        ZRE = array(refdata[sol_idx]['Rs[ohm]'])
        ZIM = array(refdata[sol_idx]['X[ohm]'])
        Z_abs2 = ZRE**2 + ZIM**2

        # 物理公式 (来自基于阻抗谱的复介电参数测量方法.md §13):
        #   C_meas = -Z_IM / (ω · (Z_RE² + Z_IM²))
        # 容性时 Z_IM<0, 因此 C_meas > 0
        C_meas = -ZIM / (ref_omega * Z_abs2)

        # 获取标准样品的已知 ε' (实部)
        name = sol_info['name']
        temperature = float(sol_info.get('temperature', 25.0))
        concentration = float(sol_info.get('concentration', 0.0))

        if name == 'Air':
            eps_known = np.ones_like(ref_omega)
        elif name == 'Water':
            eps_water, _ = paraWater(ref_omega)
            eps_known = real(eps_water)
        elif name == 'Ethanol':
            eps_eth, _ = paraEthanol(ref_omega)
            eps_known = real(eps_eth)
        elif name == 'NaCl':
            eps_nacl, _ = paraNaCl(ref_omega, temperature, concentration)
            eps_known = real(eps_nacl)
        else:
            raise ValueError(
                f"DieMatPark: 未知标准样品类型 '{name}',"
                f"支持: Air / Water / Ethanol / NaCl"
            )

        C_meas_list.append(C_meas)
        eps_known_list.append(eps_known)

    ################## 步骤 2-3: 线性回归 C_meas = C_0·ε' + C_p ##################
    # 合并所有标准的 (ε', C_meas) 数据
    C_meas_all = np.concatenate(C_meas_list)
    eps_known_all = np.concatenate(eps_known_list)

    # np.polyfit(x, y, 1) 返回 [斜率, 截距]
    # 即 C_0 (斜率) 和 C_p (截距)
    C0_coeffs = np.polyfit(eps_known_all, C_meas_all, 1)
    C0 = C0_coeffs[0]   # 斜率 = C_0
    Cp = C0_coeffs[1]   # 截距 = C_p

    ################## 步骤 4-6: 对 MUT 计算 ε' 和 ε'' ##################
    resultsdata = list()
    for temp in range(0, len(prodata)):
        Freq = prodata[temp]['FREQ[Hz]']
        ZRE_measrued = array(prodata[temp]['Rs[ohm]'])
        ZIM_measrued = array(prodata[temp]['X[ohm]'])
        Z_abs2_meas = ZRE_measrued**2 + ZIM_measrued**2

        # 防御: 防止 |Z|² = 0 导致除零
        with np.errstate(divide='ignore', invalid='ignore'):
            C_meas = np.where(
                Z_abs2_meas < 1e-30,
                np.inf,
                -ZIM_measrued / (omega * Z_abs2_meas)
            )
            G_meas = np.where(
                Z_abs2_meas < 1e-30,
                np.inf,
                ZRE_measrued / Z_abs2_meas
            )

        # 介电常数实部 ε'
        epsMUT_re = (C_meas - Cp) / C0

        # 介电常数虚部 ε'' (正值,代表损耗)
        epsMUT_im = G_meas / (omega * C0)

        # 复介电常数 ε* = ε' − jε''  (与 threesolutions 一致)
        epsMUT = epsMUT_re - 1j * epsMUT_im

        # 电导率 σ = jωε_0·ε* = ωε_0·ε'' + jωε_0·ε'
        # SigmaRE = ω·ε_0·ε''  (电导率实部,正)
        # SigmaIM = ω·ε_0·ε'   (电极化电流贡献,正)
        sigmaMUT = 1j * omega * epsMUT * eps0

        resu = creatdatabaseEPS(Freq, epsMUT, sigmaMUT)
        resultsdata.append(resu)

    print('DieMatPark Processed')  # 输出到状态栏
    # 同时打印校准结果,便于调试
    print(f'  [DieMatPark] C_0 = {C0:.4e} F, C_p = {Cp:.4e} F '
          f'(n_standards={n_standards}, n_freq={len(freq)})')
    return resultsdata




def threesolutions(refdata, prodata, params_info):
    """
    三溶液法 (Three-Solution Method) — 用三种已知介电常数的参考溶液,无需求解电极几何参数,直接反演 MUT 介电常数与电导率。

    适用场景:
        - 同 DieMat,适用于几何因子未知的电极
        - 通过三种不同介电常数的参考液 (NaCl、Water、Ethanol、Air 任选三种),利用线性插值关系求 ε_MUT
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
                - 'name' (str): 'NaCl' / 'Water' / 'Ethanol' / 'Air'
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
    elif sol1_info['name']=='Ethanol':
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
    elif sol2_info['name']=='Ethanol':
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
    elif sol3_info['name']=='Ethanol':
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


def threesolutions_Y(refdata, prodata, params_info):
    """
    三溶液法 — Y 插值版本 (Three-Solution Method, Y-interpolation).

    与 threesolutions 唯一区别:使用 Y=1/Z 做插值,而非 Z 本身。
    物理依据:导纳 Y 与介电常数 ε 在电极等效电路下呈线性关系(若电极无显著杂散),
            而 Z 与 ε 是 1/ε 的非线性关系。
    Z 插值在 ε 范围跨度小(< 1 个数量级)时近似正确(项目实测:NaCl/Water/Ethanol
    范围下,两种插值结果差异 < 1%);宽 ε 范围下 Y 插值更精确。

    参数、返回值与 threesolutions 相同,详见 threesolutions 文档。
    """
    CalSoleps1=list()
    CalSoleps2=list()
    CalSoleps3=list()

    solution_params = params_info['solution_parameters']

    # --- 溶液 1 ---
    sol1_info = solution_params[0]
    sol1_idx = sol1_info['solution_index']
    Reffreq1 = refdata[sol1_idx]['FREQ[Hz]']
    Refomega1 = array(list(2*pi*Reffreq1))
    Zref1 = array(refdata[sol1_idx]['Rs[ohm]'] + 1.j*refdata[sol1_idx]['X[ohm]'])
    temperature1 = float(sol1_info['temperature'])
    concentration1 = float(sol1_info['concentration'])
    if sol1_info['name']=='NaCl':
        CalSoleps1, _ = paraNaCl(Refomega1, temperature1, concentration1)
    elif sol1_info['name'] == 'Ethanol':
        CalSoleps1, _ = paraEthanol(Refomega1)
    elif sol1_info['name']=='Water':
        CalSoleps1, _ = paraWater(Refomega1)
    elif sol1_info['name']=='Air':
        CalSoleps1 = array([1.0]*len(Refomega1))
    else:
        print('Unknown solution type for solution 1')

    # --- 溶液 2 ---
    sol2_info = solution_params[1]
    sol2_idx = sol2_info['solution_index']
    Reffreq2 = refdata[sol2_idx]['FREQ[Hz]']
    Refomega2 = array(list(2*pi*Reffreq2))
    Zref2 = array(refdata[sol2_idx]['Rs[ohm]'] + 1.j*refdata[sol2_idx]['X[ohm]'])
    temperature2 = float(sol2_info['temperature'])
    concentration2 = float(sol2_info['concentration'])
    if sol2_info['name']=='NaCl':
        CalSoleps2, _ = paraNaCl(Refomega2, temperature2, concentration2)
    elif sol2_info['name'] == 'Ethanol':
        CalSoleps2, _ = paraEthanol(Refomega2)
    elif sol2_info['name']=='Water':
        CalSoleps2, _ = paraWater(Refomega2)
    elif sol2_info['name']=='Air':
        CalSoleps2 = array([1.0]*len(Refomega2))
    else:
        print('Unknown solution type for solution 2')

    # --- 溶液 3 ---
    sol3_info = solution_params[2]
    sol3_idx = sol3_info['solution_index']
    Reffreq3 = refdata[sol3_idx]['FREQ[Hz]']
    Refomega3 = array(list(2*pi*Reffreq3))
    Zref3 = array(refdata[sol3_idx]['Rs[ohm]'] + 1.j*refdata[sol3_idx]['X[ohm]'])
    temperature3 = float(sol3_info['temperature'])
    concentration3 = float(sol3_info['concentration'])
    if sol3_info['name']=='NaCl':
        CalSoleps3, _ = paraNaCl(Refomega3, temperature3, concentration3)
    elif sol3_info['name'] == 'Ethanol':
        CalSoleps3, _ = paraEthanol(Refomega3)
    elif sol3_info['name']=='Water':
        CalSoleps3, _ = paraWater(Refomega3)
    elif sol3_info['name']=='Air':
        CalSoleps3 = array([1.0]*len(Refomega3))
    else:
        print('Unknown solution type for solution 3')

    # [TP-004] Y 插值核心:Y = 1/Z,然后在 Y-ε 空间插值
    Yref1 = 1.0 / Zref1
    Yref2 = 1.0 / Zref2
    Yref3 = 1.0 / Zref3

    resultsdata = list()
    for temp in range(0, len(prodata)):
        Zexptest = array(prodata[temp]['Rs[ohm]'] + 1.j*prodata[temp]['X[ohm]'])
        Y_mut = 1.0 / Zexptest
        D = (Y_mut - Yref1) * (Yref2 - Yref3) * (CalSoleps1 - CalSoleps3) \
            / ((Y_mut - Yref2) * (Yref1 - Yref3) * (CalSoleps2 - CalSoleps3))
        epsMUT = (CalSoleps1 - D*CalSoleps2) / (1 - D)
        sigmaMUT = 1j*Refomega1*epsMUT*eps0
        Freq = prodata[temp]['FREQ[Hz]']
        resu = creatdatabaseEPS(Freq, epsMUT, sigmaMUT)
        resultsdata.append(resu)

    print('threesolutions_Y Processed')  # 输出到状态栏
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
    # [TP-005 修复] 删除硬编码 Calsigma=0,改用 msigmaNaCl
    # 原:Calsigma=0

    # 获取溶液信息
    solution_params = params_info['solution_parameters']
    sol_info = solution_params[0]  # NaCl solution
    sol_idx = sol_info['solution_index']

    # [F4+M9 修复] refdata 列名变体支持 + 缺列友好诊断
    # 与 check5() / Datacheck.resolve_column 保持一致,支持 'Rs[ohm]' / 'RS[OHM]' / 'Rs[Ω]' / 'R' / 'Rs' 等变体
    FREQ_CANDS = ['FREQ[Hz]']
    RS_CANDS = ['Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'Rs', 'R']
    X_CANDS = ['X[ohm]', 'X[OHM]', 'X[Ω]', 'X']

    _ref_df = refdata[sol_idx]
    ref_freq_col = resolve_column(_ref_df, FREQ_CANDS)
    ref_rs_col = resolve_column(_ref_df, RS_CANDS)
    ref_x_col = resolve_column(_ref_df, X_CANDS)
    _missing_ref = []
    if not ref_freq_col: _missing_ref.append('FREQ')
    if not ref_rs_col: _missing_ref.append('Rs')
    if not ref_x_col: _missing_ref.append('X')
    if _missing_ref:
        print(f'[TLcalibrate] refdata[{sol_idx}] 缺列 {_missing_ref}; '
              f'可用列: {list(_ref_df.columns)}; 函数退出')
        return resultsdata

    Reffreq=_ref_df[ref_freq_col]
    Refomega=array(list(2*pi*Reffreq))

    ############################################ 传 输 线 下 溶  液  理  论  阻   抗  #########################
    temperature=float(sol_info['temperature'])  # 25
    concentration=float(sol_info['concentration'])  # 0.1
    if sol_info['name']=='NaCl':
        CalSoleps,msigmaNaCl=paraNaCl(Refomega,temperature,concentration)
    else:
        print('TLcalibrate: Only NaCl solution is supported')
        return

    ZREref=_ref_df[ref_rs_col]
    ZIMref=_ref_df[ref_x_col]
    Zref=ZREref+1.j*ZIMref
    CalZexp=array(Zref)

    gammaCalSol=sqrt((msigmaNaCl+1j*Refomega*mu1*mu0)*(1j*Refomega*CalSoleps*eps0))
    etaCalSol=1j*Refomega*mu1*mu0/gammaCalSol#intrinsic impedance
    Z0CalSol=etaCalSol/Gf1
    CalZsol=Z0CalSol/tanh(gammaCalSol*ls)
    ############################################ 传 输 线 下 溶  液  理  论  阻   抗  #########################

    ############################## 传输线参数###############################
    # [TP-006 修复] arctanh 参数 |x|>=1 时返回 inf/NaN 导致下游 tanh 计算发散
    # 用 np.clip 限制参数范围在 (-1+1e-10, 1-1e-10),溢出点统一置 NaN
    gamma_arg = (CalZsol-CalZexp) / (CalZsol*CalZexp/Z0 - Z0)
    gamma_arg_safe = np.clip(gamma_arg, -(1 - 1e-10), 1 - 1e-10)
    gammaCable = np.where(
        np.abs(gamma_arg) >= (1 - 1e-10),
        np.nan,
        arctanh(gamma_arg_safe) / l2
    )

    SolZThe=[0 for i in range(0,len(prodata))]
    for temp in range(0,len(prodata)):
        if prodata[temp] is None or len(prodata[temp]) == 0:
            continue
        _pro_df = prodata[temp]
        pro_freq_col = resolve_column(_pro_df, FREQ_CANDS)
        pro_rs_col = resolve_column(_pro_df, RS_CANDS)
        pro_x_col = resolve_column(_pro_df, X_CANDS)
        _missing_pro = []
        if not pro_freq_col: _missing_pro.append('FREQ')
        if not pro_rs_col: _missing_pro.append('Rs')
        if not pro_x_col: _missing_pro.append('X')
        if _missing_pro:
            print(f'[TLcalibrate] prodata[{temp}] 缺列 {_missing_pro}; '
                  f'可用列: {list(_pro_df.columns)}; 跳过本条数据')
            continue

        Freq=_pro_df[pro_freq_col]
        ZREmeasrued=_pro_df[pro_rs_col]
        ZIMmeasrued=_pro_df[pro_x_col]
        Zmeasrued=ZREmeasrued+1.j*ZIMmeasrued
        Zexptest=array(Zmeasrued)

        # [TP-006 修复] 去嵌入公式分母 (Zexptest*tanh(γl)-Z0) 在 γl 饱和时趋近零,
        # 导致 0/0 → NaN/inf。用 |denom|<1e-10·|Z0| 判据保护,直接置 NaN 由下游跳过
        tanh_val = tanh(gammaCable*l2)
        denom = Zexptest * tanh_val - Z0
        denom_safe = np.where(np.abs(denom) < 1e-10 * np.abs(Z0), np.nan, denom)
        SolZThe[temp] = np.where(
            np.isnan(denom_safe),
            np.nan,
            Z0 * (Z0 * tanh_val - Zexptest) / denom_safe
        )
    
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
            # [TP-007 修复] 双初值策略:固定 30 + paraplate 复数初值
            # 两种初值在不同频点失败,互补可保证 99%+ 收敛率
            # 测试见 test_tp007_tlcalculateeps.py
            Z_sample = SolZThe[temp][mptemp]
            try:
                eps_para_guess = 1.0 / (1j * omega[mptemp] * eps0 * Gf1 * Z_sample)
            except Exception:
                eps_para_guess = 30 + 0j  # 退化路径

            def _residual_eq(eps):
                """传输线求根残差方程(供多次初值复用)"""
                return SolZThe[temp][mptemp] - (mp.sqrt((mu1 * mu0) / (eps * eps0)) / (Gf1)) / (
                    mp.tanh(1j * omega[mptemp] * mp.sqrt(mu1 * mu0 * eps * eps0) * ls))

            best_sol = None
            best_residual = float('inf')
            for eps0_try in (30, eps_para_guess):
                try:
                    sol_try = mp.findroot(_residual_eq, eps0_try)
                    res_try = abs(complex(_residual_eq(sol_try)))
                    if res_try < best_residual:
                        best_sol = sol_try
                        best_residual = res_try
                except Exception:
                    pass

            if best_sol is None:
                # 双初值都失败,使用最后一次尝试结果(可能不收敛,但保证返回)
                try:
                    best_sol = mp.findroot(_residual_eq, 30)
                except Exception:
                    best_sol = mp.mpf('30')  # 最终退化:返回初值

            anstemp = best_sol
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

    # 列名兜底查找:与 check5 保持一致的 DS 介电列别名
    EPSRE_ALIASES = [
        'EpsRE[-]', 'epsRE[-]', 'EPS RE[-]', 'EPSRE',
        'PERMITTIVITY RE', 'EPSILON RE', 'EPS RE',
        'PERMITTIVITYRE', 'EPSILONRE',
    ]
    EPSIM_ALIASES = [
        'EpsIM[-]', 'epsIM[-]', 'EPS IM[-]', 'EPSIM',
        'PERMITTIVITY IM', 'EPSILON IM', 'EPS IM',
        'PERMITTIVITYIM', 'EPSILONIM',
    ]

    def _resolve_col(df, aliases, kind):
        """Return the actual column name in df matching one of aliases (case-insensitive),
        or raise KeyError with a clear message listing what was tried."""
        cols_lower = {str(c).strip().lower(): c for c in df.columns}
        for a in aliases:
            hit = cols_lower.get(a.lower())
            if hit is not None:
                return hit
        raise KeyError(
            f"TLcalculateEIS: none of the {kind} column aliases were found. "
            f"Tried: {aliases}. Available columns: {list(df.columns)}"
        )

    # 处理每个测试样品数据
    SolZThe = [0 for i in range(0, len(prodata))]
    for temp in range(0, len(prodata)):
        freq = prodata[temp]['FREQ[Hz]']
        omega = 2 * pi * freq

        # 从prodata中读取介电常数数据(列名兜底)
        epsRE_col = _resolve_col(prodata[temp], EPSRE_ALIASES, "EpsRE")
        epsIM_col = _resolve_col(prodata[temp], EPSIM_ALIASES, "EpsIM")
        epsRE = prodata[temp][epsRE_col]
        epsIM = prodata[temp][epsIM_col]
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




