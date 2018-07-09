"""
Abstraction of AppleScript system events class for python
"""

import appscript

FOLDER_NAME_MAP = {
    'applications': 'applications_folder',
    'application_support': 'application_support_folder',
    'desktop':  'desktop_folder',
    'desktop_pictures': 'desktop_pictures_folder',
    'documents': 'documents_folder',
    'downloads': 'downloads_folder',
    'favorites': 'favorites_folder',
    'fonts': 'fonts_folder',
    'home': 'home_folder',
    'library': 'library_folder',
    'movies': 'movies_folder',
    'music': 'music_folder',
    'pictures': 'pictures_folder',
    'public': 'public_folder',
    'scripts': 'scripting_additions_folder',
    'shared_documents': 'shared_documents_folder',
    'sites': 'sites_folder',
    'speakable_items': 'speakable_items_folder',
    'temp': 'temporary_items_folder',
    'trash': 'trash',
    'utilities': 'utilities_folder',
    'workflows': 'workflows_folder',
}


class SystemEventsError(Exception):
    """
    Exceptions for OS/X system events
    """
    pass


class OSXUserAccounts(dict):
    """
    List of user accounts from appscript system events
    """
    def __init__(self):
        try:
            self.app = appscript.app('System Events')
        except appscript.reference.CommandError as e:
            raise SystemEventsError('Appscript initialization error: {0}'.format(e))

        for ref in self.app.users.get():
            u = OSXUserAccount(self, ref)
            self[u.name] = u


class OSXUserAccount(dict):
    """
    One user account parsed from appscript system events API
    """
    def __init__(self, app, reference):
        self.app = app
        self.reference = reference

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            pass
        raise AttributeError

    def __getitem__(self, item):
        if item not in self.keys():
            raise KeyError('No such OSXUserAccount item: {0}'.format(item))

        if item == 'home_directory':
            return getattr(self.reference, item).get().path

        return getattr(self.reference, item).get()

    def __str__(self):
        return self.full_name

    def keys(self):
        """
        User details keys
        """
        return [k.name for k in self.reference.properties.get().keys()]

    def items(self):
        """
        User details as (key, value) list
        """
        return [(k, self[k]) for k in self.keys()]


class OSXUserFolders(dict):
    """
    List of OS/X user folders from system events API
    """
    def __init__(self):
        try:
            self.app = appscript.app('System Events')
        except appscript.reference.CommandError as e:
            raise SystemEventsError('Appscript initialization error: {0}'.format(e))

        for k in sorted(FOLDER_NAME_MAP.keys()):
            ref = getattr(self.app, FOLDER_NAME_MAP[k]).get()
            if ref is None:
                self[k] = None
                continue

            self[k] = OSXFolderItem(self, ref)


class OSXFolderItem(dict):
    """
    One OS/X folder item from system events
    """
    def __init__(self, app, reference):
        if reference is None:
            raise
        self.app = app
        self.reference = reference

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            pass
        raise AttributeError

    def __getitem__(self, item):
        if item in ['ctime', 'mtime']:
            if item == 'ctime':
                item = 'creation_date'
            if item == 'mtime':
                item = 'modification_date'
            return int(getattr(self.reference, item).get().strftime('%s'))

        if item == 'path':
            item = 'POSIX_path'

        if item not in self.keys():
            raise KeyError('No such OSXFolderItem item: {0}'.format(item))

        return getattr(self.reference, item).get()

    def __str__(self):
        return self.path

    def keys(self):
        """
        Folder detail keys
        """
        return [k.name for k in self.reference.properties.get().keys()] + ['ctime', 'mtime', 'path']

    def items(self):
        """
        Folder details as (key, value) list
        """
        return [(k, self[k]) for k in self.keys()]
