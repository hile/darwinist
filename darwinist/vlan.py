#!/usr/bin/env python
"""
OS/X implementation of the systematic VLAN management API
"""

from subprocess import Popen, PIPE

NO_VLANS_MESSAGE = 'There are no VLANs currently configured on this system.'

VLANLIST_LINE_MAP = {
    'name': 'VLAN User Defined Name:',
    'parent': 'Parent Device:',
    'port': 'Device ("Hardware" Port):',
    'tag': 'Tag:',
}

class VLANError(Exception):
    def __str__(self):
        return self.args[0]

class VLAN(object):
    def __init__(self):
        for k in VLANLIST_LINE_MAP.keys():
            setattr(self, k, 'NOT SET')

    def __repr__(self):
        return '%s TAG %s PARENT %s' % (self.port, self.tag, self.parent)

    def create(self, name, parent, tag):
        cmd = ['networksetup', '-createVLAN', name, parent, str(tag)]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode!=0:
            print stdout
            raise VLANError('ERROR creating VLAN %s' % tag)

        self.name = name
        self.parent = parent
        self.tag = tag

    def remove(self):
        cmd = ['networksetup', '-deleteVLAN', self.name, self.parent, str(self.tag)]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode!=0:
            print stdout
            raise VLANError('ERROR removing VLAN %s' % self.tag)

class VLANList(list):
    def __init__(self):
        cmd = ['networksetup', '-listVLANs']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        lines = stdout.split('\n')
        if lines[0] == NO_VLANS_MESSAGE:
            return

        entry = None
        for l in [l.rstrip() for l in lines]:
            if l=='':
                if entry is not None:
                    self.append(entry)
                entry = None

            for k, v in VLANLIST_LINE_MAP.items():
                if l[:len(v)]==v:
                    if entry is None:
                        entry = VLAN()
                    setattr(entry, k, l[len(v):].lstrip())
