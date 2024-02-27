#!/usr/bin/env python

import pyVmomi
import atexit
import itertools
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import humanize
import ssl,json
from pprint import pp, pprint
import os, logging, traceback, csv, smtplib
from email.message import Message
from SureshVMware import VMware
import os, logging, traceback, csv, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import COMMASPACE
from html import escape
import pandas as pd
import shutil
from munch import munchify

ssl._create_default_https_context = ssl._create_unverified_context

MBFACTOR = float(1 << 20)

printVM = False
printDatastore = True
printHost = True
Total_VMs = []

Records = {}

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
    else:
        # logging.info("Data updated for - %s"%file_name)
        return

def HostInformation(host, Record):
    try:
        summary = host.summary
        if summary.runtime.connectionState != 'connected':
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
        print("Unable to access information for host: ", host.name)
        print(error)
        pass

def get_ComputeResource(datacenter, Records):
    print(datacenter.name)
    if isinstance(datacenter, vim.Folder):
        if hasattr(datacenter, 'childEntity'):
            for item in datacenter.childEntity:
                if datacenter.name not in Records.keys():
                    Records.update({datacenter.name:{}})
                print(item.name)
                get_ComputeResource(item, Records[datacenter.name])
        return
    if isinstance(datacenter, vim.Datacenter):
        if datacenter.name not in Records.keys():
            Records.update({datacenter.name:{}})
        if hasattr(datacenter.hostFolder, 'childEntity'):
            get_ComputeResource(datacenter.hostFolder, Records[datacenter.name])
    pprint("get_ComputeResource - "+str(datacenter))
    if isinstance(datacenter, vim.ClusterComputeResource):
        print("ClusterComputeResource")
        print(datacenter.name)
        if datacenter.name not in Records.keys():
            print('Update - '+ datacenter.name)
            pprint(Records)
            Records.update({datacenter.name:{}})
        ComputeResourceInformation(datacenter, Records[datacenter.name])
        import pdb; pdb.set_trace()
    elif isinstance(datacenter, vim.ComputeResource):
        print("ComputeResource")
        print(datacenter.name)
        pprint(Records)

        if datacenter.name not in Records.keys():
            Records.update({datacenter.name:{}})
        ComputeResourceInformation(datacenter, Records[datacenter.name])
        return 


def ComputeResourceInformation(computeResource, Record):
    try:
        
        hostList = computeResource.host
        print("##################################################")
        print("Compute resource name: ", computeResource.name)
        print("##################################################")
        for host in hostList:
            if isinstance(computeResource, vim.ClusterComputeResource):
                if host.name not in Record.keys():
                    Record.update({host.name:{}})
                    print('Host list - '+ host.name)
                    HostInformation(host, Record[host.name])
            else:
                HostInformation(host, Record)
            datastores = host.datastore
            Record[host.name].update({'Datastores':[]})
            for ds in datastores:
                DatastoreInformation(ds, Record[host.name]['Datastores'])
        return
    except Exception as error:
        print("Unable to access information for compute resource: ",
              computeResource.name)
        print(error)
        pass

def DatastoreInformation(datastore, Record):
    try:
        summary = datastore.summary
        capacity = summary.capacity
        freeSpace = summary.freeSpace
        uncommittedSpace = summary.uncommitted
        UsedSpacePercentage = (float(capacity-freeSpace) / capacity) * 100
        # print(HostName)
       
       # print("##################################################")
       # print("Datastore name: ", summary.name)
       # print("Capacity: ", humanize.naturalsize(capacity, binary=True))
        if uncommittedSpace is not None:
            provisionedSpace = (capacity - freeSpace) + uncommittedSpace
            # print("Provisioned space: ", humanize.naturalsize(provisionedSpace,
            #                                                   binary=True))
       # print("Free space: ", humanize.naturalsize(freeSpace, binary=True))
       # print("Used space percentage: " + str(UsedSpacePercentage) + "%")
       # print("##################################################")
        Record.append(round(UsedSpacePercentage,2))
        #Records[HostName].update({summary.name : {"Capacity": humanize.naturalsize(capacity, binary=True),
       # "Provisioned space": humanize.naturalsize(provisionedSpace, binary=True),
       # "Free space": humanize.naturalsize(freeSpace, binary=True),
       # "Used space percentage": str(int(UsedSpacePercentage))+ "%"}})
    except Exception as error:
        print("Unable to access summary for datastore: ", datastore.name)
        print(error)
        


