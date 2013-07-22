import ConfigParser
from os import path

class Configuration(object):
    '''When adding sections or items, add them in the reverse order of
     how you want them to be displayed in the actual file.
     In addition, please note that using RawConfigParser's and the raw
     mode of ConfigParser's respective set functions, you can assign
     non-string values to keys internally, but will receive an error
     when attempting to write to a file or when you get it in non-raw
     mode. SafeConfigParser does not allow such assignments to take place.'''

    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        #self.config_path = config_path.join('/home/daniel/Documents/Git_repo/code_tools_config.cfg')
        self.config_path = path.join('home/daniel/config_test.cfg')

    def add_entries(self):
        self.config.add_section('Paths')
        self.config.set('Paths', 'Root_Data_Directory', '/media/Data')
        self.config.set('Paths', 'Root_Data_Test_Directory', '/media/Data/Testing_grounds')

    def read_config(self):
        '''Reads the config file and returns the config as a dictionary. '''
        self.config.read(self.config_path)
        
        # getfloat() raises an exception if the value is not a float
        # getint() and getboolean() also do this for their respective types
        data_path = self.config.get('Paths', 'Root_Data_Test_Directory')
  
        return {'data_path':data_path}
  
    def write_config_file(self):
        with open(self.config_path, 'wb') as configfile:
            self.config.write(configfile)