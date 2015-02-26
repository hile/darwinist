"""
Module to parse OS/X process listing from ps command output
"""

import os
import decimal
from subprocess import Popen, PIPE

PS_COMMAND = ['ps', 'auxwww']
PS_FIELDS = [
    'username',
    'pid',
    'cpu_pct',
    'mem_pct',
    'vsz',
    'rss',
    'tty',
    'stat',
    'started',
    'time',
    'command'
]

class ProcessList(list):
    """
    List of processes based on ps output
    """
    def __init__(self, command=PS_COMMAND, fields=PS_FIELDS):
        self.command = command
        self.fields = fields
        self.update()

    def update(self):
        """
        Update list of processes
        """
        list.__delslice__(self, 0, len(self))
        cmd = self.command
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        for l in stdout.split('\n')[1:]:
            if l.strip()=='': continue
            self.append(Process(l, fields=self.fields))

    def sort_by_field(self, field, reverse=False):
        """
        Sort processes in-list by given field.
        If reverse is True, the in-line ordering is reversed after
        sorting.
        """
        self.sort(lambda x, y: cmp(x[field], y[field]))
        if reverse:
            self.reverse()

    def filter_user(self, username):
        """
        Filter processes to matching username
        """
        return filter(lambda p: p.username==username, self)

    def filter_command(self, command):
        """
        Filter processes to matching command name: the command name
        is first space separate part from 'command' column and thus
        this doesn't work for matching commands with spaces.
        """
        return filter(lambda p:
            p.command is not None and \
            os.path.basename(p.command.split(None, 1)[0]) == command,
            self
        )

    def find_pid(self, pid):
        try:
            pid = int(pid)
        except ValueError:
            raise ValueError('Invalid PID: %s' % value)
        for process in self:
            if process['pid'] == pid:
                return process
        return None


class Process(dict):
    """
    Wrapper class for information for one process
    """
    def __init__(self,line,fields):
        rest = line
        for k in fields[:-1]:
            try:
                value,rest = [x.strip() for x in rest.split(None,1)]
            except ValueError:
                self[k] = rest
                break
            self[k] = value

        if rest.strip() != '':
            self[fields[-1]] = rest.lstrip()

        for k in fields:
            if not self.has_key(k):
                self[k] = None

        for k in ['pid', 'vsz', 'rss']:
            self[k] = int(self[k])

        for k in ['cpu_pct', 'mem_pct']:
            self[k] = decimal.Decimal(self[k])

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError('No such Process attribute: %s' % attr)
