# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 13:29:49 2020

@author: zhang
"""

###########################"Equivalent circuit"###########################


import sys
sys.path.append('..')

from pandas import DataFrame,Series
from numpy import pi,real,imag,angle

from EIS.ModelFile.EquivCircM import SearchParallel,CalculateParallel,CalculateSeries,expressECM,expressSeriesECM
from EIS.ModelFile.EquivCircFUN import advanced_circuit_drawing

from EIS.ModelFile.circuit_parser import parse_circuit_string
# from EIS.ModelFile.circuit_test_utils import advanced_circuit_drawing


def simuECM(params,circuit,freq):
    plistlen=SearchParallel(circuit)
    circuittemp=circuit

    Zparalist=list()
    Zparallel={}
    ii=0####并联计算次数

    while ii<len(plistlen):
        plist=SearchParallel(circuittemp)###寻找当前电路列表中的并联电路位置

        circuittemp,Zparatemp,Zparallel=CalculateParallel(params,freq,circuittemp,plist,ii,Zparallel)#计算并联电路
        Zparalist.append(Zparatemp)

        ii=ii+1
    # print(Zparallel)
    Ztotal=CalculateSeries(params,freq,circuittemp,Zparallel)

    return Ztotal,Zparallel




        
def creatdatabaseECM(freq,Z): #############创建结果数据库   
    data =DataFrame()
    Z=Series(Z)
    data['FREQ[Hz]']=freq
    data['Z[ohm]']=Series(real(Z))
    # Phase=arctan(Series(imag(Z))/Series(real(Z)))
    Phase=Series(angle(Z))
    data['PHASE[deg]']=Series(Phase*180/pi)
    data['Rs[ohm]']=Series(real(Z))
    data['X[ohm]']=Series(imag(Z))
    data=[data]
    return data


def outputECM(circuit):
    plistlen=SearchParallel(circuit)
    circuitSeries=circuit

    ii=0####并联计算次数
    while ii<len(plistlen):
        plist=SearchParallel(circuitSeries)###寻找当前电路列表中的并联电路位置
        circuitSeries=expressECM(circuitSeries,plist,ii)

        ii=ii+1
        
    expressSeriesECM(circuitSeries)
    return 




def circuitfig(circuit):
    
    try:
        # 转换测试
        branches = parse_circuit_string(circuit)      
        # 绘制测试
        circuit_name = "SimulatedCircuit"
        drawing = advanced_circuit_drawing(circuit, circuit_name)
        
        # 保存图像，设置300dpi分辨率
        filename = 'CircuitFigure/simulated_circuit.png'
        drawing.save(filename, dpi=300)
        print(f"Circuit figure saved to: {filename} at 300 DPI")
        
    except Exception as e:
        print(f"Error generating circuit figure: {str(e)}")
        
    return
    





















