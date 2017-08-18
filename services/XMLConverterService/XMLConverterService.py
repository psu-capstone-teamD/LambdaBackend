import xml.etree.ElementTree as ET
from StringIO import StringIO


class XMLGenerator:
    def convertEvent(self, bxfXML, profile_id, output_path):

        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        metadata = self.parseMetadata(root)
        events = self.parseEvents(root)
        liveXML = self.generateEvent(metadata, events, profile_id)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def nextEvent(self, bxfXML, uuid, output_path):
        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        metadata = self.parseMetadata(root)
        try:
            events = self.nextNevents(1, self.parseEvents(root), uuid)
        except RuntimeError:
            return "Error"
        liveXML = self.generateEvent(metadata, events, "11")
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

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
        try:
            events = self.nextNevents(2, self.parseEvents(root), None)
        except RuntimeError:
            return "Error"
        liveXML = self.generateSchedule(profileID, metadata, events)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

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
        try:
            events = self.nextNevents(1, self.parseEvents(root), currentVideoUUID)
        except RuntimeError:
            return "Error"
        liveXML = self.generateUpdate(events)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def convertProfile(self, bxfXML, profileName):
        """
        Create a new profile for one event in a BXF playlist. The returned
        XML can be used for creating new profiles or updating old ones.
        :param bxfXML: BXF file as a string.
        :param profileNAme: Unique name for the profile.
        :return: XML for a live event profile.
        """
        liveXML = self.generateProfile(profileName)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def generateEvent(self, metadata, events, profile_id):
        eventHeader = ET.Element("live_event")
        ET.SubElement(eventHeader, "name").text = metadata['name']
        if len(events) >= 1:
            for i in range(1):
                inputHeader = ET.SubElement(eventHeader, "input")
                ET.SubElement(inputHeader, "name").text = events[i]['uid']
                ET.SubElement(inputHeader, "order").text = str(events[i]['order'])
                fileHeader = ET.SubElement(inputHeader, "file_input")
                ET.SubElement(fileHeader, "uri").text = events[i]['uri']
        else:
            inputHeader = ET.SubElement(eventHeader, "input")
            ET.SubElement(inputHeader, "name").text = events[0]['uid']
            ET.SubElement(inputHeader, "order").text = str(events[0]['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            ET.SubElement(fileHeader, "uri").text = events[0]['uri']
        ET.SubElement(eventHeader, "node_id").text = "3"
        ET.SubElement(eventHeader, "profile").text = profile_id
        return ET.ElementTree(eventHeader)

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
        ET.SubElement(eventHeader, "start_time").text = metadata['startTime']  # TODO use start and end modes
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
        i = 1
        for input in inputs:
            inputHeader = ET.SubElement(eventHeader, "input")
            ET.SubElement(inputHeader, "order").text = str(input['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            ET.SubElement(fileHeader, "certificate_file").text = input['uid']
            ET.SubElement(fileHeader, "uri").text = input['uri']
            videoSelector = ET.SubElement(inputHeader, "video_selector")
            ET.SubElement(videoSelector, "name").text = "Capstone" + str(i)
            ET.SubElement(videoSelector, "order").text = "1"
            audioSelector = ET.SubElement(inputHeader, "audio_selector")
            #ET.SubElement(audioSelector, "name").text = "audio_selector1"
            #ET.SubElement(audioSelector, "default_selection").text = "false"
            ET.SubElement(audioSelector, "order").text = "1"
            ET.SubElement(audioSelector, "program_selection").text = "1"
            ET.SubElement(audioSelector, "unwrap_smpte337").text = "true"
            i += 1
        return ET.ElementTree(eventHeader)

    def generateProfile(self, profileName):
        """
        Generate an XML tree for a live event profile.
        :param profileName: Unique name for the profile.
        :return: Element tree object for the new profile.
        """
        profileHeader = ET.Element("live_event_profile")
        ET.SubElement(profileHeader, "name").text = profileName
        failureRule = ET.SubElement(profileHeader, "failure_rule")
        ET.SubElement(failureRule, "priority").text = "50"
        ET.SubElement(failureRule, "restart_on_failure").text = "false"
        streamAssembly = ET.SubElement(profileHeader, "stream_assembly")
        ET.SubElement(failureRule, "backup_rule").text = "none"
        ET.SubElement(streamAssembly, "name").text = "SA1"
        videoDescription = ET.SubElement(streamAssembly, "video_description")
        ET.SubElement(videoDescription, "height").text = "720"
        ET.SubElement(videoDescription, "width").text = "1280"
        ET.SubElement(videoDescription, "codec").text = "h.264"
        h264 = ET.SubElement(videoDescription, "h264_settings")
        ET.SubElement(h264, "framerate_denominator").text = "1"
        ET.SubElement(h264, "framerate_follow_source").text = "false"
        ET.SubElement(h264, "framerate_numerator").text = "30"
        ET.SubElement(h264, "gop_size").text = "60.0"
        ET.SubElement(h264, "par_denominator").text = "1"
        ET.SubElement(h264, "par_follow_source").text = "false"
        ET.SubElement(h264, "par_numerator").text = "1"
        ET.SubElement(h264, "slices").text = "4"
        ET.SubElement(h264, "level").text = "4.1"
        videoPreProcessors = ET.SubElement(videoDescription, "video_preprocessors")
        deinterlacer = ET.SubElement(videoPreProcessors, "deinterlacer")
        ET.SubElement(deinterlacer, "algorithm").text = "interpolate"
        ET.SubElement(deinterlacer, "deinterlace_mode").text = "Deinterlace"
        ET.SubElement(deinterlacer, "force").text = "false"
        ET.SubElement(h264, "bitrate").text = "2500000"
        ET.SubElement(h264, "buf_size").text = "5000000"
        audioDescription = ET.SubElement(streamAssembly, "audio_description")
        ET.SubElement(audioDescription, "audio_source_name").text = "Audio Selector 1"
        ET.SubElement(audioDescription, "audio_type").text = "0"
        ET.SubElement(audioDescription, "follow_input_audio_type").text = "true"
        ET.SubElement(audioDescription, "follow_input_language_code").text = "true"
        ET.SubElement(audioDescription, "codec").text = "aac"
        outputGroup = ET.SubElement(profileHeader, "output_group")
        ET.SubElement(outputGroup, "type").text = "apple_live_group_settings"
        ALGsettings = ET.SubElement(outputGroup, "apple_live_group_settings")
        ET.SubElement(ALGsettings, "cdn").text = "Basic_PUT"
        destination = ET.SubElement(ALGsettings, "destination")
        ET.SubElement(destination, "uri").text = "http://delta-1-yanexx65s8e5.live.elementalclouddev.com/in_put/test"
        output = ET.SubElement(outputGroup, "output")
        ET.SubElement(output, "name_modifier").text = "output"
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
        metadata["startTime"] = root.attrib['ScheduleStart']
        metadata["endTime"] = root.attrib['ScheduleEnd']
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
            event["startTime"]  = xmlevent.find("./EventData/StartDateTime/SmpteDateTime/SmpteTimeCode").text
            event["duration"] = xmlevent.find("./EventData/LengthOption/Duration/SmpteDuration/SmpteTimeCode").text
            event["endTime"] = event["startTime"] + event["duration"]
            events.append(event)
            i += 1
        return events

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

    def validateXML(self, bxf_xml):
        try:
            ET.fromstring(bxf_xml)
        except ET.ParseError:
            return "StatusCode: 400: Not valid .xml structure"
        return "StatusCode: 200"