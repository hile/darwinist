"""
IOS mobile backups parser
"""

import os
import plistlib
import sqlite3

from operator import attrgetter
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from xml.parsers.expat import ExpatError

# Path of mobile backups on OS/X
BACKUP_PATH = os.path.expanduser('~/Library/Application Support/MobileSync/Backup')

# Database hashed names in backups
DATABASE_FILENAMES = {
    'sms':      '3d0d7e5fb2ce288813306e4d4636395e047a3d28',
    'contacts': '31bb7ba8914766d4ba40d6dfb6113c8b614be442',
    'calendar': '2041457d5fe04d39d0ab481178355df6781e6858',
    'notes':    'ca3bc056d4da0bbf88b5fb3be254f3b7147e639c',
    'calls':    '2b2b0084a1bc3a5ac8c27afdf14afb42c61a19ca',
}

# Message dates are stored starting 2001-01-01
START_DATE = datetime(year=2001, month=1, day=1, hour=0, minute=0, second=0)

# Standard labels in addressbok contacts
CONTACTS_LABEL_MAP = {
    1:  'telephone',
    2:  'work',
    3:  'homepage',
    4:  'mobile',
    5:  'home',
}


class IOSBackupError(Exception):
    pass


class IOSDatabaseBackup(object):
    name = 'no name'
    db_hash = ''

    def __init__(self, backup):
        self.backup = backup
        self.path = os.path.join(backup.path, self.db_hash)
        self.__connection__ = None
        self.__cached_data__ = {}

    @property
    def exists(self):
        return os.path.isfile(self.path)

    @property
    def readable(self):
        return os.access(self.path, os.R_OK)

    @property
    def connection(self):
        if self.__connection__ is not None:
            return self.__connection__
        self.__connection__ = sqlite3.Connection(self.path)
        return self.__connection__

    @property
    def cursor(self):
        return self.connection.cursor()


class SortedContainer(object):

    sort_keys = ()

    def __init__(self):
        self.__cached_data__ = {}


class Handle(SortedContainer):
    sort_keys = ('country', 'service', 'id', 'number')

    def __init__(self, database, handle_id, country, service, number):
        super(Handle, self).__init__()

        self.id = int(handle_id)
        self.country = country
        self.service = service
        self.number = number

    def __repr__(self):
        return self.number


class Message(SortedContainer):
    sort_keys = ('database', 'date')

    def __init__(self, database, message_id, sender_handle_id, date, subject, text, is_from_me):
        super(Message, self).__init__()

        self.database = database
        self.id = message_id
        self.subject = subject
        self.text = text
        self.is_from_me = is_from_me == 1

        self.handle = self.database.find_handle(sender_handle_id)
        self.date = START_DATE + timedelta(seconds=date)

    @property
    def sender(self):
        if self.is_from_me:
            return 'ME'
        else:
            contact = self.database.backup.addressbook.lookup_by_number(self.handle.number)
            if contact is not None:
                return contact
            else:
                return 'UNKNOWN'


class Chat(SortedContainer):

    sort_keys = ('id',)

    def __init__(self, database, chat_id):
        self.database = database
        self.id = chat_id

    @property
    def first(self):
        try:
            return self.messages[0]
        except IndexError:
            return None

    @property
    def latest(self):
        try:
            return self.messages[-1]
        except IndexError:
            return None

    @property
    def messages(self):
        cursor = self.database.cursor
        cursor.execute("""SELECT message_id FROM chat_message_join WHERE chat_id=?""", (self.id,))
        message_ids = [v[0] for v in cursor.fetchall()]
        messages = []
        for message in self.database.messages:
            if message.id in message_ids:
                messages.append(message)
        return sorted(messages, key=attrgetter(*Message.sort_keys))


class SMSDatabase(IOSDatabaseBackup):
    name = 'sms'
    db_hash = '3d0d7e5fb2ce288813306e4d4636395e047a3d28'

    @property
    def handles(self):
        try:
            return self.__cached_data__['handles']
        except KeyError:
            return self.fetch_handles()

    @property
    def messages(self):
        try:
            return self.__cached_data__['messages']
        except KeyError:
            return self.fetch_messages()

    @property
    def chats(self):
        try:
            return self.__cached_data__['chats']
        except KeyError:
            return self.fetch_chats()

    def fetch_handles(self):
        cursor = self.cursor
        cursor.execute("""SELECT rowid, country, service, id FROM handle""")
        self.__cached_data__['handles'] = sorted(
            [Handle(self, *data) for data in cursor.fetchall()],
            key=attrgetter(Handle.sort_keys)
        )
        return self.__cached_data__['handles']

    def fetch_messages(self):
        cursor = self.cursor
        cursor.execute("""
            SELECT rowid AS message_id, handle_id AS sender_handle_id, date, subject, text, is_from_me
            FROM message
        """)
        self.__cached_data__['messages'] = sorted(
            [Message(self, *data) for data in cursor.fetchall()],
            key=attrgetter(*Message.sort_keys)
        )
        return self.__cached_data__['messages']

    def fetch_chats(self):
        cursor = self.cursor
        cursor.execute("""SELECT rowid FROM chat""")
        self.__cached_data__['chats'] = sorted(
            [Chat(self, *data) for data in cursor.fetchall()],
            key=attrgetter(*Chat.sort_keys)
        )
        return self.__cached_data__['chats']

    def find_handle(self, handle_id):
        for handle in self.handles:
            if handle.id == handle_id:
                return handle
        return None


