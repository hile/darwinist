#!/usr/bin/env python
"""
OS/X application bundle processing tools
"""

import os
import plistlib

from xml.parsers.expat import ExpatError

INFO_BUNDLE_NAME_MAP = {
    'name':             'CFBundleName',
    'bundle_id':        'CFBundleIdentifier',
    'version':          'CFBundleVersion',
    'short_version':    'CFBundleShortVersionString',
}

class ApplicationError(Exception):
    pass

class Application(object):
    """
    Class to represent OS/X application bundles (.app)
    """
    def __init__(self,path):
        self.path = path
        self.__cached_info = None

        if not os.path.isdir(path):
            raise ApplicationError('No such directory: %s' % self.path)

        if os.path.splitext(os.path.realpath(path))[1] != '.app':
            raise ApplicationError('Not an application bundle: %s' % path)

    def __repr__(self):
        return self.path

    @property
    def info(self):
        if not self.__cached_info:
            self.__cached_info = ApplicationInfo(self)
        return self.__cached_info

    @property
    def version(self):
        info = self.info

        for k in ('version', 'short_version'):
            value = getattr(info,k)
            if value is not None:
                return value

        return 'UNKNOWN'

class ApplicationInfo(dict):
    """
    Information for an application, as dictionary
    """
    def __init__(self,application):
        self.path = os.path.join(application.path,'Contents','Info.plist')

        if not os.path.isfile(self.path):
            raise ApplicationError('No such file: %s' % self.path)

        try:
            self.update(plistlib.readPlist(self.path).items())
        except ExpatError,emsg:
            raise ApplicationError('Error parsing %s: %s' % (self.path,emsg))

    def __repr__(self):
        return unicode('%s %s' % (self.name,self.version))

    def __getattr__(self,attr):
        if attr in INFO_BUNDLE_NAME_MAP.keys():
            attr = INFO_BUNDLE_NAME_MAP[attr]

        try:
            return self[attr]
        except KeyError:
            return None

class ApplicationTree(list):
    """
    Tree of OS/X applications (.app directory bundles)
    """
    def __init__(self,path='/Applications',max_depth=2):
        self.path = path
        self.max_depth = max_depth

        self.update()

    def update(self):
        """
        Update application tree recursively with load_tree()
        """

        def load_tree(path,depth=0):
            """
            Load tree items from given path
            """
            if depth >= self.max_depth:
                return []

            apps = []
            for s in sorted(os.path.join(path,d) for d in os.listdir(path)):
                if not os.path.isdir(s):
                    continue

                if os.path.splitext(s)[1][1:] == 'app':
                    apps.append(Application(s))
                else:
                    apps.extend(load_tree(s,depth=depth+1))

            return apps

        if not os.path.isdir(self.path):
            return

        list.__delslice__(self,0,len(self))
        self.extend(load_tree(self.path))
