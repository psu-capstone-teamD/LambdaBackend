import unittest
from S3Service import S3Service

class MyTestCase(unittest.TestCase):
    def test_storexml_live_bucket(self):
        s3 = S3Service()
        s3.storexml('livexmlstorage', 'afilename.xml', 'afile.xml')

    def test_storexml_bxf_bucket(self):
        s3 = S3Service()
        s3.storexml('bxfstorage', 'afilename.xml', 'afile.xml')

    def test_storexml_wrong_bucket(self):
        s3 = S3Service()
        s3.storexml('incorrectBucketName', 'afilename.xml', 'afile.xml')

    def test_storexml_wrong_bucket(self):
        s3 = S3Service()
        s3.storexml(1, 'afilename.xml', 'afile.xml')

    def test_storexml_wrong_filename(self):
        s3 = S3Service()
        s3.storexml('livexmlstorage', 1, 'afile.xml')

    def test_storexml_notAFile(self):
        s3 = S3Service()
        s3.storexml('livexmlstorage', 'afilename.xml', 'afile.xml')

    def test_storexml_isAFile(self):
        s3 = S3Service()
        data = open('sample.xml', 'rb')
        s3.storexml('livexmlstorage', 'afilename.xml', data)

    def test_getxml_live_bucket(self):
        s3 = S3Service()
        s3.getxml('livexmlstorage', 'afilename.xml')

    def test_getxml_bxf_bucket(self):
        s3 = S3Service()
        s3.getxml('bxfstorage', 'afilename.xml')

    def test_getxml_wrong_bucket(self):
        s3 = S3Service()
        s3.getxml('incorrectBucketName', 'afilename.xml')

    def test_storexml_wrong_filename(self):
        s3 = S3Service()
        s3.getxml('livexmlstorage', 1)


if __name__ == '__main__':
    unittest.main()
