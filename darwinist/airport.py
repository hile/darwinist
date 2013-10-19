#!/usr/bin/env python
"""
Module for Apple OS/X airport status command access from python
"""
import os
from subprocess import check_output, CalledProcessError

AIRPORT_BINARY = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'

class AirportError(Exception):
    """
    Exception raised by errors processing AirPort status
    """
    def __str__(self):
        return self.args[0]

class AirportStatus(dict):
    """
    Class to call the system 'airport' command.
    """
    def __init__(self):
        if not os.path.isfile(AIRPORT_BINARY):
            raise AirportError('No such command: %s' % AIRPORT_BINARY)

    def __repr__(self):
        self.probe()
        return '%(BSSID)s %(SSID)s channel %(channel)s %(agrCtlRSSI)s dB' % self

    def __getattr__(self, attr):
        try:
            if not self.keys():
                self.probe()
            return self[attr]

        except KeyError:
            raise AttributeError('No such AirportStatus attribute: %s' % attr)

    def probe(self):
        """
        Probe airport status
        """
        self.clear()
        try:
            data = check_output([AIRPORT_BINARY, '-I'])
        except CalledProcessError, emsg:
            print emsg
            return

        for l in data.split('\n'):
            if l.strip() == '':
                continue

            try:
                (key, value) = map(lambda x: x.strip(),  l.split(':', 1))
                self[key] = value
            except ValueError:
                raise AirportError('Error parsing line: %s' % l)

        for k in ['BSSID']:
            if not self.has_key(k):
                continue

            self[k] = ':'.join(['%02x'.upper() % int(x, 16) for x in self[k].split(':')])

    def proximity(self):
        """
        Return proximity of base stations based on signal levels
        """
        headers = ['SSID', 'BSSID', 'RSSI', 'CHANNEL', 'HT', 'CC', 'SECURITY']
        aps = []

        try:
            data = check_output([AIRPORT_BINARY, '-s', self.SSID])
        except CalledProcessError, emsg:
            print emsg
            return

        for l in data.split('\n'):
            if l.strip() == '':
                continue
            l = l.rstrip()
            if headers[:5] == [x.strip() for x in l.split()][:5]:
                continue

            ssid =  l[:32].lstrip()
            bssid = l[33:50].strip("'").upper()
            rssi =  int(l[51:55].strip())
            channel = int(l[56:58].strip())
            aps.append({
                'SSID': ssid, 'BSSID': bssid, 'RSSI': rssi, 'CHANNEL': channel
            })

        aps.sort(lambda x,y: cmp(y['RSSI'], x['RSSI']))
        return aps

