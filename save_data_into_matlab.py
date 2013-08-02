#!/usr/local/python

import code_tools
import numpy as np
import scipy.io as sio

def work(config_path, out_put_path):
    '''Given a path to a config file, load the data and store it into a 
    matlab .mat file as a cell array of comlex values, inten, mag and freq vector. '''

    arraytools = codetools.ArrayTools()
    config = code_tools.ConfigureDataSet().load_config(config_path)
    
    real_data = arraytools.load_data_files('real')
    real_array = arraytools.reshape_1D_to_3D(real_data)
    
    imag_data = arraytools.load_data_files('imag')
    imag_array = arraytools.reshape_1D_to_3D(imag_data)
    
    arraytools.save_data_as_matlab(real_array, imag_array, out_put_path)   

if __name__ == "__main__":
    from optparse import OptionParser
    
    string = """Use this program to load experiment data and save it into a
MATLAB .mat binary. The .mat file will be a cell array that holds the freq or freq vector, complex,
intensity and magnitude data. You must supply the path to the config file created with the data 
and the output path. """

    parser = OptionParser(usage = string)
    parser.add_option("-p", "--config-path", dest="config_path",
                  help="The path to the config file, i.e., /media/Data/Test1/test.cfg")
    parser.add_option("-o", "--out-path", dest="out_put_path",
                  help="Path where the .mat file will be written.")

    options = parser.parse_args()
    work(options.config_path, options.out_put_path)
