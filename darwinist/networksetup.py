"""
Wrapper to call the networksetup command line script.
"""

import os
import re
from subprocess import check_output, CalledProcessError
from seine.address import IPv4Address, EthernetMACAddress

CMD = '/usr/sbin/networksetup'

RE_ETHERNET_ADDRESS = re.compile(
    'Ethernet Address: (?P<mac>.*) \(Hardware Port: (?P<port>[^/)]+)\)$'
)


class NetworkSetupError(Exception):
    """
    Exceptions raised while parsing OS/X network setup
    """
    pass


class NetworkSetup(object):
    """
    Wrapper for OS/X 'networksetup' command line tool
    """
    def __init__(self):
        if not os.path.isfile(CMD):
            raise NetworkSetupError('No such file: {0}'.format(CMD))
        if not os.access(CMD, os.X_OK):
            raise NetworkSetupError('No permission to execute: {0}'.format(CMD))

        self.network_services = []
        for line in check_output(('networksetup', '-listallnetworkservices')).splitlines():
            line = line.decode('utf-8')
            if line != '':
                self.network_services.append(NetworkService(line))

    def __getattr__(self, attr):
        raise AttributeError('No such NetworkSetup attribute: {0}'.format(attr))


class NetworkService(object):
    """
    One specific network service parsed from 'networksetup' output
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __parse_info(self):
        """
        Parser for the device details (called when attributes are requested)
        """
        details = {}
        try:
            out = filter(lambda x: x != '', check_output(
                ['networksetup', '-getinfo', self.name]
            ).splitlines())
        except CalledProcessError:
            return details

        for line in out:
            if line == 'Manual Configuration':
                details['ipv4_mode'] = 'manual'
                continue

            if line == 'DHCP Configuration':
                details['ipv4_mode'] = 'dhcp'
                continue

            try:
                key, value = [x.strip() for x in line.split(':', 1)]
            except ValueError:
                raise ValueError('Error parsing line: {0}'.format(line))

            if value == 'none':
                value = None

            if key in ['Subnet mask', 'IP address', 'Router']:
                value = IPv4Address(value)

            if key == 'Ethernet Address':
                value = EthernetMACAddress(value)

            details[key] = value

        return details

    def __parse_mac_address(self):
        """
        Parser for device MAC address
        """
        try:
            out = check_output(
                ['networksetup', '-getmacaddress', self.name]
            ).strip('\n')
        except CalledProcessError:
            return None
        m = RE_ETHERNET_ADDRESS.match(out)
        if not m:
            return None
        mac = m.groupdict()['mac']
        if mac == '(null)':
            return None
        return mac

    @property
    def configuration(self):
        return self.__parse_info()

    @property
    def mac_address(self):
        return self.__parse_mac_address()

    def set_mode(self, mode, client_id=None, ipaddress=None, netmask=None, router=None):
        """
        Set interface mode to given value. Each mode has it's specific allowed flags,
        see OS/X documentation or source code of this module.

        Mode can be: dhcp, manual or bootp
        """
        if mode not in ['dhcp', 'manual', 'bootp']:
            raise ValueError('Invalid IPv4 configuratio mode')

        if mode == 'bootp':
            try:
                check_output(['networksetup', '-setbootp', self.name])
            except CalledProcessError:
                raise NetworkSetupError('Error setting {0} to BOOTP mode'.format(self.name))

        elif mode == 'dhcp':
            cmd = ['networksetup', '-setdhcp', self.name]
            if client_id is not None:
                cmd.append(client_id)
            try:
                check_output(cmd)
            except CalledProcessError:
                raise NetworkSetupError('Error setting {0} to DHCP mode'.format(self.name))

        elif mode == 'manual':
            if ipaddress is None:
                raise NetworkSetupError('Manual mode requires valid ipaddress')
            else:
                try:
                    ipaddress = IPv4Address(ipaddress)
                except ValueError:
                    raise NetworkSetupError('Invalid IPv4 Address: {0}'.format(ipaddress))

            if netmask is None:
                raise NetworkSetupError('Manual mode requires valid netmask')
            else:
                try:
                    netmask = IPv4Address(netmask)
                except ValueError:
                    raise NetworkSetupError('Invalid IPv4 netmask: {0}'.format(netmask))

            if router is None:
                raise NetworkSetupError('Manual mode requires valid router')
            else:
                try:
                    router = IPv4Address(router)
                except ValueError:
                    raise NetworkSetupError('Invalid IPv4 Address: {0}'.format(router))

            cmd = [
                'networksetup',
                '-setmanual', self.name,
                ipaddress.ipaddress,
                netmask.ipaddress,
                router.ipaddress
            ]

            try:
                return check_output(cmd)
            except CalledProcessError:
                raise NetworkSetupError('Error setting {0} to manual mode'.format(self.name))
