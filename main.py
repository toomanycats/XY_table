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
        take_data(data_point, index_y, index_x)
        for index_x in xrange(0,config.Num_x_pts):
            motors.mx.move_rel(config.X_res)
            take_data(data_point, index_y, index_x)
            data_point += 1         
        motors.mx.move_rel(-1*config.X_length)      
        motors.my.move_rel(config.Y_res)   

def take_data(data_point, index_y, index_x):
    print "Taking transmission data. \n"
    data = vna.take_data()
    mag_data = arraytools.get_magnitude(data)
    arraytools.save_data_to_file(data_point, mag_data)
    array3d[:,index_y, index_x] = mag_data
    ### testing, would like a handful of Z steps plotted
    im = plt.imshow(array3d[50,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
    plt.draw()
    
####### START HERE #####
try:
    config = code_tools.ConfigureDataSet()
    config.ExperimentDir = 'test'
    config.FileNamePrefix = 'test'
    config.FreqStart = 7e9
    config.FreqStop = 15e9
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
    
    ### plotting ###
    array3d = np.zeros((config.Freq_num_pts,config.Num_y_pts,config.Num_x_pts))
    plt.figure()
    plt.ion()
    im = plt.imshow(array3d[50,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
    plt.colorbar(im)
    
    ## Motor instance 
    motors = motor_tools.Main(config, set_ports = True)
    ## analyzer
    vna = vna_tools.VnaTools(config)
    vna.check_parameters()
    vna.check_cal()
    
    ### testing origin handling ###
    motors.mx.set_pos_as_sample_origin('x')
    motors.my.set_pos_as_sample_origin('y')
    
    # get to work on sample
    loop_along_sample(config)
    
    # return to origin 
    motors.mx.return_to_sample_origin(config.X_origin)
    motors.my.return_to_sample_origin(config.Y_origin)
    
    # close all devices and free ports.
    motors.mx.close()
    motors.my.close()
    vna.close()

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

    
