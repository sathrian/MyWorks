import os, logging, time


Stime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
folder = os.path.join(os.getcwd(),'Runinfo_'+Stime)
os.mkdir(folder)
file_name = os.path.join(folder, '__Task__.log')
usage = 'Job Started, please follow logs - %s'%file_name
logging.basicConfig(level=logging.INFO, filename=file_name, filemode='a',\
                datefmt='%m-%d %H:%M', \
       format='%(asctime)s TCH_AUTO : %(levelname)-8s : %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('TCH_AUTO : %(levelname)-8s : %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logging.info(usage)
    
def putsandloginfo(text):
    logging.info(text)
    return 

def putsandlogerror(text):
    logging.error(text)
    return 