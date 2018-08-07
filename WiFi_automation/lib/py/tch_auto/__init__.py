import logging
import yaml
import re
import time
import requests
import traceback
import os
import sys
import textwrap
import builtins
import argparse
from munch import munchify
from munch import Munch

class Script:
    def __init__(self):
        self.failure_detected = False
builtins.v = Script()
builtins.log = logging.getLogger('log')

def load_yaml(yaml_file):
    log_info("YAML file: %s" % yaml_file)
    data = munchify(yaml.load(open(yaml_file,'r')))
    log_info("YAML data:\n--------------\n %s" % data)
    return data

def load_topology(topo,silent=False):
    log_info("Topology file: %s" % topo)
    data = munchify(yaml.load(open(topo,'r')))
    if silent == False:
        log_info("Topology data:\n--------------\n %s" % data)
    return data
    
    
def description(obj):
    return re.sub('\n    ', '\n', str(obj.__doc__))

wrapper = textwrap.TextWrapper()

def decode_str(arg1):
    msg = arg1
    if sys.version_info.major == 2:
        if isinstance(msg,bytes):
            msg = msg.decode('ascii','replace')
        if isinstance(msg,unicode):
            msg = msg.encode('ascii','replace')
    else:
        if isinstance(msg,str):
            # This turns it into bytes. It is needed for python3
            msg = msg.encode('ascii','replace')
        if isinstance(msg,bytes):
            msg = msg.decode('ascii','replace')
    return msg
    
def log_msg(msg, char1='+', char2='=', char3='|', extra=False, log_type='info'):
    global wrapper
    width = 110 - (len(char3) * 2)
    wrapper.width = width
    wrapper.initial_indent = char3 + ' '
    wrapper.subsequent_indent = char3 + ' '

    exec("log.%s(char1 + char2*width + char1)" % log_type)
    if not extra:
        exec("log.%s(char3 + ' '*width + char3)" % log_type)

    msg = decode_str(msg)
    lines = str(msg).splitlines()
    for line in lines:
        lns = wrapper.wrap(line)
        for ln in lns:
            exec("log.%s(ln + ' ' * (110 - len(ln) - len(char3)) + char3)" % log_type)
    if not extra:
        exec("log.%s(char3 + ' '*width + char3)" % log_type)

    exec("log.%s(char1 + char2*width + char1)" % log_type)
        
def log_h1(msg, title=''):
    msg = decode_str(msg)
    log.info(title)
    log_msg(msg, '##', '#', '##', True)

def log_h2(msg, title=''):
    msg = decode_str(msg)
    log.info(title)
    log_msg(msg, '||', '|', '||', True)

def log_info1(msg, title=''):
    msg = decode_str(msg)
    log.info(title)
    log_msg(msg, '::', ':', '::', True)


def log_info2(msg, title=''):
    msg = decode_str(msg)
    log.info(title)
    log_msg(msg, '+', '*', '|')


def log_info3(msg, title=''):
    msg = decode_str(msg)
    log.info(title)
    log_msg(msg, '*', '+', '|')


def log_info(msg, title=''):
    msg = decode_str(msg)
    if title != '':
        log.info(title)
    log_msg(msg, '+', '-', '|')

def log_error(msg, title=''):
    msg = decode_str(msg)
    log.info(title)
    log_msg(msg, '>>', '>', '>>', True, 'error')

def log_warning(msg, title=''):
    msg = decode_str(msg)
    log.error(title)
    log_msg(msg, '!!', '!', '!!', True, 'warning')
    log.error('')
    
def report(v):
    line = 'http://%s/testruns/%s/__Task__.log'%(v.topo.ExeServer.interface.controlBridge.ip, 'Runinfo_'+Stime)
    log_info1('Logs will be available at below link')
    log_info1(line)
                    
Stime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
# Stime = 'test'
# folder = os.path.join(os.getcwd(),'Runinfo_'+Stime)
folder = os.path.join('/auto/WiFi_automation/Runs','Runinfo_'+Stime)
os.mkdir(folder)
file_name = os.path.join(folder, '__Task__.log')
# report_file = os.path.join(folder, 'report.log')
usage = 'Job Started, please follow logs - %s'%file_name


if os.isatty(0):
    
    logging.basicConfig(stream = sys.stdout,
                        level = logging.DEBUG,
                                 format = '%(asctime)s TCH_AUTO : %(levelname)-8s : %(message)s',
                                 datefmt = '%m-%d-%y %H:%M:%S')
else:
    builtins.log = logging.getLogger(__name__)
    builtins.log.setLevel(logging.DEBUG)



# console = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)-10s TCH_AUTO : %(levelname)-8s : %(message)s',
                              datefmt = '%m-%d-%y %H:%M:%S')
# console.setFormatter(formatter)
# console.setLevel(logging.INFO)
# logging.getLogger('').addHandler(console)

# reports = logging.FileHandler(report_file)
log_file = logging.FileHandler(file_name)
log_file.setFormatter(formatter)

builtins.log.addHandler(log_file)
builtins.results = logging.getLogger('results')
# builtins.results.addHandler(reports)
# log.info(usage)
