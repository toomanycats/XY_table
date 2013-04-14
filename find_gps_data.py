#!/usr/bin/python
import os
import sys
import re
from PIL import Image 
from PIL.ExifTags import TAGS

class find_gps_data(object):
    """
    This class uses the PIL to access exif data for evidence of GPS information hidden in jpg's. 
    Specifically, it checks for the presence of the gpsinfo tag.
    """
    def __init__(self, root):
        self.root = root
        self.pos_list = []
        self.error_list = ''
        self.exif_data = {}

    def find_data(self):
        """This the main(). """
        self.check_path()
        self.walk(self.root)   
        if self.pos_list:
            print "The following files have some kind of GPS data in them: \n"
            for file in self.pos_list:
                print file
        else:
            print "No GPS data found."
    
    def check_path(self):
        """Error checking the input path argument. """
        if not os.path.exists(self.root):
            print "The path %s does not exist, exiting program." % self.root
            sys.exit()
        
    def walk(self, root):
        """ Generate the list of dirs and files to walk while looking for jpg's. """
        print "root dir is: %s" % root
        for root, dirs, files in os.walk(root):
            if files is not None:
                for f in files:
                    self.find_jpgs(os.path.join(root,f))
            if dirs is not None:
                for dir in dirs:
                    print "dir is: %s" % dir
                    self.walk(os.path.join(root, dir))
                  
    def find_jpgs(self, path):
        """Search the individual files returned from walk() 
        and append paths for jpegs that test positive for the gpsinfo tag. """
        #print path
        if not os.path.isdir(path) and path[-3:].lower() == 'jpg' or  path[-4:].lower() == 'jpeg':
                pos = self.check_file(path)
                if pos is not None:
                    self.pos_list.append(pos)
    
    def walk_dirs(self, root, dirs):
        if dirs is not None:
            for dir in dirs:
                objs = os.walk(os.path.join(root,dir))
                for ob in objs:
                    if not os.path.isdir(ob):
                        path = os.path.join(root,dir,ob)
                        print dir, ob
                        self.find_jpgs(path)
                    else:
                        walk_dirs(path,ob)
            
    def load_exif_data(self,img):
        """ Loads the char string values for the binary exif tags."""
        for k,v in img._getexif().items():
            if k in TAGS.keys():
                self.exif_data[TAGS.get(k)] = v 
    
    def check_file(self,path):
        """ Check an individual jpg for the gpsinfo tag."""
        #print "checking %s" %path
        try:
            img = Image.open(path)
            self.exif_data = self.load_exif_data(img)
            
            for k,v in self.exif_data.items():
                if k.lower() == 'gpsinfo' and v is not None: 
                    #print "File %s contains GPS data" %path
                    return path
                
        except Exception, self.error:
            if re.match(r'.*none.*type.*', self.error.message, re.IGNORECASE):
                pass
            elif re.match(r'_getexif', self.error.message):
                pass
            else:
                print "ERROR: " + self.error.message + '\n' + path + '\n'
            
            
    
        
            
            