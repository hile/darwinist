"""
Timemachine control.

Wraps tmutil command for use from python
"""

import os
import re

from datetime import datetime
from subprocess import Popen, PIPE

TMUTIL = '/usr/bin/tmutil'
TMUTIL_VERSION_PATTERNS = (
    re.compile('^tmutil version (?P<version>[^ ]+) \(built (?P<builddate>[^)]+)\)$'),
)
TMUTIL_VERSION_DATE_PATTERNS = (
    '%b %d %Y',
)


class TimeMachineError(Exception):
    pass


class TmUtilVersion(dict):
    """Parser for tmutil version

    """
    def __init__(self, value):
        for pattern in TMUTIL_VERSION_PATTERNS:
            m = pattern.match(value)
            if m:
                self.update(m.groupdict())
                if 'builddate' in self:
                    for datefmt in TMUTIL_VERSION_DATE_PATTERNS:
                        try:
                            self['builddate'] = datetime.strptime(self['builddate'], datefmt)
                            break
                        except:  # noqa
                            pass
                    if not isinstance(self['builddate'], datetime):
                        raise TimeMachineError('Error parsing build date {0}'.format(self['builddate']))
                return

        raise TimeMachineError('Error parsing tmutil version from {0}'.format(value))


class TimeMachineDestination(dict):
    """Time machine destination

    """
    def __init__(self, data):
        for line in [line.decode('utf-8').rstrip() for line in data.splitlines() if not line.startswith('=')]:
            try:
                key, value = [x.strip() for x in line.split(':', 1)]
                self[key] = value
            except Exception as e:
                raise TimeMachineError('Error parsing destination info line {0}: {1}'.format(line, e))


class TimeMachineUtility(object):
    """Wrap tmutil cli

    Note: not all args are parsed yet.
    """

    def __init__(self):
        if not os.access(TMUTIL, os.X_OK):
            raise TimeMachineError('Not executable: {0}'.format(TMUTIL))

    def __run__(self, args):
        """Run tmutil command

        """
        if isinstance(args, str):
            args = [args]

        cmd = [TMUTIL] + args
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr

    @property
    def version(self):
        """Tmutil version

        """
        rv, stdout, stderr = self.__run__('version')
        return TmUtilVersion(stdout.strip())

    @property
    def destination(self):
        """Backup destination info

        """
        rv, stdout, stderr = self.__run__('destinationinfo')
        return TimeMachineDestination(stdout)

    def enable(self):
        """Enable backups

        Requires root
        """
        if os.geteuid() != 0:
            raise TimeMachineError('Error enabling timemachine backups: must be root')

        rv, stdout, stderr = self.__run__('enable')
        if rv != 0:
            raise TimeMachineError('Error enabling backups: {0}{1}'.format(
                ' '.join(stdout.rstrip(), stderr.rstrip()))
            )

    def disable(self):
        """Disable backups

        Requires root
        """
        if os.geteuid() != 0:
            raise TimeMachineError('Error disabling timemachine backups: must be root')

        rv, stdout, stderr = self.__run__('disable')
        if rv != 0:
            raise TimeMachineError('Error disabling backups: {0}{1}'.format(
                ' '.join(stdout.rstrip(), stderr.rstrip()))
            )
