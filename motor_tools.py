import serial
import re
from time import sleep
import subprocess
from code_tools import CodeTools

class Connection(object):
    def __init__(self):
        self.serial_con = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.x_port = None
        self.y_port = None
        sleep(0.3)
        
    def _uniq(self,input):
        output = []
        for x in input:
            if x not in output:
                output.append(x)
        return output
    
    def _get_sn(self):
        self.serial_con.write('PR SN\r\n')
        sleep(0.2)
        pat = '[0-9]{9}\r\n'
        out = self._loop_structure(pat)
        out = out.replace('\r\n','')
        return out
     
    def set_port(self):
        sleep(0.2)
        port_list = self._inspect_port_log()
        unique_ports = self._uniq(port_list)
        for port in unique_ports:
            try:
                if self.x_port is not None and self.y_port is not None:
                    break     
                self.serial_con.port = '/dev/ttyUSB%s' %port
                self.serial_con.open()
                sleep(0.3)
                sn = self._get_sn()
                if sn == '269120375' and self.y_port is None:
                    self.y_port = self.serial_con.port
                    self.serial_con.close()
                elif sn == '074130197' and self.x_port is None:
                    self.x_port = self.serial_con.port  
                    self.serial_con.close()      
            except serial.SerialException:
                print "%s is not a connected port, trying next.\n" %self.serial_con.port
        if self.y_port is None:
            raise Exception, "Y port not set. Could be a delay issue."
        if self.x_port is None:
           raise Exception, "X port not set, Could be a delay issue."      
        sleep(1) 
          
    def _inspect_port_log(self):
        '''for determing the ports of the serial-USB adaptors'''
        cmd = '''dmesg | grep -w ".*cp210x.*attached.*" | grep -o "ttyUSB[0-9]" | grep -o [0-9]'''
        p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if error:
            print "Error in calling bash for port info: %s" %error
        return output.split() #turn string into list

    def _loop_structure(self, pat):
        sleep(0.1)
        re_obj = re.compile(pat)
        readback = self.serial_con.readlines()
        for item in readback:
            if re_obj.match(item) is not None:
                return item
        return "unknown"

class Motor(Connection):
    
    def __init__(self):
        #self.con = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.con = Connection().serial_con
        self.codetools = CodeTools()
        self._LIMIT_METERS = 0.26 # maximum travel in meters
        self.CurrentPos = 0.0
        self._CurrentStep = 0
        self._steps_per_rev =  {'256':51200,'128':25600,'64':12800,'32':6400,
                                '16':3200,'8':1600,'4':800,'2':400,'1':200,
                                '250':50000,'200':40000,'125':25000,'100':2000,
                                '50':10000,'25':5000,'10':2000,'5':1000}
        self._meters_per_rev = 0.005 
        '''5mm per 1 full revolution '''
        self.Error_codes = {20:'Tried to set unknown variable or flag',
                       21:'Tried to set an incorrect value',
                       30:'Unknown label or user variable',
                       24:'Illegal data entered'
                        }
    
    def clear_error(self):
        print "clearing errors \n"
        self.write('PR ER')
        sleep(0.1)
        self.write('PR EF')
        sleep(0.1)
        self.con.readlines()

    def set_step(self, step):
        if not isinstance(step,int):
            print "Enter an integer only."
            return
        self._set_var('P',step)
        self.CurrentPos = self._calculate_pos(step)
    
    def _calculate_pos(self, steps):
        '''Current step aggregates automatically. '''
        CurrentPos =  steps * (1.0/(self._steps_per_rev[str(self.MicroStep)])) * self._meters_per_rev
        '''position = X steps * 1 rev/Y steps * 5 mm/1 rev '''

        return CurrentPos  

    def _get_ms(self):
        self.flush()
        sleep(0.1)
        self.con.write('PR MS\r\n')
        sleep(0.1)
        pat = '[0-9]+\r\n'
        ms = self._loop_structure(pat)

        return  int(ms.strip('\n').strip('\r'))

    def _get_current_step(self):
        self.flush()
        self.con.write('PR P\r\n')# P is really the step
        pat = '\-*[0-9]+\r\n'
        output = self._loop_structure(pat)
        
        return int(output.strip('\r\n'))

    def _calc_steps(self,linear_dist):
        steps = float(linear_dist)/self._meters_per_rev * float((self._steps_per_rev[str(self.MicroStep)]))
         
        return int(round(steps)) 

    def _check_limits(self, steps):
         new_pos = self.CurrentPos + self._calculate_pos(steps)
         if new_pos >= self._LIMIT_METERS:
             print "You have asked for a new position that will exceed the LIMIT variable. \n"
             return True
         else:
             return False
  
    def _query_pos(self, target):
        Flag = False
        while Flag == False:
            sleep(0.10)
            current_step = self._get_current_step()
            sleep(0.10)
            current_pos = float(self._calculate_pos(current_step))
            #print current_pos
            self.con.write('PR ER\r\n')#check if reached limit switch
            pat = '83\r\n|84\r\n'
            error_status = self._loop_structure(pat)
            if current_pos == target or error_status == '83\r\n':
                Flag = True

    def move_rel(self, linear_dist):
        steps = self._calc_steps(linear_dist)
        #print "steps: %i " %steps ;print "\n"
        if self._check_limits(steps):# True is a fail on limits
            print "Attemping to move outside limits \n"
            return
        #self.flush()
        sleep(0.1)
        self.write('MR %i' %steps)
        self._query_pos(linear_dist + self.CurrentPos)
        self._CurrentStep = self._get_current_step()
        self.CurrentPos = float(self._calculate_pos(self._CurrentStep))
        print "New Pos: %s " %self.codetools.ToSI(self.CurrentPos)
                  
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
        sleep(0.2)
        self.MicroStep = self._get_ms()

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
        sleep(0.1)
        self.con.flushOutput()
        sleep(0.1)

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
        sleep(0.1)
        self.flush()
        sleep(0.1)
        self.clear_error()
        sleep(0.1)
        print "Returning to factory defaults and rebooting motor.\n"
        self.write('FD')
        sleep(3)
        self._send_control_C()
        self._CurrentStep = 0
        self.CurrentPos = 0
           
    def _send_control_C(self):
        self.write('\03')
        sleep(2)
        print self.con.readlines()

    def close(self):
        sleep(0.1)
        self.con.close()
        bool = self.con.isOpen()
        if bool is False:
            print "Motor port closed"
        else:
            print "Closing motor failed, still connected"
            
    def open(self):
        sleep(0.3)
        self.con.open()            
