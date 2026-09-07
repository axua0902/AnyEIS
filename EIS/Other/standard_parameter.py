# -*- coding: utf-8 -*-
"""
Created on Sat Jun  9 10:25:17 2018

@author: zhang
"""

import numpy as np

import pandas as pd

from scipy import integrate
##############  constant   ##############
eps0=8.8542e-12 #F/m Vacuum permittivity
k=1.38064852e-23# J*K^-1 Boltzmann constant
##############constant##############


#################    calculate the permittivity of wtaer    ###########
def paraWater(omega):
    stnum=np.size(omega)#
    mepsWater=np.ones(stnum,complex)
    msigmaWater=np.ones(stnum,complex)
    
    def funWater(omega):
   ##########  1929 Debye water #############
        epsWater1=78.32
        epsWater2=6.32
        epsWaterli=4.57###{4.1,5.2}
        taoWater1=8.38e-12
        taoWater2=1.1e-12
    ##########  1929 Debye water #############
        epsWater=(epsWater1-epsWater2)/(1+1j*omega*taoWater1)+(epsWater2-epsWaterli)/(1+1j*omega*taoWater2)+epsWaterli
        sigmaWater=1j*omega*epsWater*eps0
        return epsWater,sigmaWater
    
    for temp in range(0,stnum):
        epsWater,sigmaWater=funWater(omega[temp])
        mepsWater[temp]=epsWater
        msigmaWater[temp]=sigmaWater

    return mepsWater,msigmaWater
#################     calculate the permittivity of wtaer    ###########



#################     calculate the permittivity of Ethanol (90% vol 乙醇水溶液)    ###########
# 注: Debye 参数对应 95% 体积分数乙醇水溶液的实测数据,
#     不是 100% 纯乙醇。纯乙醇 ε_s≈24.3,而本函数 ε_s≈24.6,差异源于水组分。
def paraEthanol(omega):
    stnum=np.size(omega)#
    mepsEthanol=np.ones(stnum,complex)
    msigmaEthanol=np.ones(stnum,complex)
    
    def funEthanol(omega):#3CC
   ##########  1929 Debye water #############
#        epsEthanol=24.47
        epsEthanol1=19.94
        epsEthanol2=0.86
        epsEthanol3=1.19
        epsEthanolli=2.6###{4.1,5.2}
        taoEthanol1=164.9e-12
        taoEthanol2=10.4e-12
        taoEthanol3=1.69e-12
    ##########  1929 Debye water #############
        epsEthanol=epsEthanol1/(1+1j*omega*taoEthanol1)+epsEthanol2/(1+1j*omega*taoEthanol2)+epsEthanol3/(1+1j*omega*taoEthanol3)+epsEthanolli
        sigmaEthanol=1j*omega*epsEthanol*eps0
        return epsEthanol,sigmaEthanol
    
    for temp in range(0,stnum):
        epsEthanol,sigmaEthanol=funEthanol(omega[temp])
        mepsEthanol[temp]=epsEthanol
        msigmaEthanol[temp]=sigmaEthanol

    return mepsEthanol,msigmaEthanol

#################     calculate the permittivity of Ethanol    ###########

#################     calculate the permittivity of Alcohol (75% vol 乙醇水溶液)    ###########
# 注: Debye 参数对应 75% 体积分数乙醇水溶液的实测数据,
#     不是纯乙醇也不是纯甲醇。乙醇-水混合液的 ε_s 随含水量增加而升高。
def paraAlcohol(omega):
    stnum=np.size(omega)#
    mepsAlcohol=np.ones(stnum,complex)
    msigmaAlcohol=np.ones(stnum,complex)

    def funAlcohol(omega):#3CC
   ##########  1929 Debye water #############
        epsAlcohol1=25.39
        epsAlcohol2=1.44
        epsAlcohol3=1.28
        epsAlcoholli=2.70###{4.1,5.2}
        taoAlcohol1=94.41e-12
        taoAlcohol2=8.91e-12
        taoAlcohol3=1.39e-12
    ##########  1929 Debye water #############
        epsAlcohol=epsAlcohol1/(1+1j*omega*taoAlcohol1)+epsAlcohol2/(1+1j*omega*taoAlcohol2)+epsAlcohol3/(1+1j*omega*taoAlcohol3)+epsAlcoholli
        sigmaAlcohol=1j*omega*epsAlcohol*eps0
        return epsAlcohol,sigmaAlcohol

    for temp in range(0,stnum):
        epsAlcohol,sigmaAlcohol=funAlcohol(omega[temp])
        mepsAlcohol[temp]=epsAlcohol
        msigmaAlcohol[temp]=sigmaAlcohol

    return mepsAlcohol,msigmaAlcohol
