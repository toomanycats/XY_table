import motor_tools
import vna_tools
import code_tools

def loop_along_sample(config):
    data_point = 0
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
    arraytools.save_data(data_point, mag_data)
    array3d[:,index_y, index_x] = mag_data
    ### testing, would like a handful of Z steps plotted
    half = np.floor(array3d.shape[0]/2)
    plottools.surface_plot(array3s[half,:,:])

config = code_tools.ConfigureDataSet()
config.DirectoryName = '/media/Data/test'
config.FileNamePrefix = 'test'
config.FreqStart = 7e9
config.FreqStop = 15e9
config.FreqRes = 401
config.TestSet = 'S21' #transmition always for this experiment
config.X_length = 0.05
config.Y_length = 0.05
config.X_res = 0.01
config.Y_res = 0.01
config.Origin = 0.0

arraytools = code_tools.ArrayTools(config)
arraytools.save_readme()

plottools = code_tools.PlotTools(config)
#make temp array to hold z values for plotting during the experiment
# mag are stored as col vector
array3d = np.zeros((config.FreqRes,config.Num_y_pts,config.Num_x_pts))

motors = motor_tools.Main(config)
print "pause"
vna = vna_tools.VnaTools(config)
vna.check_parameters()
vna.check_cal()

loop_along_sample(config)
motors.mx.close()
motors.my.close()
vna.close(16)
# wrap everything in a try catch and email when error occurs
# print "Fatal error occurred, email-ing system admin."
# msg = trackback.print_last()
# self._notify_admin_error(msg)   