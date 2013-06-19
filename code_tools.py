import math
import smtplib
from email.mime.text import MIMEText
import numpy as np
from  getpass import getuser
import datetime
import numpy as np
from os import path

class ConfigureDataSet(object):
    def __init__(self):
        self.Username = getuser() 
        self.Date = datetime.datetime.now()   
        self.DirectoryName = None
        self.FileNamePrefix = None
        self.FreqStart = None
        self.FreqStop = None
        self.FreqRes = None
        self.TestSet = 'S21' #transmition always for this experiment
        self.X_length = None
        self.Y_length = None
        self.X_res = None
        self.Y_res = None
        self.Origin = None
        '''Where the origin of the crystal is located '''   
        self.Num_x_pts = None
        self.Num_y_pts = None
        
        self._get_xy_res()

    def _get_xy_res(self):
        self.Num_x_pts = int(np.ceil(self.X_length / self.X_res))
        self.Num_y_pts = int(np.ceil(self.Y_length / self.Y_res))

       return (num_x_pts, num_y_pts)

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
    def __init__(self, Config):
        self.config = Config
  
    def save_readme(self):
        header_template = '''
Directory = %(path)s
FreqStart = %(freq_start)s
FreqStop =  %(freq_stop)s
FreqRes = %(freq_res)s
X_length = %(x_len)s
X_res = %(x_res)s
Y_length = %(y_len)s
Y_res = %(y_res)s
Username = %(user)s
Date = %(date)s
Origin = %(origin)s
 ''' %{'path':self.config.DirectoryName,'freq_start':self.config.FreqStart,'freq_stop':self.config.FreqStop,
       'freq_res':self.config.FreqRes,'x_len':self.config.X_length,'y_len':self.config.Y_length,
       'x_res':self.config.X_res,'y_res':self.config.Y_res,'user':self.config.Username,
       'date':self.config.Date,'origin':self.config.Date}

        fullpath = path.join(self.config.DirectoryName, self.config.FileNamePrefix + '_README.dat')
        f = open(fullpath,'w')
        f.write(header_template)
        f.close()

    def save_data(self, data_point, data):      
        file = self.config.FileNamePrefix + '_' + str(data_point).zfill(6) + '.dat'
        fullpath = path.join(self.config.DirectoryName, file)
        np.savetxt(fullpath, data)
          
        print "File Saved Successfully."

    def get_magnitude(self, data):
        mag_data = np.zeros(data.shape[0])
        mag_data = np.sqrt(data[:,0]**2 + data[:,1]**2)
        #for i in range(0,len(data)):
        #    mag_data[i] = np.sqrt(data[i,0]**2 + data[i,1]**2)

        return mag_data 

    def get_phase(self,data):
        phase_data = np.zeros(data.shape[0])
        phase_data = np.angle(data_mat[:, 0],data_mat[:, 1])
#         for i in range(0,len(data)):
#             phase_data[i] = np.angle(complex(data_mat[i, 0],data_mat[i, 1]))

        return phase_data
   
    def make_freq_vector(self):
        Deltafreq = (self.config.freqstop - self.config.freqstart) / float(self.config.FreqRes)
        freq_vec = np.arange(self.config.FreqStart, self.config.FreqStop, Deltafreq)

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
                