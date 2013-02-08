#!/usr/bin/env python
"""
Parse and list network interfaces on the system
"""

from subprocess import Popen,PIPE

from seine.address import EthernetMACAddress,IPv4Address,IPv6Address
from systematic.log import Logger,LoggerError

class NetworkInterfaces(list):
    def __init__(self):
        self.log = Logger('interfaces').default_stream
        p = Popen(['/sbin/ifconfig'],stdin=PIPE,stdout=PIPE,stderr=PIPE)
        (stdout,stderr) = p.communicate()

        interface = None
        for l in stdout.split('\n'):
            if l.strip()=='':
                continue
            if not l.startswith('	'):
                name,flags = l.split(':',1)
                if interface:
                    self.append(interface)
                interface = Interface(name,flags)
                continue
            interface.parse(l)
            continue
            print l

class Interface(dict):
    def __init__(self,name,flags=''):
        self.log = Logger('interfaces').default_stream
        self.name = name
        self.flags = flags
        self.addresses = []
        print self.name

    def parse(self,line):
        try:
            key,value = line.strip().split(None,1)
            if key=='ether':
                value = EthernetMACAddress(value)
            if key=='inet':
                (ip,l1,netmask,l2,broadcast) = value.split()
                self.addresses.append({
                    'addr_type': 'IPv4',
                    'address': IPv4Address(ip),
                    'netmask': IPv4Address(netmask),
                    'broadcast': IPv4Address(broadcast)
                })
                return

        except ValueError:
            try:
                key,value = line.strip().split('=',1)
            except ValueError:
                print 'Error splitting line %s' % line
        self[key] = value