def printVmInformation(virtual_machine, depth=1):
    maxdepth = 10
    if hasattr(virtual_machine, 'childEntity'):
        if depth > maxdepth:
            return
        vmList = virtual_machine.childEntity
        for c in vmList:
            printVmInformation(c, depth + 1)
        return

    try:
        PowerON = False
        summary = virtual_machine.summary
        cpuUsagePercentage = None
        if summary.runtime.powerState == 'poweredOn':
            PowerON = True
        if PowerON:
            cpuUsagePercentage = summary.quickStats.overallCpuUsage/(summary.config.numCpu*cpuMhz)
            memUsagePercentage = summary.quickStats.overallCpuUsage/(summary.config.numCpu*cpuMhz)
        # print("State : ", summary.runtime.powerState)
        Records.update({'VMs':{virtual_machine.name :{
                                    'Power State' : summary.runtime.powerState
        }}})
        nic_count = 0
        for nic in virtual_machine.guest.net:
            nicName = 'Nic' + str(nic_count+1)
            ipAddress = list(nic.ipAddress)
            macAddress = nic.macAddress
            Nics = {nicName:{'IP Address':ipAddress, 'MAC Address': macAddress}}
            Records['VMs'][virtual_machine.name ].update({
                                    'vNICs': Nics
        })
        pprint(Records)
    except Exception as error:
        logging.error("Unable to access summary for VM: ", virtual_machine.name)
        logging.error(virtual_machine.guest.net)
        logging.error(error)
        # exit()
        #pass

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


def VMware(host, user, pwd, csv_file2, csv_file3, Heading1, port=443):
    try:
        si = SmartConnect(host=host, user=user, pwd=pwd, port=port)
        # si = SmartConnect(host="10.124.130.5", user="administrator@vsphere.local", pwd="St0p0ver1!", port=443)
        # si = SmartConnect(host="10.124.130.5", user="administrator@vsphere.local", pwd="Password@123", port=443)
        atexit.register(Disconnect, si)
        content = si.RetrieveContent()
    except vim.fault.InvalidLogin:
        raise Exception("Invalid username or password.")
    try:
        Records = {}
        for datacenter in content.rootFolder.childEntity:
            get_ComputeResource(datacenter, Records)
        csv_list = []
        for dc in Records.keys():
            for host in Records[dc].keys():
                for team in Records[dc][host].keys():
                    csv_file2 = os.path.join(os.getcwd(), f'vCenter_health_ngfw_{team}_{host.replace(".","_")}_{Stime}.csv')
                    write_csv(Heading1, csv_file2, 'w')
                    csv_list.append(csv_file2)
                    for rack in Records[dc][host][team].keys():
                        for Host in Records[dc][host][team][rack].keys():
                            if Records[dc][host][team][rack][Host]['ConnectionState'] == 'connected':
                                
                                write_csv([[dc, team, rack, Host, Records[dc][host][team][rack][Host]['CPU Usage'], 
                                Records[dc][host][team][rack][Host]['Memory Usage'], 
                                str(Records[dc][host][team][rack][Host]['Datastores']), 
                                Records[dc][host][team][rack][Host]['Number of VMs']]], csv_file2)
                            else:
                                txt = Host+'(disconnected)'
                                write_csv([[dc, team, rack, txt, '', '', '', '']], csv_file2)
    except Exception as e:
        logging.error(traceback.format_exc(6))
        # import pdb; pdb.set_trace()
    try:
        container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        for vm in container.view:
            if vm.runtime.powerState == 'poweredOff':
                data = get_events(si, vm)
                print('VM-name: '+vm.name)
                if data > 30:
                    print(vm.runtime.host.name, vm.name, data)
                    write_csv([[vm.runtime.host.name, vm.name, data]], csv_file3)
                elif data <= 30:
                    print(data)
    except Exception as e:
        logging.error(vm)
        logging.error(traceback.format_exc(6))
    return csv_list

