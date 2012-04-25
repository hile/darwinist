#!/usr/bin/env python
"""
Abstraction of filesystem mount points for OS/X
"""
import os,re
from subprocess import check_output,CalledProcessError
from mactypes import Alias

from systematic.filesystems import MountPoint,FileSystemError
from darwinist.diskutil import DiskInfo,DiskUtilError

re_mountpoint = re.compile(r'([^\s]*) on (.*) \(([^\)]*)\)$')
re_df = re.compile(r'^([^\s]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(.*)$')

class MountPoints(dict):
    """
    OS/X mount points parser
    """
    def __init__(self):
        dict.__init__(self)
        self.update()

    def update(self):
        """
        Update mount points from /sbin/mount output
        """
        self.clear()
        try:
            output = check_output(['/sbin/mount'])
        except CalledProcessError,e:
            raise FileSystemError('Error getting mountpoints: %s' % e)

        for l in output.split('\n'):
            if l == '': 
                continue
            if l[:4] == 'map ': 
                continue
            m = re_mountpoint.match(l)
            if not m:
                continue
            device = m.group(1)
            mountpoint = m.group(2)
            flags = map(lambda x: x.strip(), m.group(3).split(','))
            filesystem = flags[0]
            flags = flags[1:]
            entry = OSXMountPoint(mountpoint,device,filesystem)
            for f in flags:
                if f[:11] == 'mounted by ':
                    v = f[11:]
                    f = 'owner'
                    entry.flags.set(f,v)
                else:
                    entry.flags.set(f,True)
            self[entry.path] = entry

class OSXMountPoint(MountPoint):
    """
    One OS/X mountpoint parsed from /sbin/mount output

    Extra attributes:
    hfspath     Returns OS/X 'hfs path', if available, or None
    """
    def __init__(self,mountpoint,device=None,filesystem=None):
        MountPoint.__init__(self,device,mountpoint,filesystem)
        try:
            self.hfspath = Alias(self.mountpoint).hfspath
        except ValueError:  
            self.hfspath = None
        self.update_diskinfo()

    def update_diskinfo(self):
        if os.access(self.device,os.R_OK):
            self.diskinfo = DiskInfo(self.device)
        else:
            self.diskinfo = {} 

    def __getattr__(self,attr):
        if attr == 'name':
            if self.diskinfo.has_key('VolumeName'):
                return self.diskinfo['VolumeName']
            # No return: fallback to name parsed from mountpoint
        if attr in ['writable']:
            if self.diskinfo.has_key('Writable'):
                return self.diskinfo['Writable']
            return False
        if attr in ['bootable']:
            if self.diskinfo.has_key('Bootable'):
                return self.diskinfo['Bootable']
            return False
        if attr in ['internal']:
            if self.diskinfo.has_key('Internal'):
                return self.diskinfo['Internal']
            return True
        if attr in ['ejectable','removable']:
            if self.diskinfo.has_key('Ejectable'):
                return self.diskinfo['Ejectable']
            return False
        if attr in ['bs','blocksize']:
            if self.diskinfo.has_key('DeviceBlockSize'):
                return int(self.diskinfo['DeviceBlockSize'])
            return 0 
        return MountPoint.__getattr__(self,attr)

    def checkusage(self):
        """
        Check usage percentage for this mountpoint.
        Returns dictionary with usage details.
        """
        try:
            output = check_output(['df','-k',self.mountpoint])
        except CalledProcessError,e:
            raise FileSystemError('Error checking filesystem usage: %s' % e)

        (header,usage) = output.split('\n',1)
        m = re_df.match(usage)
        if not m:
            raise FileSystemError('Error matching line %s' % usage)
        size = m.group(2)
        used = m.group(3)
        free = m.group(4)
        percent = m.group(5)

        return {
            'mountpoint': self.mountpoint,
            'size': long(size),'used': long(used), 
            'free': long(free),'percent': int(percent)
        }

