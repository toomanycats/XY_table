#!/usr/bin/python

import motor_tools
import vna_tools
import code_tools
import code
import numpy as np
import traceback
import matplotlib.pyplot as plt

def loop_along_sample(config):
    data_point = 0 # used to name the individual data point files. 
    index_x = 0
    for index_y in xrange(0,config.Num_y_pts):
        take_data(data_point, index_y, index_x, config)
        for index_x in xrange(0,config.Num_x_pts):
            mx.move_rel(config.X_res)
            take_data(data_point, index_y, index_x, config)
            data_point += 1         
        mx.move_rel(-1*config.X_length)      
        my.move_rel(config.Y_res)   

def take_data(data_point, index_y, index_x, config):
    print "Taking transmission data. \n"
    # get the raw data as complex pairs
    data = _take_data(config)
    # get the mag from the raw data
    real_data = arraytools.get_real(data)
    # send to mag_array for in-vivo plotting
    real_array[:,index_y, index_x] = real_data
    # save the mag data from a single point to it's own file
        # in the Single_Point dir
    arraytools.save_data_to_file(data_point, real_data, 'real')
    # get the phase from the raw data 
    imag_data = arraytools.get_imag(data)
    # send the phase data to the in-vivo phase_array
    imag_array[:,index_y,index_x] = imag_data
    # save the phase data from a single point to it's own file
        # in the Single_Point dir
    arraytools.save_data_to_file(data_point, imag_data, 'imag')    
    # plot the in-vivo data
    plottools.plot(real_array, imag_array)

def _take_data(config):
    if config.mode == 'sweep':
        data = vna.take_sweep_data()
    elif config.mode == 'single':
        data = vna.take_single_point_data(config.SingleFrequency)
    else:
        raise Exception,"%s is not a valid mode. \n" %config.mode

    return data

def set_sample_origin(mx,my, config):
    flag = raw_input("Do you know the sample origin or do you wish to start at the center ? y/n")
    if flag == 'y':
        config.X_origin = int(raw_input("Enter the X origin of the sample: "))
        config.Y_origin = int(raw_input("Enter the Y origin of the sample: "))
        mx.move_absolute(config.X_origin)
        my.move_absolute(config.Y_origin)
    elif flag == 'n':
        print "Moving sample to roughly center, this will be the sample origin.\n"    
        mx.move_absolute(25)
        my.move_absolute(25)
        config.X_origin = mx._calculate_pos(mx._CurrentStep)
        config.Y_origin = my._calculate_pos(my._CurrentStep)
    else:
        raise Exception, "Not a 'y' or a 'n'."

def get_config_from_user(): 
        '''Have the user fill out config values interactively. ''' 
        
        config = code_tools.ConfigureDataSet()
        config.mode = raw_input("Enter the mode 'sweep' or 'single':")
        config.ExperimentDir = raw_input("Enter the name of the directotry to hold this experiment: ")
        config.FileNamePrefix = raw_input("ENter the prefix for the files that will be saved: ")
        
        if config.mode == 'sweep':
            config.FreqStart = float(raw_input("Enter the start freq of the sweep i.e., 3e9 or 10e9: "))
            config.FreqStop = float(raw_input("Enter the stop freq: "))
        elif config.mode == 'single':
             config.SingleFrequency = float(raw_input("Enter the single freq, i.e., 12e9: ")) # single freq mode

        if config.mode == 'single':
            config.Freq_num_pts = 1
        else:
            config.Freq_num_pts = int(raw_input("Enter the number of points that the analyzer is set to take: "))
    
        config.X_length = float(raw_input("Enter the length along X in meters: "))
        config.Y_length = float(raw_input("Enter the length along Y in meters: "))
        config.X_res = float(raw_input("Enter the distance between X data points in meters: "))
        config.Y_res = float(raw_input("Enter the distance between Y data points in meters: "))
    
        ### static config entries
        config.TestSet = 'S21' # transmission always for this experiment
        config.set_xy_num_pts()
        config.make_sub_dirs()
    
        return config

def experiment_main():
    '''Run the experiment. '''
### test the load from files method
    #     codetools = code_tools.ArrayTools(config)
    #     real_data = codetools.load_data_files('real')
    #     real_array3d = codetools.reshape_1D_to_3D(real_data)
    #     imag_data = codetools.load_data_files('imag')
    #     imag_array3d = codetools.reshape_1D_to_3D(imag_data)
    #     plottools.plot(real_array3d,imag_array3d)    
    try:
        # get the config setup interactively
        config = get_config_from_user()
        
        ## Motor instances 
        mx,my = motor_tools.Connection(config).connect_to_ports()
        mx.main()
        my.main()
        # return motors to home limit switches
        #mx.return_home()
        my.return_home()
        set_sample_origin(mx,my,config)

        ## analyzer instance
        vna = vna_tools.VnaTools(config)
        
        # save the readme file to the directory
        arraytools = code_tools.ArrayTools(config)
        arraytools.save_readme()
        
        # make an array to hold the data for plotting or in vivo testing
        real_array =   arraytools.make_3d_array()
        imag_array = arraytools.make_3d_array()
        # plotting 
        plottools = code_tools.PlotTools(config)
        
        # Where the work is done on the sample
        loop_along_sample(config)
        # done collecting data from a sample.
        print "returning to origin \n"
        mx.move_absolute(config.X_origin)
        my.move_absolute(config.Y_origin)
        
        # close all devices and free ports.
        mx.close()
        my.close()
        vna.close()
    
    except ValueError:
        print """A value error was thrown. It is likely that the Freq_num_pts was 
    changed and does not match the values used in to create the variables "mag_array" and "phase_array" which 
    holds the data for the in-vivo plots."""
        tb = traceback.format_exc()
        print tb
    except:
        print "Exception raised, closing gpib and serial connections, emailing admin."
        tb = traceback.format_exc()
        print tb
        try:
            mx.close()
            my.close()
            vna.close()
        except:
            pass
        finally:  
            pass  
            #code_tools.CodeTools()._notify_admin_error(config.Username, config.Date, tb)

if __name__ == "__main__":
    experiment_main()  
