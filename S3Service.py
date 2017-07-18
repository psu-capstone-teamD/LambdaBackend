import boto3


class S3Service:
    def __init__(self):
        self.access_key = ''
        self.secret_key = ''
        self.livexmlstorage = 'livexmlstorage'
        self.bxfstorage = 'bxfstorage'

    def storexml(self, bucketName, filename, xml_file):
        if(bucketName is not self.livexmlstorage and bucketName is not self.bxfstorage):
            return self.respond("Bucket name is incorrect", None)

        if(not isinstance(filename, basestring)):
            return self.respond("File name must be a string", None)

        if (not isinstance(xml_file, basestring)):
            return self.respond("Incorrect storage type: Must be in .xml or string format", None)

        conn = boto3.resource('s3',
                              aws_access_key_id=self.access_key,
                              aws_secret_access_key=self.secret_key)

        try:
            conn.Bucket(bucketName).put_object(Key=filename, Body=xml_file)
            return self.respond(None, 'Stored successfully to S3')
        except Exception as e:
            return self.respond("Store unsuccessful: Could not connect or authentication denied", None)

    def getxml(self, bucketName, filename):
        if (bucketName is not self.livexmlstorage and bucketName is not self.bxfstorage):
            return
        if (not isinstance(filename, basestring)):
            return
        # Get the service client
        s3 = boto3.client('s3', aws_access_key_id=self.access_key,
                          aws_secret_access_key=self.secret_key)

        try:
            return s3.get_object(Bucket=bucketName, Key=filename)
        except Exception as e:
            return self.respond("Connection unsuccessful: Could not connect or authentication denied", None)

    def respond(self, error, response):
        return {
            'statusCode': '400' if error else '200',
            'body': error if error else response,
        }
