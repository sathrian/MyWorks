#!/usr/bin/env python3
'''
Autor - Suresh Subramanian 
'''

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
import ssl,json, pprint



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

def html_table(records):
    # records is expected to be a list of dicts
    column_names = []
        # first detect all posible keys (field names) that are present in records
    for record in records:
        for name in record.keys():
            # print(name)
            if name not in column_names:
                column_names.append(name)

    print(column_names)
                
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
            #try:
            value = record.get(name, '')
            #    print(value)
            #except:
            #    lines.append('    <{0};style="color: rgb(192, 0, 0)"><i>{1}</td>\n'.format(rowstyle,'&lt ; No Data Available &gt ;'))
            #    lines.append('    <{0}>{1}</td>\n'.format(rowstyle,value))
            #    continue
            if name == 'IP Address':
                value = '<a href=https://{0}/ui title="Exsi-link";><i>{0}</i></a>'.format(record['IP Address'])
                lines.append('    <{0}color: #444">{1}</td>\n'.format(rowstyle,value))
                continue
            if name == '#VMs':
                lines.append('    <{0}">{1}</td>\n'.format(rowstyle,int(float(value))))
                continue
            if name == 'HostName':
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
    
    
def sendMAil(Sender, alias,subject, csv_file ,server='smtp.pa.com'):
    
    #sort_csv(csv_file, 0)

    #table2 = html_table(records)
    file = pd.read_csv(csv_file) 
    file.sort_values(["CPU usage in %"], 
                    axis=0,
                    ascending=[False], 
                    inplace=True)
    file.sort_values(["Memory usage in %"], 
                    axis=0,
                    ascending=[False], 
                    inplace=True)
    file.to_csv(csv_file, index=False)
    records = list(read_csv(csv_file, ['HostName', 'IP Address','CPU usage in %','Memory usage in %','Datastore usage in %','#VMs']))
    print(records[0])
    records.pop(0)
    table2 = html_table(records)
    Keep_Col = ['HostName', 'IP Address','CPU usage in %','Memory usage in %','Datastore usage in %','#VMs']
    file = file[Keep_Col]
    file.to_csv(csv_file, index=False) 
    
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
<p class="MsoNormal"><span style="color: rgb(192, 0, 0); font-size: 10pt;">***This is an Auto Generated Email for EXSI utilization Tracking***&nbsp;</span></p>

<p><i><span stlye="font-family:Arial, sans-serif;font-size:14px;">The below table - represents the EXSI utilization tracking, w.r.t  CPU, Memory and Datastore </b><br><br></span></p>

<br><b>Exsi server health status table:</b><br>

%s


<br>

<p><i><span style="color : rgb(128,128,128) ; font-family : Arial, sans-serif ; font-size : 10px ; "Note : <br> Please let me know, if any errors <br>

<p class="MsoNormal"><b><i><span style = "font-size : 10.0pt ; font-family : Fixed Width, sans-serif ;
color:#C0504D">--<br>Thanks,<br>Suresh Subramanian</p>

'''%(table2)
    #print(html)
    #logging.info(html)
    message = MIMEMultipart(
    "alternative", None, [MIMEText(html,'html')])
    message['From'] = 'sursubramani@pa.com'
    message['Subject'] = subject
    message['To'] = COMMASPACE.join(alias)
    # message['To'] = COMMASPACE.join('sursubramani@pa.com')
    #message['Cc'] = 'sursubramani@pa.com'
    alias = alias
    alias.add('sursubramani@pa.com')
    #part1 = MIMEText(html,'html')
    #message.attach(part1)
    #print(part1)
    #part = MIMEBase('application', "octet-stream")
    #part.set_payload(open(csv_file, "rb").read())
    #encoders.encode_base64(part)
    #part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(csv_file))  
    #message.attach(part)
    #alias.add("sursubramani@pa.com")
    server = smtplib.SMTP(server)
    server.ehlo()
    server.starttls()
    server.sendmail(Sender, alias , message.as_string())            # Send email to managers (to list)
    # server.sendmail(Sender, [Sender], message.as_string())           # Send email to myself for debugging
    server.quit()
    
    return True

if __name__=="__main__":
    usage = 'EXSI - Suresh Subramanian'
    Stime = datetime.today().strftime('%Y-%m-%d')
    # Stime = time.ctime().replace(" ", "_")
    file_name = os.path.join(os.getcwd(), 'LogFile.'+ Stime + '.log')
    csv_file1 = os.path.join(os.getcwd(), 'Servers_cpt.csv')
    csv_file2 = os.path.join(os.getcwd(), 'Records_'+ Stime+ '.csv')
    if os.path.exists(csv_file2):
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
    Mail1 = {'Email':{'Subject': 'EXSI utilization - Tracking!!', 
                       'From':'sursubramani@pa.com'},
        #    'Mail_list': set(['ror@pa.com'])}   jsathik@pa.com            # This mail list to be used for sending email to Managers
            #  'Mail_list': set(['jsathik@pa.com'])}
             'Mail_list': set(['sursubramani@pa.com'])}
    records = list(read_csv(csv_file1, ['host','user','Pwd']))
    records.pop(0)
    Heading = [['HostName', 'IP Address','CPU usage in %','Memory usage in %','Datastore usage in %','#VMs']]
    write_csv(Heading, csv_file2, 'w')
    for host in records:
        host = munchify(host)
        print(host)
        try:
            data = VMware(host=host.host, user=host.user, pwd=host.Pwd, port=443)
            pprint(data)
            write_csv([[data['Host Name'], host.host, data['CPU Usage'],data['Memory Usage'], data['Used space percentage'],data['Number of VMs']]], csv_file2)
            pass
        except Exception as e:
            write_csv([[e, host.host, '', '', '','']], csv_file2)
            logging.error(traceback.format_exc(6))
    
    if sendMAil(Mail1['Email']['From'], Mail1['Mail_list'] ,Mail1['Email']['Subject'], csv_file2):
        logging.info('Mail Sent Successfully')
        #shutil.copy(csv_file2,csv_file1)          #Comment this line when testing