#################     calculate the permittivity of Alcohol    ###########

#################     calculate the permittivity of NaCl 0.1mol/L   ###########
def paraNaCl01(omega):
    stnum=np.size(omega)#
    mepsNaCl=np.ones(stnum,complex)
    msigmaNaCl=np.ones(stnum,complex)
    
    def funNaCl(omega):#3CC
   ##########  1929 Debye water #############
        epsNaClli=5###{4.1,5.2}
        epsNaCls=78.2
        
        taoNaCl=9.08e-12
        alphaNaCl=0.006
        sigmaNaCli=0.96
    ##########  1929 Debye water #############
        epsNaCl=epsNaClli+(epsNaCls-epsNaClli)/(1+(1j*omega*taoNaCl)**(1-alphaNaCl))+sigmaNaCli/(1j*omega*eps0)
        sigmaNaCl=1j*omega*epsNaCl*eps0
        return epsNaCl,sigmaNaCl
    
    for temp in range(0,stnum):
        epsNaCl,sigmaNaCl=funNaCl(omega[temp])
        mepsNaCl[temp]=epsNaCl
        msigmaNaCl[temp]=sigmaNaCl

    return mepsNaCl,msigmaNaCl
#################     calculate the permittivity of NaCl 0.1mol/L   ###########
    
#################     calculate the permittivity of NaCl   ###########
def paraNaCl(omega,temperature,concentration):
    stnum=np.size(omega)#
    mepsNaCl=np.ones(stnum,complex)
    msigmaNaCl=np.ones(stnum,complex)
    if concentration<=1:
        def funNaCl(omega,temperature,concentration):
            epsNaClli=5.77-0.0274*temperature
            epsNaClsw=10**(1.94404-temperature*1.991*10**(-3))
            epsNaCls=epsNaClsw*(1.0-3.742*10**(-4)*temperature*concentration+0.034*concentration**2-0.178*concentration+temperature*1.515*10**(-4)-4.929*10**(-6)*temperature**2)
            taoNaClw=3.745*10**(-15)*(1+(7*10**(-5))*(temperature-27.5)**2)*np.exp(2.2957*10**3/(temperature+273.15))
            taoNaCl=taoNaClw*(1.012-temperature*concentration*5.282*10**(-3)+0.032*concentration**2-0.01*concentration-temperature*1.724*10**(-3)+3.766*10**(-5)*temperature**2)     
            alphaNaCl=-6.348*10**(-4)*temperature*concentration-5.1*10**(-2)*concentration**2+9*10**(-2)*concentration
            sigmaNaCli=0.174*temperature*concentration-1.582*concentration**2+5.923*concentration

            epsNaCl=epsNaClli+(epsNaCls-epsNaClli)/(1+(1j*omega*taoNaCl)**(1-alphaNaCl))+sigmaNaCli/(1j*omega*eps0)
            sigmaNaCl=1j*omega*epsNaCl*eps0
            return epsNaCl,sigmaNaCl
    else:
        def funNaCl(omega,temperature,concentration):
            epsNaClli=5.77-0.0274*temperature
            epsNaCls=84.328+0.117*temperature*concentration+0.77*concentration**2-13.257*concentration-0.207*temperature-4.859*10**(-3)*temperature**2
            taoNaCl=17.76+0.022*temperature*concentration+0.09*concentration**2-1.222*concentration-0.525*temperature+5.361*10**(-3)*temperature**2   
            alphaNaCl=0.011+4.326*10**(-4)*temperature*concentration+4.431*10**(-3)*concentration**2+4.754*10**(-3)*concentration+1.82*10**(-3)*temperature-6.154*10**(-5)*temperature**2          
            sigmaNaCli=0.061*temperature*concentration-0.667*concentration**2+6.485*concentration-0.439-1.2*10**(-2)*temperature+3.374*10**(-3)*temperature**2

            epsNaCl=epsNaClli+(epsNaCls-epsNaClli)/(1+(1j*omega*taoNaCl*10**(-12))**(1-alphaNaCl))+sigmaNaCli/(1j*omega*eps0)
            sigmaNaCl=1j*omega*epsNaCl*eps0
            return epsNaCl,sigmaNaCl
    
    for temp in range(0,stnum):
        epsNaCl,sigmaNaCl=funNaCl(omega[temp],temperature,concentration)
        mepsNaCl[temp]=epsNaCl
        msigmaNaCl[temp]=sigmaNaCl

    return mepsNaCl,msigmaNaCl
