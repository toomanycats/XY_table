import serial
import re
from time import sleep
import subprocess
from code_tools import CodeTools
import code_tools

class Connection(object):
    def __init__(self):
        self.con1 = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.con2 = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.connection_attempts = 0
        
    def _get_sn(self, con):
        '''Query the motor for it's serial number. '''
        con.flushInput()
        sleep(0.5)
        con.flushOutput()
        sleep(0.5)
        con.write('PR SN\r\n')
        sleep(0.5)
        pat = "[0-9]{9}\\r\\n|[0-9]{9}\\n"
        sn = self._loop_structure(con, pat)
        print sn
        sn = sn.replace('\r\n','')

        return sn
     
    def connect_to_ports(self):
        '''Try to open motors on ports 0-9. Returns motor objects mx, my . '''
        x_port_flag = False
        y_port_flag = False
        
        for port in xrange(0,9):
            try:
                if x_port_flag is True and y_port_flag is True:
                    return self.motor_x, self.motor_y 

                if x_port_flag is False and y_port_flag is False: 
                    self.con1.port = '/dev/ttyUSB%s' %port
                    self.con1.open()
                    sleep(2)
                    sn = self._get_sn(self.con1)
                    x_port_flag, y_port_flag = self.assign_serial_num(sn, x_port_flag, y_port_flag, self.con1)
                else:
                    self.con2.port = '/dev/ttyUSB%s' %port  
                    self.con2.open()
                    sleep(2)
                    sn = self._get_sn(self.con2) 
                    x_port_flag, y_port_flag = self.assign_serial_num(sn, x_port_flag, y_port_flag, self.con2)        

            except serial.SerialException:
                print "%s is not a connected port, trying next.\n" %port

        if x_port_flag is False or y_port_flag is False:
            print "Connection failed waiting 5 seconds and trying again.\n"
            try:
                self.con1.close()
                self.con2.close()
            except:
                pass  
            if self.connection_attempts < 4:  
                sleep(5)
                self.connection_attempts += 1
                self.connect_to_ports()
            else:    
                raise Exception, "The x or y motor has not been connected, 4 attempts have been made.\n"     

    def _loop_structure(self, con, pat):
        '''A method used to complete all the queries in this class. The mdrive motor
        echos all sent commands and returns values as a list. This method uses regex to 
        sift out the desired information for that list. Notice the pattern sent in is a
        regex pattern pertinent to the task at hand.'''
        sleep(0.1)
        re_obj = re.compile(pat)
        readback = con.readlines()
        for item in readback:
            if re_obj.match(item) is not None:
                return item

        return "unknown"

    def assign_serial_num(self, sn, x_port, y_port, con):
        if sn == '269120375' and y_port is False:
            y_port = True
            self.motor_y = Motor(con)
            
        elif sn == '074130197' and x_port is False:
            x_port = True
            self.motor_x = Motor(con)
            
          
        return x_port, y_port    

class Motor(object):
    '''This is a collection of methods which control an Mdrive 23 step motor. '''
    
    def __init__(self, serial_con):
        #self.con = serial.Serial(None, 9600, timeout = 0, writeTimeout = 0)
        self.con = serial_con
        self.codetools = CodeTools()
        self._steps_per_rev =  {'256':51200,'128':25600,'64':12800,'32':6400,
                                '16':3200,'8':1600,'4':800,'2':400,'1':200,
                                '250':50000,'200':40000,'125':25000,'100':2000,
                                '50':10000,'25':5000,'10':2000,'5':1000}
        self._meters_per_rev = 0.005 
        '''5mm per 1 full revolution '''
        self.Error_codes = {20:'Tried to set unknown variable or flag',
                       21:'Tried to set an incorrect value',
                       30:'Unknown label or user variable',
                       24:'Illegal data entered',
                       25: 'Tried to set a read only variable'
                         }
        
    def main(self, acceleration, max_vel, init_vel):
        '''Sets the basic parameters of the motor. '''
        self.clear_error()
        self.MicroStep = self._get_ms()
        self._set_var('S1','3,0,0') # limit switch for home 
        self._set_var('S2','2,0,0')# limit switch for farthest end
        self._set_var('LM', 2)# decel ramp, stops all motion that dir
        self._set_var('A',acceleration) # acceleration
        self._set_var('VM',max_vel)# max velocity
        self._set_var('VI',init_vel)# initial velocity
       
    def _check_reached_limit_switch(self):
        '''Query the motor to determine if either limit switch has been reached. Returns 
        True is a limit has been tripped or False if it has not. '''
        error_status = False
        self.con.write('PR ER\r\n')#check if reached limit switch
        sleep(0.1)
        pat = '83\r\n|84\r\n' # boolean "or" in the regex
        out_put = self._loop_structure(pat)
        if out_put == '83\r\n' or out_put == '84\r\n':
            error_status = True    
        if out_put == '84\r\n':
            print "Reached limit switch at HOME. \n"
            self.y_lock = True
        elif out_put == '83\r\n':
            print "Reached limit switch at farthest end. \n"    

        return error_status
    
    def clear_error(self):
        '''Query the motor for errors, return the error code and clear the errors. '''
        print "clearing errors \n"
