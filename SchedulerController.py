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
        self.profileID = None
        self.indexOfCurrentUUID = 0
        self.listOfInputTimes = []
        self.totalDuration = None
        self.currentUUID = None
        self.livexmlstorage = 'livexmlstorage'
        self.s3service = S3Service()
        self.bxfFileName = "year_" + \
            time.strftime("%Y/month_%m/day%d") + "time_" + \
            time.strftime("%H:%M:%S")
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

        # create a profile id to get the correct output and settings for event.
        # set the profile id on return that has the settings for event
        try:
            profileXML = xmlConverterService.convertProfile(
                bxfXML=xml, profileName=self.profileName)
        except Exception as e:
            return self.xmlError
        try:
            profileResult = self.createLiveProfile(profileXML)
            if(profileResult.status_code != 201):
                return {'statusCode': '400', "body": profileResult.content}
            self.profileID = self.parseProfileID(profileResult)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Create Live Profile, Error: ' + str(e)}

        # get the live xml from the bxf xml with the correct profile id
        try:
            createEventXML = xmlConverterService.convertEvent(
                xml, self.profileID)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Convert Schedule .xml, Error: ' + str(e)}

        # create event in Live
        try:
            resultCreateEvent = self.createLiveEvent(createEventXML)
            if(resultCreateEvent.status_code != 201):
                return {'statusCode': '400', "body": resultCreateEvent.content}
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Create Schedule in Live, Error: ' + str(e)}

        # start the event in Live
        try:
            resultOfStart = self.startLiveEvent()
            if(resultOfStart.status_code != 200):
                return {'statusCode': '400', "body": resultOfStart.content}
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not start Live Event, Error: ' + str(e)}

        # get the start/end/duration times for each video from converter
        # service
        try:
            tree = ET.ElementTree(xml)
            root = xmlConverterService.iteratetoSchedule(
                xmlConverterService.stripNameSpace(tree.getroot()))
            self.listOfInputTimes = xmlConverterService.parseEvents(root)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get start/end times from BXF .xml, Error: ' + str(e)}

        """
        get the duration of the first video
        increment the index to the next uuid and get the second..
        get duration of second video
        the total is the duration of both so that we can find out how long the videos are running
        since the initial create event is sending 2 videos, this needs to happend 2 times.
        """
        try:
            self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get(
                'uid')
            duration1 = self.listOfInputTimes[self.indexOfCurrentUUID].get(
                'duration')
            hours1, minutes1, seconds1 = map(int, duration1.split(':'))
            self.indexOfCurrentUUID += 1
            if(self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours2 = 0
                minutes2 = 0
                seconds2 = 0
            if(self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get(
                    'uid')
                duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get(
                    'duration')
                hours2, minutes2, seconds2 = map(int, duration2.split(':'))
                self.indexOfCurrentUUID += 1
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

        totalHours = hours1 + hours2
        totalMinutes = minutes1 + minutes2
        totalSeconds = seconds1 + seconds2
        self.totalDuration = (totalHours * 3600) + \
            (totalMinutes * 60) + totalSeconds

        flagEventFinished = True

        while(flagEventFinished):
            resultXML = self.getLiveEvent()
            elapsedTime = self.getElapsedInSeconds(resultXML)

            # if seconds left on video is under 30, send another 2 videos up
            if((self.totalDuration - int(elapsedTime)) < 30):
                print("sending another video up")
                try:
                    xmlCode = xmlConverterService.convertUpdate(
                        xml, self.currentUUID)
                    print xmlCode
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not convert .xml, Error: ' + str(e)}
                try:
                    resultOfUpdate = self.updateLiveEvent(xmlCode)
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not update Live event, Error: ' + str(e)}

                # get video times and add the video times to the duration total
                if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                    hours2 = 0
                    minutes2 = 0
                    seconds2 = 0
                    flagEventFinished = False
                if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                    self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get(
                        'uid')
                    duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get(
                        'duration')
                    hours2, minutes2, seconds2 = map(int, duration2.split(':'))
                    self.indexOfCurrentUUID += 1

                totalHours = hours1 + hours2
                totalMinutes = minutes1 + minutes2
                totalSeconds = seconds1 + seconds2
                self.totalDuration += (totalHours * 3600) + \
                    (totalMinutes * 60) + totalSeconds

            time.sleep(3)

        # when all the videos are done playing, delete the event from Live
        try:
            resultOfDelete = self.deleteLiveEvent()
            return resultOfDelete
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not delete Live event, Error: ' + str(e)}

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

    def deleteLiveEvent(self):
        liveservice = LiveService()
        self.EVENT_ID = self.getCurrentEventId()
        results = liveservice.removeEvent(self.EVENT_ID)
        return results

    def startLiveEvent(self):
        liveservice = LiveService()
        results = liveservice.startLiveEvent(self.EVENT_ID)
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

        # send to LiveService to create Event
        liveservice = LiveService()
        results = liveservice.createEvent(convertedxml)
        # need time.sleep(0.5) after posting first event to getting live event
        # info otherwise info wont be correct
        time.sleep(.05)
        # get the Event ID from the returned xml
        root = ET.fromstring(results.content)
        try:
            self.EVENT_ID = root.find('id').text
        except:
            self.EVENT_ID = None

        return results

    def updateLiveEvent(self, convertedxml):
        if (not isinstance(convertedxml, basestring)):
            return {'statusCode': '400', 'body': 'Not a valid string input'}

        # send to LiveService
        liveservice = LiveService()
        # get and set live event id
        self.EVENT_ID = self.getCurrentEventId()

        results = liveservice.updatePlaylist(self.EVENT_ID, convertedxml)
        print results.content
        return results

    def getLiveEvent(self):
        self.EVENT_ID = self.getCurrentEventId()
        live = LiveService()
        return live.getLiveEvent(self.EVENT_ID)

    def getLiveEventForFrontEnd(self):
        live = LiveService()
        # Get Live Event
        self.EVENT_ID = self.getCurrentEventId()

        # get status which gives the current running input
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
            # strip off the /live_events/ to just get the event number
            event = href[13:]
        except Exception as e:
            return "StatusCode: 400: Failed to get Current Event ID. Be sure that Event has been created"
        return event

    def getDurationInSeconds(self, xml_code):
        # Get duration from LIVE. Returns video duration rounded down to the
        # minute.
        try:
            root = ET.fromstring(xml_code.content)
            totalDuration = 0
            for input in root.iter('input'):
                input_info = input.find('input_info')
                general = input_info.find('general')
                durationTag = general.find('duration')
                duration = durationTag.text
                # Strip the min and sec off of the time for the duration
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

    def parseProfileID(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            href = root.get('href')
            # strip off the /live_events_profile/ to just get the event number
            event = href[21:]
        except Exception as e:
            return "StatusCode: 400: Failed to get Current Event ID. Be sure that Event has been created"

        return event
