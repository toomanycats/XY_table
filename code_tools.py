from email.mime.text import MIMEText
from getpass import getuser
from mpl_toolkits.mplot3d import Axes3D
from os import path, makedirs
from time import sleep
import ConfigParser
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
import numpy as np
import scipy.io as sio
import smtplib
from matplotlib import rc

class ConfigureDataSet(object):
    '''Mehtods to setup of the experiment variables and store them in the config file. '''
    def __init__(self):
        self.config_parser = ConfigParser.RawConfigParser()
        
        self.Username = getuser() 
        self.Date = datetime.datetime.now()   
        self.DirectoryRoot = '/media/Data'
        self.ExperimentDir = ''
        self.FileNamePrefix = ''
        self.Mode = ''
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
        
    def set_misc_paths(self):
        '''Set the paths for the config, log and .mat file. '''
        self.config_path = path.join(self.DirectoryRoot,self.ExperimentDir,self.FileNamePrefix + '.cfg' )
        self.log_file = path.join(self.DirectoryRoot,self.ExperimentDir,self.FileNamePrefix + '.log')
        self.mat_data_path = path.join(self.DirectoryRoot,self.ExperimentDir,self.FileNamePrefix + '.mat')

    def make_sub_dirs(self):
        '''Make sub-directories for the experiment. '''
        p = path.join(self.DirectoryRoot,self.ExperimentDir)
        if not path.exists(p):
            makedirs(p)
        
        self.real_point_dir = path.join(self.DirectoryRoot,self.ExperimentDir,'Data_Points','Real')
        if not path.exists(self.real_point_dir):
            makedirs(self.real_point_dir)

        self.imag_point_dir = path.join(self.DirectoryRoot,self.ExperimentDir,'Data_Points','Imag')
        if not path.exists(self.imag_point_dir):
            makedirs(self.imag_point_dir)  
        
    def set_xy_num_pts(self):
        '''The total number of data points will be the number of points in X times
        the number of points in Y. '''
        
        self.Num_x_pts = int(np.ceil(self.X_length / self.X_res))
        self.Num_y_pts = int(np.ceil(self.Y_length / self.Y_res))

    def get_config_from_user(self): 
        '''Have the user fill out config values interactively. ''' 
        
        self.Mode = raw_input("Enter the mode 'sweep' or 'single':")
        self.ExperimentDir = raw_input("Enter the name of the directory to hold this experiment: ")
        self.FileNamePrefix = raw_input("ENter the prefix for the files that will be saved: ")
        
        if self.Mode == 'sweep':
            self.FreqStart = float(raw_input("Enter the start freq of the sweep i.e., 3e9 or 10e9: "))
            self.FreqStop = float(raw_input("Enter the stop freq: "))
        elif self.Mode == 'single':
             self.SingleFrequency = float(raw_input("Enter the single freq, i.e., 12e9: ")) # single freq mode
        else:
            raise Exception, "Not a valid choice, 'sweep' or 'single' only."
            
        if self.Mode == 'single':
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
        self.set_misc_paths()
  
    def _add_entries(self):
        '''Add variables set from get_config_from_user(), to a config file.'''
        self.config_parser.add_section('Paths')
        self.config_parser.set('Paths', 'DirectoryRoot', self.DirectoryRoot)
        self.config_parser.set('Paths', 'ExperimentDir', self.ExperimentDir)
        self.config_parser.set('Paths', 'FilenamePrefix', self.FileNamePrefix)
        self.config_parser.set('Paths','Config Path', self.config_path)
        self.config_parser.set('Paths','Log Path', self.log_file)
        self.config_parser.set('Paths','Real Point Dir', self.real_point_dir)
        self.config_parser.set('Paths','Imag Point Dir', self.imag_point_dir)
        
        self.config_parser.add_section('User')
        self.config_parser.set('User','User',self.Username)
        
        self.config_parser.add_section('Date')
        self.config_parser.set('Date', 'Date', self.Date)

        self.config_parser.add_section('Sample')
        self.config_parser.set('Sample', 'X length', self.X_length)
        self.config_parser.set('Sample', 'Y length', self.Y_length)
        self.config_parser.set('Sample', 'X res', self.X_res)
        self.config_parser.set('Sample', 'Y res', self.Y_res)
        self.config_parser.set('Sample', 'X origin', self.X_origin)
        self.config_parser.set('Sample', 'Y origin', self.Y_origin)
        
        self.config_parser.add_section('Analyzer')
        self.config_parser.set('Analyzer', 'Test Set', self.TestSet)
        self.config_parser.set('Analyzer', 'Mode', self.Mode)
        self.config_parser.set('Analyzer', 'Start Freq', self.FreqStart)
        self.config_parser.set('Analyzer', 'Stop Freq', self.FreqStop)
        self.config_parser.set('Analyzer', 'Single Freq', self.SingleFrequency)
        self.config_parser.set('Analyzer', 'Number Points', self.Freq_num_pts)
        
    def load_config(self, config_path = None):
        '''Reads the config file and sets the class attributes. You can pass in
        a config file path or the default is the one in the config object,
        self.config_path. '''
        #ascii cfg file can't read back other types, str must be caste
        if config_path is None:
            config_path = self.config_path
        
        self.config_parser.read(config_path)
        
        self.DirectoryRoot = self.config_parser.get('Paths', 'DirectoryRoot')
        self.ExperimentDir = self.config_parser.get('Paths', 'ExperimentDir')
        self.FileNamePrefix = self.config_parser.get('Paths', 'FilenamePrefix')
        self.config_path = self.config_parser.get('Paths','Config Path')
        self.log_file = self.config_parser.get('Paths','Log Path')
        self.real_point_dir = self.config_parser.get('Paths','Real Point Dir')
        self.imag_point_dir = self.config_parser.get('Paths','Imag Point Dir')
        
        self.Username = self.config_parser.get('User','User')
        
        self.Date = self.config_parser.get('Date', 'Date')

        self.X_length = float(self.config_parser.get('Sample', 'X length'))
        self.Y_length = float(self.config_parser.get('Sample', 'Y length'))
        self.X_res = float(self.config_parser.get('Sample', 'X res'))
        self.Y_res = float(self.config_parser.get('Sample', 'Y res'))
        self.X_origin = float(self.config_parser.get('Sample', 'X origin'))
        self.Y_origin = float(self.config_parser.get('Sample', 'Y origin'))
        
        self.TestSet = self.config_parser.get('Analyzer', 'Test Set')
        self.Mode = self.config_parser.get('Analyzer', 'Mode')
        self.FreqStart = float(self.config_parser.get('Analyzer', 'Start Freq'))
        self.FreqStop = float(self.config_parser.get('Analyzer', 'Stop Freq'))
        self.SingleFrequency = float(self.config_parser.get('Analyzer', 'Single Freq'))
        self.Freq_num_pts = float(self.config_parser.get('Analyzer', 'Number Points'))   
   
        # must be set after the load just like the UI version 
        self.set_xy_num_pts()
  
    def write_config(self):
        '''Write the config object to disk as an ascii file. '''
        self._add_entries()
        with open(self.config_path, 'w') as configfile:
            self.config_parser.write(configfile)


