import gpib as g
import numpy as np
import time
import matplotlib.pyplot as mp
import scipy.io
import os
import sys
import traceback

class VnaTools(object):
    def __init__(self, Config):
        self.config = Config 
        self.freqstart = self.config.FreqStart
        self.freqstop =  self.config.FreqStop
        self._open_con()

    def _open_con(self):
        print "Opening connection to VNA \n Address of VNA (Should be 16!):"
        chan = g.find("VNA")
        print str(chan) + "\n"
        self.clear()   
        g.write(16,"FORM4")#set up ascii format           

    def clear(self):
        g.clear(16)
        time.sleep(0.2)
        
    def check_parameters(self):
        #Checks the parameter setting.
        g.write(16, "PARA?")
        param = g.read(16, 100)
        self.param = param.replace('\n','').replace('"','')
        if self.param == 'S12':
            self.ystr = "Transmission"
            print "You are taking TRANSMISSION(S12) data."
        elif self.param =='S11':
            self.ystr = "Reflection"
            print "You are taking REFLECTION(S11) data."
        elif self.param =='S21':
            self.ystr = "Transmission"
            print "You are taking TRANSMISSION(S21) data."
        elif self.param == 'S22':
            self.ystr = "Reflection"
            print "You are taking REFLECTION(S22) data."

    def turn_calibration_on(self):
        #Enable calibration. Usually done manually before running this prog.
        g.write(16,"CORRON")
        g.write(16,"CALS1")
                 
    def check_cal(self):
        #Checks the CAL setting.
        g.clear(16)
        time.sleep(.5)
        g.write(16,"CALS?")
        self.cals = g.read(16, 100)[0] #Takes only the first char in the string.
        if self.cals=='0':
             print "Calibration is OFF"
             self.calsstring = "no cal"
        else:
             print "You are under CAL set " + self.cals
             self.calsstring = "CAL" + self.cals

    def take_data(self):
        g.clear(16)
        time.sleep(.5)
        g.write(16,"SING")
          
        print "Waiting for data.\n"
        self.status_byte() 
        #Recieve data as a long ascii string.
        g.write(16,"OUTPDATA")
        raw_data = g.read(16,1000000)#read many bytes
        g.clear(16)
         
        #Parse string to create numerical data matrix.
        data = raw_data.replace("\n",",")
        data = np.fromstring(data,sep=",")
        print "Number of floats read: " + str(len(data)) + "\n"
        #Should help let the user know things worked properly.
       
        len_data = (len(data)) / 2 
        data_mat = np.zeros((len_data), dtype=complex)
    
        #Put data into a two column matrix. Also gets the magnitude and phase.
        for i in range(0,len_data):
            data_mat[i] = np.complex(data[2*i],data[2*i+1])
        
        return data_mat

    def status_byte(self):
         #Get the statusbyte and look at just the 5th bit to determine when sweep has finished
         singdone = False
         while singdone == False:
             hex_byte = g.rsp(16)
             hex_byte = "%r" %hex_byte
             hex_byte = hex_byte.replace("\\","0")
             hex_byte = hex_byte.replace("'","")
             stat_byte = bin(int(hex_byte,16))
             #output: '0b10001' when complete
             if len(stat_byte) >= 7:
                 singdone = True

    def _make_changes(self):
        manualchanges = raw_input("Do you want a break to change some settings manually? (y/n): ")
        if manualchanges == 'y':
            print "Wait a moment..."
            g.close(16)
            time.sleep(2)
            pausescript = raw_input("Okay. Press the LOCAL button and change any settings you want. Hit enter here when you're done.")
            #Reconnect and check the settings. ASSUMES FREQ RANGE IS UNCHANGED.
        self._open_con()

    def close(self):
        g.clear(16)
        g.close(16)
