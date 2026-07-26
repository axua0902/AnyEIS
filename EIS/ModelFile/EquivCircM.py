# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 13:29:49 2020

@author: takeilab
"""

###########################"Equivalent circuit"###########################

import sys
sys.path.append('..')


from numpy import pi,tanh,arctanh
from lmfit import Parameter



def R(pval,freq):#Resistor (SI: pval in ohm)
    Zre=pval
    Zim=0*freq
    Z=Zre+Zim*1j
    return Z

def C(pval,freq):#Capacitor (SI: pval in farad)
    Zre=0
    Zim=-1/(2*pi*freq*pval)
    Z=Zre+Zim*1j
    return Z

def L(pval,freq):#Inductor (SI: pval in henry)
    Zre=0
    Zim=2*pi*pval*freq
    Z=Zre+Zim*1j
    return Z

def CPE(T,P,freq):
    Z=1/(T*(1j*2*pi*freq)**P)
    return Z

def Zws(RR,T,P,freq):
    Z=RR*tanh((1j*T*2*pi*freq)**P)/((1j*T*2*pi*freq)**P)
    return Z

def Zwo(RR,T,P,freq):
    Z=RR*arctanh((1j*T*2*pi*freq)**P)/((1j*T*2*pi*freq)**P)
    return Z


def s(series):#sums elements in series
    Z=0
    for elem in series:
        Z+=elem
    return Z

def p(parallel):#adds elements in parallel
    Z=0
    for elem in parallel:
        Z += 1/elem
    return 1/Z

def Zp(pval,freq):#Resistor
    Z=pval
    return Z




def check(circuit):
    return print('wrong')


def creatparas(params,name1,init_val):
    params[name1]=Parameter(name1,value=init_val)#,min=min_val,max=max_val)
    # params[name1].set(value=10)
    # print(params)
    return params


def elementsZ(element,pm,freq):
    if -1!=element.find('C',0,1):
        ss=pm[element].value
        Z=C(ss,freq)
        return Z
    elif -1!=element.find('R',0,1):
        ss=pm[element].value
        Z=R(ss,freq)
        return Z
    elif -1!=element.find('L',0,1):
        ss=pm[element].value
        Z=L(ss,freq)
        return Z

    else:
        return
    
    
def expressZ(element):
    # print(type(element))
    if -1!=element.find('C',0,1):
        Zexpress='1/(j*omega*'+str(element)+')'
        return Zexpress
    elif -1!=element.find('R',0,1):
        Zexpress=str(element)
        return Zexpress
    elif -1!=element.find('L',0,1):
        Zexpress='j*omega*'+str(element)
        return Zexpress
    # elif-1!=element.find('Zpara',0,5):
        # Zexpress=element
    #     return Zexpress
    else:
        Zexpress=element
        return Zexpress
    
    


def SearchParallel(circuit):   
    circuitlist=[i for i in range(0,len(circuit))]
    pbklist=list()######'p(' 的位置
    rbklist=list()########')'的位置
    plist=list()############并联元件的位置
    
    ############################分析电路中的并联#########
    for tem1 in circuitlist:
        if circuit[tem1]=='p(':###寻找并联标志
            pbklist.append(tem1)

    for tempk in range(len(pbklist)-1,-1,-1):
        maxpk=pbklist[tempk]
        for tem2 in range(maxpk,len(circuit)):
            if circuit[tem2]==')' and tem2 not in rbklist:#####确定并联结尾位置
                rbklist.append(tem2)  
                l=[maxpk,tem2]
                plist.append(l)
                break 
    return plist      
    ############################分析电路中的并联#########


    
def CalculateParallel(paratest,freq,circuit,plist,ii,Zparallel):###阻抗计算
    # print(circuit)
    # print(plist)    
   ###############获得并联电路############
    plisttemp=0
    circuitLpos=plist[plisttemp][0]
    circuitRpos=plist[plisttemp][1]
    circuitpara=circuit[circuitLpos:circuitRpos+1]####并联电路
    # print('并联电路是',circuitpara)
    ###############获得并联电路############
     
    
    circuittemp=list()###并联中子部分临时电路
    Zparapart=list()###并联中子部分阻抗值
    Zparapartsub=list()#####并联中单一元件的阻抗值
    
    #####################计算并联电路中每一子部分阻抗 #####################
    num=0###并联中子部分计数器
    for tem3 in range(0,len(circuitpara)):
        if circuitpara[tem3]!=',' and circuitpara[tem3]!=')' and circuitpara[tem3]!='p(':##并联中子部分部分，
            circuittemp.append(circuitpara[tem3])####并联中的子部分，为串联电路
        elif circuitpara[tem3]==',' or circuitpara[tem3]==')' or circuitpara[tem3]=='+':####并联中的子部分结束，开始计算串联电路阻抗
            num=num+1
            # print(circuittemp)
            subtemp=0
            for  t in range(0,len(circuittemp),2):####计算并联中每一支路的阻抗
                subtemp=subtemp+1
                # print(circuittemp[t])
                partsubname='Zpara'+str(ii+1)+'part'+str(num)+'sub'+str(subtemp)
                #########计算每一部分阻抗###########                
                if  -1!=circuittemp[t].find('Zpara',0,5):
                    Zparapartsubtemp=Zparallel[circuittemp[t]]###每一个元件的阻抗
                    Zparapartsub.append(Zparapartsubtemp)    
                else:
                    Zparapartsubtemp=elementsZ(circuittemp[t],paratest,freq)
                    Zparallel[partsubname]=Zparapartsubtemp#记录阻抗计算结果
                    Zparapartsub.append(Zparapartsubtemp) 
                
                # print('element',Zparapartsubtemp) 
                #########计算每一部分阻抗###########

            ########计算子部分串联阻抗###########  
            # print('-------')
            # print('sublist',Zparapartsub)####并联中每一支路的阻抗
            # print('---------')
            Zparaparttemp=s(Zparapartsub)
            Zparapartsub=list()#####清除并联中单一元件的阻抗值
            # print('part',Zparaparttemp)
            Zparapart.append(Zparaparttemp)####并联中各个支路的阻抗
            
            paraname='Zpara'+str(ii+1)+'part'+str(num)
            Zparallel[paraname]=Zparaparttemp
            # print("Zparapart:",Zparapart)
            ########计算子部分串联阻抗########### 
            # print('----------------------')
            circuittemp=list()
        elif circuitpara[tem3]=='p(':
            circuittemp=list()
            pass
     #####################计算并联电路中每一子部分阻抗 ##################### 
     
    ########计算并联阻抗###########
    # print('partlist',Zparapart)#并联中各个支路的阻抗
    Zpara=p(Zparapart)
    # print('para',Zpara)
    Zexpressname='Zpara'+str(ii+1) 
    Zparallel[Zexpressname]=Zpara
    #######计算并联阻抗###########

############更新电路##################
    templ=circuit[0:circuitLpos]
    tempr=circuit[circuitRpos+1:len(circuit)]
    newcircuit=templ+[Zexpressname]+tempr
  ############更新电路##################

    return newcircuit,Zpara,Zparallel
                   

def CalculateSeries(paratest,freq,circuit,Zparallel):
    ZSeries=list()   
    for  t in range(0,len(circuit),2):   
        if  -1!=circuit[t].find('Zpara',0,5):
            ZSeriestemp=Zparallel[circuit[t]]
            ZSeries.append(ZSeriestemp)   
        else:
            ZSeries.append(elementsZ(circuit[t],paratest,freq))    

    Ztotal=s(ZSeries)

    return Ztotal
    



def expressECM(circuit,plist,ii):
    ###############获得并联电路############
    plisttemp=0
    circuitLpos=plist[plisttemp][0]
    circuitRpos=plist[plisttemp][1]
    circuitpara=circuit[circuitLpos:circuitRpos+1]####并联电路
    ###############获得并联电路############
       
    circuittemp=list()###并联中子部分临时电路
    Zexpresspart=list()###并联中子部分表达式
    Zexpresspara=list()
    
     #####################计算并联电路中每一子部分阻抗的表达式 #####################
    num=0###并联中子部分计数器
    for tem3 in range(0,len(circuitpara)):
        # print(circuitpara[tem3])
        if circuitpara[tem3]!=',' and circuitpara[tem3]!=')' and circuitpara[tem3]!='p(':##并联中子部分部分，
            circuittemp.append(circuitpara[tem3])####并联中的子部分，为串联电路
        elif circuitpara[tem3]==',' or circuitpara[tem3]==')' or circuitpara[tem3]=='+':####并联中的子部分结束，开始计算串联电路阻抗
            num=num+1
            Zexpresspart=list()
            
            subtemp=0
            for  t in range(0,len(circuittemp),2):####计算并联中每一部分
                subtemp=subtemp+1
                ##########输出公式##############
                # print(circuittemp[t])
                Zexpress=expressZ(circuittemp[t])
                partsubname='Zpara'+str(ii+1)+'part'+str(num)+'sub'+str(subtemp)
                print(partsubname+'='+str(Zexpress))
                Zexpresspart.append(partsubname)###记录表达式
                ########输出公式#############
                
            # ########输出公式#############
            partname='Zpara'+str(ii+1)+'part'+str(num)+'=' +'+'.join(Zexpresspart) 
            print(partname)
            paraname='Zpara'+str(ii+1)+'part'+str(num)
            Zexpresspara.append(paraname)###记录表达式
            # ########输出公式#############
            
            Zexpresspart=list()###并联中子部分表达式
            circuittemp=list()
        elif circuitpara[tem3]=='p(':
            pass
            circuittemp=list()
    ####################计算并联电路中每一子部分阻抗的表达式 ####################

    ########输出并联公式#############
    Zexpressparatemp=list()
    for i in range(0,len(Zexpresspara)):
        Zexpressparatemp.append('1/'+Zexpresspara[i])
    Zexpresspara='Zpara'+str(ii+1)+'='+'1/('+'+'.join(Zexpressparatemp) +')'
    print(Zexpresspara)
    Zexpressname='Zpara'+str(ii+1) 
    ########输出并联公式#############


############更新电路##################
    templ=circuit[0:circuitLpos]
    tempr=circuit[circuitRpos+1:len(circuit)]
    newcircuit=templ+[Zexpressname]+tempr
  ############更新电路##################
    print('---------------------------------------------')

    return newcircuit

def expressSeriesECM(circuit):
    ZSexpressname=list() 
    subtemp=0
    for  t in range(0,len(circuit),2):   
        subtemp=subtemp+1
        ##########输出公式##############
        ZSexpresstemp=expressZ(circuit[t])
        seriesname='Z'+str(subtemp)
        print(seriesname+'='+str(ZSexpresstemp))
        ZSexpressname.append(seriesname)###记录表达式
        ########输出公式#############   
    partname='Ztotal'+'=' +'+'.join(ZSexpressname) 
    print(partname)
    return 
































