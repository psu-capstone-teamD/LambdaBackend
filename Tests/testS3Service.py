import sys
import unittest
sys.path.append('services/S3Service')
from S3Service import S3Service


class MyTestCase(unittest.TestCase):

    def test_storexml__live(self):
        s3 = S3Service()
        data = "this is some text to put into s3"
        resp = s3.storexml('livexmlstorage', 'afilename.xml', data)
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_bxf(self):
        s3 = S3Service()
        data = "this is some text to put into s3"
        resp = s3.storexml('bxfstorage', 'afilename.xml', data)
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_bxf_isAFile(self):
        s3 = S3Service()
        data = "this is some text to put into s3"
        resp = s3.storexml('bxfstorage', 'afilename.xml', data)
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_live_inputnotaString(self):
        s3 = S3Service()
        resp = s3.storexml('livexmlstorage', 'afilename.xml', 1)
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_bxf_inputnotaString(self):
        s3 = S3Service()
        resp = s3.storexml('bxfstorage', 'afilename.xml', 1)
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_wrong_bucket(self):
        s3 = S3Service()
        resp = s3.storexml('incorrectBucketName', 'afilename.xml', 'afile.xml')
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_wrong_bucket2(self):
        s3 = S3Service()
        resp = s3.storexml(1, 'afilename.xml', 'afile.xml')
        self.assertEqual(resp["statusCode"], '400')

    def test_storexml_wrong_filename(self):
        s3 = S3Service()
        resp = s3.storexml('livexmlstorage', 1, 'afile.xml')
        self.assertEqual(resp["statusCode"], '400')

    def test_getxml_live_bucket(self):
        s3 = S3Service()
        s3.getxml('livexmlstorage', 'afilename.xml')

    def test_getxml_bxf_bucket(self):
        s3 = S3Service()
        s3.getxml('bxfstorage', 'afilename.xml')

    def test_getxml_wrong_bucket(self):
        s3 = S3Service()
        s3.getxml('incorrectBucketName', 'afilename.xml')

    def test_getxml_wrong_filename(self):
        s3 = S3Service()
        s3.getxml('livexmlstorage', 1)

    def test_getxml_wrong_Live_filename(self):
        s3 = S3Service()
        s3.getxml('livexmlstorage', "somenonexistentfile.xml")

    def test_getxml_wrong_bxf_filename(self):
        s3 = S3Service()
        s3.getxml('bxfstorage', "somenonexistentfile.xml")


if __name__ == '__main__':
    unittest.main()