class CodeTools(object):
    '''Misc. methods. '''    
    
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
        recipients = ['wmanlab@gmail.com', 'dpcuneo@fastmail.fm','theebbandflow@yahoo.com']
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
    '''Methods for working with Numpy arrays. '''
    def __init__(self, Config = None):
        self.config = Config
  
    def _check_data_type(self, dtype, data):
        '''Some np methods are meant to work on certain types, but won't always throw
        an error because it's not mathematically incorrect to try. '''
        if data.dtype != dtype:
            raise Exception, "The data sent into this method is not of the type %s." %dtype
        
    def save_data_to_file(self, data_point, data, dtype):  
        '''This method saves each data point vector into a text file. The arg 'type'
        is 'mag' or 'phase' . The data type arg is used to chronologically number the points for
        a later reconstruction.''' 
        
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
          
        print "%s File Saved Successfully.\n" %dtype

    def _write_single_data_point(self,fullpath, data):
        '''Used to save data that is a single point, e.g., a real or imag number. This is for data
         that is not an np array. '''
        f = open(fullpath,'w')
        f.write(str(data))
        f.close() 
                
    def make_3d_array(self):
        '''Initialize a numpy 3D or 2D array for storing  data. This is for using PYthon to
        view the data during the experiment. '''
        
        array = np.zeros((self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))
        
        return array
 
    def get_real(self, data):
        '''Return the real part of the complex data. '''
        #np.real will not throw an error is the data is other than complex.
        # in this case, the data should always be complex
        self._check_data_type('complex128',data)
        
        real_data = np.real(data)
      
        return real_data
    
    def get_imag(self,data):
        '''Return the imaginary part of the complex data. '''
        self._check_data_type('complex128',data)
        
        imag_data = np.imag(data)
        
        return imag_data
    
    def get_magnitude(self, data):
        '''Takes col of complex numbers and returns col of mag. '''
        self._check_data_type('complex128',data)
        
        mag_data = np.zeros(data.shape, dtype=float)
        mag_data = np.abs(data)
        
        return mag_data 

    def get_intensity(self,data):
        '''Return the intensity of the complex data, i.e., x^2 + i*y^2 '''
        self._check_data_type('complex128',data)
        
        inten_data = np.zeros(data.shape, dtype=float)
        inten_data = np.real(data)**2 + np.imag(data)**2
        
        return inten_data

    def get_phase(self,data):
        '''Takes cols of complex and returns col of phase '''
        self._check_data_type('complex128',data)
        
        phase_data = np.zeros(data.shape,dtype=float)
        phase_data = np.angle(data, False)# no degrees only radians

        return phase_data
   
    def get_freq_vector(self, config = None):
        '''Given a config path or use the default one, return an np array of frequency values that match 
        the ones used in the experiment. '''
        try:
            if config is None:# allows for stand alone program to call this method
                config = self.config
                
            Deltafreq = (self.config.FreqStop - self.config.FreqStart) / float(self.config.Freq_num_pts)
            freq_vec = np.arange(self.config.FreqStart, self.config.FreqStop, Deltafreq)
            
            return freq_vec

        except ZeroDivisionError:
            print """Divide by zero error. Delta Freq is 0, likely b/c the experiment your working with is
is the single point type. Check the configuration file located in the experiment root directory (.cfg) """
            raise ZeroDivisionError
            
    def load_data_files(self, type):
        '''loads data point files into a 2D array of either real or imaginary data.The return has
        columns of row data. Use reshape_1D_to_3D() to get back a numpy 3D array.'''
    
        if type == 'real':
            base_dir = self.config.real_point_dir
        elif type == 'imag':
            base_dir = self.config.imag_point_dir    
        else:
            raise Exception, "Type was not a valid choice of 'real' or 'imag'. "    

        num_files = self.config.Num_x_pts * self.config.Num_y_pts
        
        if num_files == 0:
            raise exception, "The number of files was calculated as zero."
        
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
        '''Used to recreate the np array of data in it's proper dimensions. Normally used after the
        load_data_files().'''      
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

    def save_data_as_matlab(self, real_array, imag_array, mat_data_path = None, mode = None):
        '''Given a np array of real data and another of imaginary data, write the np array into 
        a complex matrix .mat binary file for use in MATLAB. The out put path default is the experimental
        root directory. You can send in an outpath arg for use in a stand alone program.  '''

        if real_array.shape != imag_array.shape:     
            raise Exception, "Real array and Imaginary array do not have the same shape."
        
        if mat_data_path is None:
            mat_data_path = self.config.mat_data_path
            
        comp_data = np.zeros((real_array.shape), dtype=complex)
        comp_data.real = real_array
        comp_data.imag = imag_array
    
        if mode is None:
            mode = self.config.Mode
        if mode == 'sweep':
            freq_data = self.get_freq_vector()
        elif mode == 'single':
            freq_data = self.config.SingleFrequency
        else:
            raise Exception, "Mode type was not one of either 'single' or 'sweep'."
        
        data = np.zeros((real_array.shape),dtype=complex)
        data.real = real_array
        data.imag = imag_array
        inten_data = self.get_intensity(data) 

        phase_data = self.get_phase(data)

        Out_Data = np.zeros((4,), dtype = np.object)
        temp = [ freq_data, comp_data, inten_data, phase_data ]
        Out_Data[0] = temp[0]
        Out_Data[1] = temp[1]
        Out_Data[2] = temp[2]
        Out_Data[3] = temp[3]
      
        sio.savemat(mat_data_path, {'Data':Out_Data})        

    def load_mat(self, mat_data_path = None):
        '''Load  the .mat file into numpy and return a data_dict with keys:
        "freq,comp,inten,phase". You can either PlotTools.plot() a single freq point array,
        or PlotTools.plot_movie() for a sweep experiment. '''
        
        if mat_data_path is None:
            mat_data_path= self.config.mat_data_path
            
        data_dict = sio.loadmat(mat_data_path)    
        try:
            data = data_dict['Data']
        except:
            data = data_dict['Out_Data']
        
        out_data = {'freq':data[0],
                    'comp':data[1],
                    'inten':data[2],
                    'phase':data[3]
                    }
        
        return out_data                   
    
                           
