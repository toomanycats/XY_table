import gpib as g
import numpy as np
import time
import matplotlib.pyplot as mp
import scipy.io
import os
import datetime
import sys
import getpass

class takeData:
    def __init__(self):
        pass

    def main(self):
        self.setup()
        self.record_data()
        self.plot_data()
        self.save_data()

    def plot_data(self):
        mp.ion() #Turns on interactive plot mode, which allows user to use the terminal without closing the plot.
        #Get time and date for the plot title.
        self.AGAIN = 'logmag'
        self.titlestr = self.fullpath + ".dat" + "  " + self.calsstring + "  " + self.param + "  " + datestrsimp
        while True:
            if self.AGAIN == 'logmag':
                print "Plotting logmag."
                #PLOT logaritmic transmission data. Labels graph with details of the data run.
                logT = np.log10(self.trans_data) * 10
                mp.clf()
                mp.plot(self.freq, logT)
                mp.title(self.titlestr)
                mp.xlim( (self.freqstart, freqstop) )
                mp.xlabel("Frequency (GHz)")
                mp.ylabel(ystr + " (dB)")
                # xy=(x[5],logT[5])
                # mp.annotate("Fix this point?",xy)
            elif self.AGAIN == 'linmag':
                print "Plotting linmag."
                #PLOT linear transmission data.
                mp.clf()
                mp.plot(self.freq, self.trans_data)
                mp.title(self.titlestr)
                mp.xlim( (self.freqstart, freqstop) )
                mp.xlabel("Frequency (GHz)")
                mp.ylabel(ystr  + " linear")
            elif self.AGAIN == 'phase':
                print "Plotting phase."
                #PLOT phase data.
                mp.clf()
                mp.plot(self.freq, self.phi)
                mp.title(self.titlestr)
                mp.xlim( (self.freqstart, freqstop) )
                mp.xlabel("Frequency (GHz)")
                mp.ylabel(ystr+" phase (radians)")
            elif self.AGAIN == 'y' or self.AGAIN == 'n':
                break
            else:
                print "Ur doing it wrong."
             
    def setup(self):
        self.AGAIN='y'
        self.DONTOVERWRITE='y'
        self.PREVFILENAME="*example* DM_000"
    
        #Gets the name of the current user for later use.
        #p=os.popen("whoami")
        #usersname=p.readline()
        #p.close
        #usersname=usersname[0:len(usersname)-1]
        self.username = getpass.getuser()

        print "Address of VNA (Should be 16!):"
        print g.find("VNA")
    
        g.clear(16)
        time.sleep(.5)

        #Enable calibration. Usually done manually before running this prog.
        #g.write(16,"CORRON")
        #g.write(16,"CALS1")
        #set format of data output to ascii. Affects only OUTPDATA, not queries.
        g.write(16,"FORM4")
        #User chooses a folder particular to this data set.
        datasetname = raw_input("\nEnter a folder name for this data set (eg. HPUS2TM0717): ")
        directory = os.path.join("/media/Data/", datasetname)
        if not os.path.exists(directory):
             #make directory and set appropriate permissions.
             os.makedirs(directory)
             #os.system('chown :gpib '+directory) ## S bit on group for /media/Data does this for us (2744)
             #os.system('chmod g+wx '+directory) ## allows group members to add to an existing data file made by another user and x is for cd-ing to it
        else:
             self.DONTOVERWRITE=raw_input("Folder name already exists! Are you sure you want to save files in this folder? Files could be overwritten? (y/n): ")
             if self.DONTOVERWRITE!='y':
                 g.close(16)
                 sys.exit("Goodbye")
                 
        #User must manually enter freq range
        freqstart = raw_input("Enter the start frequency (GHz): ")
        freqstop = raw_input("Enter the stop frequency (GHz): ")
        self.freqstart = float(freqstart)
        self.freqstop = float(freqstop) 
        
        self.verify_continue()
 
    def check_parameters(self):
        #Checks the parameter setting.
            g.write(16, "PARA?")
            self.param = g.read(16, 100)
            if self.param == '"S12"\n':
                 ystr = "Transmission"
                 print "You are taking TRANSMISSION(S12) data."
            elif self.param =='"S11"\n':
                 ystr = "Reflection"
                 print "You are taking REFLECTION(S11) data."
            elif self.param =='"S21"\n':
                 ystr = "Transmission"
                 print "You are taking TRANSMISSION(S21) data."
            elif self.param == '"S22"\n':
                 ystr="Reflection"
                 print "You are taking REFLECTION(S22) data."
                 
    def check_CAL(self):
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

    def verify_continue(self):
        #Verify settings with user before continuing.
        checksetup = raw_input("Are you sure you want to continue with these settings?(y/n): ")
        if checksetup is not 'y' or checksetup is not 'n':
            print "\n ***You did not enter a valid choice*** \n"
            self.verify_continue()
        elif checksetup == 'n'    
            g.close(16)
            sys.exit("Goodbye")
        elif checksetup == 'y':
            print "Settings verified and continuing with Take Data."

    def record_data(self):
        #The following loop is repeated for every single data run.
        #while (self.self.AGAIN=='y'):
        #Makes the setup take a single sweep of data.
        g.clear(16)
        time.sleep(.5)
        g.write(16,"SING") 
             
        print "Waiting for data."
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
       
        self.len_data = (len(data)) / 2 #This is how we figure out the number of freq pts.
         
        self.data_mat = np.zeros((len_data,2))
        self.trans_data = np.zeros(len_data)
        self.phi = np.zeros(len_data)
        x_axis = range(0,len_data)
        Deltafreq = (self.freqstop - self.freqstart) / float(len_data)
        self.freq  = np.arange(self.freqstart, self.freqstop, Deltafreq)
         
        #Put data into a two column matrix. Also gets the magnitude and phase.
        for i in range(0,len_data):
            self.data_mat[i,0] = data[2*i]
            self.data_mat[i,1] = data[2*i+1]
            self.trans_data[i] = self.data_mat[i,0]**2 + self.data_mat[i,1]**2
            self.phi[i] = np.angle(complex(self.data_mat[i, 0], self.data_mat[i, 1]))e
        
        proc = os.popen("mplayer -really-quiet chime.wav  > /dev/null 2>&1") 
        proc.close() 
        
    def status_byte(self): 
         #Get the statusbyte and look at just the 5th bit to determine when sweep has finished
         singdone = 0
         while singdone is not 1:
             time.sleep(0.5)
             hex_byte = g.rsp(16)
             hex_byte = "%r" %hex_byte
             hex_byte = hex_byte.replace("\\","0")
             hex_byte = hex_byte.replace("'","")
             stat_byte = bin(int(hex_byte,16))
             #output: '0b10001'
             singdone = stat_byte[len(stat_byte)-5]

    def save_data(self):
        #Save data with specified filename. Also prevents accidental overwrites of files.
        savedone = False
        while savedone is not True:
        #save data using specified filename
        print "Previous file name: " + self.PREVFILENAME
        self.filename = raw_input("Saving data. Enter file name: ")
        self.fullpath = os.path.join(directory,self.filename)
              
        if os.path.exists(self.fullpath + ".mat"):
            self.get_fileowner()
            if self.fileowner == usersname:
                overwritefile = raw_input("Data file already exists! Are you sure you want to overwrite?! (y/n): ")
            elif:
                print "This file already exists. You can not overwrite it because it belongs to a different user."
                overwritefile = 'n'
            elif:
                overwritefile = 'y'

            if overwritefile == 'y':
                self.PREVFILENAME = self.filename
                datestr = datetime.datetime.now()
                datestrsimp = str(datestr)[0:19] #Cuts off the milliseconds for a simpler output.
                headerstr = self.fullpath + ".dat" + "  " + self.calsstring + "  " + self.param.replace('\n','') + "  " + datestrsimp
                #save_ascii_data(mymatrix, headerstr, usersname, freqstart, freqstop, self.fullpath)
                freq_start = str(self.freqstart) 
                freq_stop = str(self.freqstop)

                header_template = '''
%% %(headerstr)s 
%% %(freq_start)s : %(freq_stop)s GHz
'''  %{'headerstr':headerstr, 'freq_start':freq_start,'freq_stop':freq_stop}	

                np.savetxt(self.fullpath + ".dat", self.data_mat) 
                fn = open(self.fullpath + ".dat",'r')
                matrixstr = fn.read()
                fn.close()
                fn = open(os.path.join(self.fullpath,".dat"),'w')
                fn.write(header_template + '\n\n' + matrixstr)
                fn.close()

                scipy.io.savemat(self.fullpath,mdict={self.filename :  self.data_mat}) #files are named as the rotation angle of sweep
                savedone = True
                #Set correct permissions on the new file.
                #os.system('chown :gpib '+self.fullpath+".mat")  S bit set this for all files in /media/Data
                os.system('chmod g-w '+self.fullpath+".dat") # removes the write bit, so that group members other than the creater cannot
                os.system('chmod g-w '+self.fullpath+".mat") # removes the write bit, so that group members other than the creater cannot
                                                     # delete a file made by another gpib member. They must re name it. 
                print "File Saved Successfully."
 
                #repeat the process for a new data sweep?
        self.AGAIN=raw_input("Take another run? See another plot? (y/n/linmag/logmag/phase) ")
        if self.AGAIN == 'y':
            self.record_data()
        
    def run_again(self):
        if self.AGAIN ==' y':
            manualchanges = raw_input("Do you want a break to change some settings manually? (y/n): ")
            if manualchanges == 'y':
                print "Wait a moment..."
                g.close(16)
                time.sleep(2)
                pausescript = raw_input("Okay. Press the LOCAL button and change any settings you want. Hit enter here when you're done.")
                #Reconnect and check the settings. ASSUMES FREQ RANGE IS UNCHANGED.
                self.check_parameters()
        self.check_CAL()        
    def get_fileowner(self):
        p = os.popen("ls -l " + self.fullpath + ".mat")
        fileowner = p.readline()
        p.close
        self.fileowner = fileowner[13:13 + len(usersname)]
        