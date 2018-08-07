#!/usr/bin/env python
'''
TCH L&T Logfile parser
'''

import os, re, logging, yaml, time, traceback, csv
def missing_keys(IP_list, ip):
    List = ['PC', 'backtrace','Thread', 'Cause', 'Up Time']
    for key in List:
        if key not in IP_list[ip]['reboot']['type']['details'].keys():
            IP_list[ip]['reboot']['type']['details'].update({key:'Missing Entry'})
    return
        
        
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
            RebootsFound = 0
            for line in infile:
              try:
                Match = re.search(r'([0-9/@:]+).*\s+(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+.*(%s.*)'%RebootFirstLIne,line, re.S|re.I)
                # logging.info(line)
                if Match:
                    Time = Match.group(1)
                    mip = Match.group(2)
                    RebootFirstLine = Match.group(3)
                    logging.info(Time)
                    # logging.info("Reboot Detected :-\n%sfor IP - %s and Reason - %s"%(line, mip, RebootFirstLine))
                    if mip in IP_list.keys():
                        if IP_list[mip]['update']:
                            if len(IP_list[mip].keys()) == 8:
                                if len(IP_list[mip]['reboot']['type']['details'].keys()) != 5:
                                    logging.error('Details Missing for : %s - %s'% (mip,IP_list[mip]['reboot']['type']['details'].keys()))
                                    missing_keys(IP_list, mip)
                                write_csv(IP_list, mip, LogFile, model)
                                IP_list[mip].update({'update':False})
                            else:
                                logging.error('Details Missing for : %s - %s'% (mip,IP_list[mip].keys()))
                            IP_list[mip]['data'].append("\n**End of Reboot**\n")
                            t = IP_list[mip]['Time'].replace('/','-')
                            t = t.replace('@','_')
                            t = t.replace(':','-')
                            print(t)
                            filename = 'RebootLog_'+os.path.splitext(os.path.basename(LogFile))[0]+'_'+mip.replace(".", "_")+t+'.txt'
                            write_file(filename, IP_list[mip]['data'])
                            # logging.info("IP_list[ip] - %s, Details - %s"%(len(IP_list[mip].keys()), IP_list[mip]['reboot']['type']['details'].keys()))
                            # write_csv(IP_list, mip, LogFile, model)
                            IP_list[mip].update({'update':False})
                            # file_data[mip]['RebootDetected'] = False
                            logging.info("File Updated - %s"%filename)
                        IP_list[mip].update({'Time':Time,'RebootDetected':True, 'data':[line],'update':False,'reboot':{'type':{'details':{}}}})
                    else:
                        IP_list.update({mip:{'Time':Time,'RebootDetected':True, 'data':[line],'update':False,'reboot':{'type':{'details':{}}}}})
                    logging.info(line)
                else:
                    # for reason in reasons:
                    m = re.search(r'.*[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+.*Reason:\s*(.*)\n', line, re.S|re.I)
                    if m:
                        Ip = m.group(1)
                        rebootReason = m.group(2)
                        # if reason in rebootReason:
                        if IP_list[Ip]['RebootDetected']:
                            if rebootReason in IP_list[Ip]['reboot']['type']:
                                logging.info('Duplicate Reason: %s - Detected for IP %s'%(rebootReason, Ip))
                                IP_list[Ip]['reboot']['type'][rebootReason] +=1
                            else:
                                IP_list[Ip]['reboot']['type'].update({rebootReason:1})
                                logging.info('Reason:%s - Detected for IP %s'%(rebootReason, Ip))                    
                            IP_list[Ip].update({'update':True})
                            RebootsFound += 1
                            continue
                        else:
                            logging.error('Reboot Reason: %s - Not Detected for IP %s'%(rebootReason, Ip))
                        # logging.info('Reason Updated %s'%IP_list[Ip])
                    match = re.search(r'[0-9/@:]+\s*-\s*(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})+\s*[0-9a-f:\(\)\[\]\s]*:*\s+(.*)\n',line, re.S|re.I)
                    if match:
                        ip = match.group(1)
                        pmtv = match.group(2)
                        if ip in IP_list.keys():
                            if IP_list[ip]['RebootDetected']:
                                IP_list[ip]['data'].append(line)
                                # logging.info('check Updated %s'%IP_list[ip])
                                # for data in IP_list[ip]['reboot']['type']['details'].keys():
                                    # logging.info(IP_list[ip]['reboot']['type']['details'][data])
                                keys = []
                                if not 'Cause' in IP_list[ip]['reboot']['type']['details'].keys():
                                    Cause = re.search(r'Backtrace:\s*(.*)',pmtv, re.S|re.I)
                                    if Cause:
                                        IP_list[ip]['reboot']['type']['details'].update({'Cause':Cause.group(1)})
                                    
                                if not 'Thread' in IP_list[ip]['reboot']['type']['details'].keys():
                                    Thread = re.search(r'Thread:\s*(.*)',pmtv, re.S|re.I)
                                    if Thread:
                                        IP_list[ip]['reboot']['type']['details'].update({'Thread':Thread.group(1)})
                                    
                                if not 'backtrace' in IP_list[ip]['reboot']['type']['details'].keys():
                                    backtrace = re.search(r'Backtrace:\s*(.*)',pmtv, re.S|re.I)
                                    if backtrace:
                                        IP_list[ip]['reboot']['type']['details'].update({'backtrace':backtrace.group(1)})
                                        
                                if not 'Up Time' in IP_list[ip]['reboot']['type']['details'].keys():
                                    Up = re.search(r'Up Time:\s*(.*)',pmtv, re.S|re.I)
                                    if Up:
                                        IP_list[ip]['reboot']['type']['details'].update({'Up Time':Up.group(1)})
                                        
                                if not 'PC' in IP_list[ip]['reboot']['type']['details'].keys():
                                    PC = re.search(r'PC:\s*([0-9a-f]*)',pmtv, re.S|re.I)
                                    if PC:
                                        IP_list[ip]['reboot']['type']['details'].update({'PC':'\'%s\''%PC.group(1)})                                    
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
                                Version = re.search(r'[0-9/@:]+\s*-\s*(%s)+.*Version: IMAGE;[\s\w\d.]*;?\s*([0-9.ps\s]*)'%ip, line, re.S|re.I)
                                if Version:
                                    Version = Version.group(2)
                                    IP_list[ip].update({'Version':Version})
                                    # logging.info('HW Model Updated for %s as %s'%(ip, hw_model))
                            if len(IP_list[ip].keys()) == 8 and len(IP_list[ip]['reboot']['type']['details'].keys()) == 5:
                                if IP_list[ip]['update']:
                                    # logging.info("IP_list[ip] - %s, Details - %s"%(len(IP_list[ip].keys()), IP_list[mip]['reboot']['type']['details'].keys()))
                                    write_csv(IP_list, ip, LogFile, model)
                                    IP_list[ip]['update'] = False
              except KeyboardInterrupt:
                logging.error(traceback.format_exc(6))
                return
              except:
                # logging.error(IP_list[ip])
                logging.error(traceback.format_exc(6))
        write_all_to_file(IP_list, os.path.splitext(os.path.basename(LogFile))[0])
        for ip in IP_list.keys():
            if len(IP_list[ip].keys()) == 8:
                if IP_list[ip]['update']:
                    if len(IP_list[ip]['reboot']['type']['details'].keys()) != 5:
                        missing_keys(IP_list, ip)
                        logging.error('Details Missing for : %s - %s'% (ip,IP_list[ip]['reboot']['type']['details']))
                    write_csv(IP_list, ip, LogFile, model)
                    IP_list[ip].update({'update':False})
                else:
                    logging.error('Details Missing at the end for : %s - %s'% (ip,IP_list[ip]['reboot']['type']['details']))
            else:
                logging.error('Details Missing at the end for : %s - %s'% (ip,IP_list[ip]))
                
        logging.info('Task Completed for Log file - %s with %s of reboots'%(LogFile, RebootsFound))
