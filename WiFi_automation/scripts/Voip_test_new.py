#!/usr/bin/env python
import os, time, yaml, re, traceback, munch
import argparse
from connect import connect
import tch_auto
from tch_auto import *
import unittest
import voip_test
    
def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Wifi Automation: Voip traffic verification",)
    parser.add_argument('-t', '--topo',
                        required=False,
                        default='/auto/WiFi_automation/topo/topo.yaml',
                        help='Provide testbed file')
                        
    args = parser.parse_args()
    return args
    
class Voip_test(unittest.TestCase):
    tch_auto.log_h1('Voip_test TestCase start')
    def setUp(self):
        tch_auto.log_h1('Common Setup')
        try:
            log_h1('Load Testbed file')
            args = get_args()
            v.topo = load_topology(args.topo)
            
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
                v.linphone1.IP = v.topo.lnx1.interface.pciEthernet1.ip
                v.linphone2.IP = v.topo.lnx2.interface.pciEthernet2.ip
            except:
                v.failure_detected = True
                tch_auto.log_error(traceback.format_exc(6))
                
        tch_auto.log_h1('Check validations in two linux machines')
        
        if not v.failure_detected:
            voip_test.create_null_sinks(v)
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
                
        self.assertEqual(v.failure_detected, False)
        
    def testTestRun(self):
        v.failure_detected = False
        tch_auto.log_h1('TestRun - Start')
        v.calls = False
        if not v.failure_detected:
            voip_test.start_linphones(v)
            
        if not v.failure_detected:
            duration = v.lnx1.execute('sox --i -D %s'%v.topo.lnx1.wavFile)
            voip_test.call_play_recored_wav(v)
            
        if not v.failure_detected:
            v.duration = float(duration) + time.time() + 60
            cmd = 'ls -l received.wav'
            buffer = []
            while v.duration > time.time():
                out = v.lnx2.execute(cmd)
                match = re.search(r'[-rwx]*\s+\w+\s+\w+\s+(\d+).*received.wav', out)
                if match:
                    buffer.append(match.group(1))
                if len(buffer)>=3:
                    if len(set(buffer))==1:
                        tch_auto.log_info('Playback and recording completed')
                        v.failure_detected = False
                        voip_test.end_calls(v)
                        break
                    else:
                        buffer.pop(0)
                        tch_auto.log_info('Playback and recording in progress')
               
                else:
                    v.failure_detected = True
                time.sleep(10)
            
        if v.failure_detected:
            tch_auto.log_error('Playback and recording was not completed in expected time')
            voip_test.end_calls(v)
        else:
            voip_test.validate_wav_files(v)
            
    def tearDown(self):
        tch_auto.log_h1('Common CleanUP - Start')
        if v.failure_detected:
            voip_test.end_calls(v)
        for lnx in v.linphones:
            lnx.execute('killall pulseaudio')
        try:
            tch_auto.log_info('Clear all ssh console sessions')
            for linphone in v.linphones:
                linphone.close()
            for lnx in v.lnxs:
                lnx.close()
        except:
            tch_auto.log_error(traceback.format_exc(6))
        tch_auto.report(v)
        tch_auto.log_h1('Voip_test TestCase End')


        
if __name__ == "__main__":
    unittest.main()