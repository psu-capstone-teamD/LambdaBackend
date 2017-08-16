import unittest
import sys
import xml.etree.ElementTree as ET
sys.path.append('services/XMLConverterService')
from XMLConverterService import XMLGenerator


class ConverterTests(unittest.TestCase):

    converter = XMLGenerator()

    def testparseEvents(self):
        root = ET.parse('Tests/test_XML/BXFShort.xml')
        val = self.converter.parseEvents(root)
        self.assertEqual(val, [])

    def testgenerateSchedule(self):
        meta = {'name': 'aname', 'startTime': 1, 'endTime': 2}
        inputs = [{'order': 1, 'uid': 1, 'uri': 1},
                  {'order': 2, 'uid': 2, 'uri': 2}]
        val = self.converter.generateSchedule(4, meta, inputs)
        self.assertEqual(val.find('./input/order').text, '1')

    def testGenerateUpdate(self):
        inputs = [{'order': 1, 'uid': 1, 'uri': 1},
                  {'order': 2, 'uid': 2, 'uri': 2}]
        val = self.converter.generateUpdate(inputs)
        self.assertEqual(val.find('./input/order').text, '1')

    def testgenerateEventWithtwoInputs(self):
        meta = {'name': 'aname', 'startTime': 1, 'endTime': 2}
        inputs = [{'order': 1, 'uid': 1, 'uri': 1},
                  {'order': 2, 'uid': 2, 'uri': 2}]
        val = self.converter.generateEvent(meta, inputs, 4)
        self.assertEqual(val.find('./input/order').text, '1')

    def testgenerateEventWithOneInput(self):
        meta = {'name': 'aname', 'startTime': 1, 'endTime': 2}
        inputs = [{'order': 1, 'uid': 1, 'uri': 1}]
        val = self.converter.generateEvent(meta, inputs, 4)
        self.assertEqual(val.find('./input/order').text, '1')

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
            'test').getroot()), '<live_event_profile><name>test</name><failure_rule><priority>50</priority><restart_on_failure>false</restart_on_failure><backup_rule>none</backup_rule></failure_rule><stream_assembly><name>SA1</name><video_description><height>720</height><width>1280</width><codec>h.264</codec><h264_settings><framerate_denominator>1</framerate_denominator><framerate_follow_source>false</framerate_follow_source><framerate_numerator>30</framerate_numerator><gop_size>60.0</gop_size><par_denominator>1</par_denominator><par_follow_source>false</par_follow_source><par_numerator>1</par_numerator><slices>4</slices><level>4.1</level><bitrate>2500000</bitrate><buf_size>5000000</buf_size></h264_settings><video_preprocessors><deinterlacer><algorithm>interpolate</algorithm><deinterlace_mode>Deinterlace</deinterlace_mode><force>false</force></deinterlacer></video_preprocessors></video_description><audio_description><audio_source_name>Audio Selector 1</audio_source_name><audio_type>0</audio_type><follow_input_audio_type>true</follow_input_audio_type><follow_input_language_code>true</follow_input_language_code><codec>aac</codec></audio_description></stream_assembly><output_group><type>apple_live_group_settings</type><apple_live_group_settings><cdn>Basic_PUT</cdn><destination><uri>http://delta-1-yanexx65s8e5.live.elementalclouddev.com/in_put/test</uri></destination></apple_live_group_settings><output><name_modifier>output</name_modifier><stream_assembly_name>SA1</stream_assembly_name><container>m3u8</container></output></output_group></live_event_profile>')

    # def teststripNameSpace(self):
    #     xml = "<?xml version='1.0' encoding='utf-8'?>\n<live_event>\n  <name>testX</name>\n  <profile>test_profile</profile>\n  <node_id>3</node_id>\n  <input>\n    <order>1</order>\n    <file_input>\n      <uri>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</uri>\n    </file_input>\n  </input>\n</live_event>"
    #     xmlWithoutNamespace = "<live_event>\n  <name>testX</name>\n  <profile>test_profile</profile>\n  <node_id>3</node_id>\n  <input>\n    <order>1</order>\n    <file_input>\n      <uri>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</uri>\n    </file_input>\n  </input>\n</live_event>"

    #     self.assertEqual(self.converter.stripNameSpace(xml).text,
    #                      xmlWithoutNamespace)


if __name__ == '__main__':
    unittest.main()
