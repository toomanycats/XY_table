import math
import smtplib
from email.mime.text import MIMEText
import numpy as np
from  getpass import getuser
import datetime
import numpy as np
from os import path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class ConfigureDataSet(object):
    def __init__(self):
        self.Username = getuser() 
        self.Date = datetime.datetime.now()   
        self.DirectoryName = ''
        self.FileNamePrefix = ''
        self.FreqStart = 0
        self.FreqStop = 0
        self.FreqRes = 0
        self.TestSet = 'S21' #transmition always for this experiment
        self.X_length = 0
        self.Y_length = 0
        self.X_res = 0
        self.Y_res = 0
        self.Origin = 0
        '''Where the origin of the crystal is located '''   
        self.Num_x_pts = 0
        self.Num_y_pts = 0

    def set_xy_num_pts(self):
        self.Num_x_pts = int(np.ceil(self.X_length / self.X_res))
        self.Num_y_pts = int(np.ceil(self.Y_length / self.Y_res))

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
        mag_data = np.zeros(data.shape[0], dtype=float)
        mag_data = np.abs(data)
        
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
    def __init__(self, Config):
        self.config = Config

    def plot_slice(self, slice):        
        num_x = int(np.floor(self.config.X_length/self.config.X_res))
        num_y = int(np.floor(self.config.Y_length/self.config.Y_res))
        
        x = np.linspace(0,self.config.X_length,num_x)
        y = np.linspace(0,self.config.Y_length, num_y)
        X,Y = np.meshgrid(x,y)
        
        im = plt.imshow(slice, interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
        plt.colorbar(im)   
        

    def redraw_plot(self,slice):
        plt.imshow(slice, interpolation='nearest', origin='lower', cmap = plt.cm.jet) 
             