import os, logging

class tch_auto():
    def __ini__(self,):
        
        self.Stime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        folder = os.path.join(os.getcwd(),'Runinfo_'+self.Stime)
        os.mkdir(folder)
        file_name = os.path.join(folder, '__Task__.log')
        usage = 'Job Started, please follow logs - %s'%file_name
        logging.basicConfig(level=logging.INFO, filename=file_name, filemode='a',\
                        datefmt='%m-%d %H:%M', \
               format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        logging.info(usage)
    
    def putsandloginfo(text):
        global logging
        return logging.info(text)
    
    def putsandloginfo(text):
        global logging
        return logging.error(text)