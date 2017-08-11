import uuid
from services.S3Service.S3Service import S3Service
from services.LiveService.LiveService import LiveService
import xml.etree.ElementTree as ET
import time
from services.XMLConverterService.XMLConverterService import XMLGenerator



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
            profileXML = xmlConverterService.convertProfile(bxfXML=xml, profileName=self.profileName)
        except Exception as e:
            return self.xmlError
        try:
            profileResult = self.createLiveProfile(profileXML)
            if(profileResult.status_code != 201):
                return {'statusCode': '400', "body": profileResult.content}
            self.profileID = self.parseProfileID(profileResult)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Create Live Profile, Error: ' + str(e) + profileResult.content}

        try:
            createScheduleXML = xmlConverterService.convertSchedule(xml, self.profileID)
            print createScheduleXML
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Convert Schedule .xml, Error: ' + str(e) + createScheduleXML}

        try:
            resultCreateSchedule = self.createLiveSchedule(createScheduleXML)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not Create Schedule in Live, Error: ' + str(e) + resultCreateSchedule.content}

        try:
            tree = ET.ElementTree(xml)
            root = xmlConverterService.iteratetoSchedule(xmlConverterService.stripNameSpace(tree.getroot()))
            self.listOfInputTimes = xmlConverterService.parseEvents(root)
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not get start/end times from BXF .xml, Error: ' + str(e)}

        #add the first 2 videos durations to the total duration
        try:
            self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
            duration1 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
            hours1, minutes1, seconds1, frames = map(int, duration1.split(':'))
            self.indexOfCurrentUUID += 1
            if(self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours2 = 0
                minutes2 = 0
                seconds2 = 0
            if(self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
                duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
                hours2, minutes2, seconds2, frames = map(int, duration2.split(':'))
                self.indexOfCurrentUUID += 1
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not parse input duration times, Error: ' + str(e)}

        totalHours = hours1 + hours2
        totalMinutes = minutes1 + minutes2
        totalSeconds = seconds1 + seconds2
        self.totalDuration = (totalHours * 3600) + (totalMinutes * 60) + totalSeconds

        flagEventFinished = True

        while(flagEventFinished):
            resultXML = self.getLiveEvent()
            elapsedTime = self.getElapsedInSeconds(resultXML)

            if((int(elapsedTime) - self.totalDuration) < 30):
                try:
                    xmlCode = xmlConverterService.convertUpdate(xml, self.currentUUID)
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not convert .xml, Error: ' + str(e)}
                try:
                    resultOfUpdate = self.updateLiveEvent(xmlCode)
                except Exception as e:
                    return {'statusCode': '400', "body": 'Could not update Live event, Error: ' + str(e) + resultOfUpdate.content}

            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours2 = 0
                minutes2 = 0
                seconds2 = 0
                flagEventFinished = False
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
                duration2 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
                hours2, minutes2, seconds2, frames = map(int, duration2.split(':'))
                self.indexOfCurrentUUID += 1
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') == None):
                hours1 = 0
                minutes1 = 0
                seconds1 = 0
                flagEventFinished = False
            if (self.listOfInputTimes[self.indexOfCurrentUUID].get('uid') != None):
                self.currentUUID = self.listOfInputTimes[self.indexOfCurrentUUID].get('uid')
                duration1 = self.listOfInputTimes[self.indexOfCurrentUUID].get('duration')
                hours1, minutes1, seconds1, frames = map(int, duration1.split(':'))
                self.indexOfCurrentUUID += 1

            totalHours = hours1 + hours2
            totalMinutes = minutes1 + minutes2
            totalSeconds = seconds1 + seconds2
            self.totalDuration += (totalHours * 3600) + (totalMinutes * 60) + totalSeconds

        try:
            resultOfDelete = self.deleteLiveEvent()
            return resultOfDelete
        except Exception as e:
            return {'statusCode': '400', "body": 'Could not delete Live event, Error: ' + str(e) + resultOfUpdate.content}

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

    def parseProfileID(self, xml_code):
        try:
            root = ET.fromstring(xml_code.content)
            href = root.get('href')
            # strip off the /live_events_profile/ to just get the event number
            event = href[21:]
        except Exception as e:
            return "StatusCode: 400: Failed to get Current Event ID. Be sure that Event has been created"

        return event

sched = SchedulerController()
result = sched.inputxml('<?xml version="1.0" encoding="ISO-8859-1"?><BxfMessage xmlns="http://smpte-ra.org/schemas/2021/2008/BXF" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:pmcp="http://www.atsc.org/XMLSchemas/pmcp/2007/3.1" id="urn:uuid:6d7a271f-7fd8-40f2-9b3b-329ee4c2afcd" dateTime="2011-09-07T11:49:34.22" messageType="Information" origin="Traffic System" originType="Traffic" userName="Traffic System User" destination="Automation" xsi:schemaLocation="http://smpte-ra.org/schemas/2021/2008/BXF BxfSchema.xsd"><BxfData action="add"><Schedule type="Primary" scheduleId="urn:uuid:7af7ac59-57b2-4d40-9ace-0dc337e534a6" scheduleStart="2011-09-07T00:00:00.00" scheduleEnd="2011-09-07T23:59:46.05" action="add"><Channel channelNumber="0-1" status="active" type="digital_television" ca="false" shortName="WBCC" outOfBand="true" action="add"><pmcp:Name lang="eng" action="add">WBCC CHANNEL TV68/DT68-1</pmcp:Name></Channel><ScheduleName>WBCC_09072011_1315410574</ScheduleName><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:058ff320-2044-4c71-9f90-f6ef3234f53a</EventId></EventId><PrimaryEvent><ProgramEvent><SegmentNumber>0</SegmentNumber><ProgramName>GROWING A GREENER WORLD</ProgramName></ProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:26:46:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Fixed</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>50006</HouseNumber></ContentId><Name>GROWING A GREENER WORLD</Name><Description>GROWING A GREENER WORLD</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>1080i</Format><AspectRatio>16:9</AspectRatio><PrivateInformation><ScreenFormatText>HD-FF</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:15:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:26:46:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content><ContentType>0</ContentType><Series><SeriesName>GROWING A GREENER WORLD</SeriesName><EpisodeName>BACKYARD CHICKENS (RALEIGH, NC &amp; LOS ANGELES, CA)</EpisodeName><EpisodeCode>210</EpisodeCode></Series></ScheduledEvent><ScheduledEvent><EventData eventType="NonPrimary" action="add"><EventId><EventId>urn:uuid:e618de18-9787-445f-ab4f-f0f7764ad1a7</EventId></EventId><NonPrimaryEvent><NonPrimaryEventName>SI</NonPrimaryEventName><PrimaryEventId>urn:uuid:058ff320-2044-4c71-9f90-f6ef3234f53a</PrimaryEventId><Offset offsetFrom="BeginningofEvent" offsetType="Start" direction="Positive"><OffsetTime><SmpteTimeCode>00:01:00:00</SmpteTimeCode></OffsetTime></Offset><Macros><MacroName>LOGO4               </MacroName></Macros><NonProgramEvents><Details><SpotType>SI</SpotType></Details></NonProgramEvents></NonPrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:01:00:00</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:24:46:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>LOGO4</HouseNumber></ContentId><Name>STATION BUG - TRANSPARENT</Name><Description>STATION BUG - TRANSPARENT</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:24:46:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="NonPrimary" action="add"><EventId><EventId>urn:uuid:60d273d1-fcc5-474d-b518-5c54dc510699</EventId></EventId><NonPrimaryEvent><NonPrimaryEventName>SI</NonPrimaryEventName><PrimaryEventId>urn:uuid:058ff320-2044-4c71-9f90-f6ef3234f53a</PrimaryEventId><Offset offsetFrom="BeginningofEvent" offsetType="Start" direction="Positive"><OffsetTime><SmpteTimeCode>00:25:46:00</SmpteTimeCode></OffsetTime></Offset><Macros><MacroName>LOGO4               </MacroName></Macros><NonProgramEvents><Details><SpotType>SI</SpotType></Details></NonProgramEvents></NonPrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:25:46:00</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:24:46:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>LOGO4OFF</HouseNumber></ContentId><Name>STATION BUG - TRANSPARENT</Name><Description>STATION BUG - TRANSPARENT</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:24:46:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:b3c3e3fe-280c-43fd-830a-8abe838e6f8e</EventId></EventId><PrimaryEvent><NonProgramEvent><Details><SpotType>FI</SpotType></Details></NonProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:26:46:00</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>207-94</HouseNumber></ContentId><Name>NEW BEGINNINGS SD C4V6B</Name><Description>NEW BEGINNINGS SD C4V6B</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>16:9</AspectRatio><PrivateInformation><ScreenFormatText>SD-LB</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:57d6bdf4-a5f3-4756-9bc6-b09819cd1bc9</EventId></EventId><PrimaryEvent><NonProgramEvent><Details><SpotType>FI</SpotType></Details></NonProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:27:16:00</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>206-324</HouseNumber></ContentId><Name>BCC FACULTY PROMO - PAT FULLER 30 C1V1</Name><Description>BCC FACULTY PROMO - PAT FULLER 30 C1V1</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:8c702615-f1f6-428e-a8e2-4f88f596659d</EventId></EventId><PrimaryEvent><NonProgramEvent><Details><SpotType>FI</SpotType></Details></NonProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:27:46:00</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:00:59:28</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>207-115</HouseNumber></ContentId><Name>BCC WILL MAKE YOU MOVE</Name><Description>BCC WILL MAKE YOU MOVE</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:00:59:28</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:740f8073-da93-4231-b7c7-fe69527d3d90</EventId></EventId><PrimaryEvent><NonProgramEvent><Details><SpotType>FI</SpotType></Details></NonProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:28:45:28</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>206-214</HouseNumber></ContentId><Name>B - HANNAH ALLEN @ BEACH</Name><Description>B - HANNAH ALLEN @ BEACH</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:2e001c0e-6548-4fd8-a388-fcc5461b6aab</EventId></EventId><PrimaryEvent><NonProgramEvent><Details><SpotType>FI</SpotType></Details></NonProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:29:15:28</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>206-247</HouseNumber></ContentId><Name>A - FACULTY SUSAN PHILLIPS CUT 1</Name><Description>A - FACULTY SUSAN PHILLIPS CUT 1</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:00:30:00</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent><ScheduledEvent><EventData eventType="Primary" action="add"><EventId><EventId>urn:uuid:b6d99b03-4baa-47c7-a6e9-fb002cd3552f</EventId></EventId><PrimaryEvent><NonProgramEvent><Details><SpotType>ID</SpotType></Details></NonProgramEvent></PrimaryEvent><StartDateTime><SmpteDateTime broadcastDate="2011-09-07"><SmpteTimeCode>00:29:45:28</SmpteTimeCode></SmpteDateTime></StartDateTime><LengthOption><Duration><SmpteDuration frameRate="30"><SmpteTimeCode>00:00:14:02</SmpteTimeCode></SmpteDuration></Duration></LengthOption><StartMode>Follow</StartMode><EndMode>Duration</EndMode><Transitions><VideoTransitions><TransitionOutType>Cut</TransitionOutType><TransitionOutRate>Medium</TransitionOutRate></VideoTransitions></Transitions></EventData><Content><ContentId><HouseNumber>3-6</HouseNumber></ContentId><Name>NEW ID #6 (:10 - :30)</Name><Description>NEW ID #6 (:10 - :30)</Description><Media><PrecompressedTS><TSVideo><DigitalVideo>true</DigitalVideo><Format>480i</Format><AspectRatio>4:3</AspectRatio><PrivateInformation><ScreenFormatText>SD-FF</ScreenFormatText></PrivateInformation></TSVideo><TSCaptioning>true</TSCaptioning></PrecompressedTS><MediaLocation><Location><AssetServer playoutAllowed="true" fileTransferAllowed="true"><PathName>http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4</PathName><ReferenceName/></AssetServer></Location><SOM><SmpteTimeCode>00:00:00:00</SmpteTimeCode></SOM><Duration><SmpteDuration><SmpteTimeCode>00:00:14:02</SmpteTimeCode></SmpteDuration></Duration></MediaLocation></Media></Content></ScheduledEvent></Schedule></BxfData></BxfMessage>')
