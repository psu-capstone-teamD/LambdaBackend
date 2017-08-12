import unittest
import sys
sys.path.append('services/XMLConverterService')
from XMLConverterService import XMLGenerator


class ConverterTests(unittest.TestCase):

    converter = XMLGenerator()

    def testBadValidate(self):
        bad_xml = "<a><b></b></c>"
        self.assertEqual(self.converter.validateXML(bad_xml), 'StatusCode: 400: Not valid .xml structure')

    def testGoodValidate(self):
        good_xml = "<a><b></b></a>"
        self.assertEqual(self.converter.validateXML(good_xml), 'StatusCode: 200')

if __name__ == '__main__':
    unittest.main()
