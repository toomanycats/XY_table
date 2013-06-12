import motor_tools
import code_tools
from vna_tools import VnaTools

config = code_tools.ConfigureDataSet()

config.DirectoryName = 'test'
config.FreqStart = 10e9 
config.FreqStop =  15e9

Con = motor_tools.Connection()
Con.set_port()

mx = motor_tools.Motor()
mx.con.port = Con.x_port
mx.open()
mx.MicroStep = mx._get_ms()
mx._set_var('P',0)
mx._set_var('A',51200)

my = motor_tools.Motor()
my.con.port = Con.y_port
my.open()
my.MicroStep = my._get_ms()
my._set_var('P',0)
my._set_var('A',51200)

vna = VnaTools(config)
vna.setup()
#mx.move_rel(0.005)
vna.clear()

pass