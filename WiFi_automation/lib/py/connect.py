import re
import Exscript
import time
from tch_auto import *
import os

class connect():

    def ssh_connect(self):
        self.connected = False
        self.conn = Exscript.protocols.SSH2()
        self.prompt = re.compile(r'.*[$#] *$|.*>>> \x1b\[0m$')
        self.conn.set_prompt(re.compile(self.prompt))
        log_info('Connecting to %s' % self.VmIP)
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
                log_error(line + self.conn.response)
                log_error("buffer:\n" +line + self.conn.buffer.io.getvalue())
                raise
            str1 = re.sub('\|', '__PIPE__', self.conn.response)
            str2 = re.sub('\|', '__PIPE__', cmd)
            str3 = re.sub(str2, '', str1)
            response_raw = str3
            resp = response_raw.replace('\r\n\r\x00', '\n')
            self.conn.response = resp
            if resp != '' and resp != '\r':
                log_info(line + '\n' + resp)
            else:
                log_info(line)
            if not raw:
                return resp
            else:
                return response_raw
        else:
            log_error('ERROR: %s is not connected' % self.Hostname)
            
    def fill_buffer(self):
        if self.connected:
            if not self.conn._wait_for_data():
                log_error = 'Timeout while waiting for response from device'
                raise Exception(log_error)
            data = self.conn.shell.recv(200).decode("utf-8")
            if not data:
                return False
            self.conn._receive_cb(data)
            self.conn.buffer.append(data)
            return True
            
    def send_control_c(self):
        try:
            self.conn.send('\x03')
        except:
            pass
            
    def get_full_buffer(self,command, wait_time=5):
        if self.connected:
            log_info(command, 'Executing:')
            print('Executing: \n', command)
            self.conn.send(command + '\r')
            end_time = time.time() + wait_time
            old_timeout = self.conn.get_timeout()
            self.conn.set_timeout(1)
            response = ''
            while time.time() < end_time:
                try:
                    self.fill_buffer()
                    response += self.conn.buffer.__str__()
                    response = response.replace('\r\n\r\x00', '\n')
                    self.conn.buffer.clear()                    
                except Exception as e:
                    pass
            self.conn.buffer.clear()
            self.conn.set_timeout(old_timeout)
            log_info(response, 'Response:')
            return response
        else:
            log_error('ERROR: %s is not connected' % self.Hostname)
            return False
    
    def close(self):
        log_info('Disconnecting from %s' % self.Hostname)
        self.conn.close(force=True)
        self.conn.close(force=True)
        self.connected = False

    def expect(self,value):
        try:
            self.conn.expect(value)
            out = self.conn.response
            log_info("response:\n" + self.conn.response)
            log_info("buffer:\n" + self.conn.buffer.io.getvalue())
        except:
            log_error("response:\n" + self.conn.response)
            log_error("buffer:\n" + self.conn.buffer.io.getvalue())
            out = self.conn.buffer.io.getvalue()
            raise
        return out
        
    def start_tshark(self):
        out = self.get_full_buffer("tshark -l -i mon0 -f 'wlan src 9a:87:31:53:02:81 and type data' -T fields -e wlan_radio.signal_dbm -e wlan_radio.data_rate")
        if "Capturing on 'mon0'" in out:
            log_info("Started capturing packets")
            return True
        else:
            log_error("Not able to start tshark: \n", out)
            return False

    def associate_with_ap(self):
        cmds = ["ip link set wlp2s0 down",
        "iwconfig wlp2s0 essid 1-ccsp-5g",
        "iwconfig wlp2s0 channel 36",
        "ip link set wlp2s0 up",
        "iwconfig wlp2s0"]
        for cmd in cmds:
            self.conn.execute(cmd)
        return
        
    def startIperfClient(self):
        out = self.get_full_buffer("iperf3 -u -p 5002 -c 192.168.0.12 -t 1000 -b 500M -f k")
        if "connected with 192.168.0.26" in out:
            log_info("client up and connected to server")
            return True
        else:
            log_error("Iperf Client not able to connect: \n", out)
            return False

    def startIperfServer(self):
    
        out = self.get_full_buffer("iperf3 -s -p 5002 -i 1 -f k")
        pattern="Server listening .*\-+"
        if pattern in out:
            log_info("Server listens")
            return True
        else:
            log_error("Iperf Server not listening: \n", out)
            return False
            
    def cmd_check(self, cmd, validation, iteration=1, interval = 5):
        count = 0 
        while iteration > count:
            try:
                status = True
                count +=1
                output = self.execute(cmd)
                if validation.present:
                    for pattern in validation.present:
                        if re.search(pattern, output, re.S|re.I):
                            log_info('%s - present as expected in %s'%(pattern, self.Hostname))
                        else:
                            log_error('%s - absent which is not expected in %s'%(pattern, self.Hostname))
                            status = False
                if validation.absent:
                    for pattern in validation.present:
                        if not re.search(pattern, output, re.S|re.I):
                            log_info('%s - absent as expected'%(pattern, self.Hostname))
                        else:
                            log_error('%s - exists which is not expected in %s'%(pattern, self.Hostname))
                            status = False
                if not status:
                    time.sleep(interval)
                else:
                    break
            except Exception as e:
                status = False
                log_error(e)
                log_error(traceback.format_exc(6))
        return status
        
            
    def __init__(self,  device, retry=0, retry_interval=15):
        
        if 'hostname' in device.keys():
            self.Hostname = device.hostname
            
        if 'prompt' not in device.keys():
            if device.platform == 'stb':
                device.prompt = re.compile(r'.*[>#] *$')
            elif device.platform == 'linux':
                #device.prompt = re.compile(r'.*[$#] *$|.*>>> *$')
                device.prompt = re.compile(r'.*[$#] *$|linphonec\>|.*>>> \x1b\[0m$')
                
        if 'console' in device.keys():
            device.protocol = device.console.split()[0]
            device.host = device.console.split()[1]
            if len(device.console.split()) == 3:
                device.port = device.console.split()[2]
                
        if device.protocol.lower() == 'ssh':
            self.conn = Exscript.protocols.SSH2()

            #
            # Set driver
            #
            self.conn.set_driver('generic')

            if 'host' in device.keys():
                if 'prompt' in device.keys() and device.prompt != '':
                    self.conn.set_prompt(re.compile(device.prompt))

                self.conn.connect(device.host, device.port)

                if 'username' in device.keys() and 'password' in device.keys():
                    account = Exscript.Account(device.username,
                                               device.password)
                self.conn.login(account)

                #Nick: change default conn_timeout to 30 secs
                #self.conn.set_timeout(5)
                self.conn.set_timeout(30)

                self.connected = True
                if device.platform == 'linux':
                    self.execute('uname -a')
                elif device.platform == 'stb':
                    self.execute('show version')
        
        
        elif device.protocol.lower() == 'telnet':
            self.conn = Exscript.protocols.Telnet()
            self.conn.proto_authenticated = False
            if 'stb' in device.platform.lower():
                self.conn.app_authenticated = True
                self.conn.app_authorized = True
            else:
                self.conn.app_authenticated = False
                self.conn.app_authorized = False
            self.conn.set_timeout(5)
            if 'host' in self.connect_method.keys():
                Exscript.protocols.drivers.driver._user_re =\
                        [re.compile(r'(user ?name|login): ?$', re.I)]
                self.conn.set_driver('ios')
                self.conn.connect(device.host, device.port)
                self.conn.set_prompt(re.compile(device.prompt))

                a1 = Exscript.Account(None, None)
                a2 = Exscript.Account(None, None)
                if 'password' in self.connect_method.keys():
                    a1 = Exscript.Account(device.username,
                                          device.password)
                # Login
                time.sleep(1)
                self.conn.send('\r\r\r')
                tch_auto.log_nb('Telnet login')
                cnt = 0
                max = 3
                while not self.conn.is_protocol_authenticated() and cnt < max:
                    cnt += 1
                    try:
                        tch_auto.log_nb("connected")
                        self.conn.send('\r\r\r')
                        if 'stb' in device.platform.lower():
                            self.conn.authenticate(a1)
                            try:
                                tch_auto.log_nb('username: %s ; password: hidden' % (a1.name))
                                tch_auto.log_nb(self.conn.response)
                            except Exception as e:
                                tch_auto.log_nb('username: %s ; password: %s' % (a1.name, a1.password))
                                print(e)
                                tch_auto.log_nb(self.conn.buffer.io.getvalue().decode())
                                raise
                        else:
                            self.conn.authenticate(a1, None, flush=False)
                        break
                    except:
                        if cnt < max:
                            time.sleep(1)
                        else:
                            self.conn.close(True)
                            raise TimeoutException

                #
                # Get prompt
                #
                try:
                    self.conn.send('\r\r\r')
                    p = self.conn.expect_prompt()
                    resp = p[1].group()
                except:
                    self.conn.close(True)
                    raise

                tch_auto.log_nb(resp)
                if 'stb' in device.platform.lower():
                    self.conn.app_authenticated = False

                if not self.conn.is_app_authorized():
                    tch_auto.log_nb('2nd level login')
                    self.conn.send('\r\r')
                    self.conn.app_authorize(a2)

                self.connected = True
                self.execute('show version')
        