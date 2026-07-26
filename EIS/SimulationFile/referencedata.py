# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 17:54:39 2020

@author: zhan2
"""
import os, sys
import pandas as pd
import numpy as np


from random import randint
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *




class topRWidget(QWidget):

     def __init__(self, parent=None):
        super(topRWidget,self).__init__(parent)

        self.toplsublayout = QGridLayout()##定义布局
        self.inputdataGB = QGroupBox('Input Data',self)
        self.inputdataGB.setGeometry(0,0,480,150) #一定要有个东西把它撑起来
        self.inputdataGB.setLayout(self.toplsublayout)

        self.toplsublayout.setSpacing(10)
        self.inputdataBtn=QPushButton('Input Data')
        self.toplsublayout.addWidget(self.inputdataBtn, 0, 0)
        # self.inputdataBtn.clicked.connect(self.GetInputFiles)

        self.inputdataComboBox = QComboBox()
        self.toplsublayout.addWidget(self.inputdataComboBox, 0,1,1,3)

        self.openexfilebtn=QPushButton("Open File")
        self.toplsublayout.addWidget(self.openexfilebtn, 0, 4)
        # self.openexfilebtn.clicked.connect(self.OpenFiles)

        self.plotbtn=QPushButton("Plot Files")
        self.toplsublayout.addWidget(self.plotbtn, 1, 0)
        # self.plotbtn.clicked.connect(self.plotfiles)

        self.plotTextEdit= QLineEdit()
        self.toplsublayout.addWidget(self.plotTextEdit,1,1,1,3)

        self.allCheckBox = QCheckBox('Plot All', self)
        self.allCheckBox.toggle()####默认选中
        # self.allCheckBox.setChecked(True)
        self.toplsublayout.addWidget(self.allCheckBox,1, 4)
        # self.allCheckBox.stateChanged.connect(self.)

        self.ZRBtn=QRadioButton('f-Z,Phy,Rs,X')
        self.toplsublayout.addWidget(self.ZRBtn, 2, 0)

        self.ERBtn=QRadioButton('f-Epsilon,Sigma')
        self.toplsublayout.addWidget(self.ERBtn, 2, 1)

        self.TRBtn=QRadioButton('Time order')
        self.toplsublayout.addWidget(self.TRBtn, 2, 2)

        self.ORBtn=QRadioButton('Others')
        self.toplsublayout.addWidget(self.ORBtn, 2, 3)

        self.clearinputbtn=QPushButton("Clear Input")
        self.toplsublayout.addWidget(self.clearinputbtn, 2, 4)
        # self.clearinputbtn.clicked.connect(self.clearinput)

        # self.filesnamelist=[]