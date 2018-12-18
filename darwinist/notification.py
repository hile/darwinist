"""
Send notifications to OS/X Mountain Lion notification center
"""

import Foundation
import objc
import time


class NotificationCenter(object):
    def __init__(self):
        self.notification_center = objc.lookUpClass('NSUserNotificationCenter')

    @property
    def user_notification_center(self):
        return

    def notify(self, title, subtitle, text, url=None):
        client = Notification.alloc().init()

        user_notification_center = self.notification_center.defaultUserNotificationCenter()
        user_notification_center.setDelegate_(client)

        notification = objc.lookUpClass('NSUserNotification').alloc().init()
        notification.setTitle_(str(title))
        notification.setSubtitle_(str(subtitle))
        notification.setInformativeText_(str(text))
        notification.setSoundName_('NSUserNotificationDefaultSoundName')

        if url is not None:
            notification.setUserInfo_({'action': 'open_url', 'value': url})

        user_notification_center.scheduleNotification_(notification)

        time.sleep(5)
        return client


class Notification(Foundation.NSObject):
    def userNotificationCenter_didDeliverNotification_(self, center, notification):
        pass

    def userNotificationCenter_didActivateNotification_(self, center, notification):
        pass

        userInfo = notification.userInfo()
        if userInfo['action'] == 'open_url':
            import subprocess
            subprocess.Popen(['open', userInfo['value']])
