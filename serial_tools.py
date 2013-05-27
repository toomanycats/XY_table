import serial
import re
from time import sleep
import subprocess

class SerialTools(object):

    def __init__(self):
        self.con = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.origin_pos = 0
        self.current_pos = self.origin_pos
        self.choose_port()     
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

    def getPosition(self):
        self.flush()
        self.con.write('PR P\r\n')
        pat = '[0-9]+\r\n'
        output = self._loop_structure(pat)
        
        return float(output.replace('\r\n',''))

    def move_rel(self, x_dist):
        self.flush()
        sleep(0.1)
        self.write('MR %f' %x_dist)
        sleep(0.1)
        self.current_pos = self.current_pos + self.getPosition()
        
        print "Moved: %(x_dist)s , New Pos: %(pos)s " %{'x_dist':x_dist,'pos':self.current_pos}
            
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
        self._set_var('DN',"%s" %name)   
        print "Device name: %s" %self.getDeviceName()
        
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

    def getDeviceName(self):
        self.con.flushOutput()
        self.con.write('PR DN\r\n')
        sleep(0.1)
        # the name returns like: '"Name"\r\n'
        pat = '".*"\r\n'
        DeviceName = self._loop_structure(pat)
        self.DeviceName = DeviceName.replace('\r\n','')

    def _loop_structure(self, pat):
        sleep(0.1)
        re_obj = re.compile(pat)
        self.readback = self.con.readlines()
        for item in self.readback:
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
        cmd = '''dmesg | grep -G ".*cp210x.*attached.*" | grep "*ttyUSB*"'''
        p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if error:
            print "Error in calling bash for port info: %s" %error
        print output + '\n'                
