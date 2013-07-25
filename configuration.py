import ConfigParser
from os import path

class Configuration(object):
    '''This configuration is set interactively by the user. It can be recalled and used again later.
    For now, the implementation is that this config simply replaces the earlier README file that contained the 
    experiment details.'''

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
            
if __name__ == "__main__":
    Configuration().read_config()
    Configuration().write_config_file()