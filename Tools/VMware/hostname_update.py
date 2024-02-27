import os
from munch import munchify
import csv
import pyVmomi
import argparse
import atexit
import itertools
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import humanize
import ssl,json, pprint

ssl._create_default_https_context = ssl._create_unverified_context
csv_file1 = os.path.join(os.getcwd(), f'Servers_CPT_test.csv')
def read_csv(path, column_names):
    with open(path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            record = {name: value for name, value in zip(column_names, row)}
            yield record

records = list(read_csv(csv_file1, ["hostname",'host','user','pwd','owner']))
records.pop(0)

for record in records:
    host = munchify(record)
    try:
        # si = SmartConnect(host=args.host, user=args.user, pwd=args.password, port=int(args.port))
        si = SmartConnect(host=host.host, user=host.user, pwd=host.pwd, port=443)
        # unverified=True)
        atexit.register(Disconnect, si)

        content = si.RetrieveContent()
    except vim.fault.InvalidLogin:
        raise Exception("Invalid username or password.")

    for datacenter in content.rootFolder.childEntity:
        if hasattr(datacenter.hostFolder, 'childEntity'):
            hostFolder = datacenter.hostFolder
            computeResourceList = hostFolder.childEntity
            for computeResource in computeResourceList:
                hostList = computeResource.host
                for Host in hostList:
                    dnsConfig = Host.config.network.dnsConfig
                    dnsConfig.hostName = host.hostname
                    dnsConfig.domainName = 'cpt.pa.local'
                    dnsConfig.searchDomain = ['cpt.pa.local', 'pa.local']
                    dnsConfig.address = ['10.0.167.3', '10.0.4.11']
                    Host.configManager.networkSystem.UpdateDnsConfig(dnsConfig)

# Add-DnsServerResourceRecordA -Name "banyan" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.3" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "neem" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.5" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "peepal" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.7" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "palm" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.9" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "bael" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.11" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "ashoka" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.13" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "pine" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.12" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "eucalyptus" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.174.4" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "apple" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.175.132" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "alder" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.167.107" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "basswood" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.167.109" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "birch" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.167.111" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "buckeye" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.3" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "buckthorn" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.4" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "cherry" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.5" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "chestnut" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.6" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "chinkapin" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.7" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "dogwood" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.8" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "catalpa" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.164.9" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "cypress" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.6" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "honeylocus" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.6" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "cottonwood" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.3" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "redwood" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.8" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "locust" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.4" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "hemlock" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.14" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "maple" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.18" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "tanoak" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.12" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "walnut" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.16" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "madrone" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.171.10" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "hawthorn" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.16" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "spruce" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.14" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "sweetgum" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.10" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "kannimara" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.173.12" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "kalayaan" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.162.24" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "rahmat" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.170.27" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "changi" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.170.31" -TimeToLive 00:04:00
# Add-DnsServerResourceRecordA -Name "Morinda" -ZoneName "cpt.paloaltonetworks.local" -AllowUpdateAny -IPv4Address "10.124.170.21" -TimeToLive 00:04:00
