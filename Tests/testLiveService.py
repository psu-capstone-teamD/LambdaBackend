import sys
import unittest
import requests_mock
from mock import patch
sys.path.append('services/LiveService')
from LiveService import LiveService



L = LiveService()
baseURL = "https://yanexx65s8e1.live.elementalclouddev.com/api"


class LiveServiceTest(unittest.TestCase):


    '''@patch('services.LiveService.LiveService.time', return_value=1502345833)
    def testSetHeaders(self, mock_time):
        headers = L.setHeaders("/schedules")
        self.assertEqual(headers, {'X-Auth-Expires': '1502345863',
                                    'X-Auth-Key': '9c9a72cd3a8feec48539f1943afbef8d',
                                    'Content-type': 'application/xml',
                                    'X-Auth-User': '',
                                    'Accept': 'application/xml'})'''

    @requests_mock.Mocker()
    def testGetStatus(self, m):
        m.get(baseURL + "/live_events/150/status", status_code=200)
        resp = L.getLiveEventStatus(150)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testGetEvents(self, m):
        m.get(baseURL + "/live_events", status_code=200)
        m.get(baseURL + "/live_events?filter=running", status_code=200)
        resp = L.getLiveEvents(None)
        self.assertEqual(resp.status_code, 200)
        resp = L.getLiveEvents("running")
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testGetEvent(self, m):
        m.get(baseURL + "/live_events/164", status_code=200)
        resp = L.getLiveEvent(164)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testGetSchedules(self, m):
        m.get(baseURL + "/schedules", status_code=200)
        resp = L.getSchedules()
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testGetLiveProfiles(self, m):
        m.get(baseURL + "/live_event_profiles", status_code=200)
        resp = L.getLiveProfiles()
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testGetLiveProfile(self, m):
        m.get(baseURL + "/live_event_profiles/11", status_code=200)
        resp = L.getLiveProfile(11)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testCreateLiveEvent(self, m):
        with open('Tests/test_XML/live_event.xml', 'r') as infile:
            xml = infile.read()
        m.post(baseURL + "/live_events", status_code=201)
        resp = L.createEvent(xml)
        self.assertEqual(resp.status_code, 201)

    @requests_mock.Mocker()
    def testCreateSchedule(self, m):
        with open('Tests/test_XML/schedule.xml', 'r') as infile:
            xml = infile.read()
        m.post(baseURL + "/schedules", status_code=201)
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 201)

    @requests_mock.Mocker()
    def testCreateProfile(self, m):
        with open('Tests/test_XML/schedule.xml', 'r') as infile:
            xml = infile.read()
        m.post(baseURL + "/schedules", status_code=201)
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 201)

    @requests_mock.Mocker()
    def testUpdateLiveEvent(self, m):
        with open('Tests/test_XML/live_event.xml', 'r') as infile:
            xml = infile.read()
        m.post(baseURL + "/live_events/92/playlist", status_code=200)
        resp = L.updatePlaylist(92, xml)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testUpdateSchedule(self, m):
        with open('Tests/test_XML/schedule.xml', 'r') as infile:
            xml = infile.read()
        m.put(baseURL + "/schedules/13", status_code=200)
        resp = L.updateSchedule(13, xml)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testUpdateProfile(self, m):
        with open('Tests/test_XML/live_profile.xml', 'r') as infile:
            xml = infile.read()
        m.put(baseURL + "/live_event_profiles/33", status_code=200)
        resp = L.updateProfile(33, xml)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testRemoveLiveEvent(self, m):
        m.delete(baseURL + "/live_events/191", status_code=200)
        resp = L.removeEvent(191)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testRemoveSchedule(self, m):
        m.delete(baseURL + "/schedules/13", status_code=200)
        resp = L.removeSchedule(13)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testRemoveProfile(self, m):
        m.delete(baseURL + "/live_event_profiles/33", status_code=200)
        resp = L.removeProfile(33)
        self.assertEqual(resp.status_code, 200)

    @requests_mock.Mocker()
    def testStartEvent(self, m):
        m.post(baseURL + "/live_events/50/start", status_code=200)
        resp = L.startLiveEvent(50)
        self.assertEqual(resp.status_code, 200)



if __name__ == '__main__':
    unittest.main()
