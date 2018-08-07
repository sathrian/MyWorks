#!/usr/bin/env python
import os, time, argparse, yaml, re, traceback, munch
from connect import connect
import tch_auto


def get_args():
    """ Get arguments from CLI """
    
    parser.add_argument('-t', '--topo',
                        required=False,
                        default='/auto/WiFi_automation/topo/topo.yaml',
                        help='Provide testbed file')
                        
    args = parser.parse_args()
    return args
    
tch_auto.log_h1('Common Setup')
def CommonSetup():
    if not v.failure_detected:
        try:
            tch_auto.log_h1('Load Testbed file')
            args = get_args()
            v.topo = tch_auto.load_topology(args.topo)
        except:
            v.failure_detected = True
            tch_auto.log_error(traceback.format_exc(6))
    

    tch_auto.log_info('Connect to devices')
    if not v.failure_detected:
        try:
            v.lnx1 = connect(v.topo.lnx1)
            v.lnx2 = connect(v.topo.lnx2)
            v.linphone1 = connect(v.topo.lnx1)
            v.linphone2 = connect(v.topo.lnx2)
            v.lnxs = [v.lnx1, v.lnx2]
            v.linphones = [v.linphone1, v.linphone2]
            v.linphone1.IP = v.topo.lnx1.interface.onboardEthernet.ip
            v.linphone2.IP = v.topo.lnx2.interface.onboardEthernet.ip
            
            for linphone in v.linphones:
                linphone.prompt = linphone.conn.get_prompt()
                #changing the prompt
                linphone.conn.set_prompt(re.compile(r'.*[$]|linphonec>'))
        except:
            v.failure_detected = True
            tch_auto.log_error(traceback.format_exc(6))
            
CommonSetup()

def TestSetup():

    tch_auto.log_h1('TestSetup - Start')
    tch_auto.log_h1('Check validations in two linux machines')
    
    if not v.failure_detected:
        cmds = []
        cmds.append('killall pulseaudio')
        cmds.append('pulseaudio -D')
        for cmd in cmds:
            for lnx in v.linphones:
                lnx.execute(cmd)
                
        validation = munch.munchify({
                        'present':[],
                        'absent':[]})
        cmd = 'pactl list sources'
        validation.present.append(r'Name: auto_null.monitor')
        if not v.lnx1.cmd_check(cmd, validation) or not v.lnx2.cmd_check(cmd, validation):
            v.failure_detected = True
        
        cmd = 'pactl list sinks'
        validation = munch.munchify({
                        'present':[],
                        'absent':[]})
        validation.present.append(r'Driver: module-null-sink.c')
        
        if not v.lnx1.cmd_check(cmd, validation) or not v.lnx2.cmd_check(cmd, validation):
            v.failure_detected = True
    
    tch_auto.log_h1('create virtual mic/speaker on two linux machines')
    if not v.failure_detected:
        cmds = []
        cmds.append('pactl load-module module-null-sink sink_name=fakemic')
        cmds.append('pactl load-module module-null-sink sink_name=fakespeaker')
        
        for cmd in cmds:
            for lnx in v.linphones:
                lnx.execute(cmd)
    
        validation = munch.munchify({
                        'present':[],
                        'absent':[]})
        cmd = 'pactl list short sources'
        validation.present.append(r'fakemic.monitor')
        validation.present.append(r'fakespeaker.monitor')
        if not v.lnx1.cmd_check(cmd, validation) or not v.lnx2.cmd_check(cmd, validation):
            v.failure_detected = True
        
        cmds = []
        cmds.append('pactl set-default-sink fakespeaker')
        cmds.append('pactl set-default-source fakemic.monitor')
        
        for cmd in cmds:
            for lnx in v.linphones:
                lnx.execute(cmd)
                
        validation = munch.munchify({
                        'present':[],
                        'absent':[]})
        cmd = 'cat ~/.linphonerc'
        validation.present.append(r'[sound]')
        validation.present.append(r'playback_dev_id=PulseAudio: default')
        validation.present.append(r'ringer_dev_id=PulseAudio: default')
        validation.present.append(r'capture_dev_id=PulseAudio: default')
        
        if not v.linphone1.cmd_check(cmd, validation) or not v.linphone2.cmd_check(cmd, validation):
            v.failure_detected = True
        
TestSetup()

def TestRun():
    tch_auto.log_h1('TestRun - Start')
    if not v.failure_detected:
        for linphone in v.linphones:
            linphone.execute('killall linphone linphonec parecord paplay')
            # linphone.execute('killall linphonec')
            out = linphone.execute('linphonec')
            if 'Could not start udp' not in out:
                tch_auto.log_info('Linphone started successfully in %s'%linphone.Hostname)
            else:
                tch_auto.log_error('Linphone failed to start in %s'%linphone.Hostname)
                v.failure_detected = True
                
    if not v.failure_detected:
        if 'Auto answer enabled.' in v.linphone1.execute('autoanswer enable'):
            tch_auto.log_info('Auto answer enabled successfully in %s'%v.linphone1.Hostname)
            
        pattern = 'Establishing call id to <sip:%s>, assigned id \d+.'%v.linphone1.IP
        cmd = 'call sip:%s'%v.linphone1.IP
        out = v.linphone2.execute(cmd)
        if pattern in out:
            tch_auto.log_info('Call getting established for %s'%v.linphone1.Hostname)
        
        cmd = 'calls'
        validation = munch.munchify({
                        'present':[],
                        'absent':[]})
        validation.present.append(r'.*<sip:%s>.*StreamsRunning'%v.linphone1.IP)
        # validation.present.append(r'9  __PIPE__ <sip:10.78.192.120>                 __PIPE__ StreamsRunning  __PIPE__')
        if v.linphone2.cmd_check(cmd, validation, 6):
            cmds = []
            cmds.append('killall parecord paplay')
            cmds.append('parecord --device=fakespeaker.monitor --file-format=wav received1.wav &')
            cmds.append('paplay --device=fakemic Thendral.wav &')
            pid = {}
            for cmd in cmds:
                for lnx in v.lnxs:
                    if 'paplay' in cmd:
                        key = 'paplay'
                    else:
                        key = 'parecord'
                    out = lnx.execute(cmd)
                    m = re.search(r'\[\d\]+\s+(\d+)', out)
                    if m:
                        if lnx.Hostname in pid.keys():
                            pid[lnx.Hostname].update({key:m.group(1)})
                        else:
                            pid.update({lnx.Hostname:{key:m.group(1)}})
            cmd = 'pgrep paplay'
            while True:
                for lnx in v.lnxs:
                    tch_auto.log_info(lnx.Hostname)
                    out = lnx.execute(cmd)
                    if pid[lnx.Hostname]['paplay'] not in out:
                        lnx.execute('killall parecord')
                        pid[lnx.Hostname].update({'paplay':'Done'})
                if pid[v.lnx1.Hostname]['paplay'] and pid[v.lnx1.Hostname]['paplay'] != 'Done':
                    time.sleep(30)
                if pid[v.lnx1.Hostname]['paplay'] and pid[v.lnx1.Hostname]['paplay'] == 'Done':
                    break
                if not v.failure_detected:
                    for linphone in v.linphones:
                        linphone.execute('terminate')
                        linphone.execute('quit')
            
        
        