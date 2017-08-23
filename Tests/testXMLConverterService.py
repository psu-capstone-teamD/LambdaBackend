import sys
import unittest
sys.path.append('services/XMLConverterService')
from XMLConverterService import XMLGenerator
from GenerateXML import *


class ConverterTests(unittest.TestCase):

    converter = XMLGenerator()

    def testIterateToSchedule(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        root = self.converter.iterateToSchedule(bxf)
        self.assertEqual(root.attrib['ScheduleStart'], "2011-09-07T00:00:00.00")

    def testConvertEvent(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        input = self.converter.convertEvent(bxf, None, 'path')
        inputRoot = ET.fromstring(input)

        with open('Tests/test_XML/LiveShort.xml', 'r') as infile:
            liveXML = infile.read()
        outputRoot = ET.fromstring(liveXML)

        self.assertTrue(self.converter.elementsEqual(inputRoot, outputRoot))

    def testConvertSchedule(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        input = self.converter.convertSchedule(bxf, '11')
        inputRoot = ET.fromstring(input)

        with open('Tests/test_XML/ScheduleShort.xml', 'r') as infile:
            liveXML = infile.read()
        outputRoot = ET.fromstring(liveXML)

        self.assertTrue(self.converter.elementsEqual(inputRoot, outputRoot))

    def testConvertUpdate(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        input = self.converter.convertUpdate(bxf, 'urn:uuid:57d6bdf4-a5f3-4756-9bc6-b09819cd1bc9')
        inputRoot = ET.fromstring(input)

        with open('Tests/test_XML/UpdateShort.xml', 'r') as infile:
            liveXML = infile.read()
        outputRoot = ET.fromstring(liveXML)

        self.assertTrue(self.converter.elementsEqual(inputRoot, outputRoot))

    def testGenerateEvent(self):
        meta = {'name': 'aname', 'startTime': '1', 'endTime': '2'}
        inputs = [{'order': '1', 'uid': '1', 'uri': '1'}]
        val = generateEvent(meta, inputs, "path")
        self.assertEqual(val.getroot().find('./input/order').text, '1')

    def testGeneratRedirect(self):
        deltaURL = "http://delta-1-yanexx65s8e5.live.elementalclouddev.com/in_put/test.m3u8"
        redirect = genertateRedirect(deltaURL)
        self.assertEqual(redirect.getroot().find('./output_group/output/name_modifier').text, 'output')

    def testGenerateSchedule(self):
        meta = {'name': 'aname', 'startTime': '1', 'endTime': '2'}
        inputs = [{'order': '1', 'uid': '1', 'uri': '1'},
                  {'order': '2', 'uid': '2', 'uri': '2'}]
        val = generateSchedule('11', meta, inputs)
        self.assertEqual(val.getroot().find('./input/order').text, '1')

    def testGenerateUpdate(self):
        inputs = [{'order': '1', 'uid': '1', 'uri': '1'},
                  {'order': '2', 'uid': '2', 'uri': '2'}]
        val = generateUpdate(inputs)
        self.assertEqual(val.getroot().find('./input/order').text, '1')

    def testGenerateProfile(self):
        profileName = "TestProfile"
        val = generateProfile(profileName)
        self.assertEqual(val.getroot().find('./output_group/type').text, 'udp_group_settings')

    def testParseEvents(self):
        root = ET.parse('Tests/test_XML/BXFShort.xml')
        val = self.converter.parseEvents(root)
        self.assertEqual(val, [])

    def testParseMetadata(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        root = self.converter.iterateToSchedule(bxf)
        meta = self.converter.parseMetadata(root)
        self.assertEqual(meta['name'], 'WBCC_09072011_1315410574')
        self.assertEqual(meta['startTime'], '2011-09-07T00:00:00.00')
        self.assertEqual(meta['endTime'], '2011-09-07T23:59:46.05')

    def testNextEvent(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        root = self.converter.iterateToSchedule(bxf)
        events = self.converter.parseEvents(root)
        next = self.converter.nextEvent(events, "urn:uuid:058ff320-2044-4c71-9f90-f6ef3234f53a")
        self.assertEqual(next[0]["uid"], "urn:uuid:e618de18-9787-445f-ab4f-f0f7764ad1a7")
        next = self.converter.nextEvent(events, None)
        self.assertEqual(next[0]["uid"], "urn:uuid:058ff320-2044-4c71-9f90-f6ef3234f53a")
        next = self.converter.nextEvent(events, "unknownUUID")
        self.assertEqual(next, [])

    def testNextNevents(self):
        with open('Tests/test_XML/BXFShort.xml', 'r') as infile:
            bxf = infile.read()
        root = self.converter.iterateToSchedule(bxf)
        events = self.converter.parseEvents(root)
        next = self.converter.nextNevents(2, events, "urn:uuid:058ff320-2044-4c71-9f90-f6ef3234f53a")
        self.assertEqual(next[0]["uid"], "urn:uuid:e618de18-9787-445f-ab4f-f0f7764ad1a7")
        self.assertEqual(next[1]["uid"], "urn:uuid:60d273d1-fcc5-474d-b518-5c54dc510699")
        next = self.converter.nextNevents(None, events, None)
        self.assertEqual(next, events)
        next = self.converter.nextNevents(4, events, "unknownUUID")
        self.assertEqual(next, [])

    def testElementsEqual(self):
        xmlA = "<a><b><c></c></b></a>"
        xmlB = "<a><b><c></c></b></a>"
        rootA = ET.fromstring(xmlA)
        rootB = ET.fromstring(xmlB)
        self.assertTrue(self.converter.elementsEqual(rootA, rootB))

    def testElementsNotEqual(self):
        xmlA = "<a><b><c></c></b></a>"
        xmlB = "<a><b><d></d></b></a>"
        rootA = ET.fromstring(xmlA)
        rootB = ET.fromstring(xmlB)
        self.assertFalse(self.converter.elementsEqual(rootA, rootB))

    def testBadValidate(self):
        bad_xml = "<a><b></b></c>"
        self.assertEqual(self.converter.validateXML(bad_xml), 'StatusCode: 400: Not valid XML structure')

    def testGoodValidate(self):
        good_xml = "<a><b></b></a>"
        self.assertEqual(self.converter.validateXML(good_xml), 'StatusCode: 200')



if __name__ == '__main__':
    unittest.main()
