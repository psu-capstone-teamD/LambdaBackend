import unittest
import sys
import xml.etree.ElementTree as ET
sys.path.append('services/XMLConverterService')
from XMLConverterService import XMLGenerator


class ConverterTests(unittest.TestCase):

    converter = XMLGenerator()

    # def testparseEvents(self):
    #     with open('Tests/test_xml/BXFShort.xml') as f:
    #         fileXml = f.read()
    #     self.converter.parseEvents(fileXml)
    #     self.assertEqual(fileXml, 'helloo')

    def testBadValidate(self):
        bad_xml = "<a><b></b></c>"
        self.assertEqual(self.converter.validateXML(bad_xml),
                         'StatusCode: 400: Not valid .xml structure')

    def testGoodValidate(self):
        good_xml = "<a><b></b></a>"
        self.assertEqual(self.converter.validateXML(
            good_xml), 'StatusCode: 200')

    def testWriteToFile(self):
        xml = "<?xml version='1.0' encoding='utf-8'?>\n<live_event>\n  <name>testX</name>\n  <profile>test_profile</profile>\n  <node_id>3</node_id>\n  <input>\n    <order>1</order>\n    <file_input>\n      <uri>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</uri>\n    </file_input>\n  </input>\n</live_event>"
        root = ET.parse('Tests/test_XML/live_event.xml')
        self.converter.writetofile(root)
        with open('testliveProfile.xml') as f:
            fileXml = f.read()
        self.assertEqual(xml, fileXml)

    def testGenerateProfile(self):
        self.assertEqual(ET.tostring(self.converter.generateProfile(
            'test').getroot()), '<live_event_profile><name>test</name><failure_rule><priority>50</priority><restart_on_failure>false</restart_on_failure></failure_rule><stream_assembly><name>SA1</name><video_description><codec>h.264</codec></video_description></stream_assembly><output_group><type>apple_live_group_settings</type><apple_live_group_settings><cdn>Basic_PUT</cdn><destination><uri>https://yanexx65s8e1.live.elementalclouddev.com/in_put/test</uri></destination></apple_live_group_settings><output><name_modifier>output1</name_modifier><stream_assembly_name>SA1</stream_assembly_name><container>m3u8</container></output></output_group></live_event_profile>')


if __name__ == '__main__':
    unittest.main()
