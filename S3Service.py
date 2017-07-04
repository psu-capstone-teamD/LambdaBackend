import boto3
from botocore.client import Config
from Consts import Consts
import os

class S3Service:
    def __init__(self):
        self.access_key = 'AKIAJLFWURK7YOJ7MLEA'
        self.secret_key = '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'

    def storexml(self, bucketName, filename, xml_file):
        conn = boto3.resource('s3',
                              aws_access_key_id=self.access_key,
                              aws_secret_access_key=self.secret_key,
                              config=Config(signature_version='s3v4'))
        conn.Bucket(bucketName).put_object(Key=filename, Body=xml_file)


    def getxml(self, bucketName, filename):
        # Get the service client
        s3 = boto3.client('s3', aws_access_key_id=self.access_key,
                              aws_secret_access_key=self.secret_key,
                              config=Config(signature_version='s3v4'))

        # Download object at bucket-name with key-name to filename
        nameOfStoredFile = "tempfile.xml"
        s3.download_file(bucketName, filename, nameOfStoredFile)
        #return the downloaded object, r+b is reading/writing and binary
        return open(nameOfStoredFile, 'r+b')


#TESTING FOR STORE AND GET
data = open('sample.xml', 'rb')
s3service = S3Service()
s3service.storexml('livexmlstorage', 'afilename.xml', data)


moredata= s3service.getxml('livexmlstorage', 'afilename.xml')
