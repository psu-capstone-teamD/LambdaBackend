#!/usr/bin/python

import unittest
from ConverterService import xmlConverterService


X = xmlConverterService()

class ConverterServiceTest(unittest.TestCase):

    def testBXFtoLive(self):
        return

    def testMissingInput(self):
        with open('test_XML/live_event.xml', 'r') as infile:
            bxf = infile.read()
        return

    def testMissingMediaLocation(self):
        return

    '''
    # test if elements and all their children are equal
    def elements_equal(self, e1, e2):
        if e1.tag != e2.tag: return False
        if e1.text != e2.text: return False
        if e1.tail != e2.tail: return False
        if e1.attrib != e2.attrib: return False
        if len(e1) != len(e2): return False
        return all(self.elements_equal(c1, c2) for c1, c2 in zip(e1, e2))
    '''



if __name__ == '__main__':
    unittest.main()
