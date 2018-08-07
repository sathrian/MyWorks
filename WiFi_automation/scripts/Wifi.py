import re
import Exscript
import logging
import time
import json
from requests import post
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from random import *
import traceback

class connect():
    
    def ssh_connect(self):
        self.connected = False
        self.conn = Exscript.protocols.SSH2()
        self.prompt = re.compile(r'.*[$#] *$|.*>>> \x1b\[0m$')
        self.conn.set_prompt(re.compile(self.prompt))
        logging.info('Connecting to %s' % self.VmIP)
        self.conn.connect(self.VmIP, self.port)
        account = Exscript.Account(self.username, self.password)
        self.conn.login(account)
        self.connected = True
        return self.conn
    
    def execute(self, cmd='', raw=False):
        if self.connected:
            line=''
            self.conn.buffer.clear()
            self.conn.send('\r')
            self.conn.expect_prompt()
            line = self.conn.buffer.head(80) + cmd
            try:
                self.conn.execute(cmd)
            except:
                logging.error(line + self.conn.response)
                logging.error("buffer:\n" +line + self.conn.buffer.io.getvalue())
                raise
            str1 = re.sub('\|', '__PIPE__', self.conn.response)
            str2 = re.sub('\|', '__PIPE__', cmd)
            str3 = re.sub(str2, '', str1)
            response_raw = str3
            resp = response_raw.replace('\r\n\r\x00', '\n')
            self.conn.response = resp
            if resp != '' and resp != '\r':
                logging.info(line + '\n' + resp)
            else:
                logging.info(line)
            if not raw:
                return resp
            else:
                return response_raw
        else:
            logging.error('ERROR: %s is not connected' % self.name)
            
    def _fill_buffer(self):
        if self.connected:
            if not self.conn._wait_for_data():
                error = 'Timeout while waiting for response from device'
                raise Exception(error)
            data = self.conn.shell.recv(200).decode("utf-8")
            if not data:
                return False
            self.conn._receive_cb(data)
            self.conn.buffer.append(data)
            return True
            
    def flush_buffer(self):
        if self.connected:
            try:
                self._fill_buffer()
                self.conn.buffer.clear()
            except:
                pass
                
    def send_control_c(self, wait_time=5):
        try:
            self.get_full_buffer('\x03', wait_time)
        except:
            pass
            
    def get_full_buffer(self,command = '', wait_time=5):
        if self.connected:
            logging.info('Executing: \n%s'%command)
            #print('Executing: \n', command)
            self.conn.send(command + '\r')
            end_time = time.time() + wait_time
            old_timeout = self.conn.get_timeout()
            self.conn.set_timeout(1)
            response = ''
            while time.time() < end_time:
                try:
                    self._fill_buffer()
                    response += self.conn.buffer.__str__()
                    response = response.replace('\r\n\r\x00', '\n')
                    self.conn.buffer.clear()                    
                except:
                    pass
            self.conn.buffer.clear()
            self.conn.set_timeout(old_timeout)
            logging.info('Response:\n%s'%response)
            return response
        else:
            logging.error('ERROR: %s is not connected' % self.VmIP)
            return False
    
    def close(self):
        logging.info('Disconnecting from %s' % self.VmIP)
        self.conn.close(force=True)
        self.conn.close(force=True)
        self.connected = False
    
    def expect(self,value):
        try:
            self.conn.expect(value)
            out = self.conn.response
            logging.info("response:\n" + self.conn.response)
            logging.info("buffer:\n" + self.conn.buffer.io.getvalue())
        except:
            logging.error("response:\n" + self.conn.response)
            logging.error("buffer:\n" + self.conn.buffer.io.getvalue())
            out = self.conn.buffer.io.getvalue()
            raise
        return out
        
    def tshark_capture(self):
        out = self.get_full_buffer("tshark -l -i mon0 -f 'wlan src 6e:10:61:29:c3:73 and type data' -T fields -e wlan_radio.signal_dbm -e wlan_radio.data_rate -c 10")
        
        if "10 packets captured" in out:
            logging.info("Packet capture successful")
            return out
        else:
            logging.error("Not able to start tshark: %s" %out)
            self.send_control_c()
            return None
        
    def check_association(self):
        out = self.execute("iwconfig wlp2s0")
        if "Not-Associated" not in out:
            logging.info("Association Successful")
            return True
        else:
            return False
        
    def associate_with_ap(self):
        cmds = ["ip link set wlp2s0 down",
        "iwconfig wlp2s0 essid 1-ccsp-5g",
        "iwconfig wlp2s0 channel 36",
        "ip link set wlp2s0 up"]
        for cmd in cmds:
            self.execute(cmd)
        for i in range(5):
            if self.check_association() is True:
                logging.info("Association Successful")
                return True
            else:
                time.sleep(1)
    
    def startIperfClient(self):
        out = self.get_full_buffer("iperf3 -u -p 5002 -c 192.168.0.12 -t 10000 -b 500M -l 1440")
        if "connected to 192.168.0.12 port 5002" in out:
            logging.info("client up and connected to server")
            return True
        else:
            logging.error("Iperf Client not able to connect: %s" %out)
            return False
    
    def startIperfServer(self):
        out = self.get_full_buffer("iperf3 -s -p 5002 -i 1 -f m")
        pattern="Server listening on 5002"
        if pattern in out:
            logging.info("Server listens")
            return True
        else:
            logging.error("Iperf Server not listening: %s" %out)
            return False
        
    def __init__(self,  VmIP, username, password, port = 22):
        self.VmIP = VmIP
        self.port = port
        self.username = username
        self.password = password
        self.ssh_connect()
    