def write_csv(IP_list, ip, LogFile, model):
    global CsvData
    try:
        # for ip in IP_list.keys():
        file = os.path.splitext(os.path.basename(LogFile))[0]+ '.csv'
        if len(IP_list[ip].keys()) == 8:
            # logging.info(IP_list[ip])
            # IP_list[ip]['reboot']['type']['Details']
            # print(IP_list[ip])
            for reason in IP_list[ip]['reboot']['type'].keys():
                if reason == 'backtrace' or reason == 'data' or reason == 'details':
                    continue
                if model == 'All':
                    CsvData.append([IP_list[ip]['Time'], reason, ip, 
                                    IP_list[ip]['MAC'], 
                                    IP_list[ip]['Time'], 
                                    IP_list[ip]['HWModel'],
                                    IP_list[ip]['Version'],
                                    IP_list[ip]['reboot']['type']['details']['PC'], 
                                    IP_list[ip]['reboot']['type']['details']['backtrace'], 
                                    IP_list[ip]['reboot']['type']['details']['Thread'], 
                                    IP_list[ip]['reboot']['type']['details']['Cause'], 
                                    IP_list[ip]['reboot']['type']['details']['Up Time']])
                elif IP_list[ip]['HWModel'] in model:
                    CsvData.append([IP_list[ip]['Time'], reason, ip, 
                                    IP_list[ip]['MAC'], 
                                    IP_list[ip]['HWModel'],
                                    IP_list[ip]['Version'],
                                    IP_list[ip]['reboot']['type']['details']['PC'], 
                                    IP_list[ip]['reboot']['type']['details']['backtrace'], 
                                    IP_list[ip]['reboot']['type']['details']['Thread'], 
                                    IP_list[ip]['reboot']['type']['details']['Cause'], 
                                    IP_list[ip]['reboot']['type']['details']['Up Time']])
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
            t = IP_list[mip]['Time'].replace('/','-')
            t = t.replace('@','_')
            t = t.replace(':','-')
            filename = 'RebootLog_'+LogFile+'_'+mip.replace(".", "_")+t+'.txt'
            logging.info('Writing to file %s'%filename)
            IP_list[mip]['data'].append("\n**End of Reboot**\n")
            write_file(filename, IP_list[mip]['data'])
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
    usage = 'Logfile parser Automation - Suresh Subramanian'
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
    CsvData = [['Time','Reboot Reason', 'IP Address', 'Mac Address', 'HW Model', 'Version', 'PC', 'Back Trace', 'Thread', 'Cause', 'Up Time']]
    main(file_name)
    