def html_table(records):
    # records is expected to be a list of dicts
    column_names = []
        # first detect all posible keys (field names) that are present in records
    for record in records:
        for name in record.keys():
            # print(name)
            if name not in column_names:
                column_names.append(name)

    # print(column_names)
                
        # create the HTML line by line
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
        # if record == records[1]:
        lines.append('  <tr>\n')
        for name in column_names:
            #print(name)
            if record[name].strip() == '':
                lines.append('    <{0}color: #FF0000"><i>{1}</td>\n'.format(rowstyle,'&lt;No Data Available&gt;'))
                continue
            if record[name].strip() == '501':
                lines.append('    <{0}color: #FF0000"><i>{1}</td>\n'.format(rowstyle,'30+'))
                continue
            #try:
            value = record.get(name, '')
            #except:
            #    lines.append('    <{0};style="color: rgb(192, 0, 0)"><i>{1}</td>\n'.format(rowstyle,'&lt ; No Data Available &gt ;'))
            #    lines.append('    <{0}>{1}</td>\n'.format(rowstyle,value))
            #    continue
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
                #print('    <{0}text-align:left;vertical-align:left"> {1}</td>\n'.format(rowstyle,value))
                #print(value)
                continue
            #if record[name].strip() == '':
            #    lines.append('    <{0};style="color: rgb(192, 0, 0)"><i>{1}</td>\n'.format(rowstyle,'&lt;No Data Available&gt;'))
            #    continue
            #if value == '&#128077':
            #    lines.append('    <{0} style="text-align : center ; vertical-align : center">{1}</td>\n'.format(rowstyle,value))
            #else:
            lines.append('    <{0}"><i>{1}</td>\n'.format(rowstyle,escape(value)))
        lines.append('  </tr>\n')

    lines.append('</table>')
    # join the lines to a single string and return it
    return ''.join(lines)



def sendMAil(Sender, alias,subject, csv_file2, csv_file3, server='smtp.paloaltonetworks.com'):
    
    #sort_csv(csv_file, 0)

    #table2 = html_table(records)
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
        records = list(read_csv(csv_file, ['Team Name','Rack', 'IP Address','CPU usage in %','Memory usage in %','Datastores usage in %','#VMs']))
        # print(records[0])
        records.pop(0)
        table1 = html_table(records)
        table_0 += table1+'<br><br>'
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
        print(records)
        records.pop(0)
        table2 = html_table(records)
        table_1 += table2+'<br><br>'

        # Keep_Col = ['HostName', 'IP Address','CPU usage in %','Memory usage in %','Datastore usage in %','#VMs']
        # file = file[Keep_Col]
        # file.to_csv(csv_file, index=False) 
    
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

<p><i><span stlye="font-family:Arial, sans-serif;font-size:14px;">The below table - represents the vCenter host utilization tracking, w.r.t  CPU, Memory and Datastore <br> The Very last table shows the VMs were in Powered OFF state for 30+ days. </b><br><br></span></p>

<br><b>vCenter host server health status table:</b><br>

%s
<br><b>Table of VMs in PoweredOff state:</b><br>
%s
<br>

<p><i><span style="color : rgb(128,128,128) ; font-family : Arial, sans-serif ; font-size : 10px ; "Note : <br> Please let Suresh Subramanian (sursubramani) know, if any errors<br>

<p class="MsoNormal"><b><i><span style = "font-size : 10.0pt ; font-family : Fixed Width, sans-serif ;
color:#C0504D">--<br>Thanks,<br>Suresh Subramanian</p>

