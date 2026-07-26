# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""


import os
import sys
sys.path.append('..')

from numpy import log10,real,imag,array,angle,absolute,pi,sqrt,log,tanh,arctanh
import numpy as np



import pandas as pd
# # import xlsxwriter

# from Other.standard_parameter import paraNaCl,paraNaCl01,paraWater,paraEthanol

# from InputFile.Inputfun import readfile
# # from FigureFile.Figurefun import creatanyfile,writeanydata,writeexcel,creatdataformat

from SimulationFile.simulateMT import simulateModel,creatdatabaseEPS

from lmfit import Parameters



import matplotlib.pyplot as plt

##############constant##############
eps0=8.854187817e-12 #F/m Vacuum permittivity
mu0=4*np.pi*1e-7# H/m  Permeability
##############constant##############


proj_path = os.path.dirname(os.path.abspath( "."))

path=proj_path+'\\testdata\\testdata5'
fileslist=sorted(os.listdir(path),reverse=False)
filepath=[path+"\\"+i for i in fileslist]






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


# ##################循环读取数据########################
# prodata=list()
# prodataname=list()

# for i in range(0,1):
#     prodatanametemp,prodatatemp=readfile(filepath[i])
#     prodata.append(prodatatemp[0])
#     prodataname.append(prodatanametemp[0])
# ##################循环读取数据########################



pm = Parameters()



pm.add('epsh', value=6.9,max=100,min=0)

pm.add('Deps1', value=3.8,max=500, min=0)
pm.add('Tao1', value=2.6, max=20, min=0)
pm.add('Alpha1', value=0.67, max=1,min=0)



pm.add('A', value=2.1, max=1e6, min=0)
pm.add('alphaCPE', value=0.94, max=1,min=0)

pm.add('sigmaDC', value=3.6, max=100,min=0)


# pm.add('epsh', value=78)

# pm.add('Deps1', value=9.5)
# pm.add('Tao1', value=3.2e-2)
# pm.add('Alpha1', value=1-0.87)
       


# pm.add('Deps2', value=6.32-4.57)
# pm.add('Tao2', value=1.1e-12)

# pm.add('alpha1', value=0.1, max=1,min=0)

# pm.add('eps2', value=8.3,max=200, min=0)
# pm.add('fc2', value=0.8e8, max=1e9, min=0)
# pm.add('alpha2', value=0.13, max=1,min=0)
# pm.add('epsh2', value=12,max=20,min=0)




# pm.add('A', value=2e-4)#1e-5)
# pm.add('alphaCPE', value=0.88)#0.9)


# DC=0.0
# pm.add('sigmaDC', value=DC)


option={'EP':1,'DC Conductivity':1}



modeltypetemp1={'name':'1','modeltype':'Cole-Cole'}
# modeltypetemp2={'name':'2','modeltype':'Debye'}
modelterm=[modeltypetemp1]#,modeltypetemp2]




freq=pd.Series(np.logspace(3,9,100),name='Frequency[Hz]')
omega=2*np.pi*freq
omega.rename('Angle frequency [rad/s]',inplace=True)
###################### create a set of Parameters####################### 

# results3=simulateMT(pm,freq,modelterm)
results3=simulateModel(pm,freq,modelterm,option)

results3=results3[0]




##############subplot##############

plt.figure(2,figsize=(16,9))  

ax1=plt.subplot(221) 
plt.plot(log10(freq),results3['epsRE[-]'],linewidth=2)

plt.xlabel("Log Freuency [Hz]") 
plt.ylabel("Real part of eps [-]") 


ax2=plt.subplot(222) 
plt.plot(log10(freq),results3['epsIM[-]'],linewidth=2)

plt.xlabel("Log Freuency [Hz]") 
plt.ylabel("imaginary part of eps[-]") 


ax3=plt.subplot(223)  
plt.plot(log10(freq),results3['sigmaRE[S/m]']-3.6/(omega*eps0),linewidth=2)

plt.xlabel("Log Freuency [Hz]") 
plt.ylabel("Real part of sigma[S/m]") 


# ax4=plt.subplot(224)  
# plt.plot(log10(freq),results3['sigmaIM [S/m]'],linewidth=2)

# plt.xlabel("Log Freuency [Hz]") 
# plt.ylabel("imaginary part of sigma [S/m]") 

ax4=plt.subplot(224) 
# plt.plot(results3['epsRE [-]'],(results3['sigmaRE [S/m]']-DC)/(omega*eps0),linewidth=2)
plt.plot(results3['epsRE[-]'],results3['epsIM[-]'],linewidth=2)
plt.xlabel("Real part of eps [-]") 
plt.ylabel("imaginary part of eps [-]") 

#############subplot##############









































