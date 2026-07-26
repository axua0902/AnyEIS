class FilterMethodUIs:
    def __init__(self, parent):
        self.parent = parent

    def uiSavgol(self):
        self.parent.filterp1LineEdit.setText('a:')
        self.parent.filterp1TextEdit.setText('17')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setText('b:')
        self.parent.filterp2TextEdit.setText('1')
        self.parent.filterp2LineEdit.setVisible(True)
        self.parent.filterp2TextEdit.setVisible(True)
        
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)



    def uiMedian(self):
        self.parent.filterp1LineEdit.setText('kernel_size:')
        self.parent.filterp1TextEdit.setText('5')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiWiener(self):
        self.parent.filterp1LineEdit.setText('noise:')
        self.parent.filterp1TextEdit.setText('')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiButterworth(self):
        self.parent.filterp1LineEdit.setText('order:')
        self.parent.filterp1TextEdit.setText('4')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setText('cutoff:')
        self.parent.filterp2TextEdit.setText('0.1')
        self.parent.filterp2LineEdit.setVisible(True)
        self.parent.filterp2TextEdit.setVisible(True)
        
        self.parent.filterp3LineEdit.setText('filter_type:')
        self.parent.filterp3TextEdit.setText('filtfilt')
        self.parent.filterp3LineEdit.setVisible(True)
        self.parent.filterp3TextEdit.setVisible(True)
        
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiCspline(self):
        self.parent.filterp1LineEdit.setText('lamb:')
        self.parent.filterp1TextEdit.setText('0.1')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiArithmeticAverage(self):
        self.parent.filterp1LineEdit.setText('window_size:')
        self.parent.filterp1TextEdit.setText('5')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiSlidingAverage(self):
        self.parent.filterp1LineEdit.setText('window_size:')
        self.parent.filterp1TextEdit.setText('5')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiMedianAverage(self):
        self.parent.filterp1LineEdit.setText('window_size:')
        self.parent.filterp1TextEdit.setText('5')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiAmplitudeLimitingAverage(self):
        self.parent.filterp1LineEdit.setText('window_size:')
        self.parent.filterp1TextEdit.setText('5')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setText('amplitude_limit:')
        self.parent.filterp2TextEdit.setText('1.0')
        self.parent.filterp2LineEdit.setVisible(True)
        self.parent.filterp2TextEdit.setVisible(True)
        
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiFirstOrderLag(self):
        self.parent.filterp1LineEdit.setText('alpha:')
        self.parent.filterp1TextEdit.setText('0.1')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiWeightedAverage(self):
        self.parent.filterp1LineEdit.setText('window_size:')
        self.parent.filterp1TextEdit.setText('5')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiShakeOff(self):
        self.parent.filterp1LineEdit.setText('threshold_count:')
        self.parent.filterp1TextEdit.setText('3')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiAmplitudeLimitingShakeOff(self):
        self.parent.filterp1LineEdit.setText('amplitude_limit:')
        self.parent.filterp1TextEdit.setText('1.0')
        self.parent.filterp1LineEdit.setVisible(True)
        self.parent.filterp1TextEdit.setVisible(True)
        
        self.parent.filterp2LineEdit.setText('threshold_count:')
        self.parent.filterp2TextEdit.setText('3')
        self.parent.filterp2LineEdit.setVisible(True)
        self.parent.filterp2TextEdit.setVisible(True)
        
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

    def uiother(self):
        self.parent.filterp1LineEdit.setVisible(False)
        self.parent.filterp1TextEdit.setVisible(False)
        self.parent.filterp2LineEdit.setVisible(False)
        self.parent.filterp2TextEdit.setVisible(False)
        self.parent.filterp3LineEdit.setVisible(False)
        self.parent.filterp3TextEdit.setVisible(False)
        self.parent.filterp4LineEdit.setVisible(False)
        self.parent.filterp4TextEdit.setVisible(False)

        self.parent.filterp1LineEdit.setText('P1:')
        self.parent.filterp1TextEdit.setText('')
        self.parent.filterp2LineEdit.setText('P2:')
        self.parent.filterp2TextEdit.setText('')
        self.parent.filterp3LineEdit.setText('P3:')
        self.parent.filterp3TextEdit.setText('')
        self.parent.filterp4LineEdit.setText('P4:')
        self.parent.filterp4TextEdit.setText('')