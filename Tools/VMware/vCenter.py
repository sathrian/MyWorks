#!/usr/bin/env python

import pyVmomi
import atexit
import itertools
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import humanize
import ssl,json, pprint

ssl._create_default_https_context = ssl._create_unverified_context

MBFACTOR = float(1 << 20)

printVM = False
printDatastore = True
printHost = True

Records = {}

def printHostInformation(host, Record):
    try:
        summary = host.summary
        if summary.runtime.connectionState == 'disconnected':
            Record.update({
                'ConnectionState': summary.runtime.connectionState
             })
            raise Exception
        for vinc in summary.host.config.network.vnic:
            IP = vinc.spec.ip.ipAddress
        global HostName
        global cpuMhz
        HostName = host.name
        overallStatus = host.overallStatus
        stats = summary.quickStats
        hardware = host.hardware
        cpuUsage = stats.overallCpuUsage
        cpuMhz = summary.hardware.cpuMhz
        cpuUsagePercentage = cpuUsage/(cpuMhz*summary.hardware.numCpuCores)*100
        memoryCapacityInMB = hardware.memorySize/MBFACTOR
        memoryUsage = stats.overallMemoryUsage
        MemoryPercentage = (float(memoryUsage) / memoryCapacityInMB) * 100
        Record.update({
            'IP Address':vinc.spec.ip.ipAddress,
            'CPU Usage' : round(cpuUsagePercentage,2),
            'Memory Usage' : round(MemoryPercentage,2),
            'Host Name' : HostName,
            'Number of VMs':len(host.vm),
            'OverallStatus' : overallStatus.upper(),
            'ConnectionState': summary.runtime.connectionState
        })
        
    except Exception as error:
        print("Unable to access information for host: ", host.name)
        print(error)
        pass


def printComputeResourceInformation(computeResource, Record):
    try:
        hostList = computeResource.host
        # print("##################################################")
        # print("Compute resource name: ", computeResource.name)
        # print("##################################################")
        for host in hostList:
            printHostInformation(host, Record)
    except Exception as error:
        print("Unable to access information for compute resource: ",
              computeResource.name)
        print(error)
        pass

def printDatastoreInformation(datastore, Record):
    try:
        summary = datastore.summary
        capacity = summary.capacity
        freeSpace = summary.freeSpace
        uncommittedSpace = summary.uncommitted
        UsedSpacePercentage = (float(capacity-freeSpace) / capacity) * 100
        # print(HostName)
       
       # print("##################################################")
       # print("Datastore name: ", summary.name)
       # print("Capacity: ", humanize.naturalsize(capacity, binary=True))
        if uncommittedSpace is not None:
            provisionedSpace = (capacity - freeSpace) + uncommittedSpace
            # print("Provisioned space: ", humanize.naturalsize(provisionedSpace,
            #                                                   binary=True))
       # print("Free space: ", humanize.naturalsize(freeSpace, binary=True))
       # print("Used space percentage: " + str(UsedSpacePercentage) + "%")
       # print("##################################################")
        Record.update({"Used space percentage": round(UsedSpacePercentage,2)})
        #Records[HostName].update({summary.name : {"Capacity": humanize.naturalsize(capacity, binary=True),
       # "Provisioned space": humanize.naturalsize(provisionedSpace, binary=True),
       # "Free space": humanize.naturalsize(freeSpace, binary=True),
       # "Used space percentage": str(int(UsedSpacePercentage))+ "%"}})
    except Exception as error:
        print("Unable to access summary for datastore: ", datastore.name)
        print(error)
        pass


def printVmInformation(virtual_machine, depth=1):
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
        Records.update({'VMs':{virtual_machine.name :{
                                    'Power State' : summary.runtime.powerState
        }}})
        nic_count = 0
        for nic in virtual_machine.guest.net:
            nicName = 'Nic' + str(nic_count+1)
            ipAddress = list(nic.ipAddress)
            macAddress = nic.macAddress
            Nics = {nicName:{'IP Address':ipAddress, 'MAC Address': macAddress}}
            Records['VMs'][virtual_machine.name ].update({
                                    'vNICs': Nics
        })
        #pprint.pprint(Records)
    except Exception as error:
        print("Unable to access summary for VM: ", virtual_machine.name)
        print(virtual_machine.guest.net)
        print(error)
        exit()
        #pass

def VMware():
    try:
        si = SmartConnect(host="10.124.130.5", user="administrator@vsphere.local", pwd="Password@123", port=443)
        atexit.register(Disconnect, si)

        content = si.RetrieveContent()
    except vim.fault.InvalidLogin:
        raise Exception("Invalid username or password.")
        
    for datacenter in content.rootFolder.childEntity:
        if printHost:
            if hasattr(datacenter.hostFolder, 'childEntity'):
                teamsFolder = datacenter.hostFolder.childEntity
                for team in teamsFolder:
                    Records.update({team.name:{}})
                    if hasattr(team, 'childEntity'):
                        racks = team.childEntity
                        for rack in racks:
                            # Records[team.name].update({rack.name:{}})
                            if hasattr(rack, 'childEntity'):
                                computeResourceList = rack.childEntity
                                for computeResource in computeResourceList:
                                    Records[team.name].update({computeResource.name:{}})
                                    printComputeResourceInformation(computeResource, Records[team.name][computeResource.name])
                                    if printDatastore:
                                        datastores = computeResource.datastore
                                        for ds in datastores:
                                            printDatastoreInformation(ds, Records[team.name][computeResource.name])
                                    
        
        if hasattr(datacenter.vmFolder, 'childEntity'):
            vmFolder = datacenter.vmFolder
            vmList = vmFolder.childEntity
            Records.update({'Total Number of VMs in vCenter':len(vmList) })
            if printVM:
                for vm in vmList:
                    printVmInformation(vm)
    pprint.pprint(Records)
    
    return Records

if __name__ == "__main__":
    Record1 = VMware()
    print(Record1)