'''%(table_0, table_1)
    #print(html)
    # logging.info(html)
    message = MIMEMultipart(
    "alternative", None, [MIMEText(html,'html')])
    message['From'] = 'sursubramani@paloaltonetworks.com'
    message['Subject'] = subject
    message['To'] = COMMASPACE.join(alias)
    #message['To'] = COMMASPACE.join('sursubramani@paloaltonetworks.com')
    #message['Cc'] = 'sursubramani@paloaltonetworks.com'
    alias = alias
    alias.add('sursubramani@paloaltonetworks.com')
    #part1 = MIMEText(html,'html')
    #message.attach(part1)
    #print(part1)
    #part = MIMEBase('application', "octet-stream")
    #part.set_payload(open(csv_file, "rb").read())
    #encoders.encode_base64(part)
    #part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(csv_file))  
    #message.attach(part)
    #alias.add("sursubramani@paloaltonetworks.com")
    server = smtplib.SMTP(server)
    server.ehlo()
    server.starttls()
    server.sendmail(Sender, alias , message.as_string())            # Send email to managers (to list)
    #server.sendmail(Sender, [Sender], message.as_string())           # Send email to myself for debugging
    server.quit()
    
    return True



if __name__=="__main__":
    usage = 'EXSI - Suresh Subramanian'
    Stime = datetime.today().strftime('%Y-%m-%d')
    # Stime = time.ctime().replace(" ", "_")
    file_name = os.path.join(os.getcwd(), 'LogFile.'+ Stime + '.log')
    csv_file1 = os.path.join(os.getcwd(), 'vCenters_ngfw.csv')
    if os.path.exists(csv_file1):
        print("Script Ran Already")
        #exit()              #Comment this line when testing
    logging.basicConfig(level=logging.INFO, filename=file_name, filemode='a',\
                    datefmt='%m-%d %H:%M', \
           format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info(usage)
    #write_csv(Heading, csv_file)
    Mail1 = {'Email':{'Subject': 'vCenter utilization - Tracking!!', 
                       'From':'sursubramani@paloaltonetworks.com'},
           'Mail_list': set([
                           'sursubramani@paloaltonetworks.com',
                           ])}    
        #    'Mail_list': set([
        #                    'ror@paloaltonetworks.com',
        #                    'mom@paloaltonetworks.com',
        #                    'asathuragiri@paloaltonetworks.com',
        #                    'sursubramani@paloaltonetworks.com',
        #                    ])}               # This mail list to be used for sending email to Managers

    vCenters = list(read_csv(csv_file1, ['host','user','Pwd']))
    vCenters.pop(0)
    Heading1 = [['Team Name','Rack', 'IP Address','CPU usage in %','Memory usage in %','Datastores usage in %','#VMs']]
    Heading2 = [['Exsi Host', 'VM Name', 'No. of days in PoweredOff State']]
    # write_csv(Heading, Records, 'w')
    CSV_File2 = []
    CSV_File3 = []
    for vCenter in vCenters:
        vCenter = munchify(vCenter)
        csv_file2 = os.path.join(os.getcwd(), f'vCenter_health_ngfw_{vCenter.host.replace(".","_")}_{Stime}.csv')
        csv_file3 = os.path.join(os.getcwd(), f'VMs_ngfw_{vCenter.host.replace(".","_")}_{Stime}.csv')
        print(csv_file3)
        # CSV_File2.append(csv_file2)
        CSV_File3.append(csv_file3)
        write_csv(Heading1, csv_file2, 'w')
        write_csv(Heading2, csv_file3, 'w')
        try:
            csv_list = VMware(vCenter.host, vCenter.user, vCenter.Pwd, csv_file2, csv_file3, Heading1)
            print(csv_list)
        except Exception as e:
            # write_csv([[e, vCenter.host, '', '', '','']], csv_file2)
            logging.error(traceback.format_exc(6))
    
    if sendMAil(Mail1['Email']['From'], Mail1['Mail_list'] ,Mail1['Email']['Subject'], csv_list, CSV_File3):
        logging.info('Mail Sent Successfully')
        print(csv_list)
        print(CSV_File3)
        # shutil.copy(csv_file2,csv_file1)          #Comment this line when testing
