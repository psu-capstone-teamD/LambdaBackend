#!/usr/bin/python

import requests
import time
import hashlib


class LiveService:
    def __init__(self):
        self.BASEURL = "https://yanexx65s8e1.live.elementalclouddev.com/api"


    def createSchedule(self, xml):

        resp = self.post('/schedules', xml)

        return


    def updatePlaylist(self, xml):

        resp = self.post('/live_events', xml)

        return


    def post(self, endpoint, xml):
        USER = ''
        APIKEY = ''

        # Set the time for session to expire. Should be ~30 seconds in the future
        expiration = str(int(time.time()) + 30)

        # Set the auth key using this algorithm:
        # md5(api_key + md5(url + X-Auth-User + api_key + X-Auth-Expires))
        string1 = endpoint.encode('utf-8') + USER.encode('utf-8') + APIKEY.encode('utf-8') + expiration.encode('utf-8')
        inner = hashlib.md5(string1).hexdigest()
        string2 = APIKEY.encode('utf-8') + inner.encode('utf-8')

        # Create the POST request
        headers = {"Content-type": "application/xml",
                   "Accept": "application/xml",
                   "X-Auth-User": USER,
                   "X-Auth-Expires": expiration,
                   "X-Auth-Key": hashlib.md5(string2).hexdigest()}

        return requests.post(self.BASEURL + endpoint, headers=headers, data=xml)
