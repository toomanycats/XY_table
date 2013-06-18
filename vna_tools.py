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
        time.sleep(0.5)
        
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

    def record_data(self):
        #The following loop is repeated for every single data run.
        #while (self.self.AGAIN=='y'):
        #Makes the setup take a single sweep of data.
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
       
        len_data = (len(data)) / 2 #This is how we figure out the number of freq pts.
         
        self.data_mat = np.zeros((len_data,2), dtype=complex)
        #self.trans_data = np.zeros(len_data)
        #self.phi = np.zeros(len_data)
        x_axis = range(0,len_data)
        Deltafreq = (self.freqstop - self.freqstart) / float(len_data)
        self.freq = np.arange(self.freqstart, self.freqstop, Deltafreq)
         
        #Put data into a two column matrix. Also gets the magnitude and phase.
        for i in range(0,len_data):
            #self.data_mat[i,0] = data[2*i]
            #self.data_mat[i,1] = data[2*i+1]
            self.data_mat[i] = np.complex(data[2*i],data[2*i+1])
#           self.trans_data[i] = np.sqrt(self.data_mat[i,0]**2 + self.data_mat[i,1]**2)
#           self.phi[i] = np.angle(complex(self.data_mat[i, 0], self.data_mat[i, 1]))
        
        proc = os.popen("mplayer -really-quiet chime.wav > /dev/null 2>&1")
        proc.close()
        
    def status_byte(self):
         self.clear()
         #Get the statusbyte and look at just the 5th bit to determine when sweep has finished
         singdone = 0
         while singdone == 0:
             time.sleep(0.5)
             hex_byte = g.rsp(16)
             hex_byte = "%r" %hex_byte
             hex_byte = hex_byte.replace("\\","0")
             hex_byte = hex_byte.replace("'","")
             stat_byte = bin(int(hex_byte,16))
             #output: '0b10001' when complete
             if len(stat_byte) >= 7:
                 singdone = stat_byte[2]

    def save_data(self, data_point):      
        file = self.config.FileNamePrefix + '_' + str(data_point) + '.dat'
        fullpath = os.path.join(self.config.DirectoryName, file)
        np.savetxt(fullpath, self.data_mat)
          
#         headerstr = """%(path)s %(cal)s %(param)s %(date)s
# """%{'path':self.fullpath + ".dat",'cal':self.calsstring,'param':self.param,'date':self.date_str}
#         #save_ascii_data(mymatrix, headerstr, usersname, freqstart, freqstop, self.fullpath)
#         freq_start = str(self.freqstart)
#         freq_stop = str(self.freqstop)
# 
#         header_template = '''
# %% %(headerstr)s
# %% %(freq_start)s : %(freq_stop)s GHz
# ''' %{'headerstr':headerstr, 'freq_start':freq_start,'freq_stop':freq_stop}

#         np.savetxt(fullpath + ".dat", self.data_mat)
#         f = open(self.fullpath + ".dat",'r')
#         matrixstr = f.read()
#         f.close()
#     
#         f = open(self.fullpath + ".dat",'w')
#         f.write(header_template + '\n\n' + matrixstr)
#         f.close()

#        scipy.io.savemat(self.fullpath,mdict={self.filename : self.data_mat}) 
    
        print "File Saved Successfully."

    def _make_changes(self):
        manualchanges = raw_input("Do you want a break to change some settings manually? (y/n): ")
        if manualchanges == 'y':
            print "Wait a moment..."
            g.close(16)
            time.sleep(2)
            pausescript = raw_input("Okay. Press the LOCAL button and change any settings you want. Hit enter here when you're done.")
            #Reconnect and check the settings. ASSUMES FREQ RANGE IS UNCHANGED.
        self._open_con()

    def prompt_user_for_another_run(self):
        run_again = raw_input("Do you want to take another run? y/n")
        if run_again.capitalize() == 'Y':
            self.AGAIN = True
            self._make_changes()
        else:
            self.AGAIN = False 

