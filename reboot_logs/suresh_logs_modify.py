#!/usr/bin/env python
'''
Author - Suresh Subramanian
'''

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
        RebootFirstLIne = config['LogFile']['RebootFirstLIne']
    except:
        RebootFirstLIne = None
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
        # CsvData = [['Reboot Reason', 'IP Address', 'Mac Address', 'HW Model', 'Version', 'PC', 'Back Trace', 'Number of occurance']]
        with open(LogFile , 'r', encoding='latin1') as infile:
            IP_list = {}
            file_data = {}
            for line in infile:
              try:
                Match = re.search(r'[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+.*(%s.*)'%RebootFirstLIne,line, re.S|re.I)
                if Match:
                    mip = Match.group(1)
                    RebootFirstLine = Match.group(2)
                    filename = 'RebootLog_'+os.path.splitext(os.path.basename(LogFile))[0]+'_'+mip.replace(".", "_")+'.txt'
                    if mip in IP_list.keys():
                        if IP_list[mip]['update']:
                            IP_list[mip]['reboot']['type']['data'].append("\n**End of Reboot**\n")
                            write_file(filename, IP_list[mip]['reboot']['type']['data'])
                            IP_list[mip].update({'update':False})
                            # file_data[mip]['RebootDetected'] = False
                            logging.info("File Updated - %s"%filename)
                    file_data.update({mip:{'RebootDetected':True, 'data':[line],'backtrace':[RebootFirstLine+'\n']}})
                else:
                    # for reason in reasons:
                    m = re.search(r'[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+.*Reason:\s*(.*)\n', line, re.S|re.I)
                    if m:
                        Ip = m.group(1)
                        rebootReason = m.group(2)
                        # if reason in rebootReason:
                        if Ip in IP_list.keys():
                            # file_data[Ip]['backtrace'].append(rebootReason)
                            if rebootReason in IP_list[Ip]['reboot']['type']:
                                logging.info('Duplicate Reason: %s - Detected for IP %s'%(rebootReason, Ip))
                                IP_list[Ip]['reboot']['type'][rebootReason] +=1
                                IP_list[Ip]['reboot']['type']['data'] = file_data[Ip]['data']
                                # IP_list[Ip]['reboot']['type']['backtrace'].append(file_data[Ip]['backtrace'])
                            else:
                                IP_list[Ip]['reboot']['type'].update({rebootReason:1,'data':file_data[Ip]['data'],'backtrace':file_data[Ip]['backtrace']})
                                # IP_list[Ip]['reboot']['type']['backtrace'].append(file_data[Ip]['backtrace'])
                                logging.info(line)
                                logging.info('Reason:%s - Detected for existing IP %s'%(rebootReason, Ip))
                        else:
                            IP_list.update({Ip:{'reboot':{'type':{rebootReason:1,'data':file_data[Ip]['data'],'backtrace':file_data[Ip]['backtrace']}}}})
                            logging.info('New Reason:%s - Detected for IP %s'%(rebootReason, Ip))
                        # IP_list[Ip]['reboot']['type']['data'] = file_data[Ip]['data']
                        IP_list[Ip].update({'update':True})
                        # file_data.update({mip:{'RebootDetected':False, 'data':[]}})
                    # else:
                        # file_data.update({mip:{'RebootDetected':False, 'data':[],'backtrace':[]}})
                    # match = re.search(r'[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+.*',line, re.S|re.I)
                    match = re.search(r'[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+\s*[0-9a-f:\(\)\[\]\s]*:*\s+(.*)',line, re.S|re.I)
                    if match:
                        ip = match.group(1)
                        pmtv = match.group(2)
                        if ip in file_data.keys():
                            if file_data[ip]['RebootDetected']:
                                file_data[ip]['data'].append(line)
                                file_data[ip]['backtrace'].append(pmtv)
                                if 'backtrace' in pmtv.lower():
                                    file_data.update({mip:{'RebootDetected':False, 'data':[],'backtrace':[]}})
                        if ip in IP_list.keys():
                            if IP_list[ip]['update']:
                                IP_list[ip]['reboot']['type']['data'].append(line)
                            if len(IP_list[ip].keys()) == 6:
                                write_csv(IP_list, ip, LogFile, model)
                                del IP_list[ip]
                                # write_csv(IP_list, CsvData, LogFile)
                                continue
                            if not 'Mac' in IP_list[ip].keys():
                                mac = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*RF MAC: (([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))'%ip, line, re.S|re.I)
                                if mac:
                                    #IP = mac.group(1)
                                    Mac = mac.group(2)
                                    IP_list[ip].update({'MAC':Mac})
                                    # logging.info('Mac Updated for %s as %s'%(ip, Mac))
                            if not 'HWModel' in IP_list[ip].keys():
                                hw = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*HW MODEL: ([0-9]+)'%ip, line, re.S|re.I)
                                if hw:
                                    hw_model = hw.group(2)
                                    IP_list[ip].update({'HWModel':hw_model})
                            if not 'Version' in IP_list[ip].keys():
                                Version = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*Version: IMAGE;[\s\w]*;*\s*([0-9.ps\s]*)'%ip, line, re.S|re.I)
                                if Version:
                                    Version = Version.group(2)
                                    IP_list[ip].update({'Version':Version})
							if not 'Cause' in IP_list[ip].keys():
                                Cause = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*Cause: (.*)'%ip, line, re.S|re.I)
                                if Cause:
                                    Cause = Cause.group(2)
                                    IP_list[ip].update({'Cause':Cause})
							
							if not 'Thread' in IP_list[ip].keys():
                                Thread = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*Thread: (.*)'%ip, line, re.S|re.I)
                                if Thread:
                                    Thread = Thread.group(2)
                                    IP_list[ip].update({'Thread':Thread})							
									
                            PC = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*PC:\s+([0-9a-f]*)'%ip, line, re.S|re.I)
                            if PC:
                                PC = PC.group(2)
                                if not 'PC' in file_data[ip].keys():
                                    IP_list[ip].update({'PC':[PC]})
                                else:
                                    IP_list[ip]['PC'].append(PC)
                                    # logging.info('HW Model Updated for %s as %s'%(ip, hw_model))
              except KeyboardInterrupt:
                logging.error(traceback.format_exc(6))
                return
              except:
                logging.error(traceback.format_exc(6))
        write_all_to_file(IP_list, os.path.splitext(os.path.basename(LogFile))[0])
        logging.info('Task Completed for Log file - %s'%LogFile)
        # logging.info('Data Collected:- %s'%IP_list)
def write_csv(IP_list, ip, LogFile, model):
    global CsvData
    try:
        # for ip in IP_list.keys():
        file = os.path.splitext(os.path.basename(LogFile))[0] +Stime+ '.csv'
        if len(IP_list[ip].keys()) == 6:
            # logging.info(IP_list[ip])
            IP_list[ip]['reboot']['type']['data']
            for reason in IP_list[ip]['reboot']['type'].keys():
                if reason == 'backtrace' or reason == 'data':
                    continue
                if model == 'All':
                    CsvData.append([reason, ip, IP_list[ip]['MAC'], IP_list[ip]['HWModel'],IP_list[ip]['Version'], IP_list[ip]['Cause'], IP_list[ip]['Thread'], IP_list[ip]['PC'],''.join(map(str, IP_list[ip]['reboot']['type']['backtrace'])), IP_list[ip]['reboot']['type'][reason]])
                elif IP_list[ip]['HWModel'] in model:
                    CsvData.append([reason, ip, IP_list[ip]['MAC'], IP_list[ip]['HWModel'],IP_list[ip]['Version'],IP_list[ip]['Cause'], IP_list[ip]['Thread'], IP_list[ip]['PC'],''.join(map(str, IP_list[ip]['reboot']['type']['backtrace'])), IP_list[ip]['reboot']['type'][reason]])
        else:
            logging.info('Details Missing for : %s - %s'% (ip,IP_list[ip].keys()))
            
        with open(file, 'a') as CSV:
            writer = csv.writer(CSV)
            writer.writerows(CsvData)
            CsvData = []
    except:
        # logging.error(ip)
        # logging.error(IP_list)
        logging.error(traceback.format_exc(6))
    else:
        logging.info("Data updated for - %s"%file)

        

def write_all_to_file(IP_list, LogFile, mode='a'):
    for mip in IP_list.keys():
        if IP_list[mip]['update']:
            filename = 'RebootLog_'+LogFile+'_'+mip.replace(".", "_")+'.txt'
            logging.info('Writing to file %s'%filename)
            IP_list[mip]['reboot']['type']['data'].append("\n**End of Reboot**\n")
            write_file(filename, IP_list[mip]['reboot']['type']['data'])
            IP_list[mip].update({'update':False})

def write_file(filename, data, mode='a'):
    logging.info('Write_file to file %s'%filename)
    with open(filename, mode) as f:
        if type(data)==list:
            for line in data:
                f.write(line)
        else:
            f.write(data)
        
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
    CsvData = [['Reboot Reason', 'IP Address', 'Mac Address', 'HW Model', 'Version', 'Cause', 'Thread', 'PC', 'Back Trace', 'Number of occurance']]
    main(file_name)
    