#!/usr/bin/env python

import os, re, logging, yaml, time, traceback, csv

def main(file_name):
    status = True
    config_file=os.path.join(os.getcwd(), 'log_files.yaml')
    logging.info('Config file will be used - [%s]' %config_file)
    with open(config_file, 'r') as yAml:
        config = yaml.load(yAml)
    try:
        log_files = config['LogFile']['List']
    except:
        log_files = None
    try:
        reasons = config['LogFile']['Reasons']
    except:
        reasons = None
    try:
        model = config['LogFile']['HW Model']
    except:
        model = None
    if model == None:
        model = 'All'
        
    for LogFile in log_files:
        if not os.path.isfile(LogFile):
            logging.error('Log File -%s not exists'%LogFile)
            
    for LogFile in log_files: 
        CsvData = [['Reboot Reason', 'IP Address', 'Mac Address', 'HW Model', 'Number of occurance']]
        with open(LogFile , 'r', encoding='latin1') as infile:
            IP_list = {}
            try:
                for line in infile:
                    #if not Ip:
                        # print('find IP')
                    for reason in reasons:
                        m = re.search(r'[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+.*Reason:\s*(%s.*)\n'%reason, line, re.S|re.I)
                        if m:
                            Ip = m.group(1)
                            rebootReason = m.group(2)
                            if Ip in IP_list.keys():
                                for x in IP_list[Ip]:
                                    if rebootReason in x:
                                        logging.info('Duplicate Reason: %s - Detected for IP %s'%(rebootReason, Ip))
                                        x[rebootReason] +=1
                                    else:
                                        IP_list[Ip]['Reason'].update({rebootReason:1})
                                        logging.info(line)
                                        logging.info('Reason:%s - Detected for existing IP %s'%(rebootReason, IP_list[Ip]))
                            else:
                                IP_list.update({Ip:{'Reason':{rebootReason:1}}})
                                logging.info('New Reason:%s - Detected for IP %s'%(rebootReason, Ip))
                            continue
                    for ip in IP_list.keys():
                        if len(IP_list[ip].keys()) == 3:
                            continue
                        if not 'Mac' in IP_list[ip].keys():
                            mac = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*RF MAC: (([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))'%ip, line, re.S|re.I)
                            if mac:
                                #IP = mac.group(1)
                                Mac = mac.group(2)
                                IP_list[ip].update({'MAC':Mac})
                                logging.info('Mac Updated for %s as %s'%(ip, Mac))
                        if not 'HWModel' in IP_list[ip].keys():
                            hw = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*HW MODEL: ([0-9]+)'%ip, line, re.S|re.I)
                            if hw:
                                hw_model = hw.group(2)
                                IP_list[ip].update({'HWModel':hw_model})
                                logging.info('HW Model Updated for %s as %s'%(ip, hw_model))
                        # if not 'Verion' in IP_list[ip].keys():
                            # hw = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*Version:\s*(.*)'%ip, line, re.S|re.I)
                            # if hw:
                                # hw_model = hw.group(2)
                                # IP_list[ip].update({'HWModel':hw_model})
                                # logging.info('HW Model Updated for %s as %s'%(ip, hw_model))
            except:
                logging.error(line)
                logging.error(traceback.format_exc(6))
        logging.info('Data Collected:- %s'%IP_list)
        
        try:
            for ip in IP_list.keys():
                if len(IP_list[ip].keys()) == 3:
                    for reason in IP_list[ip]['Reason'].keys():
                        if model == 'All':
                            CsvData.append([reason, ip, IP_list[ip]['MAC'], IP_list[ip]['HWModel'], IP_list[ip]['Reason'][reason]])
                        elif IP_list[ip]['HWModel'] in model:
                            CsvData.append([reason, ip, IP_list[ip]['MAC'], IP_list[ip]['HWModel'], IP_list[ip]['Reason'][reason]])
                else:
                    print('Details Missing for : %s - %s'% (ip,IP_list[ip]))
        except:
            logging.error(ip)
            logging.error(traceback.format_exc(6))
            
        with open(os.path.splitext(os.path.basename(LogFile))[0] +Stime+ '.csv', 'w') as CSV:
            writer = csv.writer(CSV)
            writer.writerows(CsvData)
        logging.info('Task Completed for Log file - %s'%LogFile)
        
def write_file(filename, data, mode='a'):
    with open(filename, mode) as f:
        f.write(data)
    logging.info("File Writen - %s"%filename)
        
if __name__=="__main__":
    usage = 'Log Automation - Suresh Subramanian'
    Stime = time.ctime().replace(" ", "_")
    file_name = os.path.join(os.getcwd(), 'LogFile.'+ Stime + '.log')
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
    