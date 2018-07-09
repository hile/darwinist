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
    pass


class VLAN(object):
    def __init__(self):
        for k in VLANLIST_LINE_MAP.keys():
            setattr(self, k, 'NOT SET')

    def __repr__(self):
        return '{0} TAG {1} PARENT {2}'.format(self.port, self.tag, self.parent)

    def create(self, name, parent, tag):
        cmd = ['networksetup', '-createVLAN', name, parent, str(tag)]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise VLANError('ERROR creating VLAN {0}'.format(tag))

        self.name = name
        self.parent = parent
        self.tag = tag

    def remove(self):
        cmd = ['networksetup', '-deleteVLAN', self.name, self.parent, str(self.tag)]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            raise VLANError('ERROR removing VLAN {0}'.format(self.tag))


class VLANList(list):
    def __init__(self):
        cmd = ['networksetup', '-listVLANs']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        stdout, stderr = p.communicate()
        lines = [line.decode('utf-8') for line in stdout.splitlines()]
        if lines[0] == NO_VLANS_MESSAGE:
            return

        entry = None
        for line in [line.rstrip() for line in lines]:
            if line == '':
                if entry is not None:
                    self.append(entry)
                entry = None

            for k, v in VLANLIST_LINE_MAP.items():
                if line[:len(v)] == v:
                    if entry is None:
                        entry = VLAN()
                    setattr(entry, k, line[len(v):].lstrip())
