#!/usr/bin/env python
"""
Abstraction of filesystem mount points for OS/X
"""
import os
import re
from subprocess import check_output, CalledProcessError
from mactypes import Alias

from systematic.filesystems import MountPoint, FileSystemError
from darwinist.diskutil import DiskInfo, DiskUtilError

re_mountpoint = re.compile(r'([^\s]*) on (.*) \(([^\)]*)\)$')
re_df = re.compile(r'^([^\s]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(.*)$')

class MountPoints(dict):
    """
    OS/X mount points parser
    """
    def __init__(self):
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

        for l in [l for l in output.split('\n') if l.strip()!='']:
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
                    entry.flags.set('owner',f[11:])
                else:
                    entry.flags.set(f,True)
            self[entry.path] = entry
            

class OSXMountPoint(MountPoint):
    """
    One OS/X mountpoint parsed from /sbin/mount output

    Extra attributes:
    hfspath     Returns OS/X 'hfs path' or None
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

    @property
    def name(self):
        return self.diskinfo.has_key('VolumeName') and self.diskinfo['VolumeName'] or os.path.basename(self.mountpoint)

    @property
    def size(self):
        try:
            return self.usage['size']
        except KeyError:
            return 0

    @property
    def used(self):
        try:
            return self.usage['used']
        except KeyError:
            return 0

    @property
    def available(self):
        try:
            return self.usage['available']
        except KeyError:
            return 0

    @property
    def percent(self):
        try:
            return self.usage['percent']
        except KeyError:
            return 0

    @property
    def writable(self):
        return self.diskinfo.has_key('Writable') and  self.diskinfo['Writable'] or False

    @property
    def writable(self):
        return self.diskinfo.has_key('Writable') and  self.diskinfo['Writable'] or False

    @property
    def bootable(self):
        return self.diskinfo.has_key('Bootable') and  self.diskinfo['Bootable'] or False

    @property
    def internal(self):
        return self.diskinfo.has_key('Internal') and  self.diskinfo['Internal'] or False

    @property
    def ejectable(self):
        return self.diskinfo.has_key('Ejectable') and  self.diskinfo['Ejectable'] or True

    @property
    def removable(self):
        return self.diskinfo.has_key('Removable') and  self.diskinfo['Removable'] or False

    @property
    def blocksize(self):
        return self.diskinfo.has_key('DeviceBlockSize') and  self.diskinfo['DeviceBlockSize'] or 0

    @property
    def usage(self):
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
            raise FileSystemError('Error matching df output line: %s' % usage)
        return {
            'mountpoint': self.mountpoint,
            'size': long(m.group(2)),
            'used': long(m.group(3)),
            'free': long(m.group(4)),
            'percent': int(m.group(5))
        }

