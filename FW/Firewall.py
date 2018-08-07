#!/usr/bin/env python

import os, re, time, sqlite3

LogFile = '/var/log/kern.log'
ConnData = {}

def MoniorFile():
    with open(LogFile , 'r+', encoding='latin1') as infile:
        for line in infile:
            pattern = r'([\w\s]+[\d:]+).*: Connection Established:.*IN=([\w]*)\s*OUT=([\w]*)\s*MAC=(([0-9A-F]{2}[:]){5}([0-9A-F]{2})):(([0-9A-F]{2}[:]){5}([0-9A-F]{2})).*SRC=(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})\s*DST=(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}).*SPT=(\d+)\s*DPT=(\d+)'
            match = re.search(pattern,line, re.S|re.I)
            if match:
                StartTime = match.group(1)
                OutInterface = match.group(2)
                InInterface = match.group(3)
                dstIP = match.group(10)
                srcIP = match.group(11)
                dstPort = match.group(12)
                srcPort = match.group(13)
                TranslatedIP = IP[OutInterface]
                TranslatedPort = srcPort
                ConnData.update({srcIP :{srcPort:{'DstPort':dstPort, 'DstIP':dstIP, 'Stime':StartTime,'TranslatedIP':TranslatedIP,'TranslatedPort':TranslatedPort}}})
                print(line)
            else:
                pattern = r'([\w\s]+[\d:]+).*: Connection Terminated:.*IN=([\w]*)\s*OUT=([\w]*)\s*MAC=(([0-9A-F]{2}[:]){5}([0-9A-F]{2})):(([0-9A-F]{2}[:]){5}([0-9A-F]{2})).*SRC=(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})\s*DST=(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}).*SPT=(\d+)\s*DPT=(\d+)'
                match = re.search(pattern,line, re.S|re.I)
                if match:
                    EndTime = match.group(1)
                    OutInterface = match.group(2)
                    InInterface = match.group(3)
                    dstIP = match.group(10)
                    srcIP = match.group(11)
                    dstPort = match.group(12)
                    srcPort = match.group(13)
                    print(line)
                    if srcIP in ConnData.keys():
                        if srcPort in ConnData[srcIP].keys():
                            ConnData[srcIP][srcPort].update({'ETime':EndTime})
                            DbUpdate(srcIP, srcPort, ConnData)
                            print('Database Updated')
        infile.truncate(0)
    return True

def connDB():
    global conn
    print(os.getcwd()+'/ConnectionLogs.db')
    conn = sqlite3.connect(os.getcwd()+'/ConnectionLogs.db')
    return conn
    
def CreateTableDB():
    conn = sqlite3.connect(os.getcwd()+'/ConnectionLogs.db')
    CreateTable = '''create table if not exists NatConn(
                    SRC_IP       TEXT    NOT NULL,
                    SRC_PORT     INT     NOT NULL,
                    DST_IP       TEXT    NOT NULL,
                    DST_PORT     INT     NOT NULL,
                    TRANSLATED_IP       TEXT    NOT NULL,
                    TRANSLATED_PORT     INT     NOT NULL,
                    START_TIME   TEXT,
                    END_TIME     TEXT);'''
    conn.execute(CreateTable)
    print('Table Created successfully')
    conn.commit()
    conn.close()
    return conn
    
def DbUpdate(srcIP, srcPort, ConnData):
    conn = sqlite3.connect(os.getcwd()+'/ConnectionLogs.db')
    # conn = connDB()
    KeyValue = ConnData[srcIP][srcPort]
    values = "'%s',%s,'%s',%s,'%s',%s,'%s','%s'"%(srcIP, srcPort,
    KeyValue['DstIP'],KeyValue['DstPort'], KeyValue['TranslatedIP'], KeyValue['TranslatedPort'], KeyValue['Stime'], KeyValue['ETime'])
    Keys = 'SRC_IP,SRC_PORT,DST_IP,DST_PORT,TRANSLATED_IP,TRANSLATED_PORT,START_TIME,END_TIME'
    print('INSERT INTO NatConn (%s) VALUES (%s);'%(Keys, values))
    conn.execute('INSERT INTO NatConn (%s) VALUES (%s);'%(Keys, values))
    conn.commit()
    cur = conn.execute('SELECT * from NatConn;')
    for row in cur:
        for r in row:
            print(r)
    
    print('Records saved')
    conn.close()
    return
    
def getAllIPs():
    ifconfig = os.popen("ifconfig | grep 'inet' -B1").read().split('\n')
    IPs = {}
    for line in ifconfig:
        m = re.search(r'(\w+):.*mtu',line,re.I|re.S)
        if m:
            iface = m.group(1)
            IPs.update({iface:''})
        else:
            m = re.search(r'inet (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})',line,re.I|re.S)
            if m:
                IPs[iface] = m.group(1)
                del iface
    print('Got IP - %s'%IPs)
    return IPs
    
def ApplyIPtables(wanIface='enp0s10'):
    cmds = []
    cmds.append('echo 1 > /proc/sys/net/ipv4/ip_forward')
    cmds.append('/sbin/iptables -F')
    cmds.append('/sbin/iptables -t nat -F')
    cmds.append('/sbin/iptables -t nat -A POSTROUTING -o %s -j MASQUERADE'%wanIface)
    cmds.append('iptables -I FORWARD 1 -p tcp --tcp-flags SYN SYN -j LOG --log-prefix "Connection Established:" -m state --state RELATED,ESTABLISHED')
    cmds.append('/sbin/iptables -I FORWARD 1 -p tcp --tcp-flags FIN FIN -j LOG --log-prefix "Connection Terminated:" -m state --state RELATED,ESTABLISHED')
    for cmd in cmds:
        print(cmd+os.popen(cmd).read())
    return
    
IP = getAllIPs()
CreateTableDB()
ApplyIPtables()
while True:
    try:
        MoniorFile()
    except KeyboardInterrupt:
        break
        
# import socket
# import contextlib
# import os

# def DomainServer(addr):
    # try:
        # if os.path.exists(addr):
            # os.unlink(addr)
        # sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        # SOCK_STREAM
        # SOCK_DGRAM
        # sock.bind(addr)
        # sock.listen(5)
        # yield sock
    # finally:
        # sock.close()
        # if os.path.exists(addr):
            # os.unlink(addr)

# addr = "/dev/log"
# addr = "/run/systemd/journal/dev-log"
# with DomainServer(addr) as sock:
    # while True:
        # print(sock)
        # conn, _ = sock.accept()
        # print(conn)
        # msg = conn.recv(1024)
        # print(msg)
        # conn.send(msg)
        # conn.close()
        
# path = "/dev/log"
# import os, stat
# mode = os.stat(path).st_mode
# isSocket = stat.S_ISSOCK(mode)
# isSocket
