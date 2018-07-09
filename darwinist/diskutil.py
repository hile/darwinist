"""
Wrapper for OS/X diskutil command for python
"""

import os
import plistlib
from xml.parsers.expat import ExpatError
from subprocess import Popen, PIPE

from io import BytesIO

INFO_FIELD_MAP = {
    'DeviceNode':       {'name': 'Device', 'value': lambda x: str(x)},
    'FilesystemName':   {'name': 'Filesystem', 'value': lambda x: str(x)},
    'UsedSpace':        {'name': 'Used', 'value': lambda x: x/1024},
    'UsedPercent':      {'name': 'Percent', 'value': lambda x: x/1024},
    'FreeSpace':        {'name': 'Free', 'value': lambda x: x/1024},
    'TotalSize':        {'name': 'Sizd', 'value': lambda x: x/1024},
    'VolumeName':       {'name': 'Volume Name', 'value': lambda x: str(x)},
    'VolumeUUID':       {'name': 'UUID', 'value': lambda x: str(x)},
}
INFO_FIELD_ORDER = [
    'DeviceNode',
    'VolumeName',
    'FilesystemName',
    'VolumeUUID',
    'UsedSpace',
    'FreeSpace',
    'TotalSize'
]


class DiskUtilError(Exception):
    pass


class DiskInfo(dict):
    def __init__(self, device):
        if not os.access(device, os.R_OK):
            raise DiskUtilError('Device not readable: {0}'.format(device))

        cmd = ('diskutil', 'info', '-plist', device)
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        try:
            plist = BytesIO(stdout)
            self.update(plistlib.readPlist(plist))
        except ExpatError:
            raise DiskUtilError('Error parsing plist: {0}'.format(stdout))

        if 'TotalSize' in self and 'FreeSpace' in self:
            self['UsedSpace'] = self.TotalSize - self.FreeSpace
            self['UsedPercent'] = int(round(1-(float(self.FreeSpace) / float(self.TotalSize))))

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError

    def keys(self):
        """
        Return keys as sorted list
        """
        return sorted(super(DiskInfo, self).keys())

    def items(self):
        """
        Return (key, value) sorted by key
        """
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        """
        Return values sorted by key
        """
        return [self[k] for k in self.keys()]
