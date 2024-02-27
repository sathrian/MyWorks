#!/usr/bin/env python

import atexit
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import ssl
from pprint import pprint
import os, logging, traceback, csv, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.utils import COMMASPACE
from html import escape
import pandas as pd
from munch import munchify

ssl._create_default_https_context = ssl._create_unverified_context

MBFACTOR = float(1 << 20)

def read_csv(path, column_names):
    with open(path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            record = {name: value for name, value in zip(column_names, row)}
            yield record


def write_csv(CsvData, file_name, mode='a'):
    try:
        with open(file_name, mode) as CSV:
            writer = csv.writer(CSV)
            writer.writerows(CsvData)
    except:
        logging.error(traceback.format_exc(6))
    return

def HostInformation(host, Record):
    try:
        summary = host.summary
        if summary.runtime.connectionState == 'disconnected':
            Record.update({
                'ConnectionState': summary.runtime.connectionState
             })
            raise Exception
        for vinc in summary.host.config.network.vnic:
            IP = vinc.spec.ip.ipAddress
        global HostName
        global cpuMhz
        HostName = host.name
        overallStatus = host.overallStatus
        stats = summary.quickStats
        hardware = host.hardware
        cpuUsage = stats.overallCpuUsage
        cpuMhz = summary.hardware.cpuMhz
        cpuUsagePercentage = cpuUsage/(cpuMhz*summary.hardware.numCpuCores)*100
        memoryCapacityInMB = hardware.memorySize/MBFACTOR
        memoryUsage = stats.overallMemoryUsage
        MemoryPercentage = (float(memoryUsage) / memoryCapacityInMB) * 100
        Record.update({
            'IP Address':vinc.spec.ip.ipAddress,
            'CPU Usage' : round(cpuUsagePercentage,2),
            'Memory Usage' : round(MemoryPercentage,2),
            'Number of VMs':len(host.vm),
            'OverallStatus' : overallStatus.upper(),
            'ConnectionState': summary.runtime.connectionState
        })
        
    except Exception as error:
        logging.error("Unable to access information for host: ", host.name)
        logging.error(error)
        

def ComputeResourceInformation(computeResource, Record):
    try:
        hostList = computeResource.host
        for host in hostList:
            HostInformation(host, Record)
            datastores = host.datastore
            Record.update({'Datastores':[]})
            for ds in datastores:
                DatastoreInformation(ds, Record['Datastores'])
    except Exception as error:
        logging.error("Unable to access information for compute resource: ",
              computeResource.name)
        logging.error(error)
        pass

def DatastoreInformation(datastore, Record):
    try:
        summary = datastore.summary
        capacity = summary.capacity
        freeSpace = summary.freeSpace
        UsedSpacePercentage = (float(capacity-freeSpace) / capacity) * 100
        Record.append(round(UsedSpacePercentage,2))
    except Exception as error:
        logging.error("Unable to access summary for datastore: ", datastore.name)
        logging.error(error)
        

def get_events(si, vm, ids = ['VmPoweredOffEvent']):
    byEntity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion="self")
    filter_spec = vim.event.EventFilterSpec(entity=byEntity, eventTypeId=ids)
    event_manager = si.content.eventManager
    events = event_manager.QueryEvent(filter_spec)
    if events:
        count = []
        for event in events:
            days = datetime.now().date()-event.createdTime.date()
            count.append(days.days)
        return min(count)
    else:
        return 501


def VMware(host, user, pwd, csv_file2, csv_file3, port=443):
    try:
        si = SmartConnect(host=host, user=user, pwd=pwd, port=port)
        atexit.register(Disconnect, si)

        content = si.RetrieveContent()
    except vim.fault.InvalidLogin:
        raise Exception("Invalid username or password.")
    try:
        Records = {}
        for datacenter in content.rootFolder.childEntity:
            Records.update({datacenter.name:{}})
            if hasattr(datacenter.hostFolder, 'childEntity'):
                computeResources = datacenter.hostFolder.childEntity
                for computeResource in computeResources:
                    Records[datacenter.name].update({computeResource.name:{}})
                    if isinstance(computeResource, vim.ComputeResource):
                        ComputeResourceInformation(computeResource, Records[datacenter.name][computeResource.name])
        for dc in Records.keys():
            for host in Records[dc].keys():
                if Records[dc][host]['ConnectionState'] == 'connected':
                    write_csv([[dc, host, Records[dc][host]['CPU Usage'], Records[dc][host]['Memory Usage'], str(Records[dc][host]['Datastores']), Records[dc][host]['Number of VMs']]], csv_file2)
                else:
                    txt = dc+'(disconnected)'
                    write_csv([[txt, host, '', '', '', '']], csv_file2)
                    
    except Exception as e:
        pprint(Records)
        pprint(Records[dc][host])
        logging.error(traceback.format_exc(6))
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    for vm in container.view:
        if vm.runtime.powerState == 'poweredOff':
            data = get_events(si, vm)
            print('VM-name: '+vm.name)
            if data > 30:
                write_csv([[vm.runtime.host.name, vm.name, data]], csv_file3)
            elif data <= 30:
                print(data)
    return True

