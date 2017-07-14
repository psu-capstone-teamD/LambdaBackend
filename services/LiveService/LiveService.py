#!/usr/bin/python

import requests
import time
import hashlib


class LiveService:
    def __init__(self):
        self.BASEURL = "https://yanexx65s8e1.live.elementalclouddev.com/api"

    def createEvent(self, xml):
        return self.post('/live_events', xml)

    def createSchedule(self, xml):
        return self.post('/schedules', xml)

    def updatePlaylist(self, event_id, xml):
        return self.post('/live_events/' + str(event_id) + '/playlist', xml)

    def removeEvent(self, event_id):
        return self.delete('/live_events/' + str(event_id))

    def removeSchedule(self, sched_id):
        return self.delete('/schedules/' + str(sched_id))

    def removeInput(self, event_id, input_id, xml):
        return self.delete('/live_events/' + str(event_id) + '/inputs/' + str(input_id))

    def setHeaders(self, endpoint):
        USER = ''
        APIKEY = ''

        # Set the time for session to expire. Should be ~30 seconds in the future
        expiration = str(int(time.time()) + 30)

        # Set the auth key using this algorithm:
        # md5(api_key + md5(url + X-Auth-User + api_key + X-Auth-Expires))
        string1 = endpoint.encode('utf-8') + USER.encode('utf-8') + APIKEY.encode('utf-8') + expiration.encode('utf-8')
        inner = hashlib.md5(string1).hexdigest()
        string2 = APIKEY.encode('utf-8') + inner.encode('utf-8')

        return {"Content-type": "application/xml",
                "Accept": "application/xml",
                "X-Auth-User": USER,
                "X-Auth-Expires": expiration,
                "X-Auth-Key": hashlib.md5(string2).hexdigest()}

    def get(self, endpoint):
        return requests.get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def post(self, endpoint, xml):
        return requests.post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def put(self, endpoint, xml):
        return requests.put(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def delete(self, endpoint):
        return requests.delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))
