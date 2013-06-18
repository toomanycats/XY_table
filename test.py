import motor_tools
import vna_tools
import code_tools

def loop_along_sample(dim3_array, config):
    data_point = 0
    for index_y in xrange(0,dim3_array.shape[1]):
        for index_x in xrange(0,dim3_array.shape[0]):
            do_stuff(data_point)
            data_point += 1
            motors.mx.move_rel(config.X_res)
        motors.mx.move_rel(-1*config.X_length)      
        motors.my.move_rel(config.Y_res)   


def do_stuff(data_point):
    data = vna.take_data()
    mag_data = arraytools.get_mag(data)
    arraytools.save_data(data_point)
    

config = code_tools.ConfigureDataSet()
config.DirectoryName = '/media/Data/test'
config.FileNamePrefix = 'test'
config.FreqStart = 7e9
config.FreqStop = 15e9
config.FreqRes = 51 
config.TestSet = 'S21' #transmition always for this experiment
config.X_length = 0.05
config.Y_length = 0.05
config.X_res = 0.01
config.Y_res = 0.01
config.Origin = 0.0

arraytools = code_tools.ArrayTools(config)
arraytools.save_readme()
dim3_array = arraytools.make_3d_array()

motors = motor_tools.Main(config)

vna = vna_tools.VnaTools(config)
vna.check_parameters()
vna.check_cal()

loop_along_sample(dim3_array, config)

# wrap everything in a try catch and email when error occurs
# print "Fatal error occurred, email-ing system admin."
# msg = trackback.print_last()
# self._notify_admin_error(msg)   