import thinkdsp
import os, time, argparse, re, traceback, munch
import numpy as np
import tch_auto
    
    
def create_null_sinks(v):
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

def start_linphones(v):
    for linphone in v.linphones:
        linphone.execute('rm -f received.wav')
        linphone.execute('killall linphone linphonec')
        # linphone.execute('killall linphonec')
        out = linphone.execute('linphonec')
        if 'Could not start udp' not in out:
            tch_auto.log_info('Linphone started successfully in %s'%linphone.Hostname)
        else:
            tch_auto.log_error('Linphone failed to start in %s'%linphone.Hostname)
            v.failure_detected = True
        out = linphone.execute('soundcard use files')
        if 'Using wav files instead of soundcard' in out:
            tch_auto.log_info('Linphone started Using wav files instead of soundcard in %s'%linphone.Hostname)
        else:
            tch_auto.log_error('Linphone failed to use wav files instead of soundcard in %s'%linphone.Hostname)
            v.failure_detected = True

def call_play_recored_wav(v):
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
        v.calls = True
        tch_auto.log_info('Start Recording on %s'%v.linphone2.Hostname)
        v.linphone2.execute('record received.wav')
        time.sleep(1)
        tch_auto.log_info('Start Playing on %s'%v.linphone1.Hostname)
        v.linphone1.execute('play %s'%v.topo.lnx1.wavFile)
        time.sleep(2)
    else:
        v.failure_detected = True
        
def end_calls(v):
    for linphone in v.linphones:
        linphone.execute('terminate')
        time.sleep(5)
        linphone.execute('quit')
        time.sleep(5)
    v.calls = False
        
def copy_wave_file(v):
    ExeServer = v.topo.ExeServer
    os.system('rm -f received.wav')
    cmd = "sshpass -p %s scp -o StrictHostKeyChecking=no received.wav %s@%s:~/received.wav"\
    %(ExeServer.password, ExeServer.username, ExeServer.interface.controlBridge.ip )
    v.lnx2.execute(cmd)
    if not os.path.isfile('received.wav'):
        v.failure_detected = True
        tch_auto.log_error('File transferred failed from %s'%v.linphone1.Hostname)
    else:
        tch_auto.log_info('File transferred successfully from %s'%v.linphone1.Hostname)
    return

def corr_time_frame(v,duration=1):

    mcor = 0.9
    match_val = {}
    while mcor > 0.5:
        time_frame1 = 0.00
        time_frame = v.start + time_frame1
        while time_frame <= v.start+1:
            time_frame = v.start + time_frame1
            seg1 = v.wav1.segment(start=v.start, duration = duration)
            seg2 = v.wav2.segment(start=time_frame, duration = duration)
            match = seg1.corr(seg2)
            if match > 6:
                tch_auto.log_info('Corelation - %s'%(match))
            if match > mcor:
                match_val.update({time_frame1:match})
                tch_auto.log_info('Corelation Match - %s, With Time Lag = %s'%(match,time_frame1))
            time_frame1 += 0.00001               
        if len(match_val) == 0:
            mcor -= 0.1
        else:
            break
    if len(match_val) == 0:
        tch_auto.log_error('No Corelation found between two samples')
        v.failure_detected = True
        return False
    else:
        max_match = max(match_val.values())
        tch_auto.log_info('MAX Match - %s'%(max_match))
        time_s = []
        for key, val in match_val.items():
            if max_match == val:
                time_s.append(key)
        tch_auto.log_info('MAX-Time-lag - %s'%(time_s))
        time_s = np.array(time_s)
        return time_s.mean()
    
def validate_wav_files(v):
    copy_wave_file(v)
    if not v.failure_detected:
        v.wav1 = thinkdsp.read_wave(v.topo.lnx2.wavFile)
        v.wav1.normalize()
        temp = thinkdsp.read_wave('received.wav')
        temp1 = temp.segment(start=temp.duration-v.wav1.duration, duration=v.wav1.duration)
        filename = os.path.join(os.getcwd(),'received1.wav')
        temp1.write(filename)
        v.wav2 = thinkdsp.read_wave(filename)
        v.wav2.normalize()
        if v.wav1.duration == v.wav2.duration:
            if v.wav1.duration > 20:
                v.start = 15
            else:
                v.start = 2
            v.time_frame = corr_time_frame(v)
            if not v.failure_detected:
                start_time = v.time_frame + v.start
                duration = v.wav1.duration - start_time
                seg1 = v.wav1.segment(start=v.start, duration = duration)
                seg2 = v.wav2.segment(start=start_time, duration = duration)
                corr = seg1.corr(seg2)
                v.correation = format(corr, '.2f')
                v.correation = float(v.correation)*100
                tch_auto.log_info('Corelation of %s%% with lag - %s'%(v.correation, v.time_frame))
                v.deviated = 100-v.correation
                tch_auto.log_info('Deviated found between played and recorded wave file - %s%%'%v.deviated)
                return 
            else:
                if v.time_frame is False:
                    return False
        else:
            tch_auto.log_error('Wave files duration mis-match')
            v.failure_detected = True

