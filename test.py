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

my = motor_tools.Motor()
my.con.port = Con.y_port
my.open()

vna = VnaTools(config)

#mx.move_rel(0.005)
vna.clear()

pass