###################
def list_mean(n):
    summing = float(sum(n))
    count = float(len(n))
    if n == []:
        return False
    return float(summing/count)

def get_tshark_data(session):
    
    if session.check_association():
        out = session.tshark_capture()
    else:
        reset_attn()
        return None
    if out is not None:
        out = out.split('\r\n')
        signal_dbm = []
        data_rate = []
        for i in out:
            m = re.search("(-[0-9]+)\s*([0-9\.]*)", i)
            if m:
                signal_dbm.append(float(m.group(1)))
                data_rate.append(float(m.group(2)))
        logging.info('Tshark Raw Data %s, %s'%(signal_dbm, data_rate))
        signal_dbm, data_rate = list_mean(signal_dbm), list_mean(data_rate)
        logging.info('Tshark Raw Data')
        data_rate = round(data_rate/3.0, 2)
        logging.info(signal_dbm)
        logging.info(data_rate)
        return signal_dbm, data_rate
    

def get_iperf_data(session):
    out = session.get_full_buffer('')
    out = out.split('\r\n')
    bw_rate = []
    start_record = None
    for i in out:
        if not i:
            start_record = True
        if start_record is True:
            m = re.search(".* ([0-9\.]*) Mbits/sec", i)
            if m:
                bw_rate.append(float(m.group(1)))
    bw_rate = bw_rate[-5:]
    logging.info('Iperf sample values for avg - %s'%bw_rate)
    bw_rate = list_mean(bw_rate)
    logging.info('Iperf Data ')
    logging.info(bw_rate)
    return bw_rate

def attenuate(attenuation):
    str_att = str(attenuation)
    try:
        logging.info(post("http://10.1.0.200/api/quadAtten", headers={"Content-type":"application/json"},
         data=json.dumps({"atten1" : str_att, "atten2" :  str_att, "atten3" :  str_att, "atten4" :  str_att})).text)
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc(6))
    return

def reset_attn():
    global attn, incr, state, sample, xdata, y1data, y2data
    attn, incr = 0,5
    iperfClient.send_control_c(5)
    iperfServer.send_control_c()
    attenuate(attn)
    time.sleep(5)
    if not linkself.associate_with_ap():
        logging.error("Not able to associate. Exiting")
        exit()
    iperfServer.startIperfServer()
    iperfClient.send_control_c(1)
    iperfClient.startIperfClient()
    state = 'init'
    sample = False
    xdata, y1data, y2data = [], [], []
    return

def data_gen():
    global state
    global attn, incr, signal_dbm, data_rate, bw_rate
    cnt = 0
    while cnt < 1000:
        cnt += 1;
        #if state == 'init':
            #if signal_dbm != []:
                #for x,y,z in zip(signal_dbm, data_rate, bw_rate):
                    #yield x, y/80.0, z/8000.0
        logging.info("In - %s"%state)
        if signal_dbm < -90:
            reset_attn()
        if state == 'ignore':
            logging.info("Ignore data from Tshark and Iperf")
            end_time = time.time() + 30
            while time.time() < end_time:
                iperfServer.flush_buffer()
                tsharkSession.flush_buffer()
                continue
            logging.info("Tshark and Iperf data flushed")
            state = "data"
        else:
            logging.info("Sleep 5 sec to stabilize traffic")
            time.sleep(10)
            data = get_tshark_data(tsharkSession)
            if data is not None:
                signal_dbm, data_rate = data
            bw_rate = get_iperf_data(iperfServer)
            logging.info("signal_dbm - %s"%signal_dbm)
            logging.info("data_rate - %s"%data_rate)
            logging.info("bw_rate - %s"%bw_rate)
            if state == 'init':
                state = 'data'
            else:
                state = 'ignore'
                if attn > 50:
                    incr = 1
                attn += incr
                attenuate(attn)
        yield signal_dbm, data_rate, bw_rate