#        self._set_var('ER', 0, True) # error code
        self.write('PR ER')
        self.write('ER 0') # not using _set_var() b/c there's not = sign used for this op
#         sleep(0.1)
#         self.write('PR EF')
#         sleep(0.1)
#         self.con.readlines()

    def _set_step(self, step):
        '''Set the number of steps that the motor uses for a full rotation. '''
        if not isinstance(step,int):
            print "Enter an integer only."
            return
        self._set_var('P',step)
        self.CurrentPos = self._calculate_pos(step)
    
    def _calculate_pos(self, steps):
        '''Calculate the position of the motor using the conversion factors.
        X steps * 1 rev/Y steps * 5 mm/1 rev '''
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
        '''How many steps it takes to get to a linear dist input.'''
        steps = float(linear_dist)/self._meters_per_rev * float((self._steps_per_rev[str(self.MicroStep)]))
         
        return int(round(steps)) 
 
    def _motor_stopped(self):
        '''Used as a poll of the location of a motor, so that the program can spit out the 
        new position after the motor has arrived. It also checks if a limit switch has been 
        tripped. '''
        Flag = True
        self.con.flushOutput()# readlines() flushes the output too
        sleep(0.1)
        while Flag:
            self.con.write('PR MP\r\n') # flag for moving to position
            sleep(0.5)
            list = self.con.readlines()
            if list[2].strip('\r\n') == '0': 
                Flag = False       

    def return_home(self):
        '''Return the motor to home position, which is at the limit switch in the bottom left corner. '''
        self.clear_error()
        error_status = False
        self.con.write('SL -51200')# 5mm per second
        while error_status == False:
            error_status = self._check_reached_limit_switch()
        self.write('SL 0') # stop the slew movement
        sleep(0.1)
        self.clear_error()
        sleep(0.1)
        self.set_pos_as_start()

    def move_rel(self, linear_dist):
        '''Tell the motor to move a linear distance as a relative position.'''
        steps = self._calc_steps(linear_dist)
        sleep(0.1)
        self.write('MR %i' %steps, echk = True)
        self._motor_stopped()
        self._CurrentStep = self._get_current_step()
        self.CurrentPos = float(self._calculate_pos(self._CurrentStep))
        print "New Pos: %s " %self.codetools.ToSI(self.CurrentPos)
        limit_flag = self._check_reached_limit_switch()
        if limit_flag:
            self.clear_error()
                  
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
        self.con.flushOutput()
        sleep(0.1)
        self.con.write('PR EF\r\n')
        sleep(0.1)
        list = self.con.readlines() #output: ['PR EF\r\n', '\n', '1\r\n', '>']
        if list[2].strip('\r\n') == '1':
            self._get_error_code()
        #pat = '.*\?.*'
        #item = self._loop_structure(pat)
        #if item is not "unknown":
        #     self._get_error_code()

    def _get_error_code(self):
        self.con.write('PR ER\r\n')
        pat = '[1-9]+\r\n'
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
        #sleep(0.3)
        self.con.open()

    def set_pos_as_start(self):
        '''Using the limit swictches, the motors return to home, 
        then this pos is set as the start.'''
        self._set_var('P', 0, True)
        self._CurrentStep = 0
        self.CurrentPos = 0

    def move_absolute(self, pos):
        '''Move the motor to an absolute position wrt to the limit switch HOME. '''
        steps = self._calc_steps(pos)
        self.con.write('MA %i\r\n' %steps)
        sleep(0.1)
        self._motor_stopped()
        self._CurrentStep = self._get_current_step()
        self.CurrentPos = float(self._calculate_pos(self._CurrentStep))

                
           
        
        