class PlotTools(object):
    '''Methods for plotting the data. '''
    def __init__(self, Config = None):
        self.config = Config     
        plt.figure()
        plt.ion()
        # LaTeX
        plt.rc('text', usetex=True)
        plt.rc('font', family='serif')    
    
    def _get_extent(self, dim):
        '''Get a tuple for the extent of an imshow() plot, so that the plot has the
        the correct ratio. Input dim is 2, or 3.'''
        
        if self.config.Num_x_pts > self.config.Num_y_pts:
            r = np.ceil(self.config.Num_x_pts / self.config.Num_y_pts)
            y_scale = r * self.config.Num_y_pts
            extent_dim = (0, self.config.Num_x_pts, 0, y_scale) 

        elif self.config.Num_x_pts < self.config.Num_y_pts:
            r = np.ceil(self.config.Num_y_pts / self.config.Num_x_pts)
            x_scale = r * self.config.Num_x_pts
            extent_dim = (0, x_scale, 0, self.config.Num_y_pts) 

        elif self.config.Num_x_pts == self.config.Num_y_pts:
            extent_dim = (0, self.config.Num_x_pts, 0, self.config.Num_y_pts)
        
        else:
            raise Exception, "Some is wrong with the config.Num_x_pts or config.Num_y_pts."
            
        if dim == 2:    
            return extent_dim 
        
        elif dim == 3:
            extent_dim = np.concatenate((extent_dim,[0, self.config.Freq_num_pts])) 
        
            return extent_dim
        else:
            raise Exception, "Argument is an int of 2 or 3 only. %g   was supplied." %dim

    def get_data_type(self, data_dict, Type):
        if Type == 'real':
            return data_dict['comp'].real
        elif Type == 'phase':
            return data_dict['phase']
        elif Type == 'inten':
            return data_dict['inten']
        elif Type == 'mag':
            return data_dict['mag']
  
    def get_data_scale(self, data_dict, Type):
        '''Send in the data_dict from load_mat() and the Type, 'real, inten, phase,mag' and get back the
        data of type requested and the scaled vmin and vmax for use with the colorbar.'''
        
        if Type == 'real':
            data = data_dict['comp'].real
            vmin = data.min(0).mean()/data.min(0).std()
            vmax = data.max(0).mean()/data.max(0).std() 
        elif Type == 'inten':
            data = data_dict['inten']
            vmin = 0
            vmax = data.max(0).mean()/data.max(0).std()
        elif Type == 'mag':
            data = data_dict['mag']
            data = np.sqrt(data)
            vmin = 0    
            vmax = data.max(0).mean()/data.max(0).std() 
        elif Type == 'phase':
            data = data_dict['phase']
            vmin = data.min()  
            vmax = data.max() 
                      
        return vmin, vmax                             
   
    def get_nearest_freq(self, freq_array, Freq):
        '''Find the closest freq value in the experimental data and return the index.'''
        
        if Freq < self.config.FreqStart:
            print "The freq you requested %.3e  is lower than the Start Freq of the experiment.\n" %Freq
            print "The range of Freq is %.3e  to    %.3e" %(self.config.FreqStart, self.config.FreqStop)
            return None
        elif Freq > self.config.FreqStop:
            print "The freq you requested %f  is higher than the Stop Freq of the experiment.\n" %Freq
            print "The range of Freq is %.3e   to    %.3e" %(self.config.FreqStart, self.config.FreqStop)
            return None
        
        index = np.where(freq_array >= Freq)[0][0] 
        
        return index

    def _get_ticks(self,x_sub_div,y_sub_div,extent_dim):
    
        Xlocs = np.arange(0, extent_dim[1], x_sub_div) 
        Ylocs = np.arange(0, extent_dim[3], y_sub_div) 
        
        if self.config.Y_res > self.config.X_res:
            r = self.config.Y_res / float(self.config.X_res)
            Xlabels = np.arange(0, self.config.X_length, x_sub_div * self.config.X_res )
            Ylabels = np.arange(0, self.config.Y_length, y_sub_div * self.config.Y_res/r )
            
        elif self.config.Y_res < self.config.X_res:    
            r = self.config.X_res / float(self.config.Y_res)
            Xlabels = np.arange(0, self.config.X_length, x_sub_div * self.config.X_res/r )
            Ylabels = np.arange(0, self.config.Y_length, y_sub_div * self.config.Y_res )
        
        elif self.config.Y_res == self.config.X_res:
            Xlabels = np.arange(0, self.config.X_length, x_sub_div * self.config.X_res )
            Ylabels = np.arange(0, self.config.Y_length, y_sub_div * self.config.Y_res )
            
        else:
            raise  Exception, "Y and/or X resolution setting in config is messed up..."    
        
        return Xlocs,Xlabels,Ylocs,Ylabels
                      
    def invivo_plot(self, real, intensity, z=0):
        '''Plot the data in real time as it is collected for a sanity check and to monitor progress. 
        The z arg is the xy plane you want to plot. For single point mode, z = 0 (default), for sweep 
        you can choose. I do not use a color bar b/c it's gets too messy and is not that useful.'''
        
        extent_dim = self._get_extent(2)
        Xlocs,Xlabels,Ylocs,Ylabels = self._get_ticks(5,5,extent_dim)
        
        plt.subplot(1,2,1)
        im1 = plt.imshow(real[z,:,:], cmap='jet', interpolation='nearest', origin='lower', extent = extent_dim)   
        plt.title('Electric Field Linear Scale')
        plt.xlabel('Position (m)')
        plt.xticks(Xlocs, Xlabels)
        plt.ylabel('Position (m)')
        plt.yticks(Ylocs,Ylabels)

        plt.subplot(1,2,2)
        im2 = plt.imshow(intensity[z,:,:], cmap='jet',interpolation='nearest', origin='lower',extent = extent_dim)   
        plt.title(r'Intensity ( $x^2 + y^2$ ) Linear Scale') 
        plt.xlabel('Position (m)')
        plt.xticks(Xlocs, Xlabels)
        plt.yticks(Ylocs,Ylabels)
        
        plt.draw()

    def plot_movie(self, data_dict, Type, interp = 'bilinear', pause = 0.25):
        '''Show movie of plots. Specify Type as 'real,inten, phase' and pause is in seconds.
        defaults are 'real' and 0.25 . Use ArrayTools.load_mat() to get the .mat file into a numpy array.
        A colorbar is used here. This method is for a completed run. '''        

        
        if len(data_dict['freq'].shape) == 0:
            raise Exception, """This method is for showing xy planes of data for multiple freq's.
The data you sent in is only one dimensional, that is, single freq (vna setting of single point) data. """
        
        data = self.get_data_type(data_dict,Type)
        v_min, v_max = self.get_data_scale(data_dict, Type)
        freq = data_dict['freq']
        
        extent_dim = self._get_extent(2)
        Xlocs,Xlabels,Ylocs,Ylabels = self._get_ticks(5,5,extent_dim)
  
        plt.imshow(data[0,:,:],cmap='jet',interpolation=interp,vmin=v_min,vmax=v_max,origin='lower',extent = extent_dim)
        plt.title('Type:  %s  Freq: %.3e Hz' %(Type,data_dict['freq'][0]) )
        plt.xlabel('Position (m)')
        plt.ylabel('Position (m)')
        plt.xticks(Xlocs, Xlabels)
        plt.yticks(Ylocs,Ylabels)
        plt.colorbar()
        sleep(pause)
        plt.clf() 
     
        for i in xrange(1,data.shape[0]):
            plt.imshow(data[i,:,:],cmap='jet',interpolation=interp,vmin=v_min,vmax=v_max,origin='lower',extent = extent_dim)
            plt.title('Type:  %s  , Freq: %.3e Hz' %(Type,data_dict['freq'][i]) ) 
            plt.xlabel('Position (m)')
            plt.ylabel('Position (m)')
            plt.xticks(Xlocs, Xlabels)
            plt.yticks(Ylocs,Ylabels)
            plt.draw()
            sleep(pause)
            plt.clf()

    def plot_3d_barchart(self, data_dict, Type, Freq):
        ''' Using the mayavi library, plot a 3D barchart of the data of requested type, and freq.'''
    
        extent_dim = self._get_extent(3)
        Xlocs,Xlabels,Ylocs,Ylabels = self._get_ticks(5,5,extent_dim)
        data = self.get_data_type(data_dict, Type)
        v_min,v_max = self.get_data_scale(data_dict, Type)
        freq_array = data_dict['freq']
        freq_ind = self.get_nearest_freq(freq_array,Freq)
        
        from mayavi import mlab
        mlab.figure( bgcolor=(0.5,0.5,0.5) )# grey bg
        mlab.barchart(data[freq_ind,:,:],vmin=v_min,vmax=v_max,auto_scale=False,colormap='jet',extent = extent_dim)
        mlab.title('Freq %.3e' %freq_array[freq_ind],size=5,height=0.1)
        mlab.show()
         
        #return f  
  
    def close_plot(self):
        plt.close('all')
        

        
        
        















