from S3Service import S3Service


class SchedulerController:
    def __init__(self):
        self.livexmlstorage = 'livexmlstorage'
        self.bxfstorage = 'bxfstorage'

    def inputxml(self, xml_file):
        self.storebxffile(xml_file)
        xmlConverterService = xmlConverterService()
        convertedxml = xmlConverterService.BXFtoLive(xml_file)
        self.storelivefile(convertedxml)

    def storebxffile(self, xml_file):
        s3service = S3Service()
        s3service.storexml(self.bxfstorage, xml_file)

    def storelivefile(self, xml_file):
        s3service = S3Service()
        s3service.storexml(self.livexmlstorage, xml_file)

    def loadLiveFile(self, filename):
        s3service = S3Service()
        return s3service.getxml(self.livexmlstorage, filename)

    def loadBXFFile(self, filename):
        s3service = S3Service()
        return s3service.getxml(self.bxfstorage, filename)

    def sendToLive(self, filename):
        liveservice = LiveService()
        liveFile = self.loadLiveFile(filename)
        liveservice.createSchedule(liveFile)
