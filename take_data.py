import gpib as g
import numpy as np
import time
import matplotlib.pyplot as mp
import scipy.io
import os
import datetime
import sys
import getpass

class TakeData:
    def __init__(self):
        self.username = getpass.getuser()
        self._open_con()
        
        self.AGAIN = True
        self.plot_type = 'logmag'
        self.plot_bool = False
        self._get_date()        
        self.PREVFILENAME = ''

    def _open_con(self):
        print "Opening connection to VNA \n Address of VNA (Should be 16!):"
        chan = g.find("VNA")
        print str(chan) + "\n"
        self.clear()   
        g.write(16,"FORM4")#set up ascii format           

    def clear(self):
        g.clear(16)
        time.sleep(0.5)

    def main(self):
        self.check_parameters()
        self.check_cal()
        self.setup()
        try:
            while self.AGAIN:
                self.record_data()
                self.prompt_user_for_plot()
                if self.plot_bool is True:
                    self.plot_data()
                self.save_data()
                self.prompt_user_for_another_run()
        finally:
            print "End of program.\n"

    def plot_data(self):
        self._set_plot_type()
        mp.ion() #Turns on interactive plot mode, which allows user to use the terminal without closing the plot.
        #Get time and date for the plot title.
        self.titlestr = self.directory + ".dat" + " " + self.calsstring + " " + self.param + " " + self.date_str
        mp.clf()
        mp.xlim( (self.freqstart, self.freqstop) )
        mp.xlabel("Frequency (GHz)")        

        if self.plot_type == 'logmag':
            print "Plotting logmag."
            #PLOT logaritmic transmission data. Labels graph with details of the data run.
            logT = np.log10(self.trans_data) * 10
            mp.plot(self.freq, logT)
            mp.title(self.titlestr)
            mp.ylabel(self.ystr + " (dB)")
   
        elif self.plot_type == 'linmag':
            print "Plotting linmag."
            #PLOT linear transmission data.
            mp.plot(self.freq, self.trans_data)
            mp.title(self.titlestr)
            mp.ylabel(self.ystr + " linear")
        
        elif self.plot_type == 'phase':
            print "Plotting phase."
            #PLOT phase data.
            mp.plot(self.freq, self.phi)
            mp.title(self.titlestr)
            mp.ylabel(self.ystr + " phase (radians)")
             
    def setup(self):
        #self.AGAIN='y'
        #self.DONTOVERWRITE='y'
        #self.PREVFILENAME="*example* DM_000"
 
        #User chooses a folder particular to this data set.
        self.datasetname = raw_input("\nEnter a folder name for this data set (eg. HPUS2TM0717): ")
       
        self.directory = os.path.join("/media/Data/", self.datasetname)
        if not os.path.exists(self.directory):
             #make directory and set appropriate permissions.
             os.makedirs(self.directory)
             #os.system('chown :gpib '+directory) ## S bit on group for /media/Data does this for us (2744)
             #os.system('chmod g+wx '+directory) ## allows group members to add to an existing data file made by another user and x is for cd-ing to it
        else:
             self.DONTOVERWRITE=raw_input("Folder name already exists! Are you sure you want to save files in this folder? Files could be overwritten? (y/n): ")
             if self.DONTOVERWRITE!='y':
                 print "Enter a new name for the folder \n"
                 self.setup()
                 #g.close(16)
                 #sys.exit("Goodbye")         
         
        #User must manually enter freq range
        freqstart = raw_input("Enter the start frequency (GHz): ")
        freqstop = raw_input("Enter the stop frequency (GHz): ")
        self.freqstart = float(freqstart)
        self.freqstop = float(freqstop)
        
        self.verify_continue()
 
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
                 
    def check_cal(self):
        #Enable calibration. Usually done manually before running this prog.
        #g.write(16,"CORRON")
        #g.write(16,"CALS1")
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
        if checksetup != 'y' and checksetup != 'n':
            print "\n %s: ***You did not enter a valid choice*** \n" %checksetup
            self.verify_continue()
        elif checksetup == 'n':
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
         
        self.data_mat = np.zeros((len_data,2))
        self.trans_data = np.zeros(len_data)
        self.phi = np.zeros(len_data)
        x_axis = range(0,len_data)
        Deltafreq = (self.freqstop - self.freqstart) / float(len_data)
        self.freq = np.arange(self.freqstart, self.freqstop, Deltafreq)
         
        #Put data into a two column matrix. Also gets the magnitude and phase.
        for i in range(0,len_data):
            self.data_mat[i,0] = data[2*i]
            self.data_mat[i,1] = data[2*i+1]
            self.trans_data[i] = self.data_mat[i,0]**2 + self.data_mat[i,1]**2
            self.phi[i] = np.angle(complex(self.data_mat[i, 0], self.data_mat[i, 1]))
        
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

    def save_data(self):
      
        print "Previous file name is: " + self.datasetname + '\n'
        self.filename = raw_input("Saving data. Enter file name: ")
        self.fullpath = os.path.join(self.directory,self.filename)
          
        if os.path.exists(self.fullpath + ".dat"):
            self.get_fileowner()
            if self.fileowner == self.usersname:
                overwrite = raw_input("Data file already exists! Are you sure you want to overwrite?! (y/n): ")
                if overwrite == 'y':
                    self._save_data()
                else:
                    self.save_data()
            else:
                print "This file already exists. You can not overwrite it because it belongs to a different user."
           
        self.PREVFILENAME = self.filename
 
    def _save_data(self):
       
        headerstr = """%(path)s %(cal)s %(param)s %(date)s
"""%{'path':self.fullpath + ".dat",'cal':self.calsstring,'param':self.param,'date':self.date_str}
        #save_ascii_data(mymatrix, headerstr, usersname, freqstart, freqstop, self.fullpath)
        freq_start = str(self.freqstart)
        freq_stop = str(self.freqstop)

        header_template = '''
%% %(headerstr)s
%% %(freq_start)s : %(freq_stop)s GHz
''' %{'headerstr':headerstr, 'freq_start':freq_start,'freq_stop':freq_stop}

        np.savetxt(self.fullpath + ".dat", self.data_mat)
        f = open(self.fullpath + ".dat",'r')
        matrixstr = f.read()
        f.close()
    
        f = open(self.fullpath + ".dat",'w')
        f.write(header_template + '\n\n' + matrixstr)
        f.close()

        scipy.io.savemat(self.fullpath,mdict={self.filename : self.data_mat}) 
    
        #Set correct permissions on the new file.
        #os.system('chown :gpib '+self.fullpath+".mat") S bit set this for all files in /media/Data
        os.system('chmod g-w ' + self.fullpath + ".dat") # removes the write bit, so that group members other than the creater cannot
        os.system('chmod g-w ' + self.fullpath + ".mat") # removes the write bit, so that group members other than the creater cannot
	                                        # delete a file made by another gpib member. They must re name it.
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
    
    def get_fileowner(self):
        p = os.popen("ls -l " + self.fullpath + ".mat")
        fileowner = p.readline()
        p.close
        self.fileowner = fileowner[13:13 + len(usersname)]
        
    def _get_date(self):
        datestr = datetime.datetime.now()
        self.date_str = str(datestr)[0:19] #Cuts off the milliseconds for a simpler output.
        
    def prompt_user_for_plot(self):
        plot_bool = raw_input("Do you wish to plot this data run? y/n: ")
        plot_bool = plot_bool.capitalize()
        if plot_bool == 'Y':
            self.plot_bool = True
        else:
            self.plot_bool = False
            
    def _set_plot_type(self):
        types = {'1':'logmag','2':'linmag','3':'phase'}
        for key in types.iterkeys():
            print "%(key)s  %(val)s" %{'key':key,'val':types[key]}
        
        choice = raw_input("Select the type of plot you want(num): ")
        
        try:
            self.plot_type = types[choice]
        finally:
            pass

    def prompt_user_for_another_run(self):
        run_again = raw_input("Do you want to take another run? y/n")
        if run_again.capitalize() == 'Y':
            self.AGAIN = True
            self._make_changes()
        else:
            self.AGAIN = False 