class ContactProperty(object):
    def __init__(self, contact, label, value):
        self.contact = contact
        self.label = label
        self.value = value

    def __repr__(self):
        return '%s %s' % (self.name, self.value)

    @property
    def name(self):
        try:
            return CONTACTS_LABEL_MAP[self.label]
        except KeyError:
            return self.label


class Contact(SortedContainer):
    sort_keys = ('last', 'middle', 'first')

    def __init__(self, database, contact_id, first, last, middle):
        super(Contact, self).__init__()

        self.database = database
        self.id = contact_id
        self.first = first is not None and first or ''
        self.last = last is not None and last or ''
        self.middle = middle is not None and middle or ''

        self.__cached_data = {}

    def __repr__(self):
        name = ''
        for value in (self.first, self.middle, self.last):
            if value:
                name += '%s ' % value
        return name.strip()

    @property
    def properties(self):
        try:
            return self.__cached_data__['properties']
        except KeyError:
            return self.fetch_properties()

    def fetch_properties(self):
        cursor = self.database.cursor
        cursor.execute("""SELECT label, value FROM ABMultiValue WHERE record_id=?""", (self.id, ))
        self.__cached_data__['properties'] = [ContactProperty(self, *data) for data in cursor.fetchall()]
        return self.__cached_data__['properties']


class AddressbookDatabase(IOSDatabaseBackup):
    name = 'contacts'
    db_hash = '31bb7ba8914766d4ba40d6dfb6113c8b614be442'

    def __init__(self, backup):
        super(AddressbookDatabase, self).__init__(backup)

    @property
    def contacts(self):
        try:
            return self.__cached_data__['contacts']
        except KeyError:
            return self.fetch_contacts()

    def fetch_contacts(self):
        cursor = self.cursor
        cursor.execute("""SELECT rowid AS contact_id, first, last, middle FROM ABPerson""")
        self.__cached_data__['contacts'] = sorted(Contact(self, *data) for data in cursor.fetchall())
        return self.__cached_data__['contacts']

    def lookup_by_number(self, number):
        for contact in self.contacts:
            for prop in contact.properties:
                if prop.value is None:
                    continue
                if number == prop.value.replace(' ', ''):
                    return contact
        return None


class CalendarDatabase(IOSDatabaseBackup):
    name = 'calendar'
    db_hash = '2041457d5fe04d39d0ab481178355df6781e6858'

    def __init__(self, backup):
        IOSDatabaseBackup.__init__(self, backup)


class NotesDatabase(IOSDatabaseBackup):
    name = 'notes'
    db_hash = 'ca3bc056d4da0bbf88b5fb3be254f3b7147e639c'

    def __init__(self, backup):
        IOSDatabaseBackup.__init__(self, backup)


class CallsDatabase(IOSDatabaseBackup):
    name = 'calls'
    db_hash = '2b2b0084a1bc3a5ac8c27afdf14afb42c61a19ca'

    def __init__(self, backup):
        IOSDatabaseBackup.__init__(self, backup)


class IOSBackup(object):
    def __init__(self, path):
        self.path = path

        self.sms = SMSDatabase(self)
        self.addressbook = AddressbookDatabase(self)
        self.notes = NotesDatabase(self)
        self.calendar = CalendarDatabase(self)
        self.calls = CallsDatabase(self)

        self.configuration = '248ed6d5d0a8c3a9cc5f8bd2048aac03b273f296'

    def __repr__(self):
        return '%s (updated %s)' % (self.device_name, self.updated)

    def __read_binary_plist__(self, path):
        p = Popen(['plutil', '-convert', 'xml1', '-o', '-', path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return plistlib.readPlistFromString(stdout)

    @property
    def device_name(self):
        path = os.path.join(self.path, '13fcec800c483aa9cc21b0f0e731757ac0f2dea9')
        if not os.path.isfile(path):
            raise IOSBackupError('No such file: {0}'.format(path))

        try:
            plist = self.__read_binary_plist__(path)
        except ExpatError as e:
            raise IOSBackupError('Error reading {0}: {1}'.format(path, e))

        try:
            return plist['UserAssignedDeviceName']
        except KeyError:
            return None

    @property
    def updated(self):
        try:
            return datetime.fromtimestamp(os.stat(self.path).st_mtime)
        except OSError as e:
            raise IOSBackupError('Error checking mtime of %s: %s' % (self.path, e))

    @property
    def id(self):
        return os.path.basename(self.path)


class IOSDeviceBackups(list):
    def __init__(self, path=BACKUP_PATH):
        if not os.path.isdir(path):
            raise IOSBackupError('Not a directory: {}'.format(path))

        try:
            paths = [os.path.join(path, name) for name in os.listdir(path)]
        except OSError as e:
            raise IOSBackupError('Error listing directory {}: {}'.format(path, e))

        for path in paths:
            self.append(IOSBackup(path))
