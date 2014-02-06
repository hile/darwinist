"""
Wrapper classes to store configuration file of dmg parameters and to attach
and detach the configured DMGs.
"""

import os
import sys

from subprocess import Popen, PIPE
from configobj import ConfigObj, Section

from systematic.shell import CONFIG_PATH
from darwinist.diskutil import DiskInfo, DiskUtilError

DEFAULT_CONFIG_PATH = os.path.join(CONFIG_PATH, 'diskimages.conf')
DEFAULT_VOLUMES = '/Volumes/'
VALID_CONFIG_ARGS = [ 'description', 'image', 'mountpoint', 'args' ]

class DiskImageError(Exception):
    pass

class DiskImagesConfig(dict):
    def __init__(self, path=DEFAULT_CONFIG_PATH):
        self.path = path
        if os.path.isfile(path):
            self.read()

    def read(self):
        config = ConfigObj(self.path)
        for name, options in config.items():
            if not isinstance(options, Section):
                continue
            diskimage_opts = {}
            for arg, value in options.items():
                if arg not in VALID_CONFIG_ARGS:
                    raise DiskImageError('Invalid option: %s' % arg)
            self[name] = DiskImage(self, name, **options)

    def keys(self):
        return sorted(dict.keys(self))

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        return [self[k] for k in self.keys()]

    def match(self, value):
        if value in self.keys():
            return self[value]

        for name, dmg in self.items():
            if dmg.image == value:
                return dmg

            if dmg.mountpoint == value:
                return dmg

        return None

class DiskImage(object):
    def __init__(self, config, name, image, mountpoint, args, description=None):
        self.config = config
        self.name = name
        self.image = image
        self.mountpoint = mountpoint
        self.description = description is not None and description or ''

        if not isinstance(args, list):
            args = [args]
        if not self.mountpoint[:len(DEFAULT_VOLUMES)] == DEFAULT_VOLUMES:
            args.extend(['-mountpoint', self.mountpoint])
        self.args = args

    def __repr__(self):
        return '%s mounted on %s (%s)' % (
            self.image, self.mountpoint, ' '.join(self.args)
        )

    def __getattr__(self, attr):
        if attr == 'connected':
            try:
                if self.info.has_key('MountPoint'):
                    return True
                return False
            except AttributeError:
                return False
        if attr == 'info':
            try:
                return DiskInfo(self.mountpoint)
            except DiskUtilError:
                return {}
        raise AttributeError('No such DiskImage attribute: %s' % attr)

    def detach(self):
        if not self.connected:
            raise DiskImageError('Not attached: %s' % self.mountpoint)

        cmd = ['hdiutil', 'detach', self.mountpoint]
        p = Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        p.wait()
        if p.returncode!=0:
            raise DiskImageError('Error detaching %s' % self.mountpoint)

    def attach(self, passphrase=None):
        if self.connected:
            raise DiskImageError('Already attached: %s' % self.mountpoint)

        cmd = ['hdiutil', 'attach']+self.args+[self.image]
        if passphrase is None:
            p = Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        else:
            p = Popen(cmd, stdin=PIPE, stdout=sys.stdout, stderr=sys.stderr)
            (stdout, stderr) = p.communicate(passphrase)
        p.wait()
        if p.returncode!=0:
            raise DiskImageError('Error attaching %s' % self.image)

