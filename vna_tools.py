import gpib as g
import time
import os
import sys
import numpy as np

class VnaTools(object):
    '''Library of methods to control an HP8510C Vector Network Analyzer. '''
    def __init__(self, Config):
        self.config = Config 
        self.freqstart = self.config.FreqStart
        self.freqstop =  self.config.FreqStop
        self._open_con()

    def _open_con(self):
        '''Open a connectino to the VNA via gpib and confirm that the channel is 16. '''
        print "Opening connection to VNA \n Address of VNA (Should be 16!):"
        chan = g.find("VNA")
        print str(chan) + "\n"
        self.check_for_errors()# head off synxtax errors and corrupted buffer
        g.write(16,"FORM4")#set up ascii format    
        time.sleep(0.5)      
        self.check_remote_or_local()
        self.check_average_on()
        self.check_cal()
        self.check_parameters()
        
    def check_remote_or_local(self):    
        g.write(16,"SYSB?")
        time.sleep(0.5)
        string = g.read(16,50).strip("\n")
        print "\n *** VNA is in %s mode. *** \n" %string

    def clear(self, TIME = 0.5):
        '''Clear the VNA buffers. '''
        g.clear(16)
        time.sleep(TIME)
        
    def check_parameters(self):
        '''Check and print the test, S21, S11, S12, S22. '''
        #Checks the parameter setting.
        g.write(16, "PARA?")
        time.sleep(0.5)
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
        '''Enable calibration. Usually done manually before running this prog.'''
        g.write(16,"CORRON")
        self.clear()
        g.write(16,"CALS1")
        self.clear()

    def check_average_on(self):
        #self.clear()
        g.write(16,"AVER?")
        self.aver_state = g.read(16,100)[0]
        if self.aver_state == '1':
            print "averaging is on. \n"
        elif self.aver_state == '0':
            print "averaging is off. \n"    
                 
    def check_cal(self):
        '''Checks the CAL setting.'''
        #self.clear()
        g.write(16,"CALS?")
        time.sleep(0.5)
        self.cals = g.read(16, 100)[0] 
        if self.cals=='0':
             print "Calibration is OFF"
             self.calsstring = "no calibration is being used."
        else:
             print "You are under CAL set " + self.cals
             self.calsstring = "CAL" + self.cals

    def average_on(self):
        g.write(16,"AVERON")

    def take_single_point_data(self, freq):
        '''Take a single data point.'''
        self.check_for_errors()
        g.write(16,"FREQ;SINP;CENT,%f" %freq)
        self.status_byte(2)
        data_mat = self._read_data()
        # one element of a np array is an np scalar and
        # causes problems with np.savetxt since that method wants
        # a array with shape != ()
        return data_mat[0]

    def take_sweep_data(self):
        '''Take a single sweep, wait for the sweep to finish, then record the data. '''
        self.check_for_errors()
        g.write(16,"SING")
        print "Waiting for data.\n"
        
        self.status_byte(16)
        self._print_and_clear_error()
        
        data_mat = self._read_data()
      
        return data_mat
 
    def _read_data(self, len_data = 1000000):
        #Recieve data as a long ascii string.
        g.write(16,"OUTPDATA")
        print "Getting data from analyzer \n"
        time.sleep(0.5)
        raw_data = g.read(16,len_data)#read many bytes
        #Parse string to create numerical data matrix.
        data = raw_data.replace("\n",",")
        data = np.fromstring(data,sep=",")
        print "Number of floats read: " + str(len(data)) + "\n"
        #Should help let the user know things worked properly.
       
        len_data = (len(data)) / 2 
        data_mat = np.zeros((len_data), dtype=complex)
    
        #Put data into a two column matrix. 
        data_mat.real = data[1::2]
        data_mat.imag = data[::2]
        
        return data_mat

    def status_byte(self, code):
        '''Read the status byte of the VNA and check for the completion of the 
           single sweep. '''         
        singdone = False
        while singdone == False:
            time.sleep(0.25)
            hex = g.rsp(16)
            time.sleep(0.25)
            hex = "%r" %hex # cast into raw string
            hex = hex.replace('\\','0').strip("'") 
            stat = int(hex,16)
            #print 'status byte: ' + str(stat) + '\n'
            if stat >= code:
                singdone = True
                g.write(16,"CLES")# clear the status byte for next read
                time.sleep(0.25)
        print "Sweep completed. \n"   

    def _make_changes(self):
        '''Prompt the user if they want to make a change on the VNA panel.'''
        manualchanges = raw_input("Do you want a break to change some settings manually? (y/n): ")
        if manualchanges == 'y':
            print "Wait a moment..."
            g.close(16)
            time.sleep(2)
            pausescript = raw_input("Okay. Press the LOCAL button and change any settings you want. Hit enter here when you're done.")
            #Reconnect and check the settings. ASSUMES FREQ RANGE IS UNCHANGED.
        self._open_con()

    def close(self):
        '''Close the gpib connectin to the VNA. '''
        self.clear()
        g.close(16)
        print "Vna connection closed \n"

    def _print_and_clear_error(self):
        '''Prints the error from the VNA and clears them. '''
        print "Clearing error from VNA. \n"
        g.write(16,"OUTPERRO")
        error_msg = g.read(16,1000)
        print error_msg + '\n'
            
    def check_for_errors(self):
        '''Check the status byte and if there's an error, print and clear it. '''
        g.write(16,"OUTPSTAT")
        stat_bytes = g.read(16,100)
        if stat_bytes[2] == '1':
            print "Error found in status byte, clearing now. \n"
            self._print_and_clear_error()        
        