import gpib as g
import numpy as np
import time
import matplotlib.pyplot as mp
import scipy.io
import os
import datetime
import sys


mp.ion() #Turns on interactive plot mode, which allows user to use the terminal without closing the plot.
again='y'
dontoverwrite='y'
prevfilename="*example* DM_000"

#Gets the name of the current user for later use.
p=os.popen("whoami")
usersname=p.readline()
p.close
usersname=usersname[0:len(usersname)-1]

print ""
print "Address of VNA (Should be 16!):"
print g.find("VNA")

g.clear(16)
time.sleep(.5)

#Enable calibration. Usually done manually before running this prog.
#g.write(16,"CORRON")
#g.write(16,"CALS1")

#set format of data output to ascii. Affects only OUTPDATA, not queries.
g.write(16,"FORM4")

#Checks the parameter setting.
g.write(16, "PARA?")
param=g.read(16, 100)
if param=='"S12"\n':
     ystr="Transmission"
     print "You are taking TRANSMISSION(S12) data."
elif param=='"S11"\n':
     ystr="Reflection"
     print "You are taking REFLECTION(S11) data."
elif param=='"S21"\n':
     ystr="Transmission"
     print "You are taking TRANSMISSION(S21) data."
elif param=='"S22"\n':
     ystr="Reflection"
     print "You are taking REFLECTION(S22) data."

#Checks the CAL setting.
g.clear(16)
time.sleep(.5)
g.write(16,"CALS?")
cals=g.read(16, 100)[0] #Takes only the first char in the string.
if cals=='0':
     print "Calibration is OFF"
     calsstring="no cal"
else:
     print "You are under CAL set "+cals
     calsstring="CAL"+cals

#Verify settings with user before continuing.
checksetup=raw_input("Are you sure you want to continue with these settings?(y/n): ")
if checksetup!='y':
     g.close(16)
     sys.exit("Goodbye")

#User chooses a folder particular to this data set.
print ""
datasetname=raw_input("Enter a folder name for this data set (eg. HPUS2TM0717): ")
directory="/media/Data/"+datasetname+"/"
if not os.path.exists(directory):
     #make directory and set appropriate permissions.
     os.makedirs(directory)
     #os.system('chown :gpib '+directory) ## S bit on group for /media/Data does this for us (2744)
     #os.system('chmod g+wx '+directory) ## allows group members to add to an existing data file made by another user and x is for cd-ing to it
else:
     dontoverwrite=raw_input("Folder name already exists! Are you sure you want to save files in this folder? Files could be overwritten? (y/n): ")
     if dontoverwrite!='y':
         g.close(16)
         sys.exit("Goodbye")

#User must manually enter freq range
freqstart=raw_input("Enter the start frequency (GHz): ")
freqstop=raw_input("Enter the stop frequency (GHz): ")
freqstart=float(freqstart)
freqstop=float(freqstop)

