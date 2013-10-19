#!/usr/bin/env python
"""
coreStorage status classes: just a wrapper to parse output from the
command line commands to dictionaries, grouping the hierarchy for
easy consumption.
"""

import re
from subprocess import check_output, CalledProcessError

re_header = re.compile('^CoreStorage logical volume groups \((\d+) found\)$')
re_lvg_header = re.compile('^Logical Volume Group ([A-Z0-9-]+)$')
re_pv_header = re.compile('^Physical Volume ([A-Z0-9-]+)$')
re_lvf_header = re.compile('^Logical Volume Family ([A-Z0-9-]+)$')
re_lv_header = re.compile('^Logical Volume ([A-Z0-9-]+)$')

re_size = re.compile('^(\d+) B \(([\d.]+) GB\)$')

LVG_HEADER_MAP = {
    'Name':                     'name',
    'Free Space':               'free_space',
    'Sequence':                 'sequence',
}

PV_HEADER_MAP = {
    'Status':                   'status',
    'Index':                    'index',
    'Disk':                     'disk',
    'Size':                     'Size',
}

LVFAMILY_HEADER_MAP = {
    'Encryption Status':        'encryption_status',
    'Encryption Context':       'encryption_content',
    'Conversion Status':        'conversion_status',
    'Sequence':                 'sequence',
    'Has Encrypted Extents':    'encrypted',
    'Conversion Direction':     'conversion_direction',
    'Encryption Type':          'encryption_type',
}

LV_HEADER_MAP = {
    'Status':               'status',
    'Sequence':             'sequence',
    'Size (Converted)':     'size_converted',
    'Size (Total)':         'size_total',
    'Volume Name':          'volume_name',
    'LV Name':              'lv_name',
    'Content Hint':         'content_hint',
    'Disk':                 'disk',
    'Revertible':           'revertible',
}

class coreStorage(list):
    """
    Class for OS/X corestorage LVM implementation status parsing
    """
    def __init__(self):
        self.lvg_count = 0
        self.update()

    def __str__(self):
        return '%d groups' % self.lvg_count

    def update(self):
        """
        Parse output of diskutil corestorage list to update data
        """
        lvg = None
        pv = None
        lvf = None
        lv = None
        try:
            for l in check_output(['diskutil', 'coreStorage', 'list']).split('\n'):
                l = l.lstrip('|+-<> ')
                if l.strip() == '' or l.strip('-=') == '':
                 continue
                m = re_header.match(l)
                if m:
                    self.lvg_count = int(m.group(1))
                    continue
                m = re_lvg_header.match(l)
                if m:
                    lvg = coreStorageLVG(m.group(1))
                    self.append(lvg)
                    pv = None
                    lvf = None
                    lv = None
                    continue
                m = re_pv_header.match(l)
                if m:
                    pv = coreStoragePV(lvg, m.group(1))
                    lvg.pvs.append(pv)
                    lv = None
                    lvf = None
                    continue
                m = re_lvf_header.match(l)
                if m:
                    lvf = coreStorageLVFamily(lvg, m.group(1))
                    lvg.lvfs.append(lvf)
                    lv = None
                    continue
                m = re_lv_header.match(l)
                if m:
                    lv = coreStorageLV(lvg, m.group(1))
                    lvf.lvs.append(lv)
                    continue
                try:
                    (key, value) = map(lambda x: x.strip(),  l.split(':', 1))
                except ValueError:
                    raise ValueError('Error parsing line %s' % l)
                if lv is not None:
                    lv[key] = value
                elif lvf is not None:
                    lvf[key] = value
                elif pv is not None:
                    pv[key] = value
                elif lvg is not None:
                    lvg[key] = value
                else:
                    raise ValueError('Out of order line: %s' % l)
        except CalledProcessError:
            raise ValueError('Error listing corestorege volumes')

class coreStorageLVG(dict):
    """
    Class to represent one corestorage LVG (logical volume group)
    """
    def __init__(self, uuid):
        self.uuid = uuid
        self.pvs = []
        self.lvfs = []

    def __str__(self):
        return 'LVG %s\n%s' % (
            self.uuid,
            '\n'.join('%20s %s' % (k, v) for k, v in self.items())
        )

    def __setitem__(self, item, value):
        try:
            item = LVG_HEADER_MAP[item]
        except KeyError:
            pass
        dict.__setitem__(self, item, value)

class coreStoragePV(dict):
    """
    Class to represent one corestorage PV (physical volume)
    """
    def __init__(self, lvg, uuid):
        self.lvg = lvg
        self.uuid = uuid

    def __str__(self):
        return 'PV %s\n%s' % (
            self.uuid,
            '\n'.join('%20s %s' % (k, v) for k, v in self.items())
        )

    def __setitem__(self, item, value):
        try:
            item = PV_HEADER_MAP[item]
        except KeyError:
            pass
        dict.__setitem__(self, item, value)

class coreStorageLVFamily(dict):
    """
    Core storage LV (Logical Volume) family
    """
    def __init__(self, lvg, uuid):
        self.lvg = lvg
        self.uuid = uuid
        self.lvs = []

    def __str__(self):
        return 'LV Family %s\n%s' % (
            self.uuid,
            '\n'.join('%20s %s' % (k, v) for k, v in self.items())
        )

    def __setitem__(self, item, value):
        try:
            item = LVFAMILY_HEADER_MAP[item]
        except KeyError:
            pass
        dict.__setitem__(self, item, value)

class coreStorageLV(dict):
    """
    Core storage LV (logical volume)
    """
    def __init__(self, lvf, uuid):
        self.lvf = lvf
        self.uuid = uuid

    def __str__(self):
        return 'LV %s\n%s' % (
            self.uuid,
            '\n'.join('%20s %s' % (k, v) for k, v in self.items())
        )

    def __setitem__(self, item, value):
        try:
            item = LV_HEADER_MAP[item]
        except KeyError:
            pass
        if item in ['size', 'free_space', 'size_total', 'size_converted']:
            m = re_size.match(value)
            if m:
                value = long(m.group(1))

        dict.__setitem__(self, item, value)
