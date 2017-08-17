from services.S3Service.S3Service import S3Service
from services.LiveService.LiveService import LiveService
from services.XMLConverterService.XMLConverterService import XMLGenerator
import xml.etree.ElementTree as ET
import time
import uuid

class SchedulerController:
    def __init__(self):
        self.bxfstorage = 'bxfstorage'
        self.profileName = str(uuid.uuid4())
        self.indexOfCurrentUUID = 0
        self.listOfInputTimes = []
        self.totalDuration = None
        self.currentUUID = None
        self.s3service = S3Service()
        self.bxfFileName = "year_" + time.strftime("%Y/month_%m/day%d") + "time_" + time.strftime("%H:%M:%S")
        self.EVENT_ID = None
        self.xmlError = {'statusCode': '400', "body": 'Not valid xml structure'}

    def inputxml(self, xml):
        if (not isinstance(xml, basestring)):
            return {'statusCode': '400', "body": 'input needs to be a string'}

        # create instance of xml generator and check valid xml structure
        xmlConverterService = XMLGenerator()
        if xmlConverterService.validateXML(xml) == self.xmlError:
            return self.xmlError

        # store the bxf.xml file to s3
        bxfBucketResponse = self.storebxffile(self.bxfFileName, xml)
        if(bxfBucketResponse["statusCode"] != '200'):
            return bxfBucketResponse

        convertResult = self.convertSendStartInitialLiveEvent(xml)
        if (convertResult["statusCode"] != '200'):
            return convertResult
        setTimesResult = self.setListOfInputTimes(xml)
        if (setTimesResult["statusCode"] != '200'):
            return setTimesResult
        totalDurationResult = self.setInitialTotalDurationForTwoVideos()
        if (totalDurationResult["statusCode"] != '200'):
            return totalDurationResult

        flagEventFinished = True

        while(flagEventFinished):
            resultXML = self.getLiveEvent()
            elapsedTime = self.getElapsedInSeconds(resultXML)

            #if seconds left on video is under 30, send another video up
            if((self.totalDuration - int(elapsedTime)) < 30):
                try:
                    xmlCode = xmlConverterService.convertUpdate(xml, self.currentUUID)
                    print xmlCode
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not convert .xml, Error: ' + str(e)}
                try:
                    resultOfUpdate = self.createLiveEvent(xmlCode)
                    #TODO Get Live event id for pending event
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not update Live event, Error: ' + str(e)}

                try:
                    flagEventFinished = self.addToTotalDurationForOneVideo()
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

            #play video when last video close to complete. This may take some tweaking depending on delay.
            if ((self.totalDuration - int(elapsedTime)) < 2):
                # start the event in Live
                try:
                    #TODO put in EventId of pending event
                    resultOfStart = self.startLiveEvent("10000000000")
                    if (resultOfStart.status_code != 200):
                        return {'statusCode': '400', "body": resultOfStart.content}
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not start Live Event, Error: ' + str(e)}

            time.sleep(1)

    def convertSendStartInitialLiveEvent(self, xml):
        xmlConverterService = XMLGenerator()
        # get the live xml from the bxf xml with the correct profile id
        try:
            createEventXML = xmlConverterService.convertEvent(xml)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Convert Schedule .xml, Error: ' + str(e)}

        # create event in Live
        try:
            resultCreateEvent = self.createLiveEvent(createEventXML)
            if (resultCreateEvent.status_code != 201):
                return {'statusCode': '400', "body": resultCreateEvent.content}
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Create Schedule in Live, Error: ' + str(e)}

        # start the event in Live
        try:
            resultOfStart = self.startLiveEvent()
            if (resultOfStart.status_code != 200):
                return {'statusCode': '400', "body": resultOfStart.content}
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not start Live Event, Error: ' + str(e)}

        return {'statusCode': '200'}

    def setListOfInputTimes(self, xml):
        # get the start/end/duration times for each video from converter service
        xmlConverterService = XMLGenerator()
        try:
            tree = ET.ElementTree(xml)
            root = xmlConverterService.iteratetoSchedule(xmlConverterService.stripNameSpace(tree.getroot()))
            self.listOfInputTimes = xmlConverterService.parseEvents(root)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get start/end times from BXF .xml, Error: ' + str(e)}

        return {'statusCode': '200'}

    def setInitialTotalDurationForTwoVideos(self):
        """
                get the duration of the first video
                increment the index to the next uuid and get the second..
                get duration of second video
                the total is the duration of both so that we can find out how long the videos are running
                since the initial create event is sending 2 videos, this needs to happend 2 times.
                """
        try:
            self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
            duration1 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
            hours1, minutes1, seconds1 = map(int, duration1.split(':'))
            self.indexOfCurrentUUID += 1
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours2 = 0
                minutes2 = 0
                seconds2 = 0
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
                duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
                hours2, minutes2, seconds2 = map(int, duration2.split(':'))
                self.indexOfCurrentUUID += 1
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

        totalHours = hours1 + hours2
        totalMinutes = minutes1 + minutes2
        totalSeconds = seconds1 + seconds2
        self.totalDuration = (totalHours * 3600) + (totalMinutes * 60) + totalSeconds
        return {'statusCode': '200'}

    def addToTotalDurationForOneVideo(self):
        # get video times and add the video times to the duration total
        flagToJumpOutOfLoop = True
        if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
            hours2 = 0
            minutes2 = 0
            seconds2 = 0
            flagToJumpOutOfLoop = False
        if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
            self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
            duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
            hours, minutes, seconds = map(int, duration2.split(':'))
            self.indexOfCurrentUUID += 1

        self.totalDuration += (hours * 3600) + (minutes * 60) + seconds
        return flagToJumpOutOfLoop

    def storebxffile(self, filename, xml_file):
        if (not isinstance(filename, basestring)):
            return {'statusCode': '400', 'body': 'filename must be a string'}
        return self.s3service.storexml(self.bxfstorage, filename=filename, xml_file=xml_file)

    def deleteLiveEvent(self, eventID):
        liveservice = LiveService()
        self.EVENT_ID = self.getCurrentEventId()
        results = liveservice.removeEvent(eventID)
        return results

    def startLiveEvent(self, eventID):
        liveservice = LiveService()
        results = liveservice.startLiveEvent(eventID)
        return results

    def createLiveSchedule(self, convertedXML):
        if (not isinstance(convertedXML, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        # send to LiveService to create Profile
        liveservice = LiveService()
        results = liveservice.createSchedule(convertedXML)
        return results

    def createLiveProfile(self, profileXML):
        if (not isinstance(profileXML, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        # send to LiveService to create Profile
        liveservice = LiveService()
        results = liveservice.createProfile(profileXML)
        return results

    def createLiveEvent(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        #send to LiveService to create Event
        liveservice = LiveService()
        results  = liveservice.createEvent(convertedxml)
        return results

    def updateLiveEvent(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}
        #send to LiveService
        liveservice = LiveService()
        #get and set live event id
        self.EVENT_ID = self.getCurrentEventId()
        results = liveservice.updatePlaylist(self.EVENT_ID, convertedxml)
        return results

    def getLiveEvent(self):
        self.EVENT_ID = self.getCurrentEventId()
        live = LiveService()
        return live.getLiveEvent(self.EVENT_ID)

    def getLiveEventForFrontEnd(self):
        live = LiveService()
        #Get Live Event
        self.EVENT_ID = self.getCurrentEventId()

        #get status which gives the current running input
        status = live.getLiveEventStatus(self.EVENT_ID)
        root = ET.fromstring(status.content)
        active_input_id = root.find('active_input_id')

        currentEventInfo = self.getLiveEvent()
        try:
            rootOfEvent = ET.fromstring(currentEventInfo.content)
            uuidStringForPending = ""
            runningUuid = ""
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
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get uuids from event or no running event' + str(e)}

        return {'statusCode': '200', 'running': runningUuid, 'pending': uuidStringForPending}

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
            return {'statusCode': '400', 'body': 'Failed to get Current Event ID. Be sure that Event has been created Error: ' + str(e)}
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
        except Exception as e:
            return {'statusCode': '400','body': 'Failed to get Elapsed time. Error: ' + str(e)}

    def getElapsedInSeconds(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            elapsedText = root.find('elapsed')
            return elapsedText.text
        except Exception as e:
            return {'statusCode': '400','body': 'Failed to get Elapsed time. Error: ' + str(e)}

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
        except Exception as e:
            return {'statusCode': '400', 'body': 'Failed to get last UUID. Error: ' + str(e)}

    def parseProfileID(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            href = root.get('href')
            # strip off the /live_events_profile/ to just get the event number
            event = href[21:]
        except Exception as e:
            return {'statusCode': '400', 'body': 'Failed to get Profile ID. Error: ' + str(e)}
        return event

    def getCurrentRunningEventID(self):
        live = LiveService()
        try:
            results = live.getLiveEvents("running")
            root = ET.fromstring(results.content)
            child = root.find('live_event')
            href = child.get('href')
            #strip off the /live_events/ to just get the event number
            event = href[13:]
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get current running Live event, Error: ' + str(e)}
        return event


