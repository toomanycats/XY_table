#!/usr/bin/python
import os
import sys
import re
from PIL import Image 
from PIL.ExifTags import TAGS

class find_gps_data(object):
    def __init__(self, root):
        self.root = root
        self.pos_list = []
        self.error_list = ''
        self.exif_data = {}

    def find_data(self):
        self.check_path()
        self.walk(self.root)   
        if self.pos_list:
            print "The following files have some kind of GPS data in them: \n"
            for file in self.pos_list:
                print file
        else:
            print "No GPS data found."
    
    def check_path(self):
        if not os.path.exists(self.root):
            print "The path %s does not exist, exiting program." % self.root
            sys.exit()
        
    def walk(self, root):
        #print root
        for root, dirs, files in os.walk(root):
            if files is not None:
                for file in files:
                    self.find_jpgs(os.path.join(root,file))
            if dirs is not None:
                for dir in dirs:
                    self.walk(os.path.join(root, dir))
    
    def find_jpgs(self, path):
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
        for k,v in img._getexif().items():
            if k in TAGS.keys():
                self.exif_data[TAGS.get(k)] = v 
    
    def check_file(self,path):
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
            
            
#if __name__ == '__main__':
#    print "Starting program to find GPS meta data in JPG files. \n"
#    gps_data = find_gps_data.find_gps_data(str(sys.argv[1])).find_data()
    
        
            
            