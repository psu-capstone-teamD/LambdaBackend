from services.S3Service.S3Service import S3Service
from services.LiveService.LiveService import LiveService
from services.ConverterService.ConverterService import ConverterService

class SchedulerController:
    def __init__(self):
        self.s3service = S3Service()
        self.xmlConverterService = ConverterService()
        self.livexmlstorage = 'livexmlstorage'
        self.bxfstorage = 'bxfstorage'
        self.bxfFileName = 'bxffile.xml'
        self.liveFileName = 'livefile.xml'

    def inputbxf(self, bxf):
        if (not isinstance(bxf, basestring)):
            return "StatusCode: 400: Not a valid string input"

        # store the bxf.xml file to s3
        bxfBucketResponse = self.storebxffile(self.bxfFileName, bxf)
        if(bxfBucketResponse["statusCode"] != '200'):
            return bxfBucketResponse

        # convert bxf to live xml
        try:
            convertedxml = self.xmlConverterService.BXFtoLive(bxf)
        except Exception as e:
            return "StatusCode: 400: Not valid .xml structure"

        # store the live xml to s3
        liveBucketResponse = self.storelivefile(self.liveFileName, convertedxml)
        if (liveBucketResponse["statusCode"] != '200'):
            return liveBucketResponse
        return self.sendToLive(convertedxml)

    def storebxffile(self, filename, xml_file):
        if (not isinstance(filename, basestring)):
            return {'statusCode': '400', 'body': 'filename must be a string'}
        return self.s3service.storexml(self.bxfstorage, filename=filename, xml_file=xml_file)

    def storelivefile(self, filename, xml_file):
        if (not isinstance(filename, basestring)):
            return {'statusCode': '400', 'body': 'filename must be a string'}
        return self.s3service.storexml(self.livexmlstorage, filename, xml_file)

    def loadLiveFile(self, filename):
        if (not isinstance(filename, basestring)):
            return {'statusCode': '400', 'body': 'filename must be a string'}
        return self.s3service.getxml(self.livexmlstorage, filename)

    def sendToLive(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        liveservice = LiveService()
        return liveservice.createEvent(convertedxml)

    def getLiveEvent(self):
        live = LiveService()
        return live.getLiveEvents()

    def getNextTwo(self, bxf, currentVideoUUID):
        if (not isinstance(currentUUID, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        convertedxml = self.xmlConverterService.bxfToLiveUpdate(bxf, currentVideoUUID)
        return convertedxml
