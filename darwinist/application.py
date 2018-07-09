"""
OS/X application bundles
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
    Class to parse OS/X application bundle (.app) directory
    """

    def __init__(self, path):
        self.path = path
        self.__cached_info = None

        if not os.path.isdir(path):
            raise ApplicationError('No such directory: {0}'.format(self.path))

        if os.path.splitext(os.path.realpath(path))[1] != '.app':
            raise ApplicationError('Not an application bundle: {0}'.format(path))

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

        for key in ('version', 'short_version'):
            value = getattr(info, key)
            if value is not None:
                return value

        return 'UNKNOWN'


class ApplicationInfo(dict):
    """
    Information for an application, as dictionary
    """

    def __init__(self, application):
        self.path = os.path.join(application.path, 'Contents', 'Info.plist')

        if not os.path.isfile(self.path):
            raise ApplicationError('No such file: {0}'.format(self.path))

        try:
            self.update(plistlib.readPlist(self.path).items())
        except ExpatError as e:
            raise ApplicationError('Error parsing {0}: {1}'.format(self.path, e))

    def __repr__(self):
        return str('{0} {1}'.format(self.name, self.version))

    def __getattr__(self, attr):
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

    def __init__(self, path='/Applications', max_depth=2):
        self.path = path
        self.max_depth = max_depth
        self.update()

    def update(self):
        """
        Update application tree recursively with load_tree()
        """

        def load_tree(path, depth=0):
            """
            Load tree items from given path
            """
            if depth >= self.max_depth:
                return []

            apps = []
            for s in sorted(os.path.join(path, d) for d in os.listdir(path)):
                if not os.path.isdir(s):
                    continue

                if os.path.splitext(s)[1][1:] == 'app':
                    apps.append(Application(s))
                else:
                    apps.extend(load_tree(s, depth=depth+1))

            return apps

        if not os.path.isdir(self.path):
            return

        self.__delslice__(0, len(self))
        self.extend(load_tree(self.path))
