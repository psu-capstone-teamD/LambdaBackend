#!/usr/bin/python

from requests import get, post, put, delete
from time import time
from hashlib import md5


class LiveService:
    def __init__(self):
        self.BASEURL = "https://yanexx65s8e1.live.elementalclouddev.com/api"

    def getLiveEvents(self):
        endpoint = '/live_events'
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def getSchedules(self):
        endpoint = '/schedules'
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def createEvent(self, xml):
        endpoint = '/live_events'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def createSchedule(self, xml):
        endpoint = '/schedules'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def updatePlaylist(self, eventID, xml):
        endpoint = '/live_events/' + str(eventID) + '/playlist'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def removeEvent(self, eventID):
        endpoint = '/live_events' + str(eventID)
        return delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def removeSchedule(self, schedID):
        endpoint = '/schedules/' + str(schedID)
        return delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def removeInput(self, eventID, inputID, xml):
        endpoint = '/live_events/' + str(eventID) + '/inputs/' + str(inputID)
        return delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def setHeaders(self, endpoint):
        USER = ''
        APIKEY = ''

        # Set the time for session to expire. Should be ~30 seconds in the future
        expiration = str(int(time()) + 30)

        # Set the auth key using this algorithm:
        # md5(api_key + md5(url + X-Auth-User + api_key + X-Auth-Expires))
        string1 = endpoint.encode('utf-8') + USER.encode('utf-8') + APIKEY.encode('utf-8') + expiration.encode('utf-8')
        inner = md5(string1).hexdigest()
        string2 = APIKEY.encode('utf-8') + inner.encode('utf-8')

        return {"Content-type": "application/xml",
                "Accept": "application/xml",
                "X-Auth-User": USER,
                "X-Auth-Expires": expiration,
                "X-Auth-Key": md5(string2).hexdigest()}
