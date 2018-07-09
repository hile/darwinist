"""
Control and see status of OS/X network interfaces from python.
"""

import os
import appscript
from configobj import ConfigObj

NETWORK_CONNECTION_TYPES = {
    'wlan':         [2],
    'thunderbolt':  [5],
    'ethernet':     [6],
    'dialup':       [7, 8],  # Both bluetooth and USB 3G connections
    'firewire':     [9],
    'vpn':          [10, 13],
}


class NetworkConfigError(Exception):
    pass


class NetworkProfileList(object):
    """
    List of network profiles found on the OS/X system
    """
    def __init__(self, config=None):
        self.config = self.__read_config__(config)

        try:
            self.app = appscript.app('System Events')
            self.location = self.app.network_preferences.get().current_location.get()

        except appscript.reference.CommandError as e:
            raise NetworkConfigError('Appscript initialization error: {0}'.format(e))

    def __read_config__(self, config):
        if not os.path.isfile(config):
            return {}
        return ConfigObj(config)

    def __getitem__(self, item):
        names = filter(
            lambda s: s.name.get() == item,
            self.location.services.get()
        )
        if not names:
            raise KeyError('No such connection: {0}'.format(item))

        try:
            return NetworkConnection(item, profiles=self)

        except appscript.reference.CommandError:
            raise KeyError('No such network service configured: {0}'.format(item))

    def keys(self):
        """
        Return names of network locations
        """
        return [s.name.get() for s in self.location.services.get()]

    def items(self):
        """
        Return (name,NetworkConnection() list based on self.keys()
        """
        return [(k, NetworkConnection(k, profiles=self)) for k in self.keys()]

    def values(self):
        """
        Return NetworkConnection() list based on self.keys()
        """
        return [NetworkConnection(k, profiles=self) for k in self.keys()]

    def filter(self, connection_type):
        """
        Return network connections matching connection_type
        """
        try:
            connection_types = int(connection_type)

        except ValueError:
            try:
                connection_types = NETWORK_CONNECTION_TYPES[connection_type]
            except KeyError:
                raise NetworkConfigError('Unknown connection type: {0}'.format(connection_type))

        if not isinstance(connection_types, list):
            connection_types = [connection_types]

        filtered = []
        for service in self.location.services.get():
            if service.kind.get() in connection_types:
                filtered.append(NetworkConnection(service.name.get(), self))

        return filtered


class NetworkConnection(object):
    """
    Details and control of one OS/X network connection
    """
    def __init__(self, name, profiles=None):
        if profiles is None:
            profiles = NetworkProfileList()
        self.name = name
        self.app = profiles.app

        names = filter(lambda s: s.name.get() == name, profiles.location.services.get())
        if not len(names):
            raise NetworkConfigError('No such connection: {0}'.format(name))

        try:
            self.connection = profiles.location.services[name].get()
        except KeyError as e:
            raise NetworkConfigError(str(e).strip("'"))

    def __eq__(self, other):
        if not hasattr(other, 'app'):
            return 0

        if self.connection_type != other.connection_type:
            return

    def __hash__(self):
        return '{0} {1}'.format(self.connection_type, self.name)

    def __repr__(self):
        return '{0} {1}: {2}'.format(
            self.connection_type,
            self.name,
            self.connected and 'connected' or 'not connected'
        )

    def get_interface_attribute(self, item):
        try:
            interface = self.connection.interface.get()
            return getattr(interface, item).get()

        except appscript.reference.CommandError:
            raise AttributeError('Value {0} not available for interface {1}'.format(
                item,
                self.name
            ))

    @property
    def mac(self):
        return self.get_interface_attribute('MAC_address')

    @property
    def mac_address(self):
        return self.get_interface_attribute('MAC_address')

    @property
    def kind(self):
        try:
            return self.connection.kind.get()

        except appscript.reference.CommandError:
            raise NetworkConfigError('Error getting service type for {0}'.format(self.name))

    @property
    def connection_type(self):
        for k, values in NETWORK_CONNECTION_TYPES.items():
            if self.kind in values:
                return k
        return 'unknown'

    @property
    def connected(self):
        try:
            return self.connection.current_configuration.connected.get()

        except appscript.reference.CommandError:
            return False

    def connect(self):
        """
        Connects the network interface.

        If the interface is a VPN and it requires a password, you will still
        get graphical password request dialog. Patches welcome how to enter
        the passphrase with appscript.
        """
        if self.connected:
            raise NetworkConfigError('Already connected: {0}'.format(self.name))

        self.app.connect(self.connection)

    def disconnect(self):
        """
        Disconnect the network interface
        """
        if not self.connected:
            raise NetworkConfigError('Not connected: {0}'.format(self.name))

        self.app.disconnect(self.connection)
