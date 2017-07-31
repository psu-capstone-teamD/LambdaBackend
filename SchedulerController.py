from services.S3Service.S3Service import S3Service
from services.LiveService.LiveService import LiveService
import xml.etree.ElementTree as ET
import time
from services.XMLConverterService.XMLConverterService import XMLGenerator


class SchedulerController:
    def __init__(self):
        self.livexmlstorage = 'livexmlstorage'
        self.bxfstorage = 'bxfstorage'
        self.s3service = S3Service()
        self.bxfFileName = 'bxffile.xml'
        self.liveFileName = 'livefile.xml'
        self.EVENT_ID = None

    def inputxml(self, xml):
        if (not isinstance(xml, basestring)):
            return "StatusCode: 400: Not a valid string input"

        # store the bxf.xml file to s3
        bxfBucketResponse = self.storebxffile(self.bxfFileName, xml)
        if(bxfBucketResponse["statusCode"] != '200'):
            return bxfBucketResponse

        # convert bxf to live xml
        xmlConverterService = XMLGenerator()
        try:
            convertedxml = xmlConverterService.run(xml)
        except Exception as e:
            return "StatusCode: 400: Not valid .xml structure"

        # store the live xml to s3

        liveBucketResponse = self.storelivefile(self.liveFileName, convertedxml)
        if (liveBucketResponse["statusCode"] != '200'):
            return liveBucketResponse


        # send the live xml to Live
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
        #send to LiveService
        liveservice = LiveService()

        #call justins method to return only 2 at a time
        #need time.sleep(0.5) after posting first event to getting live event info

        results  = liveservice.createEvent(convertedxml)
        #get the Event ID from the returned xml
        root = ET.fromstring(results.content)
        try:
            self.EVENT_ID = root.find('id').text
        except:
            self.EVENT_ID = None

        return results

    def getLiveEvent(self):
        if(self.EVENT_ID == None):
            self.EVENT_ID = self.getCurrentEventId()
        live = LiveService()
        return live.getLiveEventsByEventId(self.EVENT_ID)

    def getCurrentEventId(self):
        live = LiveService()
        results = live.getLiveEvents()
        root = ET.fromstring(results.content)
        child = root.find('live_event')
        href = child.get('href')
        #strip off the /live_events/ to just get the event number
        event = href[13:]
        return event

    def getDurationInSeconds(self, xml_code):
        root = ET.fromstring(xml_code.content)
        totalDuration = 0
        for input in root.iter('input'):
            input_info = input.find('input_info')
            general = input_info.find('general')
            durationTag = general.find('duration')
            duration = durationTag.text
            #Strip the min and sec off of the time for the duration
            digits = []
            for i in duration:
                if i.isdigit():
                    digits.append(i)
                if not i.isdigit():
                    if i == ' ':
                        continue
                    if i == 's':
                        strippedDuration = ''.join(digits)
                        sec = int(strippedDuration)
                        totalDuration = totalDuration + sec
                        break
                    if i == 'm':
                        strippedDuration = ''.join(digits)
                        min = int(strippedDuration)
                        sec = 60 * min
                        totalDuration = totalDuration + sec
                        break
        strippedDuration = str(totalDuration)
        return strippedDuration

    def getElapsedInSeconds(self, xml_code):
        root = ET.fromstring(xml_code.content)
        elapsedText = root.find('elapsed')
        return elapsedText.text

    def getLastUUID(self, xml_code):
        root = ET.fromstring(xml_code.content)
        uuids = []
        for input in root.iter('input'):
            file_input = input.find('file_input')
            uuid = file_input.find('certificate_file')
            uuid = uuid.text.replace("urn:uuid:", "")
            uuids.append(uuid)
        return uuids[-1]

    def getNextTwo(self, bxf, currentVideoUUID):
        if (not isinstance(currentVideoUUID, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        convertedxml = self.xmlConverterService.bxfToLiveUpdate(bxf, currentVideoUUID)
        return convertedxml