#################     calculate the permittivity of NaCl   ###########
    
##############  cacluate the IMA area paramitters ############
def IMEs(s,w,L,N):
    a=w/(s+w)
    k=np.cos(0.5*np.pi*a)
 
    def funcK(t,temp):
        return 1/np.sqrt((1-t**2)*(1-(temp**2)*(t**2)))
    
    temp1=k
    Kk=integrate.quad(funcK,0,1,args=(temp1))[0]
    
    temp2=np.sqrt(1-k**2)
    K1k=integrate.quad(funcK,0,1,args=(temp2))[0]
    
    
    Kcell=2*Kk/(L*(N-1)*K1k)#m-1
#    ka=1/Kcell
    return Kcell
##############  cacluate the IMA area paramitters ############



##############  ECM cacluate  paramitters of solusions  ############

def ZECMtheory(eps,freq,Kcell,CDIsol):
    sigma=1j*2*np.pi*freq*eps*eps0
    sigmaRE=np.real(sigma)
    epsRE=np.real(eps)
    Rsol=Kcell/sigmaRE
    Csol=eps0*epsRE/Kcell
    
    if CDIsol==0:
        Zsol1=Rsol
        Zsol2=1/(1.j*2*np.pi*freq*Csol)
    else:
#        CDIsol=0.4e-11
        Zsol1=1/(1.j*2*np.pi*freq*Csol)
        Zsol2=(1+1.j*np.pi*freq*Rsol*CDIsol)/(1.j*np.pi*freq*CDIsol)
    
    Zsol=1/(1/Zsol1+1/Zsol2)
    
    return Zsol
##############  ECM cacluate  paramitters of solusions  ############

##############  MMT cacluate  paramitters of solusions  ############
def ZMMTtheory(eps,freq,Kcell):
    Zp=1/(1.j*2*np.pi*freq*eps*eps0/Kcell)
    return Zp
##############  MMT cacluate  paramitters of solusions  ############



###############   parameter of IMEs area paramitters############
#s=3e-6#m
#w=3e-6#m
#L=2.5e-3#m
#N=65
##############   parameter of IMEs area paramitters##########
#
#Kcell=IMEs(s,w,L,N)

ramin=6
ramax=10
stnum=200
freq=np.logspace(ramin, ramax, num=stnum)
omega=list(2*np.pi*freq)
temperature=20
concentration=0.1
epsNaCl,sigmaNaCl=paraNaCl(omega,temperature,concentration)
epsNaCl=np.real(epsNaCl).tolist()
#Kcell=12.4999
#
#
#CDIsol=0
#Zsol11=ZECMtheory(epsWater,freq,Kcell,CDIsol)
#
#Zsol12=ZMMTtheory(epsWater,freq,Kcell)
#
#s=Zsol11-Zsol12



























