from S3Service import S3Service
from LiveService import LiveService
from ConverterService import ConverterService


class SchedulerController:
    def __init__(self):
        self.livexmlstorage = 'livexmlstorage'
        self.bxfstorage = 'bxfstorage'
        self.s3service = S3Service()
        self.bxfFileName = 'bxffile.xml'
        self.liveFileName = 'livefile.xml'

    def inputxml(self, xml):
        if (not isinstance(xml, basestring)):
            return "Not a string valid input"

        # store the bxf.xml file to s3
        self.storebxffile(self.bxfFileName, xml)

        # convert bxf to live xml
        xmlConverterService = ConverterService()
        try:
            convertedxml = xmlConverterService.BXFtoLive(xml_file=xml)
        except Exception as e:
            return "Not valid .xml structure"

        # store the live xml to s3
        self.storelivefile(self.liveFileName, convertedxml)

        # send the live xml to Live
        return self.sendToLive(convertedxml)

    def storebxffile(self, filename, xml_file):
        if (not isinstance(filename, basestring)):
            return
        self.s3service.storexml(
            self.bxfstorage, filename=filename, xml_file=xml_file)

    def storelivefile(self, filename, xml_file):
        if (not isinstance(filename, basestring)):
            return
        self.s3service.storexml(self.livexmlstorage, filename, xml_file)

    def loadLiveFile(self, filename):
        if (not isinstance(filename, basestring)):
            return
        return self.s3service.getxml(self.livexmlstorage, filename)

    def sendToLive(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return
        # try to send to LiveService
        liveservice = LiveService()
        try:
            return liveservice.createSchedule(convertedxml)
        except Exception as e:
            return "statusCode': '400"
