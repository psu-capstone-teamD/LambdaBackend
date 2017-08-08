from services.S3Service.S3Service import S3Service
from services.LiveService.LiveService import LiveService
import xml.etree.ElementTree as ET
import time
from services.XMLConverterService.XMLConverterService import XMLGenerator


class SchedulerController:
    def __init__(self):
        self.bxfstorage = 'bxfstorage'
        self.livexmlstorage = 'livexmlstorage'
        self.s3service = S3Service()
        self.bxfFileName = 'bxffile.xml'
        self.liveFileName = 'livefile.xml'
        self.EVENT_ID = None
        self.xmlError = 'StatusCode: 400: Not valid .xml structure'

    def inputxml(self, xml):
        if (not isinstance(xml, basestring)):
            return "StatusCode: 400: Not a valid string input"

        # create instance of xml generator and check valid xml structure
        xmlConverterService = XMLGenerator()
        if xmlConverterService.validateXML(xml) == self.xmlError:
            return self.xmlError

        # store the bxf.xml file to s3
        bxfBucketResponse = self.storebxffile(self.bxfFileName, xml)
        if(bxfBucketResponse["statusCode"] != '200'):
            return bxfBucketResponse

        # convert bxf to live xml
        try:
            convertedxml = xmlConverterService.run(xml)
        except Exception as e:
            return self.xmlError

        # send the live xml to Live
        try:
            self.createLiveEvent(convertedxml)
        except Exception as e:
            return "StatusCode: 400: Failed to create Live Event"

        '''while(True):
            resultXML = self.getLiveEvent()
            elapsedTime = self.getElapsedInSeconds(resultXML)
            durationTime = self.getDurationInSeconds(resultXML)
            totalTimeLeft = elapsedTime - durationTime
            #check if time is less than 30 seconds
            if(totalTimeLeft < 30):
                try:
                    convertedxml = xmlConverterService.run(xml)
                except Exception as e:
                    return "StatusCode: 400: Not valid .xml structure or could not be converted to Live .xml correctly"

                # send the live xml to Live
                try:
                    self.updateLiveEvent(convertedxml)
                except Exception as e:
                    return "StatusCode: 400: Failed to update Live Event"'''

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

    def createLiveEvent(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}

        #send to LiveService to create Event
        liveservice = LiveService()
        results  = liveservice.createEvent(convertedxml)
        # need time.sleep(0.5) after posting first event to getting live event info otherwise info wont be correct
        time.sleep(.05)
        #get the Event ID from the returned xml
        root = ET.fromstring(results.content)
        try:
            self.EVENT_ID = root.find('id').text
        except:
            self.EVENT_ID = None

        return results

    def updateLiveEvent(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}

        #send to LiveService
        liveservice = LiveService()
        #check if event Id is set, otherwise get it from Live
        if (self.EVENT_ID == None):
            self.EVENT_ID = self.getCurrentEventId()

        results = liveservice.updatePlaylist(self.EVENT_ID, convertedxml)
        return results

    def getLiveEvent(self):
        if(self.EVENT_ID == None):
            self.EVENT_ID = self.getCurrentEventId()
        live = LiveService()
        return live.getLiveEvent(self.EVENT_ID)

    def getLiveEventForFrontEnd(self):
        live = LiveService()
        # check if event Id is set, otherwise get it from Live
        if (self.EVENT_ID == None):
            self.EVENT_ID = self.getCurrentEventId()

        #get status which gives the current running input
        status = live.getLiveEventStatus(self.EVENT_ID)
        root = ET.fromstring(status.content)
        active_input_id = root.find('active_input_id')

        currentEventInfo = self.getLiveEvent()
        try:
            rootOfEvent = ET.fromstring(currentEventInfo.content)
            uuidStringForPending = ""
            flagForreachingCurrentVideo = False
            for pendingInput in rootOfEvent.iter('input'):
                idOfInput = pendingInput.find('id')
                if (flagForreachingCurrentVideo == True):
                    file_input = pendingInput.find('file_input')
                    uuidTemp = file_input.find('certificate_file')
                    pendingUuid = uuidTemp.text.replace("urn:uuid:", "")
                    uuidStringForPending += pendingUuid + ","
                if(idOfInput.text == active_input_id.text):
                    file_input = pendingInput.find('file_input')
                    uuidTemp = file_input.find('certificate_file')
                    runningUuid = uuidTemp.text.replace("urn:uuid:", "")
                    flagForreachingCurrentVideo = True
        except:
            uuidStringForPending = "No pending events"
            runningUuid = "No running events"

        return {'statusCode': '200', 'running': runningUuid, 'pending:': uuidStringForPending}

    def getCurrentEventId(self):
        live = LiveService()
        try:
            results = live.getLiveEvents(None)
            root = ET.fromstring(results.content)
            child = root.find('live_event')
            href = child.get('href')
            #strip off the /live_events/ to just get the event number
            event = href[13:]
        except Exception as e:
            return "StatusCode: 400: Failed to get Current Event ID. Be sure that Event has been created"
        return event

    def getDurationInSeconds(self, xml_code):
        #Get duration from LIVE. Returns video duration rounded down to the minute.
        try:
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
        except:
            return "StatusCode: 400: Failed to get Elapsed time."

    def getElapsedInSeconds(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            elapsedText = root.find('elapsed')
            return elapsedText.text
        except:
            return "StatusCode: 400: Failed to get Elapsed time."

    def getLastUUID(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            uuids = []
            for input in root.iter('input'):
                inputFile = input.find('file_input')
                uuidpending = inputFile.find('certificate_file')
                pendingUuid = uuidpending.text.replace("urn:uuid:", "")
                uuids.append(pendingUuid)
                result = uuids[-1]
                return result
        except:
            return "StatusCode: 400: Failed to get last UUID."
