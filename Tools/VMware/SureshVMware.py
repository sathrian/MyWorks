#!/usr/bin/env python

import pyVmomi
import argparse
import atexit
import itertools
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import humanize
import ssl,json, pprint

ssl._create_default_https_context = ssl._create_unverified_context

MBFACTOR = float(1 << 20)
GBFACTOR = float(1 << 30)

printVM = True
printDatastore = True
printHost = True

Records = {}


def GetArgs():
    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')
    parser.add_argument('-s', '--host', required=False, action='store',default="10.124.132.44",
                        help='Remote host to connect to')
    parser.add_argument('-o', '--port', type=int, default=443, action='store',
                        help='Port to connect on')
    parser.add_argument('-u', '--user', required=False, action='store', default="root",
                        help='User name to use when connecting to host')
    parser.add_argument('-p', '--password', required=False, action='store', default="Password@123",
                        help='Password to use when connecting to host')
    args = parser.parse_args()
    return args


def printHostInformation(host):
    try:
        summary = host.summary
        for vinc in summary.host.config.network.vnic:
            IP = vinc.spec.ip.ipAddress
        global HostName
        global cpuMhz
        HostName = host.name
        vendor = host.hardware.systemInfo.vendor
        model = host.hardware.systemInfo.model
        # Host.summary.host.config.storageDevice.scsiLun[0].model
        serialNumber = host.hardware.systemInfo.serialNumber
        cpuCores = summary.hardware.numCpuCores
        cpuModel = summary.hardware.cpuModel
        Ram = round(summary.hardware.memorySize/GBFACTOR)
        overallStatus = summary.overallStatus
        stats = summary.quickStats
        hardware = host.hardware
        cpuUsage = stats.overallCpuUsage
        cpuMhz = summary.hardware.cpuMhz
        cpuUsagePercentage = cpuUsage/(cpuMhz*summary.hardware.numCpuCores)*100
        memoryCapacityInMB = hardware.memorySize/MBFACTOR
        memoryUsage = stats.overallMemoryUsage
        MemoryPercentage = (float(memoryUsage) / memoryCapacityInMB) * 100
        Records.update({'IP Address':vinc.spec.ip.ipAddress,
                                   'CPU Usage' : round(cpuUsagePercentage,2),
                                   'Memory Usage' : round(MemoryPercentage,2),
                                   'Host Name' : HostName,
                        'vendor':vendor,
                        'model': model,
                        'serialNumber': serialNumber,
                        'cpuCores':cpuCores,
                        'cpuModel': cpuModel,
                        'Ram':Ram
        })
        #'OverallStatus' : overallStatus.upper(),
    except Exception as error:
        print("Unable to access information for host: ", host.name)
        print(error)
        pass

def printComputeResourceInformation(computeResource):
    try:
        hostList = computeResource.host
       # print("##################################################")
       # print("Compute resource name: ", computeResource.name)
       # print("##################################################")
        for host in hostList:
            printHostInformation(host)
    except Exception as error:
        print("Unable to access information for compute resource: ",
              computeResource.name)
        print(error)
        pass

def printDatastoreInformation(datastore):
    try:
        Records.update({"Storage": []})
        summary = datastore.summary
        # for extent in datastore.info.vmfs:
        #     Records['Storage'].append(extent.diskName)
        capacity = summary.capacity
        freeSpace = summary.freeSpace
        uncommittedSpace = summary.uncommitted
        UsedSpacePercentage = (float(capacity-freeSpace) / capacity) * 100
        print(HostName)
       
       # print("##################################################")
       # print("Datastore name: ", summary.name)
       # print("Capacity: ", humanize.naturalsize(capacity, binary=True))
        if uncommittedSpace is not None:
            provisionedSpace = (capacity - freeSpace) + uncommittedSpace
            print("Provisioned space: ", humanize.naturalsize(provisionedSpace,
                                                              binary=True))
       # print("Free space: ", humanize.naturalsize(freeSpace, binary=True))
       # print("Used space percentage: " + str(UsedSpacePercentage) + "%")
       # print("##################################################")
        Records.update({"Used space percentage": round(UsedSpacePercentage,2)})
        #Records[HostName].update({summary.name : {"Capacity": humanize.naturalsize(capacity, binary=True),
       # "Provisioned space": humanize.naturalsize(provisionedSpace, binary=True),
       # "Free space": humanize.naturalsize(freeSpace, binary=True),
       # "Used space percentage": str(int(UsedSpacePercentage))+ "%"}})
    except Exception as error:
        print("Unable to access summary for datastore: ", datastore.name)
        print(error)
        pass


def printVmInformation(virtual_machine, Record, depth=1):
    maxdepth = 10
    if hasattr(virtual_machine, 'childEntity'):
        if depth > maxdepth:
            return
        vmList = virtual_machine.childEntity
        for c in vmList:
            printVmInformation(c, depth + 1)
        return
    try:
        PowerON = False
        summary = virtual_machine.summary
        cpuUsagePercentage = None
        if summary.runtime.powerState == 'poweredOn':
            PowerON = True
        if PowerON:
            cpuUsagePercentage = summary.quickStats.overallCpuUsage/(summary.config.numCpu*cpuMhz)
            memUsagePercentage = summary.quickStats.overallCpuUsage/(summary.config.numCpu*cpuMhz)
        print("State : ", summary.runtime.powerState)
        Record.update({'Power State' : summary.runtime.powerState})
        nic_count = 0
        Nics = None
        for nic in virtual_machine.guest.net:
            nicName = 'Nic' + str(nic_count+1)
            ipAddress = list(nic.ipAddress)
            macAddress = nic.macAddress
            Nics = {nicName:{'IP Address':ipAddress, 'MAC Address': macAddress}}
        if not Nics:
            Nics = {'Nic1':{'IP Address':'NA', 'MAC Address': 'NA'}}
        Record.update({'vNICs': Nics})
        # pprint.pprint('Records')
        # pprint.pprint(Record)
        # return Record
    except Exception as error:
        print("Unable to access summary for VM: ", virtual_machine.name)
        print(virtual_machine.guest.net)
        print(error)
        exit()
        #pass

def VMware(host, user, pwd, port):
    #args = GetArgs()
    try:
    #si = SmartConnect(host=args.host, user=args.user, pwd=args.password, port=int(args.port))
        si = SmartConnect(host=host, user=user, pwd=pwd, port=port)
                     # unverified=True)
        atexit.register(Disconnect, si)

        content = si.RetrieveContent()
    except vim.fault.InvalidLogin:
        raise Exception("Invalid username or password.")
            
    for datacenter in content.rootFolder.childEntity:
        if printHost:
            if hasattr(datacenter.hostFolder, 'childEntity'):
                hostFolder = datacenter.hostFolder
                computeResourceList = hostFolder.childEntity
                for computeResource in computeResourceList:
                    printComputeResourceInformation(computeResource)

    if printDatastore:
        datastores = datacenter.datastore
        for ds in datastores:
            printDatastoreInformation(ds)
            
    if hasattr(datacenter.vmFolder, 'childEntity'):
        vmFolder = datacenter.vmFolder
        vmList = vmFolder.childEntity
        Records.update({'Number of VMs': len(vmList)})
        # if printVM:
        #     Records.update({'VMs':{}})
            # for vm in vmList:
            #     Records['VMs'].update({vm.name:{}})
                # printVmInformation(vm, Records['VMs'][vm.name])
        # pprint.pprint('Records - global')
        # pprint.pprint(Records)
        
    
    return Records

if __name__ == "__main__":
    args = GetArgs()
    VMware(host=args.host, user=args.user, pwd=args.password, port=int(args.port))