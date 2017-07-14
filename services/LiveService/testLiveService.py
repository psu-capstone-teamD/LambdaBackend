#!/usr/bin/python

import unittest
from LiveService import LiveService


L = LiveService()

class LiveServiceTest(unittest.TestCase):

    def test_get_nodes(self):
        resp = L.get('/nodes')
        self.assertEqual(resp.status_code, 200)

    def test_create_live_event(self):
        with open('test_XML/live_event.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createEvent(xml)
        self.assertEqual(resp.status_code, 201)

    def test_bad_event(self):
        resp = L.post('/live_events', '<Im a bad event></>')
        self.assertEqual(resp.status_code, 422)

    def test_bad_schedule(self):
        resp = L.post('/schedules', '<Im a bad schedule></>')
        self.assertEqual(resp.status_code, 422)

    def test_bad_endpoint(self):
        resp = L.get('/I_dont_exist')
        self.assertEqual(resp.status_code, 404)

    def test_bad_start_time(self):
        with open('test_XML/bad_start_time.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 422)

    def test_bad_uri(self):
        with open('test_XML/bad_uri.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 422)

    def test_missing_input(self):
        with open('test_XML/missing_input.xml', 'r') as infile:
            xml = infile.read()
        resp = L.createSchedule(xml)
        self.assertEqual(resp.status_code, 422)



if __name__ == '__main__':
    unittest.main()
