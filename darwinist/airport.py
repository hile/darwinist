"""
Module for Apple OS/X airport status command access from python
"""

from operator import itemgetter
import os
from subprocess import check_output, CalledProcessError

AIRPORT_BINARY = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'


class AirportError(Exception):
    pass


class AirportStatus(dict):
    """
    Class to call the system 'airport' command.
    """
    def __init__(self):
        if not os.path.isfile(AIRPORT_BINARY):
            raise AirportError('No such command: {0}'.format(AIRPORT_BINARY))

    def __repr__(self):
        self.probe()
        return '%(BSSID)s %(SSID)s channel %(channel)s %(agrCtlRSSI)s dB' % self

    def __getattr__(self, attr):
        try:
            if not self.keys():
                self.probe()
            return self[attr]

        except KeyError:
            raise AttributeError('No such AirportStatus attribute: {0}'.format(attr))

    def probe(self):
        """
        Probe airport status
        """
        self.clear()

        cmd = (AIRPORT_BINARY, '-I')
        try:
            data = check_output(cmd)
        except CalledProcessError as e:
            raise AirportError('Error running {0}: {1}'.format(' '.join(cmd), e))

        for line in [line.decode('utf-8') for line in data.splitlines()]:
            if not line.strip():
                continue

            try:
                key, value = [x.strip() for x in line.split(':', 1)]
                self[key] = value
            except ValueError:
                raise AirportError('Error parsing line: {0}'.format(line))

        for key in ('BSSID',):
            if key not in self:
                continue
            self[key] = ':'.join(['%02x'.upper() % int(x, 16) for x in self[key].split(':')])

    def proximity(self):
        """
        Return proximity of base stations based on signal levels
        """
        headers = ('SSID', 'BSSID', 'RSSI', 'CHANNEL', 'HT', 'CC', 'SECURITY')
        aps = []

        cmd = (AIRPORT_BINARY, '-s', self.SSID)
        try:
            data = check_output(cmd)
        except CalledProcessError as e:
            raise AirportError('Error running {0}: {1}'.format(' '.join(cmd), e))
            return

        for line in [line.decode('utf-8') for line in data.splitlines()]:
            if not line.strip():
                continue

            line = line.rstrip()
            if headers[:5] == [x.strip() for x in line.split()][:5]:
                continue

            ssid = line[:32].lstrip()
            bssid = line[33:50].strip("'").upper()
            rssi = int(line[51:55].strip())
            channel = int(line[56:58].strip())
            aps.append({
                'SSID': ssid,
                'BSSID': bssid,
                'RSSI': rssi,
                'CHANNEL': channel,
            })

        aps.sort(key=itemgetter('RSSI'))
        return aps
