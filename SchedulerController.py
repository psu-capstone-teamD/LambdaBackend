from services.S3Service.S3Service import S3Service
from services.LiveService.LiveService import LiveService
from services.XMLConverterService.XMLConverterService import XMLGenerator
import xml.etree.ElementTree as ET
import time
import uuid
import re


class SchedulerController:
    def __init__(self):
        self.bxfstorage = 'bxfstorage'
        self.secondsLeftSendingNextVideo = 30
        self.secondsLeftPlayingNextVideo = 2
        self.outPutPath = None
        self.profileName = str(uuid.uuid4())
        self.indexOfCurrentUUID = 0
        self.sizeOfCurrentUUID = 0
        self.listOfInputTimes = []
        self.listOfEventIds = []
        self.totalDuration = None
        self.currentUUID = None
        self.s3service = S3Service()
        #this sets the year directory, month and day/time in the bxfBucket of S3
        self.bxfFileName = "year_" + \
            time.strftime("%Y/month_%m/day%d") + "time_" + \
            time.strftime("%H:%M:%S")
        self.EVENT_ID = None
        self.xmlError = {'statusCode': '400', "body": 'Not valid xml structure'}

    def inputxml(self, xml, output_path):
        if (not isinstance(xml, basestring)):
            return {'statusCode': '400', "body": 'input needs to be a string'}
        if (not isinstance(output_path, basestring)):
            return {'statusCode': '400', "body": 'input needs to be a string'}

        self.outPutPath = output_path

        # create instance of xml generator and check valid xml structure
        xmlConverterService = XMLGenerator()
        if xmlConverterService.validateXML(xml) == self.xmlError:
            return self.xmlError

        # store the bxf.xml file to s3
        bxfBucketResponse = self.storebxffile(self.bxfFileName, xml)
        if(bxfBucketResponse["statusCode"] != '200'):
            return bxfBucketResponse

        # this gets the duration times for each UUID that was retrieved from the BXF for all the videos
        # Sets them in a List
        setTimesResult = self.setListOfInputTimes(xml)
        if (setTimesResult["statusCode"] != '200'):
            return setTimesResult

        index = 0
        flagForEventsPlayingAlready = True
        initialRunningEvents = True
        noInitialRunningEvents = True
        incrementedIndex = False
        while(flagForEventsPlayingAlready):
            resultOfEvents = self.getLiveEventForFrontEnd()
            runningEvent = resultOfEvents["running"]
            pendingEvent = resultOfEvents["pending"]

            currentUUID = self.listOfInputTimes[index].get('uid')
            currentUUID = currentUUID.replace("urn:uuid:", "")

            if(runningEvent != "" and initialRunningEvents):
                noInitialRunningEvents = False
                if(runningEvent == currentUUID):
                    self.indexOfCurrentUUID = index + 1
                    initialRunningEvents = False
                    noInitialRunningEvents = True
                    incrementedIndex = True
                    continue

                if(pendingEvent == currentUUID):
                    initialRunningEvents = False
                    noInitialRunningEvents = True
                    self.indexOfCurrentUUID = index
                    incrementedIndex = True
                    continue

                if (runningEvent != currentUUID and pendingEvent != currentUUID):
                    index += 1
                    incrementedIndex = True


            #if there is no events running or pending, then start this one right up since it is the first one to start.
            if (runningEvent == "" and pendingEvent == "" and noInitialRunningEvents):
                initialRunningEvents = False
                if (incrementedIndex):
                    # this converts and starts the initial event in Live
                    tempUUID = self.listOfInputTimes[self.indexOfCurrentUUID - 1].get('uid')
                    convertResult = self.convertSendStartInitialLiveEvent(xml, tempUUID)
                    if (convertResult["statusCode"] != '200'):
                        return convertResult

                if(not incrementedIndex):
                    # this converts and starts the initial event in Live
                    convertResult = self.convertSendStartInitialLiveEvent(xml, None)
                    if (convertResult["statusCode"] != '200'):
                        return convertResult

                # This sets the duration time for the first video and sets it..It returns just the status code if passes.
                totalDurationResult = self.setInitialTotalDuration()
                if (totalDurationResult["statusCode"] != '200'):
                    return totalDurationResult

                flagForEventsPlayingAlready = False

            if ((self.sizeOfCurrentUUID - 1) <= self.indexOfCurrentUUID and incrementedIndex):
                flagForEventsPlayingAlready = False

            if ((self.sizeOfCurrentUUID - 1) <= index and incrementedIndex):
                convertResult = self.convertSendStartInitialLiveEvent(xml, None)
                if (convertResult["statusCode"] != '200'):
                    return convertResult
                # This sets the duration time for the first video and sets it..It returns just the status code if passes.
                totalDurationResult = self.setInitialTotalDuration()
                if (totalDurationResult["statusCode"] != '200'):
                    return totalDurationResult
                flagForEventsPlayingAlready = False

        if ((self.sizeOfCurrentUUID - 1) <= self.indexOfCurrentUUID and incrementedIndex):
            resultDeleteEvents = self.deleteEvents()
            if (resultDeleteEvents["statusCode"] != '200'):
                return resultDeleteEvents

            return {'statusCode': '200', "body": 'The process was successfully loaded to Live and finished'}


        resultOfUploadAndPlay = self.uploadAndPlayNextEvents(xml)
        if (resultOfUploadAndPlay["statusCode"] != '200'):
            return resultOfUploadAndPlay

        resultDeleteEvents = self.deleteEvents()
        if (resultDeleteEvents["statusCode"] != '200'):
            return resultDeleteEvents


        return {'statusCode': '200', "body": 'The process was successfully loaded to Live and finished'}

    def uploadAndPlayNextEvents(self, xml):
        xmlConverterService = XMLGenerator()
        # Need to put in a delay otherwise it won't give Live enough time to start and elapsedTime will be initially off.
        time.sleep(1)
        flagEventFinished = True
        waitingToPlay = True
        flagForLastPlay = True
        # Keep looping until no more videos to upload and no more pending videos to play
        while (flagEventFinished or flagForLastPlay):
            runningEventID = self.getCurrentRunningEventID()
            if(not runningEventID.isdigit()):
                return {'statusCode': '400', "body": 'Could not get current running event id'}
            resultXML = self.getLiveEvent(runningEventID)
            elapsedTime = self.getElapsedInSeconds(resultXML)
            if (not elapsedTime.isdigit()):
                return {'statusCode': '400', "body": 'Could not get elapsed time'}

            # check if elapsed time has gone over. If so, try playing video again
            # this isn't really needed, just in very rare cases.  Usually if elapsed does go over, it will still work right.
            if (not isinstance(int(elapsedTime), int)):
                if (not flagEventFinished):
                    flagForLastPlay = False
                    # start the event in Live
                try:
                    pendingEventID = self.getCurrentPendingEventID()
                    if (not pendingEventID.isdigit()):
                        return {'statusCode': '400', "body": 'Could not get current pending event id'}
                    resultOfStart = self.startLiveEvent(pendingEventID)
                    waitingToPlay = True
                    if (resultOfStart.status_code != 200):
                        return {'statusCode': '400', "body": resultOfStart.content}
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not start Live Event, Error: ' + str(e)}

                try:
                    flagEventFinished = self.addToTotalDurationForOneVideo()
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

                continue

            # if seconds left on video is under self.secondsLeftSendingNextVideo time, send another video up
            if ((self.totalDuration - int(
                    elapsedTime)) < self.secondsLeftSendingNextVideo and waitingToPlay and flagEventFinished):
                # Get the uuid of the last video that played and run through converter service to get Live code for next video
                try:
                    auuid = self.listOfInputTimes[self.indexOfCurrentUUID - 1].get('uid')
                    xmlCode = xmlConverterService.convertEvent(xml, auuid, self.outPutPath)
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not convert .xml, Error: ' + str(e)}
                # If there are no more uuids in the list, then there are no more videos to load.
                # This sets flag to not go into this if statement anymore
                if ((self.sizeOfCurrentUUID - 1) <= self.indexOfCurrentUUID):
                    flagEventFinished = False
                # Sends the Live code to live to create the event
                # set waitingToPlay to false so that it doesn't enter this function until it is played.
                # Otherwise it will keep loading events the entire time
                try:
                    resultOfUpdate = self.createLiveEvent(xmlCode)
                    waitingToPlay = False
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not update Live event, Error: ' + str(e)}

            # play video when last video close to complete. This may take some tweaking depending on delay.
            if ((self.totalDuration - int(elapsedTime)) < self.secondsLeftPlayingNextVideo):
                # if there are no more videos to load to Live, this is the last video to play.
                # set flag to false so that the while loop is set to false and it stops looping
                if (not flagEventFinished):
                    flagForLastPlay = False
                # start the event in Live
                try:
                    pendingEventID = self.getCurrentPendingEventID()
                    if (not pendingEventID.isdigit()):
                        return {'statusCode': '400', "body": 'Could not get current pending event id'}
                    resultOfStart = self.startLiveEvent(pendingEventID)
                    waitingToPlay = True
                    if (resultOfStart.status_code != 200):
                        return {'statusCode': '400', "body": resultOfStart.content}
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not start Live Event, Error: ' + str(e)}
                # This gets the duration for the next video that is playing.
                # it returns true if the duration was successful and false if it wasn't
                # If statement check if this is the last video to be played, and if so, set flagEventFinished to false to jump out of while loop.
                try:
                    flagEventFinished = self.addToTotalDurationForOneVideo()
                    if (not flagForLastPlay):
                        flagEventFinished = False
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

                # add the event id to the list of event id's to delete later. Wait 1 second so it gives Live time to start it.
                try:
                    time.sleep(1)
                    eventRunning = self.getCurrentRunningEventID()
                    if (not eventRunning.isdigit()):
                        return {'statusCode': '400', "body": 'Could not get current running event id'}
                    self.listOfEventIds.append(eventRunning)
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not get Event ID, Error: ' + str(e)}

            # ping every second
            time.sleep(1)

        return {'statusCode': '200'}

    def deleteEvents(self):
        # delete the events when there are no more running or pending events left.
        # this uses the list of event Id's from earlier and goes through and deletes them.
        # timer in there so that it give Live enough time to do the deletion
        index = 0
        runningPendingEvents = True
        while (runningPendingEvents):
            resultOfEvents = self.getLiveEventForFrontEnd()
            runningEvent = resultOfEvents["running"]
            pendingEvent = resultOfEvents["pending"]

            if (runningEvent == "" and pendingEvent == ""):
                time.sleep(2)
                tempID = self.listOfEventIds[index]
                try:
                    self.deleteLiveEvent(tempID)
                    index += 1
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not Delete events, Error: ' + str(e)}

            if (index >= len(self.listOfEventIds)):
                runningPendingEvents = False

        return {'statusCode': '200'}

    def convertSendStartInitialLiveEvent(self, xml, uuid):
        xmlConverterService = XMLGenerator()
        # get the live xml from the bxf xml with the correct profile id
        try:
            createEventXML = xmlConverterService.convertEvent(xml, uuid, self.outPutPath)
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
            self.EVENT_ID = self.getCurrentEventId()
            if (not self.EVENT_ID.isdigit()):
                return {'statusCode': '400', "body": 'Could not get the Current event ID'}
            self.listOfEventIds.append(self.EVENT_ID)
            resultOfStart = self.startLiveEvent(self.EVENT_ID)
            if (resultOfStart.status_code != 200):
                return {'statusCode': '400', "body": resultOfStart.content}
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not start Live Event, Error: ' + str(e)}

        return {'statusCode': '200'}

    def setListOfInputTimes(self, xml):
        # get the start/end/duration times for each video from converter service
        xmlConverterService = XMLGenerator()
        try:
            bxfxml = re.sub('\\sxmlns="[^"]+"', '', xml, count=1)  # prevents namespaces
            root = (ET.fromstring(bxfxml)).find('.//BxfData/Schedule')
            self.listOfInputTimes = xmlConverterService.parseEvents(root)
            self.sizeOfCurrentUUID = len(self.listOfInputTimes)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get start/end times from BXF .xml, Error: ' + str(e)}

        return {'statusCode': '200'}

    def setInitialTotalDuration(self):
        """
                get the duration of the first video
                If there is no first video, then there is no duration and set everything to 0
        """
        if ((self.sizeOfCurrentUUID - 1) < self.indexOfCurrentUUID):
            return
        try:
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours = 0
                minutes = 0
                seconds = 0
            else:
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
                duration1 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
                hours, minutes, seconds = map(int, duration1.split(':'))
                self.indexOfCurrentUUID += 1
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

        #convert to seconds
        self.totalDuration = (hours * 3600) + (minutes * 60) + seconds
        return {'statusCode': '200'}

    def addToTotalDurationForOneVideo(self):
        # get video duration for the next video
        #If there is no next video, then set duration to 0 and return false
        flagToJumpOutOfLoop = True
        if ((self.sizeOfCurrentUUID - 1) < self.indexOfCurrentUUID):
            return False
        try:
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours = 0
                minutes = 0
                seconds = 0
                flagToJumpOutOfLoop = False
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
                duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
                hours, minutes, seconds = map(int, duration2.split(':'))
                self.indexOfCurrentUUID += 1
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

        self.totalDuration = (hours * 3600) + (minutes * 60) + seconds
        return flagToJumpOutOfLoop

    def storebxffile(self, filename, xml_file):
        if (not isinstance(filename, basestring)):
            return {'statusCode': '400', 'body': 'filename must be a string'}
        return self.s3service.storexml(self.bxfstorage, filename=filename, xml_file=xml_file)

    def deleteLiveEvent(self, eventID):
        liveservice = LiveService()
        self.EVENT_ID = self.getCurrentEventId()
        if (not self.EVENT_ID.isdigit()):
            return {'statusCode': '400', "body": 'Could not get the Current event ID'}
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
        # get and set live event id
        self.EVENT_ID = self.getCurrentEventId()
        if (not self.EVENT_ID.isdigit()):
            return {'statusCode': '400', "body": 'Could not get the Current event ID'}
        results = liveservice.updatePlaylist(self.EVENT_ID, convertedxml)
        return results

    def getLiveEvent(self, eventID):
        live = LiveService()
        return live.getLiveEvent(eventID)

    def getLiveEventForFrontEnd(self):
        """
        Retrieves the currently running event and a list of all the pending events.
        Assumes that there is only one running event besides the one named "Redirect"
        and there is one video per event. UUID is found under the certificate_file tag
        in the input section.
        :return: UUIDs for the running event and a comma-separated
                 list of all the pending events.
        """
        live = LiveService()

        try:
            # Extract the UUID for the running event
            runningEventUUID = ''
            runningEvent = live.getLiveEvents('running')
            root = ET.fromstring(runningEvent.content)
            for event in root.iter('live_event'):
                name = event.find('name')
                if name.text != 'Redirect':
                    input = event.find('input')
                    fileInput = input.find('file_input')
                    tempID = fileInput.find('certificate_file')
                    runningEventUUID = tempID.text.replace("urn:uuid:", "")

            # Concatenate all pending event UUIDs in a comma-separated list
            pendingEventUUIDs = ''
            pendingEvents = live.getLiveEvents('pending')
            root = ET.fromstring(pendingEvents.content)
            for event in root.iter('live_event'):
                input = event.find('input')
                fileInput = input.find('file_input')
                tempID = fileInput.find('certificate_file')
                pendingEventUUIDs += tempID.text.replace("urn:uuid:", "")
                pendingEventUUIDs += ','

        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get UUIDs from running or pending events' + str(e)}

        return {'statusCode': '200', 'running': runningEventUUID, 'pending': pendingEventUUIDs}

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
            return {'statusCode': '400', 'body': 'Failed to get Current Event ID. Be sure that Event has been created Error: ' + str(e)}
        return event

    def getElapsedInSeconds(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            elapsedText = root.find('elapsed')
            return elapsedText.text
        except Exception as e:
            return {'statusCode': '400','body': 'Failed to get Elapsed time. Error: ' + str(e)}

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

    def getCurrentPendingEventID(self):
        #gets the event id of the most recent pending event
        live = LiveService()
        try:
            results = live.getLiveEvents("pending")
            root = ET.fromstring(results.content)
            child = root.find('live_event')
            href = child.get('href')
            #strip off the /live_events/ to just get the event number
            event = href[13:]
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get current running Live event, Error: ' + str(e)}
        return event

    # This function was needed when we were adding video inputs for one event.
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

    # If working with profile, This gets the id of the profile
    def parseProfileID(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            href = root.get('href')
            # strip off the /live_events_profile/ to just get the event number
            event = href[21:]
        except Exception as e:
            return {'statusCode': '400', 'body': 'Failed to get Profile ID. Error: ' + str(e)}
        return event

sched = SchedulerController()
res = sched.inputxml("<?xml version='1.0'?><BxfMessage><BxfData action='add'><Schedule action='add' ScheduleEnd='2017-08-17T21:06:01.026Z' ScheduleStart='2017-08-17T20:56:53.026Z' ScheduleId='fcdef9e0-7614-401e-9fc2-01834de2e81a' type='Primary'><Channel action='add' type='digital_television' outOfBand='true' shortName='Default Name' ca='false' status='active' channelNumber='0-1'/><ScheduleName>Default Name</ScheduleName><ScheduledEvent><EventData action='add' eventType='primary'><EventId><EventId>urn:uuid:fed86d46-bfef-4799-a662-fe5c7382f030</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>1</SegmentNumber><ProgramName>big</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate=''><SmpteTimeCode>2017-08-17T20:56:53.026Z</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate='30'><SmpteTimeCode>00:01:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Duration</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>big_buck_bunny.mp4</HouseNumber></ContentId><Name>big</Name><Description>program description</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080p</Format><AspectRatio>16:9</AspectRatio></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed='true' fileTransferAllowed='true'><PathName>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</PathName></AssetServer></Location></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData action='add' eventType='primary'><EventId><EventId>urn:uuid:88d37a88-08fd-41bd-b53a-7376affe6c19</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>2</SegmentNumber><ProgramName>big2</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate=''><SmpteTimeCode>2017-08-17T20:57:53.026Z</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate='30'><SmpteTimeCode>00:01:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Duration</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>big_buck_bunny.mp4</HouseNumber></ContentId><Name>big2</Name><Description>program description</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080p</Format><AspectRatio>16:9</AspectRatio></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed='true' fileTransferAllowed='true'><PathName>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</PathName></AssetServer></Location></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData action='add' eventType='primary'><EventId><EventId>urn:uuid:916c5133-5d9c-44b9-b28a-456ac92da65a</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>3</SegmentNumber><ProgramName>cat</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate=''><SmpteTimeCode>2017-08-17T20:58:53.026Z</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate='30'><SmpteTimeCode>00:03:36</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Duration</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>nyan-cat-sample.mp4</HouseNumber></ContentId><Name>cat</Name><Description>program description</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080p</Format><AspectRatio>16:9</AspectRatio></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed='true' fileTransferAllowed='true'><PathName>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/nyan-cat-sample.mp4</PathName></AssetServer></Location></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData action='add' eventType='primary'><EventId><EventId>urn:uuid:3e260f42-f25a-4c1e-8fa7-9d83da184bea</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>4</SegmentNumber><ProgramName>rick</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate=''><SmpteTimeCode>2017-08-17T21:02:29.026Z</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate='30'><SmpteTimeCode>00:03:32</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Duration</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>Rick Astley - Never Gonna Give You Up [HQ].mp4</HouseNumber></ContentId><Name>rick</Name><Description>program description</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080p</Format><AspectRatio>16:9</AspectRatio></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed='true' fileTransferAllowed='true'><PathName>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/Rick%20Astley%20-%20Never%20Gonna%20Give%20You%20Up%20%5BHQ%5D.mp4</PathName></AssetServer></Location></MediaLocation></Media></Content></ScheduledEvent></Schedule></BxfData></BxfMessage>", "path")
#res = sched.inputxml("<?xml version='1.0'?><BxfMessage><BxfData action='add'><Schedule action='add' ScheduleEnd='2017-08-18T17:47:44.951Z' ScheduleStart='2017-08-18T17:43:08.951Z' ScheduleId='41678f6c-bc25-40d5-be04-876fa68add9a' type='Primary'><Channel action='add' type='digital_television' outOfBand='true' shortName='Default Name' ca='false' status='active' channelNumber='0-1'/><ScheduleName>Default Name</ScheduleName><ScheduledEvent><EventData action='add' eventType='primary'><EventId><EventId>urn:uuid:4286f3a6-4f3b-43b5-bce8-7d6e1ab8498f</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>1</SegmentNumber><ProgramName>jkj</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate=''><SmpteTimeCode>2017-08-18T17:43:08.951Z</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate='30'><SmpteTimeCode>00:01:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Duration</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>big_buck_bunny.mp4</HouseNumber></ContentId><Name>jkj</Name><Description>program description</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080p</Format><AspectRatio>16:9</AspectRatio></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed='true' fileTransferAllowed='true'><PathName>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/big_buck_bunny.mp4</PathName></AssetServer></Location></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData action='add' eventType='primary'><EventId><EventId>urn:uuid:5f2e3beb-66e3-457e-a1f4-c7a0baf796ed</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>2</SegmentNumber><ProgramName>jkhk</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate=''><SmpteTimeCode>2017-08-18T17:44:08.951Z</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate='30'><SmpteTimeCode>00:03:36</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Duration</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>nyan-cat-sample.mp4</HouseNumber></ContentId><Name>jkhk</Name><Description>program description</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080p</Format><AspectRatio>16:9</AspectRatio></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed='true' fileTransferAllowed='true'><PathName>https://s3-us-west-2.amazonaws.com/pdxteamdkrakatoa/nyan-cat-sample.mp4</PathName></AssetServer></Location></MediaLocation></Media></Content></ScheduledEvent></Schedule></BxfData></BxfMessage>", "path")
print res