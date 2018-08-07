#!/usr/bin/env python
'''
Author - Suresh Subramanian(20154492)
'''
import os, time, random, argparse, smtplib, logging, yaml, re, subprocess
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

StartTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
MailText = "!!!This is an Auto Generated mail from MoTo Script!!!\r\nPlease look into attached log file for more info!\r"
MailText = MailText + "\r\nScript Started at %s\r\n"%StartTime
Text = ''

def get_args():
    """ Get arguments from CLI """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''\
            Arguments for Moto version verification''',
         epilog='''\
    usage: Moto.py [-h] [-c moto yaml File]
                                Or
           Moto.py [-s SERVER] [-v VERSION] 
           ''')
    
    parser.add_argument('-c', '--config',
                        required=False,
                        action='store',
                        default=os.path.join(os.getcwd(), 'moto.yaml'),
                        help='Provide config file')
                        
    parser.add_argument('-l', '--clone',
                        default=None,
                        required=False,
                        action='store',
                        help='Provide True/False if you repo init/sync is not needed')
                        
    parser.add_argument('-r', '--repoURL',
                        required=False,
                        default=None,
                        action='store',
                        help='Provide git RepoURL')    
    
    parser.add_argument('-b', '--repoBranch',
                        required=False,
                        default=None,
                        action='store',
                        help='Provide git RepoBranch')

    parser.add_argument('-i', '--manifestURL',
                        required=False,
                        action='store',
                        default=None,
                        help='Provide manifestURL')
                        
    parser.add_argument('-v', '--version',
                        required=False,
                        action='store',
                        default="LA.UM.6.7.r1-04900-8x09.0.xml",
                        help='Provide release version')
                        
    parser.add_argument('-m', '--mailTo',
                        required=False,
                        action='store',
                        default=None,
                        help='Recepients')
    

    args = parser.parse_args()
    if args.config is None:
        parser.error('''\
    usage: Moto.py [-h] [-c moto yaml File]
                                Or
           Moto.py [-s SERVER] [-v VERSION] [-m MAIL-TO] 
           ''')
    return args

def Mkdir(folderName='AOSP'):
    if not os.path.exists(folderName):
        os.mkdir(folderName)
        if os.path.exists(folderName):
            logging.info("Folder - %s created successfully"%folderName)
    else:
        logging.info("Folder %s already exists"%folderName)
    os.chdir(folderName)
    logging.info("Changed to %s directory"%folderName)
    return
    
def cmdexe(cmd):
    logging.info('\r\nExecuting - %s'%cmd)
    #output = os.popen(cmd).read()
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
    #time.sleep(5)
    output = pipe.communicate()[0]
    logging.info('\r\nOutput:\r\n%s'%output)
    return output
    
def repoInit(cmd):
    repo = True
    if not os.path.isfile(os.path.expanduser('~')+"/bin/repo"):
        bin_path = os.path.expanduser('~')+"/bin"
        Mkdir(os.path.expanduser('~')+"/bin")
        cmdexe("PATH=%s:$PATH"%bin_path)
        cmdexe("curl http://commondatastorage.googleapis.com/git-repo-downloads/repo > %s/repo"%bin_path)
        os.chmod(bin_path+'/repo', 0777)
    
    out = cmdexe(cmd)
    if 'repo has been initialized' in out:
        logging.info(out)
        return True
    else:
        logging.error(out)
        return False

def repoSync():
    out=cmdexe("repo sync")
    logging.info("repoSync output:\r\n %s"%out)
    # if 'repo has been initialized' in out:
        # logging.info(out)
        # return True
    # else:
        # logging.error(out)
        # return False
        
def setJavaPath():
    status = True
    logging.info("Checking for Java Path")
    if not re.search(r'/usr/lib/jvm/java-8-openjdk-[\w]+/bin', os.popen('echo $PATH').read()):
        javav =os.popen('ls /usr/lib/jvm').read()
        if 'java-8-openjdk' in javav:
            javav = re.search(r'java-8-openjdk-[\w]+',javav).group(0)
            path = '/usr/lib/jvm/'+javav+"/bin"
            if os.path.exists(path):
                os.environ['PATH'] = path+':'+os.environ['PATH']
        else:
            logging.error("Java not Installed")
            status = False
        if re.search(r'/usr/lib/jvm/java-8-openjdk-[\w]+/bin', os.popen('echo $PATH').read()):
            logging.info("Java Path set successfully")
        else:
            status = False
            logging.info("Java Path not set succ")
    else:
        logging.info("Java Path Aleady Exists")
    return status
    
def LogText(string):
    global Text
    Text = Text + '\r\n'+string
    return
    
def SetEnv(): 
    command = ['bash', '-c', 'source init_env && env']
    proc = subprocess.Popen(command, stdout = subprocess.PIPE)
    for line in proc.stdout:
      (key, _, value) = line.partition("=")
      os.environ[key] = value
    proc.communicate()
    
    return dict(os.environ)
    
def Compile(ChooseCombo, Make=None):
    status = True
    path=os.path.join(os.getcwd(), 'build/envsetup.sh')
    logging.info("Checking for file exists - %s"%path)
    if os.path.exists(path):
        if Make:
            make = "make %s"%Make
        else:
            make = "make"
        out = cmdexe("source %s; choosecombo %s ;%s"%(path, ChooseCombo, make))
        logging.info("Make output:\r\n%s"%out)

        if 'completed successfully' in out:
            LogText("Make build Successful!!\r\n")
        elif 'ninja: no work to do' in out:
            LogText("Make build already processed!!\r\nRefer below logs!")
            logging.info("Make build already processed!!\r\nRefer below logs!")
        else:
            logging.error(out)
            LogText("Make build Failed!!\r\nRefer below logs!")
            logging.info("Make build Failed!!\r\nRefer below logs!")
            status = False
        LogText(out)
    else:
        logging.error("file not found - %s"%path)
        LogText("file not found - %s"%path)
        status = False
    return status
    
def main(file_name):
    global MailText
    status = True
    args = get_args()
    config_file = args.config
    logging.info('Config file will be used - [%s]' %config_file)
    with open(config_file, 'r') as yAml:
        config = yaml.load(yAml)
        
    if not args.repoURL:
        try:
            RepoURL = config['Git']['RepoURL']
        except:
            RepoURL = None
    else:
        RepoURL = args.repoURL
        
    if not args.repoBranch:
        try:
            RepoBranch = config['Git']['RepoBranch']
        except:
            RepoBranch = None
    else:
        RepoBranch = args.repoBranch
        
    if not args.manifestURL:
        try:
            ManifestURL = config['Git']['ManifestURL']
        except:
            ManifestURL = None
    else:
        ManifestURL = args.manifestURL
        
    try:
        ManifestBranch = config['Git']['ManifestBranch']
    except:
        ManifestBranch = None
        
    try:
        ManifestFile = config['Git']['ManifestFile']
    except:
        ManifestFile = None
    
    try:
        ChooseCombo = config['Git']['ChooseCombo']
    except:
        ChooseCombo = None
    try:
        Make = config['Git']['Make']
    except:
        Make = None    
    try:
        Folder = config['Git']['Folder']
    except:
        Folder = None
        
    if not args.clone:
        try:
            clone = config['Git']['Clone']
        except:
            clone = None
    else:
        clone = args.clone
    if not args.mailTo:
        try:
            mailTo = config['Reports']['Recepients']
        except:
            mailTo = None
    else:
        mailTo = args.mailTo
        
    try:
        Subject = config['Reports']['Subject']
    except:
        Subject = 'MOTO'
    
    try:
        MailServer = config['Reports']['MailServer']
    except:
        MailServer = 'mail.ltindia.com'
    
    try:
        SmtpPort = config['Reports']['SmtpPort']
    except:
        SmtpPort = '25'
    try:
        DeleteLogFile = config['Reports']['DeleteLogFile']
    except:
        DeleteLogFile = False
        
    if DeleteLogFile == 'True':
        DeleteLogFile = True
    else:
        DeleteLogFile = False
    
    
    #Commented for demo run
    if (clone == 'True' or clone == True):
        logging.info("Git Clone set to True detected, Starting Git clone")
        cmd = 'git clone -b %s %s'%(RepoBranch,RepoURL)
        logging.info(cmd)
        # out = cmdexe(cmd)
        # logging.info("Clone output - %s"%out)
        Mkdir(Folder)
    else:
        Mkdir(Folder)
        cmd = "repo init -u %s -b %s -m %s --repo-url=%s --repo-branch=%s" %(ManifestURL, ManifestBranch, ManifestFile, RepoURL , RepoBranch)
        logging.info(cmd)
        if not repoInit(cmd):
            logging.error("repo init got errored out")
            LogText("repo init got errored out")
            status = False
            
        if status:
            if not repoSync():
                logging.error("repo Sync got errored out")
                LogText("repo Sync got errored out")
                status = False
    if status:
        if not setJavaPath():
            logging.error("seting Java path got errored out")
            LogText("seting Java path got errored out")
            status = False
    if status:
        logging.info("Start Compiling")
        #Env = SetEnv()
        if Make == "None" or Make == '':
            output = Compile(ChooseCombo)
            logging.info("Make None")
        else:
            output = Compile(ChooseCombo, Make)
            
        if output:
            logging.info("Build completed successfully")
            LogText("Build completed successfully")
    logging.info("Sending logs to - %s"%(",".join([str(x) for x in mailTo])))
    
    files = [file_name]
    mailServer = MailServer+':'+str(SmtpPort)
    logging.info(mailServer)
    EndTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    size = file_size(file_name)
    m = re.search(r'([0-9\.]+)\s+(\w+)',size)
    if m:
        if m.group(2) == 'GB':
            files = []
        if 10.0 < float(m.group(1)):
            if m.group(2) == 'MB':
                files = []
    if files == []:
        MailText = '\r\nLog file - %s attachment is not possible due size(%s) constrain\r\n'%(file_name, m) + MailText
    MailText = MailText + "\r\nScript Ended at %s\r\n"%EndTime + '\r\n'+Text+ '\r\n\r\n'
    sendMAil(mailTo, Subject, MailText, files, mailServer)
    
    if DeleteLogFile:
        os.remove(file_name)
    return status
        
def generateMessageID(msg_h):
    domain = msg_h.split("@")[1]
    r = "%s.%s" % (time.time(), random.randint(0, 100))
    mid = "<%s@%s>" % (r, domain)
    return mid

def sendMAil(to, subject, text,
    files=[],server="localhost", debug=False):
    assert type(to)==list
    assert type(files)==list
    String_h = "7375726573682e73756272616d616e69616e406c6e747465636873657276696365732e636f6d"
    msg_h = String_h.decode('hex')
    msg = MIMEMultipart()
    msg['From'] = msg_h
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    text = text.decode("utf-8")
    text = MIMEText(text, 'plain', "utf-8")
    msg.attach(text)

    msg.add_header('Message-ID', generateMessageID(msg_h))
    
    for file in files:

        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(file,"r").read())
        #Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(file))
        msg.attach(part)

    if not debug:
        smtp = smtplib.SMTP(server)
        smtp.sendmail(msg_h, to, msg.as_string())
        smtp.close()

    return msg
    
def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)
        
if __name__=="__main__":
    usage = 'Moto Automation - Suresh Subramanian'
    file_name = os.path.join(os.getcwd(), 'MotoLogFile.'+ time.ctime().replace(" ", "_") + '.log')
    logging.basicConfig(level=logging.INFO, filename=file_name, filemode='a',\
                    datefmt='%m-%d %H:%M', \
           format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info(usage)
    file_name=os.path.join(os.getcwd(), file_name)
    main(file_name)
    
