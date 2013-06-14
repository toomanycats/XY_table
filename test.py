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
>>>>>>>>>>>>>>>>>>>> File 1
mx.clear_error()
mx.MicroStep = mx._get_ms()

my._set_var('S1','2,0,0')
my._set_var('LM', 2)

mx._set_var('P',0)
mx._set_var('A',51200)
>>>>>>>>>>>>>>>>>>>> File 2
mx.MicroStep = mx._get_ms()
mx._set_var('P',0)
mx._set_var('A',51200)
>>>>>>>>>>>>>>>>>>>> File 3
<<<<<<<<<<<<<<<<<<<<

my = motor_tools.Motor()
my.con.port = Con.y_port
my.open()
>>>>>>>>>>>>>>>>>>>> File 1
mx.clear_error()
my.MicroStep = my._get_ms()
my._set_var('P',0)
my._set_var('A',51200)

my._set_var('S1','2,0,0')
my._set_var('LM', 2)


print "pause"
>>>>>>>>>>>>>>>>>>>> File 2
my.MicroStep = my._get_ms()
my._set_var('P',0)
my._set_var('A',51200)
>>>>>>>>>>>>>>>>>>>> File 3
<<<<<<<<<<<<<<<<<<<<

vna = VnaTools(config)
>>>>>>>>>>>>>>>>>>>> File 1
vna.setup()
>>>>>>>>>>>>>>>>>>>> File 2
vna.setup()
>>>>>>>>>>>>>>>>>>>> File 3

<<<<<<<<<<<<<<<<<<<<
#mx.move_rel(0.005)
vna.clear()

pass
