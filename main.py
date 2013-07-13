#!/usr/bin/python
#TODO: move all the methods here to code_tools
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

def set_pos_as_sample_origin():
        '''Arg is the axis name, 'x' or 'y'. Set this position as the origin of the sample.
        Recall: steps are always aggregate, and the zeros position is always defined wrt to the 
        'HOME' position set by the limit switches. '''
        config.X_origin = mx._calculate_pos(mx._CurrentStep)
        config.Y_origin = my._calculate_pos(my._CurrentStep)

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
        print "The VNA must already be in Single sweep mode on.\n"
        config.Freq_num_pts = 1
    else:
        config.Freq_num_pts = 51
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
    config.make_sub_dirs()
    # save the readme file to the directory
    arraytools = code_tools.ArrayTools(config)
    arraytools.save_readme()
    
    # make an array to hold the data
    real_array =   arraytools.make_3d_array()
    imag_array = arraytools.make_3d_array()
    # plotting 
    plottools = code_tools.PlotTools(config)

    ### test the load from files method
#     codetools = code_tools.ArrayTools(config)
#     mag_data = codetools.load_data_files('mag')
#     mag_array3d = codetools.reshape_1D_to_3D(mag_data)
#     phase_data = codetools.load_data_files('phase')
#     phase_array3d = codetools.reshape_1D_to_3D(phase_data)
#     plottools.plot(mag_array3d,phase_array3d)
        
    ## Motor instance 
    mx,my = motor_tools.Connection(config).connect_to_ports()
    mx.main()
    my.main()
    ## analyzer instance
    vna = vna_tools.VnaTools(config)
    
    ### testing origin handling ###
    set_pos_as_sample_origin()
    
    # get to work on sample
    loop_along_sample(config)
    
    # save as matlab 3D matrix in binary      
    #arraytools.save_data_to_file(config.FileNamePrefix +'_DataArray.mat', array3d) 

    print "returning to origin \n"
    mx.return_to_sample_origin(config.X_origin)
    my.return_to_sample_origin(config.Y_origin)
    
    # close all devices and free ports.
    mx.close()
    my.close()
    vna.close()

except ValueError:
    print """A value error was thrown. It is likely that the Freq_num_pts was 
changed and does not match the values used in to create the variables "mag_array" and "phase_array" which 
holds the data for the in-vivo plots."""

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

    
