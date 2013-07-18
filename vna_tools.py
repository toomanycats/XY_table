import gpib as g
import time
import os
import sys
import numpy as np

class VnaTools(object):
    '''Library of methods to control an HP8510C Vector Network Analyzer. This module uses
    the ascii format for data transmission.'''
    def __init__(self,analyzer_name): 
        self._open_con(analyzer_name)
        '''The SFSU analyzer must be set to channel 16, which is set in the gpib PCI card config.'''

    def _open_con(self, analyzer_name):
        '''Open a connection to the VNA via gpib and confirm that the channel is correct. Subsequent calls
        will open GPIB on channels that increment by one. That is not OK since the GPIB bus on the HP8510C
        uses specific channels for talking to the test set and other components. The 'analyzer_name' argument, 
        is how the kernel knows which gpib interface you are refering to. That is setup with the linux_gpib config
        tool. For SFSU, that name is "VNA". '''
        
        print "Opening connection to analyzer \n"
        self.chan = g.find(analyzer_name)
        print "VNA channel is %s \n" %str(chan)
    
        self.check_for_errors()# head off synxtax errors and corrupted buffer
        g.write(self.chan,"FORM4")#set up ascii format    
        time.sleep(0.5)      
        self.check_remote_or_local()
        self.check_average_on()
        self.check_cal()
        self.check_parameters()
        
    def check_remote_or_local(self):    
        g.write(self.chan,"SYSB?")
        time.sleep(0.5)
        string = g.read(self.chan,50).strip("\n")
        print "\n *** VNA is in %s mode. *** \n" %string

    def clear(self, TIME = 0.5):
        '''Clear the VNA buffers. '''
        g.clear(self.chan)
        time.sleep(TIME)
        
    def check_parameters(self):
        '''Check and print the test, S21, S11, S12, S22. '''
        #Checks the parameter setting.
        g.write(self.chan, "PARA?")
        time.sleep(0.5)
        param = g.read(self.chan, 100)
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
        g.write(self.chan,"CORRON")
        self.clear()
        g.write(self.chan,"CALS1")
        self.clear()

    def check_average_on(self):
        #self.clear()
        g.write(self.chan,"AVER?")
        self.aver_state = g.read(self.chan,100)[0]
        if self.aver_state == '1':
            print "averaging is on. \n"
        elif self.aver_state == '0':
            print "averaging is off. \n"    
                 
    def check_cal(self):
        '''Checks the CAL setting.'''
        #self.clear()
        g.write(self.chan,"CALS?")
        time.sleep(0.5)
        self.cals = g.read(self.chan, 100)[0] 
        if self.cals=='0':
             print "Calibration is OFF"
             self.calsstring = "no calibration is being used."
        else:
             print "You are under CAL set " + self.cals
             self.calsstring = "CAL" + self.cals

    def average_on(self):
        g.write(self.chan,"AVERON")

    def take_single_point_data(self, freq):
        '''Take a single data point.'''
        self.check_for_errors()
        g.write(self.chan,"FREQ;SINP;CENT,%f" %freq)
        self.status_byte(2)
        data_mat = self._read_data()
        
        if data_mat[0] != data_mat[1]:
            raise Exception, """The VNA was not already set into single point mode.
I can tell b/c the VNA should return an array of data whose length is set to the number
of points on the menu, e.g. 801, but all values of the points should be the same. If you forgot to manually 
put the VNA into single point mode, then it will appear on the VNA screen to take a single point, but 
it is not clear that this is truly the case. I know it's annoying... """
        # one element of a np array is an np scalar and
        # causes problems with np.savetxt since that method wants
        # a array with shape != ()
        return data_mat[0]

    def take_sweep_data(self):
        '''Take a single sweep, wait for the sweep to finish, then record the data. '''
        self.check_for_errors()
        g.write(self.chan,"SING")
        print "Waiting for data.\n"
        
        self.status_byte(self.chan)
        self._print_and_clear_error()
        
        data_mat = self._read_data()
      
        return data_mat
 
    def _read_data(self, len_data = 1000000):
        #Recieve data as a long ascii string.
        g.write(self.chan,"OUTPDATA")
        print "Getting data from analyzer \n"
        time.sleep(0.5)
        raw_data = g.read(self.chan,len_data)#read many bytes
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
            hex = g.rsp(self.chan)
            time.sleep(0.25)
            hex = "%r" %hex # cast into raw string
            hex = hex.replace('\\','0').strip("'") 
            stat = int(hex,self.chan)
            #print 'status byte: ' + str(stat) + '\n'
            if stat >= code:
                singdone = True
                g.write(self.chan,"CLES")# clear the status byte for next read
                time.sleep(0.25)
        print "Sweep completed. \n"   

    def _make_changes(self):
        '''Prompt the user if they want to make a change on the VNA panel.'''
        manualchanges = raw_input("Do you want a break to change some settings manually? (y/n): ")
        if manualchanges == 'y':
            print "Wait a moment..."
            g.close(self.chan)
            time.sleep(2)
            pausescript = raw_input("Okay. Press the LOCAL button and change any settings you want. Hit enter here when you're done.")
            #Reconnect and check the settings. ASSUMES FREQ RANGE IS UNCHANGED.
        self._open_con()

    def close(self):
        '''Close the gpib connectin to the VNA. '''
        self.clear()
        g.close(self.chan)
        print "Vna connection closed \n"

    def _print_and_clear_error(self):
        '''Prints the error from the VNA and clears them. '''
        print "Clearing error from VNA. \n"
        g.write(self.chan,"OUTPERRO")
        error_msg = g.read(self.chan,1000)
        print error_msg + '\n'
            
    def check_for_errors(self):
        '''Check the status byte and if there's an error, print and clear it. '''
        g.write(self.chan,"OUTPSTAT")
        stat_bytes = g.read(self.chan,100)
        if stat_bytes[2] == '1':
            print "Error found in status byte, clearing now. \n"
            self._print_and_clear_error()        
        