def html_table(records):
    column_names = []
    for record in records:
        for name in record.keys():
            if name not in column_names:
                column_names.append(name)
    lines = []
    lines.append('<table class="tg" style="border-collapse: collapse;border-color: #9ABAD9;border-spacing: 0;">\n')
    lines.append('  <tr>\n')
    row_style = ['''td class="tg-phtq" style="background-color: #D2E4FC;border-color: inherit;border-style: solid;border-width: 2px;color: #444;
    font-family: Arial, sans-serif;font-size: 14px;overflow: hidden;padding: 10px 5px;word-break: normal;text-align: center;vertical-align: center;''' ,
     '''td class="tg-0pky" style="background-color: #EBF5FF;border-color: inherit;border-style: solid;border-width: 2px;color: #444;
    font-family: Arial, sans-serif;font-size: 14px;overflow: hidden;padding: 10px 5px;word-break: normal;text-align: center;vertical-align: center;''']
    for name in column_names:
        lines.append('''    <th class="tg-0pth" style="background-color: #409cff;border-color: inherit;border-style: solid;border-width: 2px;
        color: #fff;font-family: Arial, sans-serif;font-size: 14px;font-weight: normal;overflow: hidden;padding: 10px 5px;word-break: normal;text-align: center;vertical-align: center;"><i>{}</th>\n'''.format(escape(name)))
    lines.append('  </tr>\n')
    for record in records:
        rowstyle = row_style[records.index(record)%2]
        lines.append('  <tr>\n')
        for name in column_names:
            if record[name].strip() == '':
                lines.append('    <{0}color: #FF0000"><i>{1}</td>\n'.format(rowstyle,'&lt;No Data Available&gt;'))
                continue
            if record[name].strip() == '501':
                lines.append('    <{0}color: #FF0000"><i>{1}</td>\n'.format(rowstyle,'30+'))
                continue
            value = record.get(name, '')
            if name == 'IP Address':
                value = '<a href=https://{0}/ui title="Exsi-link";><i>{0}</i></a>'.format(record['IP Address'])
                lines.append('    <{0}color: #444">{1}</td>\n'.format(rowstyle,value))
                continue
            if name ==  'Exsi Host':
                value = '<a href=https://{0}/ui title="Exsi-link";><i>{0}</i></a>'.format(record['Exsi Host'])
                lines.append('    <{0}color: #444">{1}</td>\n'.format(rowstyle,value))
                continue
            if name == '#VMs':
                lines.append('    <{0}">{1}</td>\n'.format(rowstyle,int(float(value))))
                continue
            if name == 'DC Name / Team' or name == 'VM Name':
                lines.append('    <{0}text-align:left;vertical-align:left">{1}</td>\n'.format(rowstyle,value))
                continue
            lines.append('    <{0}"><i>{1}</td>\n'.format(rowstyle,escape(value)))
        lines.append('  </tr>\n')

    lines.append('</table>')
    return ''.join(lines)