def data_gen1():
    cnt = 0
    global t, t1, y1, y2, state
    while cnt < 5:
        if state == 'ignore':
            end_time = time.time() + 5
            while time.time() < end_time:
                pass
            print('sleep')
            state = 'data'
        else:
            t = s[cnt]
            y1 = m[cnt]
            y2 = p[cnt]
            cnt += 1
            state = 'ignore'
        yield t, y1, y2
        
def run(data):
    # update the data
    signal_dbm, data_rate, bw_rate = data
    logging.info("Plotting Values: signal_dbm :- %s, data_rate :- %s, bw_rate :- %s"%(signal_dbm, data_rate, bw_rate))
    xdata.append(signal_dbm)
    y1data.append(data_rate)
    y2data.append(bw_rate)
    # axis limits checking. Same as before, just for both axes
    for ax in [ax1, ax2]:
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if signal_dbm <= xmax:
            ax.set_xlim(xmin, 1.1*xmax)
        if data_rate >= ymax:
            ax.set_ylim(ymin, 1.1*data_rate)
        ymin, ymax = ax.get_ylim()
        if bw_rate >= ymax:
            ax.set_ylim(ymin, 1.1*bw_rate)
        ax.figure.canvas.draw()
    # update the data of both line objects
    if sample is True:
        line[0].set_data(xdata, y1data)
        line[1].set_data(xdata, y2data)
    else:
        line[2].set_data(xdata, y1data)
        line[3].set_data(xdata, y2data)
    return line




usage = 'WiFi Automation RSSi/DataRate/BW - Suresh Subramanian'
file_name = 'Wifi.'+ time.ctime().replace(" ", "_") + '.log'

logging.basicConfig(level=logging.INFO, filename=file_name, filemode='a',\
                datefmt='%m-%d %H:%M', \
       format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logging.info (usage)

iperfServer = connect("10.1.0.102", 'root', 'cpesit' )
iperfClient = connect("192.168.0.26", "root", "password")
linkself = connect("10.1.0.102", 'root', 'cpesit' )
attn = 0
incr = 5
attenuate(attn)
if not linkself.associate_with_ap():
    logging.error("Not able to associate. Exiting")
    exit()
tsharkSession = connect("10.1.0.102", 'root', 'cpesit' )
#tsharkSession.start_tshark()
iperfServer.startIperfServer()
iperfClient.startIperfClient()

state = 'init'
#-47.6 14.625 43.2966
#sig, dr, bw = 0.0
signal_dbm, data_rate, bw_rate = 0.0, 0.0, 0.0
# create a figure with two subplots
#plt.ion()
fig, (ax1, ax2) = plt.subplots(2,1)

# intialize two line objects (one in each axes)
line1, = ax1.plot([], [], lw=2, color='r', label = 'Data Rate')
line2, = ax1.plot([], [], lw=2, color='g', label='Throughput')
line3, = ax2.plot([], [], lw=2, color='r', label = 'Data Rate')
line4, = ax2.plot([], [], lw=2, color='g', label = 'Throughput')
line = [line1, line2, line3, line4]

sample = True
# the same axes initalizations as before (just now we do it for both of them)
ax1.set_title("B/W vs RSSI - Sample")
ax2.set_title("B/W vs RSSI - Iterations")
for ax in [ax1, ax2]:
    ax.set_ylim(0, 100)
    ax.set_xlim(-10, -45)
    ax.grid()
    ax.set_ylabel("B/W in Mbps")
    ax.set_xlabel("RSSI in dbm")
    ax.legend()
plt.tight_layout()

# initialize the data arrays 
xdata, y1data, y2data = [], [], []
#for a,b,c in data_gen():
#    print("iteration")
#    print(a,b,c)
ani = animation.FuncAnimation(fig, run, data_gen, blit=True, interval=1000,repeat=False)
plt.show()