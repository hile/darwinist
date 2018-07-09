"""
OSX core location API for python
"""

import json
import requests
import time
import CoreLocation

API_URL = """http://maps.googleapis.com/maps/api/geocode/json?latlng=%(latitude)s,%(longitude)s&sensor=false"""


class CoreLocationError(Exception):
    pass


class CoreLocationManager(object):
    def __init__(self):
        self.manager = CoreLocation.CLLocationManager.alloc().init()
        self.startUpdatingLocation()

    def stopUpdatingLocation(self):
        self.manager.stopUpdatingLocation()

    def startUpdatingLocation(self):
        self.manager.startUpdatingLocation()

    def get_coordinates(self, seconds=5):
        """Get location

        Returns coordinates from core location API
        """
        wait = seconds
        while True:
            location = self.manager.location()
            if location is not None:
                return location.coordinate()

            wait -= 1
            if wait == 0:
                break
            time.sleep(1)

        raise CoreLocationError('Error getting location in {0} seconds'.format(seconds))

    def get_addresses(self, coordinates, count=1):
        url = API_URL % {'latitude': coordinates.latitude, 'longitude': coordinates.longitude, }
        response = requests.get(url)
        if response.status_code != 200:
            raise CoreLocationError('Error querying google maps API: returns status code {0}'.format(
                response.status_code
            ))

        addresses = []
        try:
            data = json.loads(response.content)
            for record in data['results']:
                if 'formatted_address' in record:
                    address = record['formatted_address']
                    if address not in addresses:
                        addresses.append(address)

                    if len(addresses) >= count:
                        break

        except ValueError:
            raise CoreLocationError('Error parsing google maps location API response as JSON')

        except KeyError:
            raise CoreLocationError('Could not find formatted_address from JSON response')

        return addresses
