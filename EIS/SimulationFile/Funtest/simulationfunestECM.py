# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 16:31:29 2020

@author: zhang
"""


import os
import sys
sys.path.append('..')

from numpy import log10
import numpy as np


from SimulationFile.simulateECM import simuECM



from lmfit import Parameters

import matplotlib.pyplot as plt
from lmfit import Parameter
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



# circuit3=['R1','+','L10','+','p(','p(','C3',',','R6','+','L1',',','R7',')','+','p(','C1','+','L1',',','R3','+','p(','L3','+','C2','+','R0',',','R4',',','R5',')',')',',','L5',',','L6','+','C5','+','C6',')']
# circuit3=['R1','+','R10','+','p(','p(','C3',',','R6','+','L1',',','R7',')','+','p(','C1','+','L1',',','R3','+','p(','R0',',','R4',',','R5',')',')',',','L5',',','L6','+','C5','+','C6',')']
# circuit3=['R1','+','R10','+','p(','p(','R3',',','R6','+','R1',',','R7',')','+','p(','R1','+','R11',',','R3','+','p(','R3','+','R2','+','R0',',','R4',',','R5',')',')',',','R5',',','R6','+','R5','+','R6',')']



# circuit4=['p(','C3',',','R6','+','L2',',','R7','+','L2','+','C4',')']

# circuit3=['R1','+','p(','C3',',','R6',',','R7',')','+','p(','C1','+','L1',',','R3','+','p(','C2',',','R4',',','R5',')',')']
# circuit3=['R1','+','L1','+','p(','C3',',','R6','+','L2',',','R7',')','+','p(','C1','+','L1',',','R3','+','p(','C2',',','R4',',','R5',')',')']
circuit3=['p(','C3',',','R6',')','+','R1']


ECMlowfreq=np.log10(1e3)
ECMupfreq=np.log10(1e8)
freq=np.logspace(ECMlowfreq, ECMupfreq, num=100)




params = Parameters()

# init_val_test=1
# circuitZ=list()

# def test(params,circuit3):
#     for i in range(0,len(circuit3)):
#         if circuit3[i]!=',' and circuit3[i]!=')' and circuit3[i]!='p(' and circuit3[i]!='+' :
#             paratest=creatparas(params,circuit3[i],init_val_test)
#             # print(paratest[circuit3[i]])
#     return paratest



paratest = Parameters()
paratest['C3']=Parameter('C3',value=1e-9)
paratest['R6']=Parameter('R6',value=1000)
paratest['R1']=Parameter('R1',value=100)


# paratest=test(params,circuit3)


# outputECM(circuit3)
Z,Zparallel=simuECM(paratest,circuit3,freq)
# print(Z)





Zplot=Z























###################### create a set of Parameters####################### 







##############subplot##############

plt.figure(2,figsize=(16,9))  

ax1=plt.subplot(221) 
plt.plot(log10(freq),np.real(Zplot),linewidth=2)

plt.xlabel("Log Freuency [Hz]") 
plt.ylabel("Real part of Z") 


ax2=plt.subplot(222) 
plt.plot(log10(freq),-np.imag(Zplot),linewidth=2)

plt.xlabel("Log Freuency [Hz]") 
plt.ylabel("imaginary part of Z ") 


# ax3=plt.subplot(223)  
# plt.plot(log10(freq),results3['sigmaRE [S/m]']-DC/(omega*eps0),linewidth=2)

# plt.xlabel("Log Freuency [Hz]") 
# plt.ylabel("Real part of sigma [S/m]") 


# # ax4=plt.subplot(224)  
# # plt.plot(log10(freq),results3['sigmaIM [S/m]'],linewidth=2)

# # plt.xlabel("Log Freuency [Hz]") 
# # plt.ylabel("imaginary part of sigma [S/m]") 

ax4=plt.subplot(224) 
plt.plot(np.real(Zplot),-np.imag(Zplot),linewidth=2)
# plt.plot(results3['epsRE [-]'],results3['epsIM [-]'],linewidth=2)
plt.xlabel("Real part of Z") 
plt.ylabel("imaginary part Z") 

# #############subplot##############


































