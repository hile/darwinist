#!/usr/bin/env python
"""
Classes to handle AFP mountpoints, mounting and configuring them.
"""

import os
import re

from configobj import ConfigObj
from subprocess import call, CalledProcessError

re_mountpoint = re.compile(r'^/Volumes/[A-Za-z0-9_-]*$')

DEFAULT_CONFIG_PATH = os.path.join(os.getenv('HOME'), '.afpshares.conf')

class AFPShareError(Exception):
    """
    Exceptions raised when accessing AFP shares
    """
    def __str__(self):
        return self.args[0]

class AFPShareConfig(dict):
    """
    Reader for AFP share configuration files.
    """
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        dict.__init__(self)
        self.config = None
        self.path = config_path
        if not os.path.isfile(self.path):
            raise AFPShareError('No such file: %s' % self.path)
        if not os.access(self.path, os.R_OK):
            raise AFPShareError(
                'No permission to read configuration: %s' % self.path
            )

        self.config = ConfigObj(self.path)
        if self.config.has_key('Options'):
            self.options = dict(self.config['Options'])
        else:
            self.options = {}
        for k in filter(lambda k: k!='Options', self.config.keys()):
            try:
                self[k] = AFPShareDisk(k, self.config[k])
            except AFPShareError, e:
                print e
                continue

    def __getattr__(self, attr):
        if attr == 'disks':
            return self.values()
        try:
            return self.options[attr]
        except KeyError:
            pass
        raise AttributeError('No such AFPShareConfig attribute: %s' % attr)

    def __getitem__(self, item):
        try:
            return self[item]
        except KeyError:
            pass
        raise KeyError('No such AFP share: %s' % item)

class AFPShareDisk(dict):
    """
    AFP network share disk specification
    """
    def __init__(self, name, settings):
        dict.__init__(self)
        self.name = name
        self.update(**{
            'address': None,
            'path':None,
            'mountpoint':None,
            'username': None,
            'password': None,
        })

        for k, v in settings.items():
            if not self.has_key(k):
                raise AFPShareError('Unsupported disk option: %s' % k)
            self[k] = v
        for k in ['address', 'path', 'mountpoint']:
            if self[k] is None:
                raise AFPShareError('Missing required option %s' % k)

        if self.has_key('username') and not self.has_key('password'):
            raise AFPShareError('Username defined but no password given')

        if self.has_key('password') and not self.has_key('username'):
            raise AFPShareError('Password defined but no username given')

        if not re.match(re_mountpoint, self.mountpoint):
            raise AFPShareError(
                'Unsupported mountpoint path: %s' % self.mountpoint
            )

    def __getattr__(self, attr):
        if attr == 'afp_path_nopass':
            #noinspection PyStringFormat
            return 'afp://%(address)s%(path)s' % self
        if attr == 'afp_path':
            if self.username is not None:
                #noinspection PyStringFormat
                return 'afp://%(username)s:%(password)s@%(address)s%(path)s' % self
            #noinspection PyStringFormat
            return 'afp://%(address)s%(path)s' % self
        try:
            return self[attr]
        except KeyError:
            pass
        raise AttributeError('No such %s attr: %s' % (self.name, attr))

    def __str__(self):
        return '%s: %s mounted on %s' % (
            self.name,  self.afp_path_nopass, self.mountpoint
        )

    def status(self):
        """
        Return status of mountpoint as string:
        'not mounted', 'mounted by other user', 'mounted by myself'
        """
        if not os.path.ismount(self.mountpoint):
            return 'not mounted'
        if not os.access(self.mountpoint, os.W_OK):
            return 'mounted by other user'
        else:
            return 'mounted by myself'

    def mount(self):
        """
        Mount the AFP share
        """
        if os.path.ismount(self.mountpoint):
            raise AFPShareError('Already mounted: %s' % self.mountpoint)

        if not os.path.isdir(self.mountpoint):
            try:
                os.makedirs(self.mountpoint)
                if os.stat(self.mountpoint).st_uid != os.getuid():
                    os.chown(self.mountpoint, os.getpid(), os.getgid())
            except IOError, (ecode, emsg):
                raise AFPShareError(emsg)
            except OSError, (ecode, emsg):
                raise AFPShareError(emsg)

        try:
            call(['mount_afp', self.afp_path, self.mountpoint])
        except CalledProcessError, emsg:
            raise AFPShareError(emsg)

    def umount(self):
        """
        Umount the AFP share
        """
        if not os.path.ismount(self.mountpoint):
            return
        if not os.access(self.mountpoint, os.W_OK):
            raise AFPShareError('No write access to %s' % self.mountpoint)
        try:
            call(['hdiutil', 'detach', self.mountpoint])
        except CalledProcessError, emsg:
            raise AFPShareError(emsg)

