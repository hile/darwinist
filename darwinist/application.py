#!/usr/bin/env python
"""
OS/X application bundle processing tools
"""

import os,plistlib
from xml.parsers.expat import ExpatError

INFO_BUNDLE_NAME_MAP = {
    'name':             'CFBundleName',
    'bundle_id':        'CFBundleIdentifier',
    'version':          'CFBundleVersion',
    'short_version':    'CFBundleShortVersionString',
}

class ApplicationError(Exception):
    """
    Exceptions raised while processing an OS/X application bundle
    """
    def __str__(self):
        return self.args[0]

class Application(object):
    """
    Class to represent OS/X application bundles (.app)
    """
    def __init__(self,path):
        self.path = path
        if not os.path.isdir(path):
            raise ApplicationError('No such directory: %s' % self.path)

    def __getattr__(self,attr):
        if attr == 'info':
            return Applicationinfo(self)
        raise AttributeError('No such Application attribute: %s' % attr)

class Applicationinfo(dict):
    """
    Information for an application, as dictionary
    """
    def __init__(self,application):
        dict.__init__(self)
        self.path = os.path.join(application.path,'Contents','Info.plist')
        if not os.path.isfile(self.path):
            raise ApplicationError('No such file: %s' % self.path)
        try:
            self.update(plistlib.readPlist(self.path))
        except ExpatError,emsg:
            raise ApplicationError('Error parsing %s: %s' % (self.path,emsg))
    
    def __repr__(self):
        return unicode('%s %s' % (self.name,self.version))

    def __getattr__(self,attr):
        if attr in INFO_BUNDLE_NAME_MAP.keys():
            try:
                return self[INFO_BUNDLE_NAME_MAP[attr]]
            except KeyError:
                return None
        raise AttributeError('No such Application attribute: %s' % attr)

class ApplicationTree(list):
    """
    Tree of OS/X applications (.app directory bundles)
    """
    def __init__(self,path='/Applications',max_depth=2):
        list.__init__(self)
        self.path = path
        self.max_depth = max_depth
        self.update()

    def update(self):
        """
        Update application tree recursively with load_tree()
        """
        if not os.path.isdir(self.path):
            return
        
        list.__delslice__(self,0,len(self))

        def load_tree(path,depth=0):
            """
            Load tree items from given path
            """
            if depth >= self.max_depth:
                return []
            apps = []
            subs = sorted(filter(lambda x: 
                os.path.isdir(x),
                [os.path.join(path,d) for d in sorted(os.listdir(path))]
            ))
            for s in subs:
                if os.path.splitext(s)[1][1:] == 'app':
                    apps.append(Application(s))
                else:
                    apps.extend(load_tree(s,depth=depth+1))
            return apps

        self.extend(load_tree(self.path))
