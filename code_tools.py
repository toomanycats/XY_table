import math
import smtplib
from email.mime.text import MIMEText
import numpy as np
from  getpass import getuser
import datetime
import numpy as np
from os import path,makedirs
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.io as sio

class ConfigureDataSet(object):
    def __init__(self):
        self.Username = getuser() 
        self.Date = datetime.datetime.now()   
        self.DirectoryRoot = '/media/Data'
        self.ExperimentDir = ''
        self.FileNamePrefix = ''
        self.mode = ''
        self.SingleFrequency = 0
        self.FreqStart = 0
        self.FreqStop = 0
        self.Freq_num_pts = 0
        self.TestSet = 'S21' #transmission always for this experiment
        self.X_length = 0
        self.Y_length = 0
        self.X_res = 0
        self.Y_res = 0
        self.X_origin = 0
        self.Y_origin = 0
        '''Where the origin of the crystal is located '''   
        self.Num_x_pts = 0
        self.Num_y_pts = 0
        self.x_port = ''
        self.y_port = ''
        self.real_point_dir = ''
        self.imag_point_dir = ''
        
    def make_sub_dirs(self):
        p = path.join(self.DirectoryRoot,self.ExperimentDir)
        if not path.exists(p):
            makedirs(p)
        
        self.real_point_dir = path.join(self.DirectoryRoot,self.ExperimentDir,'Single_Point','Real')
        if not path.exists(self.real_point_dir):
            makedirs(self.real_point_dir)

        self.imag_point_dir = path.join(self.DirectoryRoot,self.ExperimentDir,'Single_Point','Imag')
        if not path.exists(self.imag_point_dir):
            makedirs(self.imag_point_dir)  
        
    def set_xy_num_pts(self):
        self.Num_x_pts = int(np.ceil(self.X_length / self.X_res))
        self.Num_y_pts = int(np.ceil(self.Y_length / self.Y_res))

    def get_config_from_user(self): 
        '''Have the user fill out config values interactively. ''' 
        
        self.mode = raw_input("Enter the mode 'sweep' or 'single':")
        self.ExperimentDir = raw_input("Enter the name of the directotry to hold this experiment: ")
        self.FileNamePrefix = raw_input("ENter the prefix for the files that will be saved: ")
        
        if self.mode == 'sweep':
            self.FreqStart = float(raw_input("Enter the start freq of the sweep i.e., 3e9 or 10e9: "))
            self.FreqStop = float(raw_input("Enter the stop freq: "))
        elif self.mode == 'single':
             self.SingleFrequency = float(raw_input("Enter the single freq, i.e., 12e9: ")) # single freq mode
        else:
            raise Exception, "Not a valid choice, 'sweep' or 'single' only."
            
        if self.mode == 'single':
            self.Freq_num_pts = 1
        else:
            self.Freq_num_pts = int(raw_input("Enter the number of points that the analyzer is set to take: "))
    
        self.X_length = float(raw_input("Enter the length of the sample along X in meters: "))
        self.Y_length = float(raw_input("Enter the length of the sample along Y in meters: "))
        self.X_res = float(raw_input("Enter the distance between X data points in meters: "))
        self.Y_res = float(raw_input("Enter the distance between Y data points in meters: "))
        if self.X_res >= self.X_length or self.Y_res >= self.Y_length:
            raise Exception, "X,Y resolution cannot be greater or equal to the X length."

        ### static config entries
        self.TestSet = 'S21' # transmission always for this experiment
        self.set_xy_num_pts()
        self.make_sub_dirs()

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
        '''Savess a text file named "README" in the experiment roor directory that 
        contains the vitals of the settings. Parse this file for import info. '''
        header_template = '''
Directory = %(path)s
FreqStart = %(freq_start)s
FreqStop =  %(freq_stop)s
Freq_num_pts = %(freq_res)s
X_length = %(x_len)s
X_res = %(x_res)s
Y_length = %(y_len)s
Y_res = %(y_res)s
Username = %(user)s
Date = %(date)s
X Origin = %(x_origin)s
Y Origin = %(y_origin)s
 ''' %{'path':path.join(self.config.DirectoryRoot,self.config.ExperimentDir),
       'freq_start':self.config.FreqStart,
       'freq_stop':self.config.FreqStop,
       'freq_res':self.config.Freq_num_pts,
       'x_len':self.config.X_length,
       'y_len':self.config.Y_length,
       'x_res':self.config.X_res,
       'y_res':self.config.Y_res,
       'user':self.config.Username,
       'date':self.config.Date,
       'x_origin':self.config.X_origin,
       'y_origin':self.config.Y_origin
       }

        fullpath = path.join(self.config.DirectoryRoot,self.config.ExperimentDir,self.config.FileNamePrefix + '_README.dat')
        f = open(fullpath,'w')
        f.write(header_template)
        f.close()

    def save_data_to_file(self, data_point, data, dtype):  
        '''This method saves each data point vector into a text file. The arg 'type'
        is 'mag' or 'phase' . The data type arg is used to chronologically number the points for
        a later reconstruction. The files are saved into their respective sub dirs, Mag and Phase.''' 
        
        file_name = "%(name_prefix)s_%(type)s_%(file_num)s.dat" %{'name_prefix':self.config.FileNamePrefix
                                                        ,'file_num':str(data_point).zfill(5),
                                                        'type':dtype
                                                        }
        if dtype == 'real':
            fullpath = path.join(self.config.real_point_dir, file_name)    
        elif dtype == 'imag':
            fullpath = path.join(self.config.imag_point_dir, file_name) 
        else:
            raise Exception, "You did not supply an accepted type of 'real' or 'imag'. "
        
        # below is a fix for the single sweep vna mode, because one element
        # of an np array is an np scalar and np.savetxt won't work with it.
        # could not find a way to cast the np scalar into ndarray.
        if isinstance(data,np.ndarray):
            if data.shape == ():#used when data = np.real(data[0])
                self._write_single_data_point(fullpath, data)
            else:#used when data = np.array()
                 np.savetxt(fullpath, data)   
        elif isinstance(data,np.float64):#used when data  = np.abs(data[0])
            self._write_single_data_point(fullpath, data)
          
        print "File Saved Successfully.\n"

    def _write_single_data_point(self,fullpath, data):
        '''Used to save data that is a single point, like a real or imag number. This is for data
         that is not an np array. '''
        f = open(fullpath,'w')
        f.write(str(data))
        f.close() 
                
    def make_3d_array(self):
        '''Initialize a numpy 3D or 2D array for storing Mag or Phase data. This is for using PYthon to
        view the data during the experiment. The lab protocol for storing the data for outside analysis is to
        save all the real and imaginary parts as separate long column of text values. '''
        
        array = np.zeros((self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))
        
        return array
 
    def get_real(self, data):
        real_data = np.real(data)
      
        return real_data
    
    def get_imag(self,data):
        imag_data = np.imag(data)
        
        return imag_data
    
    def get_magnitude(self, data):
        '''Takes col of complex numbers and returns col of mag. '''
        mag_data = np.zeros(data.shape, dtype=float)
        mag_data = np.abs(data)
        
        return mag_data 

    def get_intensity(self,data):
        inten_data = np.zeros(data.shape, dtype=float)
        inten_data = np.real(data)**2 + np.imag(data)**2
        
        return inten_data

    def get_phase(self,data):
        '''Takes cols of complex and returns col of phase '''
        phase_data = np.zeros(data.shape,dtype=float)
        phase_data = np.angle(data, False)# no degrees only radians

        return phase_data
   
    def make_freq_vector(self):
        Deltafreq = (self.config.freqstop - self.config.freqstart) / float(self.config.Freq_num_pts)
        freq_vec = np.arange(self.config.FreqStart, self.config.FreqStop, Deltafreq)

    def load_data_files(self, type):
        '''loads all data point files into a 2D array of either mag or phase data.The return has
        columns of row data. Use reshape_1D_to_3D() to get back a numpy 3D array.'''
    
        if type == 'real':
            base_dir = self.config.real_point_dir
        elif type == 'imag':
            base_dir = self.config.imag_point_dir    
        else:
            raise Exception, "Type was not a valid choice of 'real' or 'imag'. "    

        num_files = self.config.Num_x_pts * self.config.Num_y_pts
        data = np.zeros((self.config.Freq_num_pts, num_files))

        for file_num in xrange(0, num_files):
           
            file_name = "%(name_prefix)s_%(type)s_%(file_num)s.dat" %{'name_prefix':self.config.FileNamePrefix,
                                                                      'file_num':str(file_num).zfill(5),
                                                                      'type':type
                                                                      }
            
            path_str = path.join(base_dir, file_name)
            data[:,file_num] = np.loadtxt(path_str,dtype='float',comments='#',delimiter='\n')
            print "file: %i loaded into array\n" %file_num 
        
        return data    

    def reshape_1D_to_3D(self, data):        
        '''Takes col of data and writes a 3D array to disk. Used if the automatic 3D array is NOT being used. 
        FOr instance, you retook some data points and want to compile a new 3D matrix (ascii format)'''      
        outdata = np.zeros((self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))  
        outdata = np.reshape(data,(self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))
        
        #squeeze the singleton dim if it exists
        if outdata.ndim == 3 and outdata.shape[0] == 1:
            outdata = np.squeeze(outdata)
        
        return outdata
     
    def save_flattened_array(self,data):
        '''This method is for numpy 3D arrays. The only way to save n dim array as text, 
        is to flatten it out into 1D array, load into program like matlab, then reshape. '''
        dim1 = str(self.config.Num_y_pts)
        dim2 = str(self.config.Num_x_pts)
        dim3 = str(self.config.Freq_num_pts)
        fname = "%s_flattened_%s_%s_%s.txt " %(self.config.FileNamePrefix,dim1,dim2,dim3)      
        fullpath = path.join(self.config.DirectoryRoot,self.config.ExperimentDir,fname)

        np.savetxt(fullpath, data)    

    def save_real_and_inten_as_matlab(self, real_array, inten_array):
        real_data_path = path.join(self.config.DirectoryRoot,self.config.ExperimentDir,self.config.FileNamePrefix + '_REAL.mat')
        sio.savemat(real_data_path, {'real_array':real_array})
        
        inten_data_path = path.join(self.config.DirectoryRoot,self.config.ExperimentDir,self.config.FileNamePrefix + '_INTEN.mat')
        sio.savemat(inten_data_path, {'inten_array':inten_array})
                                  
