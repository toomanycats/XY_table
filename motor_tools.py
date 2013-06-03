import serial
import re
from time import sleep
import subprocess
#testing branch changes and merge back to master
class MotorTools(object):

    def __init__(self):
        self.con = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.MicroStep = '256'
        self.OriginPos = 0
        self.CurrentPos = 0
        self.choose_port()
        sleep(0.2)
        self.DeviceName = self._getDeviceName()
        self.Error_codes = {20:'Tried to set unknown variable or flag',
                       21:'Tried to set an incorrect value',
                       30:'Unknown label or user variable',
                       24:'Illegal data entered'
                        }
        
    def choose_port(self):
        print """The device log will now be printed for you to inspect and choose the port.
The port will /dev/ttyUSB[0-9].\n\n"""
        self._inspect_port_log()
        motor_port = raw_input('Enter the numerical portion of the port,i.e. 0,1,2 etc.\n\n')
        self.con.port = '/dev/ttyUSB%s' %motor_port
        try:
            self.con.open()
        except serial.SerialException:
            print "Connection to motor unsuccessful.\n"
                
        if self.con.isOpen():
            print "Connection to motor successful on port %s \n" %self.con.port
  
    def clear_error(self):
        print "clearing errors \n"
        self.write('PR ER')
        sleep(0.1)
        self.write('PR EF')
        sleep(0.1)
        self.con.readlines()

    def set_pos(self, pos):
        if not isinstance(pos,int):
            print "Enter an integer only."
            return
        self._set_var('P',pos)
        self.CurrentPos = pos

    def _get_position(self):
        self.flush()
        self.con.write('PR P\r\n')
        pat = '\-*[0-9]+\r\n'
        output = self._loop_structure(pat)

        return int(output.replace('\r\n',''))

    def move_rel(self, x_dist):
        self.flush()
        sleep(0.1)
        self.write('MR %i' %x_dist)
        sleep(0.1)
        self.CurrentPos = self._get_position()
        print "Moved: %(x_dist)s , New Pos: %(pos)s " %{'x_dist':x_dist,'pos':str(self.CurrentPos)}
            
    def write(self, arg, echk = False):
        self.con.write("%s\r\n" %arg)
        sleep(0.1)
        list = self.con.readlines()
        print list
        if echk == True:
            self._check_for_mcode_error()

    def _set_var(self, var, val, echk = False):
        string = '\r%(var)s=%(val)s\r' %{'var':var,'val':val}
        self.con.write(string)
        sleep(0.1)
        if echk == True:
            self._check_for_mcode_error()
        sleep(0.1)
        output = self.write('PR %s' %var)# mdrive echoes input
    
    def set_micro_step(self, val, echk = True):
        self._set_var('MS', str(val), echk)

    def set_device_name(self, name, echk = False):
        pat = '[A-Z]'
        if not re.match(pat, name):
            print "Names must be one Char only.\n"
            return 
        self._set_var('DN','"%s"' %name)
        sleep(0.2)
        self.DeviceName = self._getDeviceName()

    def flush(self):
        self.con.flushInput()
        sleep(0.2)
        self.con.flushOutput()
        sleep(0.2)

    def _check_for_mcode_error(self):
        pat = '.*\?.*'
        item = self._loop_structure(pat)
        if item is not "unknown":
            self._get_error_code()

    def _get_error_code(self):
        self.con.flushOutput()
        self.con.write('PR ER\r\n')
        pat = '[0-9]+\r\n'
        error_code = self._loop_structure(pat)
        error_code = int(error_code.replace('\r\n',''))
        if self.Error_codes.has_key(error_code):
            print self.Error_codes[error_code]
        else:
            print "Error code %i was raised by the motor." %error_code

    def _getDeviceName(self):
        self.flush()
        sleep(0.1)
        self.con.write('PR DN\r\n')
        sleep(0.2)
        # the name returns like: '"Name"\r\n'
        pat = '"[A-Z]"\r\n|"!"\r\n'
        DeviceName = self._loop_structure(pat)
        return DeviceName.strip('\n').strip('\r')

    def _loop_structure(self, pat):
        sleep(0.1)
        re_obj = re.compile(pat)
        readback = self.con.readlines()
        for item in readback:
            if re_obj.match(item) is not None:
                return item
        return "unknown"

    def reset(self):
        self.flush()
        self.clear_error()
        print "Returning to factory defaults and rebooting motor.\n"
        self.write('FD')
        sleep(3)
        self._send_control_C()

    def _send_control_C(self):
        self.write('\03')
        sleep(2)
        print self.con.readlines()

    def _inspect_port_log(self):
        '''for determing the ports of the serial-USB adaptors'''
        cmd = '''dmesg | grep -G ".*cp210x.*attached.*" | grep ".*ttyUSB*" | tail -5'''
        p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if error:
            print "Error in calling bash for port info: %s" %error
        print output + '\n' 

    def close(self):
        self.con.close()
        bool = self.con.isOpen()
        if bool is False:
            print "Motor port closed"
        else:
            print "Closing motor failed, still connected"
