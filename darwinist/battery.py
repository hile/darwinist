"""
Wrapper to get OS/X darwin laptop battery status from command line
"""

from darwinist.ioreg import IORegTree

BATTERY_IGNORE_FIELDS = (
    'CellVoltage',
    'IOGeneralInterest',
    'LegacyBatteryInfo',
    'ManufacturerData',
)

BATTERY_FIELD_FORMATS = {
    'AdapterInfo': lambda x: int(x),
    'Amperage': lambda x: int(x),
    'AvgTimeToEmpty': lambda x: int(x),
    'AvgTimeToFull': lambda x: int(x),
    'BatteryInstalled': lambda x: x == 'Yes' and True or False,
    'BatteryInvalidWakeSeconds': lambda x: int(x),
    'BatterySerialNumber': lambda x: str(x).strip('" '),
    'CurrentCapacity': lambda x: int(x),
    'CycleCount': lambda x: int(x),
    'DesignCapacity': lambda x: int(x),
    'DeviceName': lambda x: str(x).strip('" '),
    'ExternalChargeCapable': lambda x: x == 'Yes' and True or False,
    'ExternalConnected': lambda x: x == 'Yes' and True or False,
    'FirmwareSerialNumber': lambda x: int(x),
    'FullyCharged': lambda x: x == 'Yes' and True or False,
    'InstantAmperage': lambda x: int(x),
    'InstantTimeToEmpty': lambda x: int(x),
    'IsCharging': lambda x: x == 'Yes' and True or False,
    'Location': lambda x: int(x),
    'Manufacturer': lambda x: str(x).strip('" '),
    'MaxCapacity': lambda x: int(x),
    'MaxErr': lambda x: int(x),
    'PermanentFailureStatus': lambda x: int(x),
    'PostChargeWaitSeconds': lambda x: int(x),
    'PostDischargeWaitSeconds': lambda x: int(x),
    'Temperature': lambda x: float(x) / 100,
    'TimeRemaining': lambda x: int(x),
    'Voltage': lambda x: float(x) / 1000,
}


class Batteries(list):
    """
    All connected OS/X computer batteries based on ioreg data
    """
    def __init__(self):
        ioreg_data = IORegTree('AppleSmartBattery')
        for ioreg_group in ioreg_data:
            self.append(Battery(ioreg_group))


class Battery(dict):
    """Battery details

    """
    def __init__(self, details=None):
        if details:
            for key, value in details.items():
                if key in BATTERY_IGNORE_FIELDS:
                    continue

                if key.lower() == 'manufacturedate':
                    self[key.lower()] = self.__calculate_manufacture_date__(value.value)
                elif key in BATTERY_FIELD_FORMATS.keys():
                    self[key.lower()] = BATTERY_FIELD_FORMATS[key](value.value)
                else:
                    self[key.lower()] = value.value

        if 'currentcapacity' in self and 'maxcapacity' in self:
            self['percent'] = int(round(float(self.currentcapacity) / self.maxcapacity * 100))
        else:
            self['percent'] = 'UNKNOWN'

    def __calculate_manufacture_date__(self, value):
        """
        Based on battery controller datasheet
        http://www.ti.com/lit/er/sluu313a/sluu313a.pdf
        """
        value = int(value)
        year = (value >> 9) + 1980
        month = (value & 0b0000000111111111) >> 5
        day = value & 0b11111
        return '{}-{:02d}-{:02d}'.format(year, month, day)

    def __getattr__(self, attr):
        try:
            return self[attr.lower()]
        except KeyError:
            raise AttributeError('No such Battery attribute: {0}'.format(attr))

    def __repr__(self):
        if self.ischarging:
            prefix = 'CHARGING'
        elif self.fullycharged:
            prefix = 'FULL'
        else:
            prefix = 'DISCHARGING'
        return '{0} {1} {2:d}% {3:d}/{4:d} mAh {5:d} cycles'.format(
            self.devicename,
            prefix,
            self.percent,
            self.currentcapacity,
            self.maxcapacity,
            self.cyclecount,
        )

    def keys(self):
        return sorted(dict.keys(self))

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        return [self[k] for k in self.keys()]