#The following loop is repeated for every single data run.
while (again=='y'):
     #Makes the setup take a single sweep of data.
     g.clear(16)
     time.sleep(.5)
     g.write(16,"SING") 
     
     print "Waiting for data."
     
     #Get the statusbyte and look at just the 5th bit to determine when sweep has finished
     singdone='0'
     while singdone!='1' :
         time.sleep(0.5)
         myhex=g.rsp(16)
         myhex="%r"%myhex
         myhex=myhex.replace("\\","0")
         myhex=myhex.replace("'","")
         statbyte=bin(int(myhex,16))
         #output: '0b10001'
         singdone=statbyte[len(statbyte)-5]
     
     #Recieve data as a long ascii string.
     g.write(16,"OUTPDATA")
     mydata=g.read(16,1000000)
     g.clear(16)
     
     #Parse string to create numerical data matrix.
     mydata=mydata.replace("\n",",")
     mynumbers=np.fromstring(mydata,sep=",")
     print "Number of floats read: " + str(len(mynumbers)) #Should help let the user know things worked properly.
     print ""
     
     L=(len(mynumbers))/2 #This is how we figure out the number of freq pts.
     
     mymatrix=np.zeros((L,2))
     T=np.zeros(L)
     phi=np.zeros(L)
     x=range(0,L)
     Deltafreq=(freqstop-freqstart)/float(L)
     f=np.arange(freqstart, freqstop, Deltafreq)
     
     #Put data into a two column matrix. Also gets the magnitude and phase.
     for i in range(0,L):
         mymatrix[i,0]=mynumbers[2*i]
         mymatrix[i,1]=mynumbers[2*i+1]
         T[i]=mymatrix[i,0]**2+mymatrix[i,1]**2
         phi[i]=np.angle(complex(mymatrix[i, 0], mymatrix[i, 1]))
    
    
     #Beep to alert user that a run is finished and it is time to save the file.
     #for pitch in xrange(300,600,100):
     #    beepstring='beep -f '+str(pitch)+' -r 1 -d 150 -l 200'  
     #    os.system(beepstring)  
     p=os.popen("mplayer -really-quiet chime.wav  > /dev/null 2>&1")
     p.close

     #Save data with specified filename. Also prevents accidental overwrites of files.
     savedone=0
     while savedone==0:
          #save data using specified filename
          print "Previous file name: "+prevfilename
          filename=raw_input("Saving data. Enter file name: ")
          fullpath=directory+filename
          
          if os.path.exists(fullpath+".mat"):
             p=os.popen("ls -l "+fullpath+".mat")
             fileowner=p.readline()
             p.close
             fileowner=fileowner[13:13+len(usersname)]
             if fileowner==usersname:
                 overwritefile=raw_input("Data file already exists! Are you sure you want to overwrite?! (y/n): ")
             else:
                 print "This file already exists. You can not overwrite it because it belongs to a different user."
                 overwritefile='n'
          else:
             overwritefile='y'
          

          if overwritefile=='y':
             prevfilename=filename

             datestr=datetime.datetime.now()
             datestrsimp=str(datestr)[0:19] #Cuts off the milliseconds for a simpler output.
             headerstr=fullpath+".dat"+"  "+calsstring+"  "+param.replace('\n','')+"  "+datestrsimp
             #save_ascii_data(mymatrix, headerstr, usersname, freqstart, freqstop, fullpath)
             freq_start = str(freqstart) 
             freq_stop = str(freqstop)

             header_template = '''
%% %(headerstr)s 
%% %(freq_start)s : %(freq_stop)s GHz
'''  %{'headerstr':headerstr, 'freq_start':freq_start,'freq_stop':freq_stop}	

             np.savetxt(fullpath+".dat", mymatrix) 
             fn=open(fullpath+".dat",'r')
             matrixstr=fn.read()
             fn.close()
             fn=open(fullpath+".dat",'w')
             fn.write(header_template+'\n\n'+matrixstr)
             fn.close()

             scipy.io.savemat(fullpath,mdict={filename :  mymatrix}) #files are named as the rotation angle of sweep
             savedone=1
             #Set correct permissions on the new file.
             #os.system('chown :gpib '+fullpath+".mat")  S bit set this for all files in /media/Data
             os.system('chmod g-w '+fullpath+".dat") # removes the write bit, so that group members other than the creater cannot
             os.system('chmod g-w '+fullpath+".mat") # removes the write bit, so that group members other than the creater cannot
                                                     # delete a file made by another gpib member. They must re name it. 
             print "File Saved Successfully."
      

     print ""
     #Get time and date for the plot title.
     again='logmag'
     titlestr=fullpath+".dat"+"  "+calsstring+"  "+param+"  "+datestrsimp
     while True:
         if again=='logmag':
             print "Plotting logmag."
             #PLOT logaritmic transmission data. Labels graph with details of the data run.
             logT=np.log10(T)*10
             mp.clf()
             mp.plot(f, logT)
             mp.title(titlestr)
             mp.xlim( (freqstart, freqstop) )
             mp.xlabel("Frequency (GHz)")
             mp.ylabel(ystr+" (dB)")
             # xy=(x[5],logT[5])
             # mp.annotate("Fix this point?",xy)
         elif again=='linmag':
             print "Plotting linmag."
             #PLOT linear transmission data.
             mp.clf()
             mp.plot(f, T)
             mp.title(titlestr)
             mp.xlim( (freqstart, freqstop) )
             mp.xlabel("Frequency (GHz)")
             mp.ylabel(ystr+" linear")
         elif again=='phase':
             print "Plotting phase."
             #PLOT phase data.
             mp.clf()
             mp.plot(f, phi)
             mp.title(titlestr)
             mp.xlim( (freqstart, freqstop) )
             mp.xlabel("Frequency (GHz)")
             mp.ylabel(ystr+" phase (radians)")
         elif again=='y' or again=='n':
             break
         else:
             print "Ur doing it wrong."
     
         #repeat the process for a new data sweep?
         again=raw_input("Take another run? See another plot? (y/n/linmag/logmag/phase) ")
     
     
     if again=='y':
         manualchanges=raw_input("Do you want a break to change some settings manually? (y/n): ")
         if manualchanges=='y':
              print "Wait a moment..."
              g.close(16)
              time.sleep(2)
              pausescript=raw_input("Okay. Press the LOCAL button and change any settings you want. Hit enter here when you're done.")
              #Reconnect and check the settings. ASSUMES FREQ RANGE IS UNCHANGED.
              print "Address of VNA (Should be 16!):"
              print g.find("VNA")
              g.clear(16)
              time.sleep(.5)
              g.write(16,"FORM4")
              #Checks the parameter setting.
              g.write(16, "PARA?")
              param=g.read(16, 100)
              if param=='"S12"\n':
                  ystr="Transmission"
                  print "You are taking TRANSMISSION(S12) data."
              elif param=='"S11"\n':
                  ystr="Reflection"
                  print "You are taking REFLECTION(S11) data."
              elif param=='"S21"\n':
                  ystr="Transmission"
                  print "You are taking TRANSMISSION(S21) data."
              elif param=='"S22"\n':
                  ystr="Reflection"
                  print "You are taking REFLECTION(S22) data."
                
              #Checks the CAL setting.
              g.clear(16)
              time.sleep(.5)
              g.write(16,"CALS?")
              cals=g.read(16, 100)[0] #Takes only the first char in the string.
              if cals=='0':
                  print "Calibration is OFF"
                  calsstring="no cal"
              else:
                  print "You are under CAL set "+cals
                  calsstring="CAL"+cals
                
              #Verify settings with user before continuing.
              checksetup=raw_input("Are you sure you want to continue with these settings?(y/n): ")
              if checksetup!='y':
                  g.close(16)
                  sys.exit("Goodbye")


     print ""


g.close(16) #Disconnect from analyzer. Can press hardkey LOCAL to regain manual control.
os.system("fortune")
print ""

#theend


def save_ascii_data(mymatrix, titlestr, usersname, freqstart, freqstop, fullpath):
    freq_start = str(freqstop) 
    freq_stop = str(freqstart)
    
    header_template = '''
%% %(titlestr)s 
%% %(freq_start)s : %(freq_stop)s GHz
'''  %{'titlestr':titlestr, 'freq_start':freq_start,'freq_stop':freq_stop}	

    np.savetxt(fullpath+".dat", mymatrix) 
    f=open(fullpath+".dat",'r')
    matrixstr=f.read()
    f.close()
    f=open(fullpath+".dat",'w')
    f.write(header_template+'\n\n'+matrixstr)
    f.close()
