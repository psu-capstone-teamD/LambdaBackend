import boto3
from botocore.client import Config
import os

class S3Service:
    def __init__(self):
        self.access_key = ''
        self.secret_key = ''
        self.livexmlstorage = 'livexmlstorage'
        self.bxfstorage = 'bxfstorage'

    def storexml(self, bucketName, filename, xml_file):
        if(bucketName is not self.livexmlstorage and bucketName is not self.bxfstorage):
            return
        if(not isinstance(filename, basestring)):
            return
        if(not  isinstance(xml_file, file)):
            return
        conn = boto3.resource('s3',
                              aws_access_key_id=self.access_key,
                              aws_secret_access_key=self.secret_key,
                              config=Config(signature_version='s3v4'))
        conn.Bucket(bucketName).put_object(Key=filename, Body=xml_file)


    def getxml(self, bucketName, filename):
        if (bucketName is not self.livexmlstorage and bucketName is not self.bxfstorage):
            return
        if (not isinstance(filename, basestring)):
            return
        # Get the service client
        s3 = boto3.client('s3', aws_access_key_id=self.access_key,
                              aws_secret_access_key=self.secret_key,
                              config=Config(signature_version='s3v4'))

        # Download object at bucket-name with key-name to filename
        nameOfStoredFile = "tempfile.xml"
        s3.download_file(bucketName, filename, nameOfStoredFile)
        #return the downloaded object, r+b is reading/writing and binary
        return open(nameOfStoredFile, 'r+b')
