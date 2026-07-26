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



def paraplate(prodata,Gf):
    print("Gf",Gf)
    Reffreq1=prodata[0]['FREQ[Hz]']
    Refomega1=array(list(2*pi*Reffreq1))
    
    resultsdata=list()
    for temp in range(0,len(prodata)):
        ZREmeasrued=prodata[temp]['Rs[ohm]']
        ZIMmeasrued=prodata[temp]['Rs[ohm]']
        Zmeasrued=ZREmeasrued+1.j*ZIMmeasrued
        Zexptest=array(Zmeasrued)

        epsMUT=Zexptest/(Gf*(1+0j))
        sigmaMUT=1j*Refomega1*epsMUT*eps0
        
        Freq=prodata[temp]['FREQ[Hz]']       
        resu=creatdatabaseEPS(Freq,epsMUT,sigmaMUT)
        resultsdata.append(resu)

    print('paraplate Processed')#输出到状态栏
    return resultsdata



#############################################calibrate##########################################################################
def calibrate(refdata,prodata,params_info):
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
       
        ZMUT=Zstd*(Zshort-Zmeasrued)*(Zload-Zopen)/((Zmeasrued-Zopen)*(Zshort-Zload))
        
        resu=creatdatabase(Freq,ZMUT)
        resultsdata.append(resu)

    print('calibrate Processed')#输出到状态栏
    return resultsdata
      


#############################################permittivity calculate###########################################################################
def DieMat(refdata,prodata,params_info):

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
    Cwater=ZairX/(omega*Zwaterabs**2)
    
    
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






def threesolutions(refdata,prodata,params_info):
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





def TLcalibrate(refdata,prodata,params_info):
    
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






def TLcalculateEPS(prodata,params_info):
    mu1 = 1  # 相对磁导率
    mu0 = 4*np.pi*1e-7  # 真空磁导率
    eps0 = 8.854e-12    # 真空介电常数
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
    JAX-based implementation of TLcalculateEPS for improved performance
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






def TLcalculateEIS(prodata,params_info):
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
        # epsRE = prodata[temp]['permittivityRE']
        # epsIM = prodata[temp]['permittivityIM']
        epsRE = prodata[temp]['EPS RE[-]']
        epsIM = prodata[temp]['EPS IM[-]']
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
    pass

    return


def creatdatabase(freq, Z):  #############创建结果数据库
    data = DataFrame()
    Z = Series(Z)
    data['FREQ[Hz]'] = freq
    data['Z[ohm]'] = Series(real(Z))
    Phase = Series(angle(Z))
    data['PHASE[deg]'] = Series(Phase * 180 / pi)
    data['Rs[ohm]'] = Series(real(Z))
    data['X[ohm]'] = Series(imag(Z))
    return data


def creatdatabaseEPS(freq, epsMUT, sigmaMUT):  #############创建结果数据库
    RE = pd.Series(real(epsMUT))
    IM = pd.Series(imag(epsMUT))
    sigmaRE = pd.Series(real(sigmaMUT))
    sigmaIM = pd.Series(imag(sigmaMUT))

    result = pd.DataFrame(
        {'FREQ[Hz]': freq, 'EpsRE[-]': RE, 'EpsIM[-]': IM, 'SigmaRE[S/m]': sigmaRE, 'SigmaIM[S/m]': sigmaIM})
    return result




