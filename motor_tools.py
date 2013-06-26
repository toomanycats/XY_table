import serial
import re
from time import sleep
import subprocess
from code_tools import CodeTools
import code_tools

class Connection(object):
    '''This class determines the port of the X and Y motors. '''
    def __init__(self):
        self.serial_con = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.x_port = None
        self.y_port = None
        
    def _uniq(self,input):
        '''Shorten the list of ports returned frm the dmesg call in _inspect_port_log(),
        so that set_port() doesn't repeat on ports already tried.'''
        output = []
        for x in input:
            if x not in output:
                output.append(x)
        return output
    
    def _get_sn(self):
        '''Query the motor for it's serial number. '''
        self.serial_con.write('PR SN\r\n')
        sleep(0.2)
        pat = '[0-9]{9}\r\n'
        out = self._loop_structure(pat)
        out = out.replace('\r\n','')
        return out
     
    def set_port(self):
        '''Try to open motors on ports and set the primitive class's port string. '''
        
        print """Set ports routine running...This will take about 25 sec to run b.c we need
        to wait for the  port to reset after discovering the serial numbers."""
        
        port_list = self._inspect_port_log()
        unique_ports = self._uniq(port_list)
        for port in unique_ports:
            try:
                if self.x_port is not None and self.y_port is not None:
                    break     
                self.serial_con.port = '/dev/ttyUSB%s' %port
                self.serial_con.open()
                sn = self._get_sn()
                if sn == '269120375' and self.y_port is None:
                    self.y_port = self.serial_con.port
                    self.serial_con.close()
                    sleep(10)
                elif sn == '074130197' and self.x_port is None:
                    self.x_port = self.serial_con.port  
                    self.serial_con.close() 
                    sleep(10)     
            except serial.SerialException:
                print "%s is not a connected port, trying next.\n" %self.serial_con.port
        if self.y_port is None:
            raise Exception, "Y port not set. The port might not have reset yet. Try again."
        if self.x_port is None:
           raise Exception, "X port not set. The port might not have reset yet. Try again."       
          
    def _inspect_port_log(self):
        '''Use dmesg in the bash shell, to get a list of possible USB ports.'''
        cmd = '''dmesg | grep -w ".*cp210x.*attached.*" | grep -o "ttyUSB[0-9]" | grep -o [0-9]'''
        p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if error:
            print "Error in calling bash for port info: %s" %error
        return output.split() #turn string into list

    def _loop_structure(self, pat):
        re_obj = re.compile(pat)
        readback = self.serial_con.readlines()
        sleep(0.1)
        for item in readback:
            if re_obj.match(item) is not None:
                return item
        return "unknown"


