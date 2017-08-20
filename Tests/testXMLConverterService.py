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

    #def testGenerateProfile(self):
    #    inputs = [{'order': '1', 'uid': '1', 'uri': '1'},
    #              {'order': '2', 'uid': '2', 'uri': '2'}]
    #    val = generateProfile(inputs)
    #    self.assertEqual(val.getroot().find('./input/order').text, '1')

    def testBadValidate(self):
        bad_xml = "<a><b></b></c>"
        self.assertEqual(self.converter.validateXML(bad_xml), 'StatusCode: 400: Not valid .xml structure')

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


    # def testWriteToFile(self):
    #     xml = "<?xml version='1.0' encoding='utf-8'?>\n<live_event>\n  <name>testX</name>\n  <profile>test_profile</profile>\n  <node_id>3</node_id>\n  <input>\n    <order>1</order>\n    <file_input>\n      <uri>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</uri>\n    </file_input>\n  </input>\n</live_event>"
    #     root = ET.parse('Tests/test_XML/live_event.xml')
    #     self.converter.writetofile(root)
    #     with open('testliveProfile.xml') as f:
    #         fileXml = f.read()
    #     self.assertEqual(xml, fileXml)


if __name__ == '__main__':
    unittest.main()
