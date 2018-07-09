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
    pass


class AFPShareConfig(dict):
    """
    Reader for AFP share configuration files.
    """

    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config = None
        self.path = config_path

        if not os.path.isfile(self.path):
            raise AFPShareError('No such file: {0}'.format(self.path))

        if not os.access(self.path, os.R_OK):
            raise AFPShareError('No permission to read configuration: {0}'.format(self.path))

        self.config = ConfigObj(self.path)
        if 'Options' in self.config:
            self.options = dict(self.config['Options'])
        else:
            self.options = {}

        for key in [key for key in self.conf if key != 'Options']:
            try:
                self[key] = AFPShareDisk(key, self.config[key])
            except AFPShareError as e:
                raise AFPShareError('Error parsing configuration: {0}'.format(e))

    def __getattr__(self, attr):
        if attr == 'disks':
            return self.values()
        try:
            return self.options[attr]
        except KeyError:
            pass
        raise AttributeError('No such AFPShareConfig attribute: {0}'.format(attr))

    def __getitem__(self, item):
        try:
            return self[item]
        except KeyError:
            pass
        raise KeyError('No such AFP share: {0}'.format(item))


class AFPShareDisk(dict):
    """
    AFP network share disk specification
    """
    def __init__(self, name, settings):
        self.name = name

        self.update(**{
            'address': None,
            'path': None,
            'mountpoint': None,
            'username': None,
            'password': None,
        })

        for key, value in settings.items():
            if key not in self:
                raise AFPShareError('Unsupported disk option: {0}'.format(key))
            self[key] = value

        for key in ('address', 'path', 'mountpoint'):
            if self[key] is None:
                raise AFPShareError('Missing required option {0}'.format(key))

        if 'username' in self and 'password' not in self:
            raise AFPShareError('Username defined but no password given')

        if 'password' in self and 'username' not in self:
            raise AFPShareError('Password defined but no username given')

        if not re.match(re_mountpoint, self.mountpoint):
            raise AFPShareError('Unsupported mountpoint path: {0}'.format(self.mountpoint))

    def __getattr__(self, attr):
        if attr == 'afp_path_nopass':
            return 'afp://%(address)s%(path)s' % self

        if attr == 'afp_path':
            if self.username is not None:
                return 'afp://%(username)s:%(password)s@%(address)s%(path)s' % self
            else:
                return 'afp://%(address)s%(path)s' % self

        try:
            return self[attr]
        except KeyError:
            pass

        raise AttributeError('No such {0} attr: {1}'.format(self.name, attr))

    def __str__(self):
        return '{0}: {1} mounted on {2}'.format(
            self.name,
            self.afp_path_nopass,
            self.mountpoint,
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
            raise AFPShareError('Already mounted: {0}'.format(self.mountpoint))

        if not os.path.isdir(self.mountpoint):
            try:
                os.makedirs(self.mountpoint)
                if os.stat(self.mountpoint).st_uid != os.getuid():
                    os.chown(self.mountpoint, os.getpid(), os.getgid())

            except IOError as e:
                raise AFPShareError(e)

            except OSError as e:
                raise AFPShareError(e)

        cmd = ('mount_afp', self.afp_path, self.mountpoint)
        try:
            call(cmd)
        except CalledProcessError as e:
            raise AFPShareError('Error running {0}: {1}'.format(' '.join(cmd), e))

    def umount(self):
        """
        Umount the AFP share
        """
        if not os.path.ismount(self.mountpoint):
            return

        if not os.access(self.mountpoint, os.W_OK):
            raise AFPShareError('No write access to {0}'.format(self.mountpoint))

        cmd = ('hdiutil', 'detach', self.mountpoint)
        try:
            call(cmd)
        except CalledProcessError as e:
            raise AFPShareError('Error running {0}: {1}'.format(' '.join(cmd), e))