def sendMAil(Sender, alias,subject, csv_file2, csv_file3, Server='smtp.paloaltonetworks.local'):
    table_0 = ''
    for csv_file in csv_file2:
        file = pd.read_csv(csv_file)
        file.sort_values(["Memory usage in %"], 
                        axis=0,
                        ascending=[False], 
                        inplace=True)
        file.sort_values(["CPU usage in %"], 
                        axis=0,
                        ascending=[False], 
                        inplace=True)
        file.to_csv(csv_file, index=False)
        records = list(read_csv(csv_file, ['DC Name / Team', 'IP Address','CPU usage in %','Memory usage in %','Datastore usage in %','#VMs']))
        print(records[0])
        records.pop(0)
        table1 = html_table(records)
        table_0 += table1+'<br><br>'
        print(table_0)
    table_1 = ''
    for csv_file in csv_file3:
        file = pd.read_csv(csv_file) 
        file.sort_values(["No. of days in PoweredOff State"], 
                        axis=0,
                        ascending=[False], 
                        inplace=True)
        file.to_csv(csv_file, index=False)
        records = list(read_csv(csv_file, ['Exsi Host', 'VM Name', 'No. of days in PoweredOff State']))
        print(records[0])
        records.pop(0)
        table2 = html_table(records)
        table_1 += table2+'<br><br>'
    
    html = '''
<!DOCTYPE html> 
<style type = "text/css" >
.tg  {border-collapse : collapse ; border-color : red ; border-spacing : 0 ;}
.tg td{background-color : #EBF5FF ; border-color : #9ABAD9 ; border-style : solid ; border-width : 2px ; color : #444 ;
  font-family : Arial , sans-serif ; font-size : 14px ; overflow : hidden ; padding : 10px 5px ; word-break : normal ; }
.tg th{background-color : #409cff ; border-color : #9ABAD9 ; border-style : solid ; border-width : 2px ; color : #fff ;
  font-family : Arial , sans-serif ; font-size : 14px ; font-weight : normal ; overflow : hidden ; padding : 10px 5px ; word-break : normal ;}
.tg .tg-phtq{background-color : #D2E4FC ; border-color : inherit ; text-align : left ; vertical-align : center}
.tg .tg-0pky{border-color : inherit ; text-align : left ; vertical-align : center}
.tg .tg-0pth{border-color : inherit ; text-align : center ; vertical-align : center}
</style>
<p class="MsoNormal"><span style="color: rgb(192, 0, 0); font-size: 10pt;">***This is an Auto Generated Email for vCenter utilization Tracking***&nbsp;</span></p>

<p><i><span stlye="font-family:Arial, sans-serif;font-size:14px;">The below table - represents the vCenter host utilization tracking, w.r.t  CPU, Memory and Datastore </b><br><br></span></p>

<br><b>vCenter host server health status table:</b><br>

%s
<br><b>Table of VMs PoweredOff:</b><br>
%s
<br>

<p><i><span style="color : rgb(128,128,128) ; font-family : Arial, sans-serif ; font-size : 10px ; "Note : <br> Please let Suresh Subramanian (sursubramani) know, if any errors<br>

<p class="MsoNormal"><b><i><span style = "font-size : 10.0pt ; font-family : Fixed Width, sans-serif ;
color:#C0504D">--<br>Thanks,<br>Suresh Subramanian</p>

'''%(table_0, table_1)
    message = MIMEMultipart(
    "alternative", None, [MIMEText(html,'html')])
    message['From'] = Sender
    message['Subject'] = subject
    message['To'] = COMMASPACE.join(alias)
    alias = alias
    # alias.add('sursubramani@paloaltonetworks.com')
    server = smtplib.SMTP(Server, 587)
    # server = SMTP(server)
    server.starttls()
    server.ehlo()
    server.login('svc-cpt', '$ar?wAsw#p4g-cro')
    server.sendmail(Sender, alias , message.as_string())            # Send email to managers (to list)
    server.quit()
    return True



if __name__=="__main__":
    usage = 'EXSI - Suresh Subramanian'
    Stime = datetime.today().strftime('%Y-%m-%d')
    file_name = os.path.join(os.getcwd(), 'LogFile.'+ Stime + '.log')
    csv_file1 = os.path.join(os.getcwd(), 'vCenters.csv')
    logging.basicConfig(level=logging.INFO, filename=file_name, filemode='a',\
                    datefmt='%m-%d %H:%M', \
           format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info(usage)
    Mail1 = {'Email':{'Subject': 'vCenter utilization - Tracking!!', 
                       'From':'sursubramani@pa.com'},
           'Mail_list': set(['sursubramani@pa.com'])}               # This mail list to be used for sending email to Managers

    vCenters = list(read_csv(csv_file1, ['host','user','Pwd']))
    vCenters.pop(0)
    Heading1 = [['DC Name / Team', 'IP Address','CPU usage in %','Memory usage in %','Datastores usage in %','#VMs']]
    Heading2 = [['Exsi Host', 'VM Name', 'No. of days in PoweredOff State']]
    CSV_File2 = []
    CSV_File3 = []
    for vCenter in vCenters:
        vCenter = munchify(vCenter)
        csv_file2 = os.path.join(os.getcwd(), f'vCenter_health_{vCenter.host.replace(".","_")}_{Stime}.csv')
        csv_file3 = os.path.join(os.getcwd(), f'VMs{vCenter.host.replace(".","_")}_{Stime}.csv')
        CSV_File2.append(csv_file2)
        CSV_File3.append(csv_file3)
        write_csv(Heading1, csv_file2, 'w')
        write_csv(Heading2, csv_file3, 'w')
        try:
            VMware(vCenter.host, vCenter.user, vCenter.Pwd, csv_file2, csv_file3)
            pass
        except Exception as e:
            logging.error(traceback.format_exc(6))
    
    if sendMAil(Mail1['Email']['From'], Mail1['Mail_list'] ,Mail1['Email']['Subject'], CSV_File2, CSV_File3):
        logging.info('Mail Sent Successfully')
