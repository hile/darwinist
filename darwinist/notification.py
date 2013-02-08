#!/usr/bin/env python
"""
Send notifications to OS/X Mountain Lion notification center
"""

import Foundation,AppKit,objc,time
from PyObjCTools import AppHelper

from systematic.log import Logger,LoggerError

class NotificationClient(Foundation.NSObject):
    def __init__(self,*args,**kwargs):
        Foundation.NSObject.__init__(self,*args,**kwargs)
        self.log = Logger('notification').default_stream

    def notify(self,title,subtitle,text,url=None):
        ncenter = objc.lookUpClass('NSUserNotificationCenter')
        nclass = objc.lookUpClass('NSUserNotification')
        user_notifications = ncenter.defaultUserNotificationCenter()
        user_notifications.setDelegate_(self)
        notification =  nclass.alloc().init()
        notification.setTitle_(str(title))
        notification.setSubtitle_(str(subtitle))
        notification.setInformativeText_(str(text))
        notification.setSoundName_("NSUserNotificationDefaultSoundName")
        notification.setHasActionButton_(False)
        notification.setOtherButtonTitle_("View")
        if url is not None:
            notification.setUserInfo_({"action":"open_url", "value":url})
        user_notifications.scheduleNotification_(notification)

    def userNotificationCenter_didActivateNotification_(self,center,notification):
        userInfo = notification.userInfo()
        if userInfo["action"] == "open_url":
            import subprocess
            subprocess.Popen(['open', userInfo["value"]])

if __name__ == '__main__':
    n = NotificationClient.alloc().init()
    n.notify('Test','Test Notification','This is just a text notification')
    time.sleep(5)
    n.notify('Test2','Test Notification 2','This is another text notification')

