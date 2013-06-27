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
            motors.mx.move_rel(config.X_res)
            take_data(data_point, index_y, index_x, config)
            data_point += 1         
        motors.mx.move_rel(-1*config.X_length)      
        motors.my.move_rel(config.Y_res)   

def take_data(data_point, index_y, index_x, config):
    print "Taking transmission data. \n"
    # get the raw data as complex pairs
    data = _take_data(config)
    arraytools.save_data_to_file(data_point, data)
    # get the mag and save to array3d
    mag_data = arraytools.get_magnitude(data)
    array3d[:,index_y, index_x] = mag_data
    ### testing, would like a handful of Z steps plotted
    plottools.plot(array3d[0,:,:])
    #im = plt.imshow(array3d[50,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
    #plt.draw()

def _take_data(config):
    if config.mode == 'sweep':
        data = vna.take_sweep_data()
    elif config.mode == 'single':
        data = vna.take_single_point_data(config.SingleFrequency)
    else:
        raise Exception,"%s is not a valid mode. \n" %config.mode
    return data

####### START HERE #####
try:
    config = code_tools.ConfigureDataSet()
    config.mode = 'sweep'
    config.ExperimentDir = 'test'
    config.FileNamePrefix = 'test'
    config.SingleFrequency = 14e9 # single freq mode
    config.FreqStart = 7e9
    config.FreqStop = 15e9
    # dumb temp fix
    if config.mode == 'single':
        config.Freq_num_pts = 1
    else:
        config.Freq_num_pts = 801
    config.TestSet = 'S21' #transmition always for this experiment
    config.X_length = 0.05
    config.Y_length = 0.05
    config.X_res = 0.01
    config.Y_res = 0.01
    config.X_origin = 0.0
    config.Y_origin = 0.0
    config.x_port = '/dev/ttyUSB0'
    config.y_port = '/dev/ttyUSB1'
    config.set_xy_num_pts()
    config.make_experiment_dir()
    
    # save the readme file to the directory
    arraytools = code_tools.ArrayTools(config)
    arraytools.save_readme()
    
    # make an array to hold the data
    array3d = arraytools.make_3d_array()
    # plotting 
    plottools = code_tools.PlotTools(config)
    #plottools.plot(array3d[0,:,:])
    
    ## Motor instance 
    motors = motor_tools.Main(config)
    ## analyzer instance
    vna = vna_tools.VnaTools(config)
    
    ### testing origin handling ###
    motors.mx.set_pos_as_sample_origin('x')
    motors.my.set_pos_as_sample_origin('y')
    
    # get to work on sample
    loop_along_sample(config)
    
    # save data in binary as numpy ndarray
    np.save(config.FileNamePrefix + '_DataArray',array3d)
    # save as matlab 3D matrix in binary      
    arraytools.save_data_to_file(config.FileNamePrefix +'_DataArray.mat', array3d) 
    # return to origin 
    print "returning to origin \n"
    motors.mx.return_to_sample_origin(config.X_origin)
    motors.my.return_to_sample_origin(config.Y_origin)
    
    # close all devices and free ports.
    motors.mx.close()
    motors.my.close()
    vna.close()

except ValueError:
    print """A value error was thrown. It is likely that the Freq_num_pts was 
changed and does not match the values used in to create the variable "array3d" which 
holds the data for the in-vivo plots and finally for saving."""

except:
    print "Exception raised, closing gpib and serial connections, emailing admin."
    tb = traceback.format_exc()
    print tb
    try:
        motors.mx.close()
        motors.my.close()
        vna.close()
    except:
        pass
    finally:  
        pass  
        #code_tools.CodeTools()._notify_admin_error(config.Username, config.Date, tb)

    
