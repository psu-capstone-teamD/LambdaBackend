import xml.etree.ElementTree as ET
from StringIO import StringIO


class XMLGenerator:

    def convertSchedule(self, bxfXML, profileID):
        """
        Create a schedule in Live XML from a BXF file. This can be
        used for creating new schedules or updating old ones.
        :param bxfXML: BXF file as a string.
        :param profileID: Required profile ID.
        :return: XML for a schedule.
        """
        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        metadata = self.parseMetadata(root)
        events = self.nextNevents(2, self.parseEvents(root), None)
        liveXML = self.generateSchedule(profileID, metadata, events)
        return ET.tostring(liveXML.getroot(), encoding='utf8', method='xml')

    def convertUpdate(self, bxfXML, currentVideoUUID):
        """
        Create an updated playlist for a live event. Only includes videos that
        are pending after the currently streaming video.
        :param bxfXML: BXF file as a string.
        :param currentVideoUUID: UUID of the currently streaming video.
        :return: XML for a modified live event playlist.
        """
        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        events = self.nextNevents(2, self.parseEvents(root), currentVideoUUID)
        liveXML = self.generateUpdate(events)
        return ET.tostring(liveXML.getroot(), encoding='utf8', method='xml')

    def convertProfile(self, bxfXML, videoUUID, profileName):
        """
        Create a new profile for one event in a BXF playlist. The returned
        XML can be used for creating new profiles or updating old ones.
        :param bxfXML: BXF file as a string.
        :param videoUUID: UUID of one video input.
        :param profileNAme: Unique name for the profile.
        :return: XML for a live event profile.
        """
        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        config = self.parseConfig(root, videoUUID)
        liveXML = self.generateProfile(profileName, config)
        return ET.tostring(liveXML.getroot(), encoding='utf8', method='xml')

    def generateSchedule(self, profileID, metadata, events):
        """
        Generates an XML tree with all necessary tags for a schedule.
        :param profileID: Required Profile ID.
        :param metadata: Name, start and end times for the schedule.
        :param events: List of all inputs to be included in the scheduled live event.
        :return: ElementTree object for the schedule.
        """
        eventHeader = ET.Element("schedule")
        ET.SubElement(eventHeader, "name").text = metadata['name']
        ET.SubElement(eventHeader, "node_id").text = "3"
        ET.SubElement(eventHeader, "profile").text = str(profileID)
        ET.SubElement(eventHeader, "start_time").text = metadata['startTime'] # TODO use start and end modes
        ET.SubElement(eventHeader, "end_time").text = metadata['endTime']
        for event in events:
            inputHeader = ET.SubElement(eventHeader, "input")
            ET.SubElement(inputHeader, "order").text = str(event['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            ET.SubElement(fileHeader, "certificate_file").text = event['uid']
            ET.SubElement(fileHeader, "uri").text = event['uri']
        return ET.ElementTree(eventHeader)

    def generateUpdate(self, inputs):
        """
        Generates an XML tree for a live event playlist update.
        :param inputs: New list of all modified inputs in the correct order.
        :return: ElementTree object for the playlist update.
        """
        eventHeader = ET.Element("inputs")
        for input in inputs:
            inputHeader = ET.SubElement(eventHeader, "input")
            ET.SubElement(inputHeader, "order").text = str(input['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            ET.SubElement(fileHeader, "certificate_file").text = input['uid']
            ET.SubElement(fileHeader, "uri").text = input['uri']
        return ET.ElementTree(eventHeader)

    def generateProfile(self, profileName, config):
        """
        Generate an XML tree for a live event profile.
        :param profileName: Unique name for the profile.
        :param config: configurations for the aspect ratio and resolution.
        :return: Element tree object for the new profile.
        """
        profileHeader = ET.Element("live_event_profile")
        ET.SubElement(profileHeader, "name").text = profileName
        failureRule = ET.SubElement(profileHeader, "failure_rule")
        ET.SubElement(failureRule, "priority").text = "50"
        ET.SubElement(failureRule, "restart_on_failure").text = "false"
        streamAssembly = ET.SubElement(profileHeader, "stream_assembly")
        ET.SubElement(streamAssembly, "name").text = "SA1"
        videoDescription = ET.SubElement(streamAssembly, "video_description")
        ET.SubElement(videoDescription, "codec").text = "h.264"
        ET.SubElement(videoDescription, "height").text = "1080"  #TODO adjust aspect ratio to width & height
        ET.SubElement(videoDescription, "width").text = "1920"
        h264Settings = ET.SubElement(videoDescription, "h264_settings")
        ET.SubElement(h264Settings, "bitrate").text = "5000000"    #TODO convert resolution to bitrate
        outputGroup = ET.SubElement(profileHeader, "output_group")
        ET.SubElement(outputGroup, "type").text = "apple_live_group_settings"
        ALGsettings = ET.SubElement(outputGroup, "apple_live_group_settings")
        ET.SubElement(ALGsettings, "cdn").text = "Basic_PUT"
        destination = ET.SubElement(ALGsettings, "destination")
        ET.SubElement(destination, "uri").text = "https://yanexx65s8e1.live.elementalclouddev.com/in_put/test"
        output = ET.SubElement(outputGroup, "output")
        ET.SubElement(output, "name_modifier").text = "output1"
        ET.SubElement(output, "stream_assembly_name").text = "SA1"
        ET.SubElement(output, "container").text = "m3u8"
        return ET.ElementTree(profileHeader)

    def parseMetadata(self, root):
        """
        Extract all necessary metadata about the live event from the BXF file.
        :param root: The root element of the BXF tree.
        :return: A dictionary with a key for each piece of metadata.
        """
        metadata = {}
        metadata["name"] = root.find("./ScheduleName").text
        metadata["startTime"] = root.attrib['scheduleStart']
        metadata["endTime"] = root.attrib['scheduleEnd']
        return metadata

    def parseEvents(self, root):
        """
        Extract all events from the BXF file.
        :param root: The root element of the BXF tree.
        :return: A list of all video inputs. Each input is a dictionary that includes
        information about the input, including the UUID, order, URI, and event type.
        """
        events = []
        i = 1
        for xmlevent in root.findall("./ScheduledEvent"):
            event = {}
            event["eventType"] = xmlevent.find("./EventData").attrib.get('eventType')
            event["startMode"] = xmlevent.find("./EventData/StartMode").text
            event["endMode"] = xmlevent.find("./EventData/EndMode").text
            event["uid"] = xmlevent.find("./EventData/EventId/EventId").text
            event["order"] = i
            event["uri"] = xmlevent.find("./Content/Media/MediaLocation/Location/AssetServer/PathName").text
            events.append(event)
            i += 1
        return events

    def parseConfig(self, root, videoUUID):
        """
        Extract configurations for one selected video.
        :param root: The root element of the BXF tree.
        :param videoUUID: ID for the desired input.
        :return: configurations for the video with the matching UUID
        """
        config = {}
        for xmlevent in root.findall("./ScheduledEvent"):
            if videoUUID == xmlevent.find("./EventData/EventId/EventId").text:
                config["screenRes"] = xmlevent.find("./Content/Media/PrecompressedTS/TSVideo/Format").text
                config["aspectRatio"] = xmlevent.find("./Content/Media/PrecompressedTS/TSVideo/AspectRatio").text
        return config

    def nextNevents(self, n, events, currentVideoUUID):
        """
        Exclude all inputs except the subsequent n after the currently streaming video.
        :param n: Number of inputs to include in the live XML.
        :param events: List of all inputs in the BXF file.
        :param currentVideoUUID: UUID of the currently streaming video.
        :return: A list of the next n events or fewer.
        """
        if not currentVideoUUID:
            currentVideoUUID = events[0]["uid"]
        for i in range(len(events)):
            if events[i]["uid"] == currentVideoUUID:
                return [events[i + j] for j in range(1, n + 1) if (i + j) < len(events)]
        # TODO throw error if video not found
        return []

    def iteratetoSchedule(self, root):
        return root.find('.//BxfData/Schedule')

    def stripNameSpace(self, xmlstr):
        """Removes the namespace code preceding every line of the XML document.
        :param xmlstr: String representation of xml.
        :return: The root of the xml tree without the namespaces attached.
        """
        it = ET.iterparse(StringIO(xmlstr))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        return it.root

    def writetofile(self, liveXML):
        ET.ElementTree.write(liveXML, "testLiveProfile.xml", encoding='utf-8', xml_declaration=True)