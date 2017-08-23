from requests import get, post, put, delete
from time import time
from hashlib import md5


class LiveService:
    def __init__(self):
        self.BASEURL = "https://yanexx65s8e1.live.elementalclouddev.com/api"

    def getLiveEventStatus(self, eventID):
        endpoint = '/live_events/' + str(eventID) + '/status'
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def getLiveEvents(self, filter):
        endpoint = '/live_events' if not filter else '/live_events?filter=' + filter
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def getLiveEvent(self, eventID):
        endpoint = '/live_events/' + str(eventID)
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def getSchedules(self):
        endpoint = '/schedules'
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def getLiveProfiles(self):
        endpoint = '/live_event_profiles'
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def getLiveProfile(self, profileID):
        endpoint = '/live_event_profiles/' + str(profileID)
        return get(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def createEvent(self, xml):
        endpoint = '/live_events'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def createSchedule(self, xml):
        endpoint = '/schedules'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def createProfile(self, xml):
        endpoint = '/live_event_profiles'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def updateLiveEvent(self, eventID, xml):
        endpoint = '/live_events/' + str(eventID)
        headers = self.setHeaders(endpoint)
        headers['unlocked'] = '1'
        return put(self.BASEURL + endpoint, data=xml, headers=headers)

    def updatePlaylist(self, eventID, xml):
        endpoint = '/live_events/' + str(eventID) + '/playlist'
        return post(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def updateSchedule(self, schedID, xml):
        endpoint = '/schedules/' + str(schedID)
        return put(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def updateProfile(self, profileID, xml):
        endpoint = '/live_event_profiles/' + str(profileID)
        return put(self.BASEURL + endpoint, data=xml, headers=self.setHeaders(endpoint))

    def removeEvent(self, eventID):
        endpoint = '/live_events/' + str(eventID)
        return delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def removeSchedule(self, schedID):
        endpoint = '/schedules/' + str(schedID)
        return delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def removeProfile(self, profileID):
        endpoint = '/live_event_profiles/' + str(profileID)
        return delete(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def startLiveEvent(self, eventID):
        endpoint = '/live_events/' + str(eventID) + '/start'
        return post(self.BASEURL + endpoint, headers=self.setHeaders(endpoint))

    def setHeaders(self, endpoint):
        """
        Generates headers to authenticate REST commands to Elemental Live.
        :param endpoint: The endpoint in the URL used to calculate the Auth key.
        :return: A dict object with all the headers listed below.
        """
        USER = ''
        APIKEY = ''

        # Set the time for session to expire. Should be ~30 seconds in the future
        expiration = str(int(time()) + 30)

        # discard endpoint parameters if they are there
        endpoint = endpoint.split('?')[0]

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
