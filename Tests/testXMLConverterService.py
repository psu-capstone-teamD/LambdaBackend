import sys
import unittest
sys.path.append('services/XMLConverterService')
from XMLConverterService import XMLGenerator
from GenerateXML import *


class ConverterTests(unittest.TestCase):

    converter = XMLGenerator()

    def testparseEvents(self):
        root = ET.parse('Tests/test_XML/BXFShort.xml')
        val = self.converter.parseEvents(root)
        self.assertEqual(val, [])

    def testgenerateEvent(self):
        meta = {'name': 'aname', 'startTime': '1', 'endTime': '2'}
        inputs = [{'order': '1', 'uid': '1', 'uri': '1'}]
        val = generateEvent(meta, inputs, "path")
        self.assertEqual(val.getroot().find('./input/order').text, '1')

    def testgenerateSchedule(self):
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
        outputPath = "TestPath"
        outputSettings = "UDP"
        val = generateProfile(profileName, outputPath, outputSettings)
        self.assertEqual(val.getroot().find('./output_group/type').text, 'udp_group_settings')

    def testBadValidate(self):
        bad_xml = "<a><b></b></c>"
        self.assertEqual(self.converter.validateXML(bad_xml), 'StatusCode: 400: Not valid XML structure')

    def testGoodValidate(self):
        good_xml = "<a><b></b></a>"
        self.assertEqual(self.converter.validateXML(good_xml), 'StatusCode: 200')

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



if __name__ == '__main__':
    unittest.main()
