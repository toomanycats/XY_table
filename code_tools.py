import math
import smtplib
from email.mime.text import MIMEText
import numpy as np
from  getpass import getuser
import datetime

class ConfigureDataSet(object):
    def __init__(self):
        self.username = getuser() 
        self.date = datetime.datetime.now()   
        self.DirectoryName = None
        self.FileNamePrefix = None
        self.FreqStart = None
        self.FreqStop = None
        self.TestSet = 'S21' #transmition always for this experiment
        self.X_length = None
        self.Y_length = None
        self.X_res = None
        self.Y_res = None
        self.Origin = None
        '''Where the origin of the crystal is located '''
        self.Z_length = None
            
    def setup(self):
        #User chooses a folder particular to this data set.
        datasetname = raw_input("\nEnter a folder name for this data set:")
       
        self.DirectoryName = os.path.join("/media/Data/XY_table", datasetname)
        if not os.path.exists(self.DirectoryName):
             #make directory and set appropriate permissions.
             os.makedirs(self.DirectoryName)
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
        self.FreqStart = float(freqstart)
        self.FreqStop = float(freqstop)
        
        self.verify_continue()

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

    def get_fileowner(self):
        p = os.popen("ls -l " + self.fullpath + ".mat")
        fileowner = p.readline()
        p.close
        self.fileowner = fileowner[13:13 + len(usersname)]
        
    def _get_date(self):
        datestr = datetime.datetime.now()
        self.date_str = str(datestr)[0:19] #Cuts off the milliseconds for a simpler output.        

class CodeTools(object):
    '''Contains methods used for the combination of motor tools and vna tools '''    
    
    def _notify_admin_error(self, username, date, traceback):

        email_body = """
%(username)s
%(date)s

%(traceback)s
""" %{'username':username,'date':date,'traceback':traceback}

        # Create a text/plain message
        msg = MIMEText(email_body)

        # me == the sender's email address
        me = 'Man Lab Data Machine'
        # you == the recipient's email address
        recipients = ['wmanlab@gmail.com', 'dpcuneo@gmail.com','theebbandflow@yahoo.com']
        msg['Subject'] = 'Automatically generated email.'
        msg['From'] = "Dr. Man's Lab Linux Machine."
        msg['To'] = 'System Admin.'

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.starttls()
        s.login('wmanlab','debye100!')
        s.sendmail(me, recipients, msg.as_string())
        s.quit()

    def ToSI(self,d):
        if d == 0.0 or d == 0:
            return 0

        incPrefixes = ['k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        decPrefixes = ['mm', 'mu', 'n', 'p', 'f', 'a', 'z', 'y']

        degree = int(math.floor(math.log10(math.fabs(d)) / 3))
        
        prefix = ''

        if degree!=0:
            ds = degree/math.fabs(degree)
            if ds == 1:
                if degree - 1 < len(incPrefixes):
                    prefix = incPrefixes[degree - 1]
                else:
                    prefix = incPrefixes[-1]
                    degree = len(incPrefixes)
            elif ds == -1:
                if -degree - 1 < len(decPrefixes):
                    prefix = decPrefixes[-degree - 1]
                else:
                    prefix = decPrefixes[-1]
                    degree = -len(decPrefixes)

            scaled = float(d * math.pow(1000, -degree))
            s = "{scaled} {prefix}".format(scaled=scaled, prefix=prefix)

        else:
            s = "{d}".format(d=d)

        return(s)

class ArrayTools(object):
    def __init__(self):
        pass 

    def get_magnitude(self, data):
        self.trans_data = np.zeros(len_data)
        for i in range(0,len_data):
            trans_data[i] = np.sqrt(data[i,0]**2 + data[i,1]**2)

        return trans_data 

    def get_phase(self,data):
        self.phi = np.zeros(len_data)
        for i in range(0,len_data):
            phase_data[i] = np.angle(complex(data_mat[i, 0],data_mat[i, 1]))

        return phase_data
    
    def make_3d_array(self, x_len, y_len, x_res, y_res, num_z_pts):
        num_x_pts = int(np.ceil(x_len / x_res))
        num_y_pts = int(np.ceil(y_len / y_res))
        dim3_array = np.zeros((num_x_pts,num_y_pts), dtype=[('x_ind','i4'),('y_ind','i4'),('z_data','3c8')])
        
        for i in xrange(0,num_x_pts):
            dim3_array[i,:]['x_ind'] = np.arange(0,num_x_pts)
            
        for i in xrange(0,num_y_pts):
            dim3_array[:,i]['y_ind'] = np.arange(0,num_y_pts)
        
        return dim3_array

class PlotTools(object):
    def __init__(self):
        pass
    
    def _plot_data(self):
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
            
    def prompt_user_for_plot(self):
        plot_bool = raw_input("Do you wish to plot this data run? y/n: ")
        plot_bool = plot_bool.capitalize()
        if plot_bool == 'Y':
            self._plot_data() 
            
    def _set_plot_type(self):
        types = {'1':'logmag','2':'linmag','3':'phase'}
        for key in types.iterkeys():
            print "%(key)s  %(val)s" %{'key':key,'val':types[key]}
        
        choice = raw_input("Select the type of plot you want(num): ")
        
        try:
            self.plot_type = types[choice]
        finally:
            pass            
                