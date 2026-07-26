# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 17:44:43 2020

@author: takeilab
"""

import sys

sys.path.append("..")


##############constant##############
eps0 = 8.854e-12  # F/m Vacuum permittivity
##############constant##############


def Db(pm, name, omega):
    epspart = pm["Deps" + name] / (1 + 1j * omega * pm["Tao" + name])
    return epspart


def CC(pm, name, omega):
    # epspart=pm['Deps'+name]/(1+(1j*omega*pm['Tao'+name])**(1-pm['Alpha'+name]))
    epspart = pm["Deps" + name] / (
        1 + (1j * omega * pm["Tao" + name]) ** (1 - pm["Alpha" + name])
    )

    return epspart


def DC(pm, name, omega):
    epspart = pm["Deps" + name] / (
        (1 + 1j * omega * pm["Tao" + name]) ** (pm["Beta" + name])
    )
    return epspart


def HN(pm, name, omega):
    epspart = pm["Deps" + name] / (
        (1 + (1j * omega * pm["Tao" + name]) ** (1 - pm["Alpha" + name]))
        ** pm["Beta" + name]
    )
    return epspart


def MT(pm, omega, modelterm, option):
    epstotal = 0
    for i in range(0, len(modelterm)):
        if modelterm[i]["modeltype"] == "Debye":
            epstotaltemp = Db(pm, modelterm[i]["name"], omega)
        elif modelterm[i]["modeltype"] == "Cole-Cole":
            epstotaltemp = CC(pm, modelterm[i]["name"], omega)
        elif modelterm[i]["modeltype"] == "Davidson-Cole":
            epstotaltemp = DC(pm, modelterm[i]["name"], omega)
        elif modelterm[i]["modeltype"] == "Havriliak-Negami":
            epstotaltemp = HN(pm, modelterm[i]["name"], omega)
        else:
            print("wrong")  # 输出到状态栏
            return
        epstotal = epstotaltemp + epstotal
    if option["DC Conductivity"] == 1:
        epsMT = epstotal + pm["epsh"] + pm["sigmaDC"] * 0.01 / (1j * omega * eps0)
    elif option["DC Conductivity"] == 0:
        epsMT = epstotal + pm["epsh"]
    sigmaMT = 1j * omega * epsMT * eps0
    return epsMT, sigmaMT


def EPMT(pm, omega, modelterm, option):

    epsMT, sigmaMT = MT(pm, omega, modelterm, option)
    # epsEPMT=epsMT/(1+epsMT*pm['A']*(1j*omega)**(1-pm['alphaCPE']))
    epsEPMT = epsMT / (
        1 + epsMT * 1e-5 * pm["A"] * (1j * omega) ** (1 - pm["alphaCPE"])
    )
    sigmaEPMT = 1j * omega * epsEPMT * eps0
    return epsEPMT, sigmaEPMT
