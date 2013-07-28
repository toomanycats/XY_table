!#/usr/local/python

def work(config_path, out_put_path):
    try:
        import code_tools
        import numpy as np
        import scipy.io as sio

        arraytools = codetools.ArrayTools()
        config = code_tools.ConfigureDataSet().load_config(config_path)
        
        real_data = arraytools.load_data_files('real')
        real_array = arraytools.reshape_1D_to_3D(real_data)

        imag_data = arraytools.load_data_files('imag')
        imag_array = arraytools.reshape_1D_to_3D(imag_data)
  
        if real_data.shape == imag_data.shape:     
            comp_data = np.zeros((real_data.shape), dtype=complex)
            comp_data.real = real_data
            comp_data.imag = imag_data

            freq_data = arraytools.get_freq_vector(config)

            Out_Data = np.zeros((2,) , dtype = dt)
            Out_Data[0]['complex'] = comp_data
            Out_Data[1]['freq'] = freq_data
            
            sio.savemat(out_put_path, {'Out_Data':Out_Data})        

        else:
            raise Exception, "Arrays do not have the same shape."
    

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="config_path",
                  help="The path to the config file, i.e., /media/Data/Test1")
    parser.add_option("-o", "--out-path", dest="out_put_path",
                  help="Path where the .mat file will be written.")

    options = parser.parse_args()
    work(options.config_path, options.out_put_path)
