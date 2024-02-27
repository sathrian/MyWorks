# python:rest:delete bps reports
import os, sys

# Add bps_restpy libpath *required if the library is not installed
libpath = r"../../BreakingPoint-master/RestApi/Python/RestApi_v2/Modules"
sys.path.insert(0, libpath)
from bps_restpy.bps import BPS

# BPS system information
# BPS_SYSTEM = '10.124.174.10'
# BPS_SYSTEM = '10.124.167.52'
BPS_SYSTEM = '10.5.134.25'
# BPS_SYSTEM = 'merpil1d.lbj.is.keysight.com'
# BPS_USER = 'admin'
BPS_USER = 'suresh'
# BPS_PASSWORD = '!'
# BPS_PASSWORD = '!1'
BPS_PASSWORD = 'suresh'

pyBps = BPS(BPS_SYSTEM, BPS_USER, BPS_PASSWORD)
pyBps.login()



def bps_delete_report(type, limit=100):
    status = ["passed", "failed", "error", "canceled"]
    for state in status:
        data = pyBps.reports.search(searchString=state, limit=limit, sort=type, sortorder="ascending")
        if data:
            for item in data:
                print(f"deleting report {item['name']}")
                pyBps.reports.delete(runid=item['runid'])


bps_delete_report(type="user", limit=100)