class Motor(Connection):
    '''This is a collection of methods which control an Mdrive 23 step motor. '''
    
    def __init__(self, Config):
        self.config = Config
        self.con = Connection().serial_con
        self.codetools = CodeTools()
        self._LIMIT_METERS = 0.1 # maximum travel in meters
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
        '''Query the motor for the current microstep setting. '''
        self.flush()
        sleep(0.1)
        self.con.write('PR MS\r\n')
        sleep(0.1)
        pat = '[0-9]+\r\n'
        ms = self._loop_structure(pat)

        return  int(ms.strip('\n').strip('\r'))

    def _get_current_step(self):
        '''Return the current step or position 'P' of the motor. '''
        self.flush()
        self.con.write('PR P\r\n')# P is really the step
        pat = '\-*[0-9]+\r\n'
        output = self._loop_structure(pat)
        
        return int(output.strip('\r\n'))

    def _calc_steps(self,linear_dist):
        '''How many steps it takes to get somewhere.'''
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
        '''Used as a poll of the location of a motor, so that the program can spit out the 
        new position after the motor has arrived. It also checks if a limit switch has been 
        tripped. '''
        Flag = False
        while Flag == False:
            current_step = self._get_current_step()
            sleep(0.07)
            current_pos = float(self._calculate_pos(current_step))
            #print current_pos
            self.con.write('PR ER\r\n')#check if reached limit switch
            sleep(0.07)
            pat = '83\r\n|84\r\n'
            error_status = self._loop_structure(pat)
            if abs(current_pos - target) < 1e-6 or error_status == '83\r\n':
                Flag = True

    def move_rel(self, linear_dist):
        '''Tell the motor to move a linear distance as a relative position.'''
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
        '''Write a command to the motor where the lines feed and carriage return are automatically included.
        This is unlike the primitive class pySerial where you must send the \r\n . '''
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
        '''A micro step is a division of a 2pi rotation into smaller steps.
         Default is 256 which is the finest resolution. THere are choices in powers of two and
         decimal amounts. '''
        self._set_var('MS', str(val), True)
        sleep(0.2)
        self.MicroStep = self._get_ms()

    def set_device_name(self, name, echk = False):
        '''No longer used. All motor names are "!" '''
        pat = '[A-Z]'
        if not re.match(pat, name):
            print "Names must be one Char only.\n"
            return 
        self._set_var('DN','"%s"' %name)
        sleep(0.2)
        self.DeviceName = self._getDeviceName()

    def flush(self):
        '''Flush the input and output buffers of the motor. '''
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
        '''A method used to complete all the queries in this class. The mdrive motor
        echos all sent commands and returns values as a list. This method uses regex to 
        sift out the desired information for that list. Notice the pattern sent in is a
        regex pattern pertinent to the task at hand.'''
        sleep(0.1)
        re_obj = re.compile(pat)
        readback = self.con.readlines()
        for item in readback:
            if re_obj.match(item) is not None:
                return item
        return "unknown"

    def reset(self):
        '''Flush the input and output buffer, clear errors and send Control C. '''
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
        '''Flush the motors and close the serial connection. '''
        self.flush()
        sleep(0.1)
        self.con.close()
        bool = self.con.isOpen()
        if bool is False:
            print "Motor port closed"
        else:
            print "Closing motor failed, still connected"
            
    def open(self):
        '''Open a connection to a motor. Uses pySerial instance called self.con.'''
        sleep(0.3)
        self.con.open()

    def set_pos_as_start(self):
        '''Using the limit swictches, the motors return to home, 
        then this pos is set as the start.'''
        self._set_var('P', 0, True)
        self._CurrentStep = self._get_current_step()
        self.CurrentPos = self._calculate_pos(self._CurrentStep)

    def return_to_sample_origin(self, origin):
        '''Return the sample to the origin set in the config object. '''
        steps = self._calc_steps(origin)
        self.con.write('MA %i\r\n' %steps)
    
    def set_pos_as_sample_origin(self, axis):
        '''Arg is the axis name, 'x' or 'y'. Set this position as the origin of the sample.
        Recall: steps are always aggregate, and the zeros position is always defined wrt to the 
        'HOME' position set by the limit switches. '''
        axis = axis.lower()
        if axis == 'x':
            self.config.X_origin = self._calculate_pos(self._CurrentStep)
        elif axis == 'y':
            self.config.Y_origin = self._calculate_pos(self._CurrentStep)


class Main(object):
    '''This could be a main method in Motor as well.This object created an instance of Motor
    and sets up them motor with the standard user presets used in the lab.'''
    def __init__(self, Config, set_ports = False):
        if set_ports == True:
            Con = Connection() 
            Con.set_port()
            
            self.mx = Motor(Config)
            self.mx.con.port = Con.x_port
            self.mx.open()
            self.mx.clear_error()
            self.mx.MicroStep = self.mx._get_ms()
            self.mx._set_var('S1','2,0,0')
            self.mx._set_var('LM', 2)
            self.mx._set_var('P',0)
            self.mx._set_var('A',51200)
            
            self.my = Motor(Config)
            self.my.con.port = Con.y_port
            self.my.open()
            self.my.clear_error()
            self.my.MicroStep = self.my._get_ms()
            self.my._set_var('P',0)
            self.my._set_var('A',51200)
            self.my._set_var('S1','2,0,0')
            self.my._set_var('LM', 2)
          
        else: 
            self.mx = Motor(Config)
            self.mx.con.port = Config.x_port
            try:
                self.mx.open()
                print "Connected to X motor on port %s \n" %Config.x_port
                self.mx.clear_error()
                self.mx.MicroStep = self.mx._get_ms()
                self.mx._set_var('S1','2,0,0')
                self.mx._set_var('LM', 2)
                self.mx._set_var('P',0)
                self.mx._set_var('A',51200)
            
            except serial.SerialException:
                print "The port for the x motor is incorrect. Run set_ports = True."
                
            self.my = Motor(Config)
            self.my.con.port = Config.y_port
            try:
                self.my.open()
                print "Connected to Y motor on port %s \n" %Config.y_port
                self.my.clear_error()
                self.my.MicroStep = self.my._get_ms()
                self.my._set_var('P',0)
                self.my._set_var('A',51200)
                self.my._set_var('S1','2,0,0')
                self.my._set_var('LM', 2)
            
            except serial.SerialException:
                print "The port for the y motor is incorrect. Run set_ports = True."
             
        
        