import serial
import re
from time import sleep

class SerialTools(object):

    def __init__(self):
        self.con = serial.Serial('/dev/ttyUSB1',9600, timeout = 0, writeTimeout = 0)
        self.COUNT = 0.5
        
        self.Error_codes = {20:'Tried to set unkown variable or flag',
                       21:'Tried to set an incorrect value',
                       30:'Unknown label or user variable',
                       24:'Illegal data entered'
                        }
 
    def clear_error(self):
        self.write('PR ER')
        self.write('PR EF')

    def getPosition(self):
        self.con.write('PR P\r\n')
        pat = '[0-9]+\r\n'
        output = self._loop_structure(pat)
        return float(output.replace('\r\n',''))
            
    def write(self, arg, echk = False):
        self.con.write("%s\r\n" %arg)
        sleep(0.1)
        list = self.con.readlines()
        print list
        if echk == True:
            self._check_for_mcode_error()

    def set_var(self, var, val, echk = False):
        string = '\r%(var)s=%(val)s\r' %{'var':var,'val':val}
        self.con.write(string)
        sleep(0.1)
        output = self.write('PR %s' %var)
        print output
        
        if echk == True:
            self._check_for_mcode_error()
        
    def flush(self):
        self.con.flushInput()
        self.con.flushOutput()

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
        sleep(self.COUNT)
        # the name returns like: '"Name"\r\n'
        pat = '".*"\r\n'
        DeviceName = self._loop_structure(pat)
        self.DeviceName = DeviceName.replace('\r\n','')

    def _loop_structure(self, pat):
        sleep(self.COUNT)
        re_obj = re.compile(pat)
        self.readback = self.con.readlines()
        for item in self.readback:
            if re_obj.match(item) is not None:
                return item
        return "unknown"

    def reset(self):
        print "Please wait.\n"
        self.write('FD')
        sleep(2)
        self.send_control_C()

    def send_control_C(self):
        self.write('\03')
        print "Please wait.\n"
        sleep(2)
        print self.con.readlines()

    def _get_port_number(self):
        pass
        #cmd = """dmesg | grep -G ".*cp210x.*attached.*" | tail -l | sed -r 's/.*ttyUSB//'"""
        #(cmd)
        #return PORT
