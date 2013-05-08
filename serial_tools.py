import serial
import re
#from time import sleep


class SerialTools(object):

    def __init__(self):
        self.con = serial.Serial('/dev/ttyUSB0',9600, timeout = 0)
        self.output = None

    def readback(self):
    	n = 1
        output = None
        
        while True:
       	    output = self.con.readline()
       	    if output == '\r\n':
                break 
            self.output = output    
            if self._check_for_mcode_error(self.output):
                break  
            

    def write(self, arg):
        self.con.write("%s\r\n" %arg)        
        self.readback()

    def flush(self):
        self.con.flushInput()
        self.con.flushOutput()

    def _check_for_mcode_error(self,arg):
        re_obj = re.compile('.*\?.*')
        if re_obj.match(arg) is not None:
            print  "\nError in motor code.\n"
            return False
