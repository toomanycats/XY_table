import math
import smtplib
from email.mime.text import MIMEText

class ConfigureDataSet(object):
    def __init__(self):
            self.DirectoryName = None
            self.FreqStart = None
            self.FreqStop = None
            self.TestSet = 'S21' #transmition always for this experiment
 
    def setup(self):
        #User chooses a folder particular to this data set.
        datasetname = raw_input("\nEnter a folder name for this data set:")
       
        self.DirectoryName = os.path.join("/media/Data/XY_table", datasetname)
        if not os.path.exists(self.DirectoryName):
             #make directory and set appropriate permissions.
             os.makedirs(self.DirectoryName)
             #os.system('chown :gpib '+directory) ## S bit on group for /media/Data does this for us (2744)
             #os.system('chmod g+wx '+directory) ## allows group members to add to an existing data file made by another user and x is for cd-ing to it
        else:
             self.DONTOVERWRITE=raw_input("Folder name already exists! Are you sure you want to save files in this folder? Files could be overwritten? (y/n): ")
             if self.DONTOVERWRITE!='y':
                 print "Enter a new name for the folder \n"
                 self.setup()
                 #g.close(16)
                 #sys.exit("Goodbye")         
         
        #User must manually enter freq range
        freqstart = raw_input("Enter the start frequency (GHz): ")
        freqstop = raw_input("Enter the stop frequency (GHz): ")
        self.FreqStart = float(freqstart)
        self.FreqStop = float(freqstop)
        
        self.verify_continue()

    def verify_continue(self):
        #Verify settings with user before continuing.
        checksetup = raw_input("Are you sure you want to continue with these settings?(y/n): ")
        if checksetup != 'y' and checksetup != 'n':
            print "\n %s: ***You did not enter a valid choice*** \n" %checksetup
            self.verify_continue()
        elif checksetup == 'n':
            g.close(16)
            sys.exit("Goodbye")
        elif checksetup == 'y':
            print "Settings verified and continuing with Take Data."

    def get_fileowner(self):
        p = os.popen("ls -l " + self.fullpath + ".mat")
        fileowner = p.readline()
        p.close
        self.fileowner = fileowner[13:13 + len(usersname)]
        
    def _get_date(self):
        datestr = datetime.datetime.now()
        self.date_str = str(datestr)[0:19] #Cuts off the milliseconds for a simpler output.        

class CodeTools(object):
    '''Contains methods used for the combination of motor tools and vna tools '''    
    
    def _notify_admin_error(self, username, date, traceback):

        email_body = """
%(username)s
%(date)s

%(traceback)s
""" %{'username':username,'date':date,'traceback':traceback}

        # Create a text/plain message
        msg = MIMEText(email_body)

        # me == the sender's email address
        me = 'Man Lab Data Machine'
        # you == the recipient's email address
        recipients = ['wmanlab@gmail.com', 'dpcuneo@gmail.com','theebbandflow@yahoo.com']
        msg['Subject'] = 'Automatically generated email.'
        msg['From'] = "Dr. Man's Lab Linux Machine."
        msg['To'] = 'System Admin.'

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.starttls()
        s.login('wmanlab','debye100!')
        s.sendmail(me, recipients, msg.as_string())
        s.quit()

    def ToSI(self,d):
        if d == 0.0 or d == 0:
            return 0

        incPrefixes = ['k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        decPrefixes = ['mm', 'mu', 'n', 'p', 'f', 'a', 'z', 'y']

        degree = int(math.floor(math.log10(math.fabs(d)) / 3))
        
        prefix = ''

        if degree!=0:
            ds = degree/math.fabs(degree)
            if ds == 1:
                if degree - 1 < len(incPrefixes):
                    prefix = incPrefixes[degree - 1]
                else:
                    prefix = incPrefixes[-1]
                    degree = len(incPrefixes)
            elif ds == -1:
                if -degree - 1 < len(decPrefixes):
                    prefix = decPrefixes[-degree - 1]
                else:
                    prefix = decPrefixes[-1]
                    degree = -len(decPrefixes)

            scaled = float(d * math.pow(1000, -degree))
            s = "{scaled} {prefix}".format(scaled=scaled, prefix=prefix)

        else:
            s = "{d}".format(d=d)

        return(s)
