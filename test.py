import motor_tools
import code_tools
from vna_tools import VnaTools

config = code_tools.ConfigureDataSet()

config.DirectoryName = 'test'
config.FreqStart = None
config.FreqStop =  None
config.Origin = None

motor = code_tools.Main()

# Con = motor_tools.Connection()
# Con.set_port()
# 
# mx = motor_tools.Motor()
# mx.con.port = Con.x_port
# mx.open()
# mx.clear_error()
# mx.MicroStep = mx._get_ms()
# mx._set_var('S1','2,0,0')
# mx._set_var('LM', 2)
# mx._set_var('P',0)
# mx._set_var('A',51200)
# 
# my = motor_tools.Motor()
# my.con.port = Con.y_port
# my.open()
# my.clear_error()
# my.MicroStep = my._get_ms()
# my._set_var('P',0)
# my._set_var('A',51200)
# my._set_var('S1','2,0,0')
# my._set_var('LM', 2)


print "pause"
# put vna instantiate into Main() as well.
vna = VnaTools(config)
vna.clear()

