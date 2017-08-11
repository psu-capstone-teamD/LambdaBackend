#!/usr/bin/python
import sys
import unittest
sys.path.append('services/LiveService')
from LiveService import LiveService


L = LiveService()


class LiveServiceTest(unittest.TestCase):

    def testGetEvents(self):
        resp = L.getLiveEvents()
        self.assertEqual(resp.status_code, 200)

    def testCreateLiveEvent(self):
        with open('test_XML/live_event.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createEvent(xml)
        self.assertEqual(resp.status_code, 201)

    def testBadEvent(self):
        resp = L.createEvent('<Im a bad event></>')
        self.assertEqual(resp.status_code, 422)

    def testBadSchedule(self):
        resp = L.createSchedule('<Im a bad schedule></>')
        self.assertEqual(resp.status_code, 422)

    def testUnknownEvent(self):
        resp = L.removeEvent(-5)
        self.assertEqual(resp.status_code, 404)

    def testBadStartTime(self):
        with open('test_XML/bad_start_time.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 422)

    def testBadUri(self):
        with open('test_XML/bad_uri.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 422)

    def testMissingInput(self):
        with open('test_XML/missing_input.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 422)


if __name__ == '__main__':
    unittest.main()
