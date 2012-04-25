"""
Wrapper for OS/X diskutil command for python
"""

import os,plistlib,StringIO
from xml.parsers.expat import ExpatError

from subprocess import Popen,PIPE

class DiskUtilError(Exception):
    def __str__(self):
        return self.args[0]

class DiskInfo(dict):
    def __init__(self,device):
        if not os.access(device,os.R_OK):
            raise DiskUtilError('Device not readable: %s' % device)

        cmd = ['diskutil','info','-plist',device]
        p = Popen(cmd,stdin=PIPE,stdout=PIPE,stderr=PIPE)
        (stdout,stderr) = p.communicate()
        try:
            plist = StringIO.StringIO(stdout)
            self.update(plistlib.readPlist(plist))
        except ExpatError,emsg:
            raise DiskUtilError('Error parsing plist: %s' % stdout)

    def keys(self):
        """
        Return keys as sorted list
        """
        return sorted(dict.keys(self))

    def items(self):
        """
        Return (key,value) sorted by key
        """
        return [(k,self[k]) for k in self.keys()]

    def values(self):
        """
        Return values sorted by key
        """
        return [self[k] for k in self.keys()]

if __name__ == '__main__':
    import sys
    for dev in sys.argv[1:]:
        for k,v in DiskInfo(dev).items():
            print '%-32s %s' % (k,v)
            