class PlotTools(object):
    def __init__(self, Config):
        self.config = Config 
        plt.figure()
        plt.ion()    
        dummy = np.zeros((self.config.Num_x_pts,self.config.Num_y_pts))
 
        im1 = plt.imshow(dummy, interpolation='nearest', origin='lower', cmap = plt.cm.jet)       
        #plt.colorbar(im1)   
 
        im2 = plt.imshow(dummy, interpolation='nearest', origin='lower', cmap = plt.cm.jet)       
        plt.colorbar(im2)  
          
               
    def plot(self, real, intensity, z=0):
        '''Plot the data in-vivo as a check on the experiment using numpy. The z arg is the
        xy plane you want to plot. For single point mode, z = 0 (default), for sweep you must choose. '''
        
        plt.subplot(1,2,1)
        im1 = plt.imshow(real[z,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
        plt.title('Electric Field Linear Scale')
        plt.xlabel('X axis points')
        plt.ylabel('Y axis points')

        plt.subplot(1,2,2)
        im2 = plt.imshow(intensity[z,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
        plt.title('Intensity ( x^2 + y^2) Linear Scale') 
        plt.xlabel('X axis points')
        plt.ylabel('Y axis points')
        
        plt.draw()
        
    def close_plot(self):
        plt.close('all')
        
















