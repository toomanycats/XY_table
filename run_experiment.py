#!/usr/bin/python

import motor_tools
import vna_tools
import code_tools
import code
import numpy as np
import traceback
import matplotlib.pyplot as plt
from IPython import Shell
import scipy.io as sio

def prompt_for_return_home():
    return_home = raw_input("""Do you want the motors to reference the home location ?
You should enter 'yes', if this is your first experimental run. If you are repeating an experiment then you likely
do not need to re-reference the home location (no). : """)
    if return_home == 'yes':
        # return motors to home limit switches
        mx.return_home()
        my.return_home()
    elif return_home == 'no':
        return
    else:
        print "You did not enter 'yes' or 'no' ."
        return_home()

def confirm_origin():
    bool = raw_input("Do you want to use your current/new position as the origin, or the one previously set? (current/previous): ")
    if bool == 'current':
        print "Setting current position as sample origin. \n"
        config.X_origin = mx.CurrentPos
        config.Y_origin = my.CurrentPos
    elif bool == 'previous':
        print "Moving sample back to previously defined origin. \n"
        mx.move_absolute(config.X_origin)
        my.move_absolute(config.Y_origin) 
    else:
        print "Enter 'current' or 'previous'. "
        confirm_origin()       

def open_interactive():
    '''Opens an interactive interpreter that has access to the local variables. Exit with "exit()" '''
    ipshell = Shell.IPShellEmbed()
    ipshell.banner = '*** You are now in the ipython interpreter, exit with "exit()" ***'
    ipshell.exit_msg = '\n\n*** Back in main program. ***\n'    

    return ipshell

def loop_along_sample(direction):
    '''The real meat of the experiment is controlled here. The sample is
    looped across and data is taken and saved. The motors move along the negative
    x axis, then return to the x origin, move negative along y axis, then repeat the x movements.'''
    data_point = 0 # used to name the individual data point files. 
    index_x = 0
    for index_y in xrange(0,config.Num_y_pts):
        take_data(data_point, index_y, index_x)
        for index_x in xrange(0,config.Num_x_pts):
            mx.move_rel(direction*config.X_res)
            take_data(data_point, index_y, index_x)
            data_point += 1         
        mx.move_rel(-1*direction*config.X_length) # swing back to x = 0     
        my.move_rel(direction*config.Y_res)   

def take_data(data_point, index_y, index_x):
    '''Calls to the analyzer are made and the data is recorded. '''
    print "Taking transmission data. \n"
    # get the raw data as complex pairs
    data = _take_data()

    real_data = arraytools.get_real(data)
    real_array[:,index_y, index_x] = real_data
    arraytools.save_data_to_file(data_point, real_data, 'real')
   
    imag_data = arraytools.get_imag(data)
    imag_array[:,index_y, index_x] = imag_data
    arraytools.save_data_to_file(data_point, imag_data, 'imag')    
   
    inten_data = arraytools.get_intensity(data)
    inten_array[:,index_y,index_x] = inten_data

    plottools.plot(real_array, inten_array)

def _take_data():
    '''Sub routine of take_data() that deals with the single or sweep mode. '''
    if config.mode == 'sweep':
        data = vna.take_sweep_data()
    elif config.mode == 'single':
        data = vna.take_single_point_data(config.SingleFrequency)
    else:
        raise Exception,"%s is not a valid mode. \n" %config.mode

    return data

def set_sample_origin():
    '''The user can set the origin or center of the table will be used. '''
    flag = raw_input("If you know the origin cordinates you'd like to use, enter 'y', or 'n':  (y/n): ")
    if flag == 'y':
        config.X_origin = float(raw_input("Enter the X origin of the sample: "))
        config.Y_origin = float(raw_input("Enter the Y origin of the sample: "))
        mx.move_absolute(config.X_origin)
        my.move_absolute(config.Y_origin)

    elif flag == 'n':
        print "Moving sample to roughly center.\n"    
        mx.move_absolute(0.20)
        my.move_absolute(0.20)
    else:
        print "You did not enter a 'y' or a 'n'."
        set_sample_origin()

def review_config_settings(config):
    '''Print the values stored in the config object and prompt for changes. '''
    print "Review the config you just made. \n"
    for k,v in config.__dict__.iteritems():
        print "%s ........ %s" %(str(k).rjust(15),str(v).rjust(15))
    cont = raw_input("Are these settings correct ? (y/n)")
    if cont == 'y':
        return
    elif cont == 'n':
        config.get_config_from_user()
    else:
        print "Enter 'y' or 'n'."
        review_config_settings(config)
   
try:
    # get the config setup interactively
    config = code_tools.ConfigureDataSet()
    config.get_config_from_user()
     
    # user review the config settings
    review_config_settings(config)
     
    ## Motor instances 
    mx,my = motor_tools.Connection().connect_to_ports()
    mx.main(acceleration = 51200, max_vel = 100000, init_vel = 100)
    my.main(acceleration = 51200, max_vel = 100000, init_vel = 100)

    # might not need to return home for a reference
    prompt_for_return_home()
    
    # enter the current position into the config object        
    set_sample_origin()

    ## analyzer instance
    vna = vna_tools.VnaTools(analyzer_name = "VNA", log_file = config.log_file)
    
    # make an array to hold the data for plotting , vivo testing and .mat save
    arraytools = code_tools.ArrayTools(config)
    real_array =   arraytools.make_3d_array()
    imag_array = arraytools.make_3d_array()
    inten_array = arraytools.make_3d_array()# for plotting

    # plotting 
    plottools = code_tools.PlotTools(config)
    
    ### go into interactive mode to jog the motors or do additional placement or handle the unforeseen 
    interactive = raw_input("Do you want to drop into an interactive shell for manual control ?(y/n): ")
    if interactive == 'y':
        ipshell = open_interactive()
        ipshell()
    
    # origin could have changed during interactive setting
    confirm_origin()

    # Write the config to file.
    config.write_config_file()
    
    # Where the work is done on the sample
    loop_along_sample(direction = -1)

    # done collecting data from a sample.
    print "returning to origin \n"
    mx.move_absolute(config.X_origin)
    my.move_absolute(config.Y_origin)
    
    #save the numpy arrays as matlab .mat files for easy in house analysis.
    arraytools.save_data_as_matlab(real_array, imag_array)

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
