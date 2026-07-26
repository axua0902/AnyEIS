# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 17:44:43 2020

@author: zhang
"""

import sys
sys.path.append('..')




from numpy import pi,real,imag
from pandas import DataFrame,Series


from EIS.ModelFile.MultiTerm import EPMT,MT

        
        
##############constant##############
eps0=8.854e-12 #F/m Vacuum permittivity
##############constant##############




def simulateModel(pm,freq,modelterm,option):
    omega=2*pi*freq

    if option['EP']==1 :
        epsTotal,sigmaTotal=EPMT(pm,omega,modelterm,option)
    elif option['EP']==0:
        epsTotal,sigmaTotal=MT(pm,omega,modelterm,option)
    else:
        pass
    data=creatdatabaseEPS(freq,epsTotal)  
    return data



def creatdatabaseEPS(freq,epsTotal): #############创建结果数据库   
    omega=2*pi*freq
    sigmaTotal=1j*omega*epsTotal*eps0
    data = DataFrame()
 
    data['FREQ[Hz]']=freq
    data['epsRE[-]']=Series(real(epsTotal))
    data['epsIM[-]']=-Series(imag(epsTotal))
    data['sigmaRE[S/m]']=Series(real(sigmaTotal))
    data['sigmaIM[S/m]']=Series(imag(sigmaTotal))
    
    data=[data]
    return data







