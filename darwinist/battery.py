#!/usr/bin/env python
"""
Wrapper to get OS/X darwin laptop battery status from command line
"""

from darwinist.ioreg import IORegTree, IORegError

BATTERY_IGNORE_FIELDS = [
    'CellVoltage',
    'IOGeneralInterest',
    'LegacyBatteryInfo',
    'ManufacturerData',
]

BATTERY_FIELD_FORMATS = {
    'AdapterInfo': lambda x: int(x),
    'Amperage': lambda x: int(x),
    'AvgTimeToEmpty': lambda x: int(x),
    'AvgTimeToFull': lambda x: int(x),
    'BatteryInstalled': lambda x: x=='Yes' and True or False,
    'BatteryInvalidWakeSeconds': lambda x: int(x),
    'BatterySerialNumber': lambda x: str(x).strip('" '),
    'CurrentCapacity': lambda x: int(x),
    'CycleCount': lambda x: int(x),
    'DesignCapacity': lambda x: int(x),
    'DeviceName': lambda x: str(x).strip('" '),
    'ExternalChargeCapable': lambda x: x=='Yes' and True or False,
    'ExternalConnected': lambda x: x=='Yes' and True or False,
    'FirmwareSerialNumber': lambda x: int(x),
    'FullyCharged': lambda x: x=='Yes' and True or False,
    'InstantAmperage': lambda x: int(x),
    'InstantTimeToEmpty': lambda x: int(x),
    'IsCharging': lambda x: x=='Yes' and True or False,
    'Location': lambda x: int(x),
    'Manufacturer': lambda x: str(x).strip('" '),
    'MaxCapacity': lambda x: int(x),
    'MaxErr': lambda x: int(x),
    'PermanentFailureStatus': lambda x: int(x),
    'PostChargeWaitSeconds': lambda x: int(x),
    'PostDischargeWaitSeconds': lambda x: int(x),
    'Temperature': lambda x: float(x)/100,
    'TimeRemaining': lambda x: int(x),
    'Voltage': lambda x: float(x)/1000,
}

class Batteries(list):
    """
    All connected OS/X computer batteries based on ioreg data
    """
    def __init__(self):
        list.__init__(self)
        ioreg_data = IORegTree('AppleSmartBattery')
        for ioreg_group in ioreg_data:
            self.append(Battery(ioreg_group))

class Battery(dict):
    def __init__(self, details={}):
        for k, v in details.items():
            if k in BATTERY_IGNORE_FIELDS:
                continue
            if k in BATTERY_FIELD_FORMATS.keys():
                self[k.lower()] = BATTERY_FIELD_FORMATS[k](v.value)
            else:
                self[k.lower()] = v.value

        if self.has_key('currentcapacity') and self.has_key('maxcapacity'):
            self['percent'] = int(
                round(float(self.currentcapacity)/self.maxcapacity*100)
            )
        else:
            self['percent'] = 'UNKNOWN'

    def __getattr__(self, attr):
        try:
            return self[attr.lower()]
        except KeyError:
            raise AttributeError('No such Battery attribute: %s' % attr)

    def keys(self):
        return sorted(dict.keys(self))

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        return [self[k] for k in self.keys()]

    def __repr__(self):
        if self.ischarging:
            prefix = 'CHARGING'
        elif self.fullycharged:
            prefix = 'FULL'
        else:
            prefix = 'DISCHARGING'
        return '%s %s %d%% %d/%d mAh %d cycles' % (
            self.devicename,
            prefix,
            self.percent,
            self.currentcapacity,
            self.maxcapacity,
            self.cyclecount,
        )
