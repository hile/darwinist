"""
Module to parse output from 'ioreg' command to python data structures
"""

import os
import re
from subprocess import Popen, PIPE

IOREG_COMMAND = '/usr/sbin/ioreg'

RE_IOREG_HEADER = re.compile('^\+-o\s(?P<name>.*)\s+<class (?P<ioclass>[\w]+),(?P<flags>[^>]*)')


class IORegError(Exception):
    """
    Execptions raised by ioreg command output parsers.
    """
    pass


class IORegItem(object):
    """
    One information item line from ioreg command output
    """
    def __init__(self, line):
        try:
            key, value = line.split('=', 1)
        except ValueError:
            try:
                key, value = line.split(':', 1)
            except ValueError:
                raise IORegError('Error splitting item line {0}'.format(line))

        self.key = key.rstrip().strip('"')
        self.value = value.strip()

    def __repr__(self):
        return '{0}: {1}'.format(self.key, self.value)


class IORegGroup(dict):
    """
    A group of items in ioreg command output
    """
    def __init__(self, parent, header):
        self.parent = parent
        self.name = 'UNPARSED'

        m = RE_IOREG_HEADER.match(header)
        if not m:
            raise IORegError('Error parsing ioreg group header: {0}'.format(header))

        for k, v in m.groupdict().items():
            setattr(self, k, v.strip())

    def __repr__(self):
        return 'IORegGroup {0}'.format(self.name)

    def append(self, line):
        """
        Add an IORegItem entry to this group
        """
        line = line.strip()
        if line in ['"', '']:
            return

        item = IORegItem(line)
        self[item.key] = item


class IORegTree(list):
    """
    Parser for ioreg output entries to a dictionary
    """
    def __init__(self, path=None):
        if not os.access(IOREG_COMMAND, os.X_OK):
            raise IORegError('Not executable: {0}'.format(IOREG_COMMAND))

        if path is not None:
            cmd = [IOREG_COMMAND, '-r', '-w0', '-n', path]
        else:
            cmd = [IOREG_COMMAND, '-lw0']

        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()

        parent = None
        group = None
        for line in [l.decode('utf-8').lstrip(' |').rstrip() for l in stdout.splitlines()]:
            if line in ['', '{']:
                continue

            elif line[:3] == '+-o':
                group = IORegGroup(parent, line)
                parent = group
                self.append(group)

            elif line == '}':
                group = None

            elif group is not None:
                group.append(line)
