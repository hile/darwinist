"""
Parse and list network interfaces on the system
"""

import re
from subprocess import Popen, PIPE
from seine.address import EthernetMACAddress, IPv4Address, IPv6Address

RE_INET_LINE = [
    re.compile('^\s+inet\s+(?P<address>[0-9.]+)\s+netmask\s+(?P<netmask>[.x0-9a-f]+)$'),
    re.compile('^\s+inet\s+(?P<address>[0-9.]+)\s+netmask\s+(?P<netmask>[.x0-9a-f]+)\s+broadcast\s+(?P<broadcast>[0-9.]+)$'), # noqa
]
RE_INET6_LINE = [
    re.compile('^\s+inet6\s+(?P<address>[0-9:a-f]+)\s+prefixlen\s+(?P<prefix>\d+)$'),
    re.compile('^\s+inet6\s+(?P<address>[0-9:a-f]+)%(?P<scope>[^s]+)\s+prefixlen\s+(?P<prefix>\d+)\s+scopeid\s+(?P<scope_id>[x0-9a-f]+)$'), # noqa
]


class NetworkInterfaces(list):
    def __init__(self):
        p = Popen(['/sbin/ifconfig'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()

        interface = None
        for line in [x.rstrip() for x in stdout.split('\n')]:
            if line.strip() == '':
                continue

            if line.startswith('	'):
                interface.parse(line)

            else:
                name, flags = line.split(':', 1)
                if interface:
                    self.append(interface)
                interface = Interface(name, flags)


class Interface(dict):
    def __init__(self, name, flags=''):
        self.name = name
        self.flags = flags
        self['addresses'] = []

    def parse(self, line):
        """
        Parse a configuration line for interface
        """

        for inet_re in RE_INET_LINE:
            m = inet_re.match(line)
            if m:
                data = m.groupdict()
                data['addr_type'] = 'IPv4'
                data['address'] = IPv4Address(data['address'])
                data['netmask'] = IPv4Address(data['netmask'])
                if 'broadcast' in data:
                    data['broadcast'] = IPv4Address(data['broadcast'])
                else:
                    data['broadcast'] = None

                self['addresses'].append(data)
                return

        for inet6_re in RE_INET6_LINE:
            m = inet6_re.match(line)
            if m:
                data = m.groupdict()
                data['addr_type'] = 'IPv6'
                data['address'] = IPv6Address(data['address'])
                if 'prefix' in data:
                    data['prefix'] = int(data['prefix'])

                self['addresses'].append(data)
                return

        try:
            key, value = line.strip().split(None, 1)
            if key == 'ether':
                value = EthernetMACAddress(value)

        except ValueError:
            try:
                key, value = line.strip().split('=', 1)
            except ValueError:
                raise ValueError('Error splitting line {0}'.format(line))

        self[key] = value
