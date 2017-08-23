from GenerateXML import *
import re


class XMLGenerator:

    def iterateToSchedule(self, bxfXML):
        """
        Iterates to the Schedule tag of the BXF file and removes default namespaces.
        :param bxfXML: BXF file as a string.
        :return: The root element of the bxf XML tree.
        """
        bxfXML = re.sub('\\sxmlns="[^"]+"', '', bxfXML, count=1)    # remove namespace
        return (ET.fromstring(bxfXML)).find('.//BxfData/Schedule')

    def convertEvent(self, bxfXML, uuid, outputPath):
        """
        Create a new live event without a profile.
        :param bxfXML: BXF file as a string.
        :param uuid: UUID of the currently streaming event. Can be set to None.
        :param outputPath: The destination address for the stream.
        :return: XML for a live event without a profile.
        """
        root = self.iterateToSchedule(bxfXML)
        metadata = self.parseMetadata(root)
        try:
            events = self.nextEvent(self.parseEvents(root), uuid)
        except RuntimeError:
            return "Error: Could not find the next event."
        liveXML = generateEvent(metadata, events, outputPath)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def convertEventWithProfile(self, bxfXML, profileID, uuid):
        """
        Create a new live event using a profile.
        :param bxfXML: BXF file as a string.
        :param profileID: Required profile ID.
        :param uuid: UUID of the currently streaming event. Can be set to None.
        :return: XML for a live event with profile number.
        """
        root = self.iterateToSchedule(bxfXML)
        metadata = self.parseMetadata(root)
        try:
            events = self.nextEvent(self.parseEvents(root), uuid)
        except RuntimeError:
            return "Error: Could not find the next event."
        liveXML = generateEventWithProfile(metadata, events, profileID)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def convertSchedule(self, bxfXML, profileID):
        """
        Create a schedule in Live XML from a BXF file. This can be
        used for creating new schedules or updating old ones.
        :param bxfXML: BXF file as a string.
        :param profileID: Required profile ID.
        :return: XML for a schedule.
        """
        root = self.iterateToSchedule(bxfXML)
        metadata = self.parseMetadata(root)
        try:
            events = self.nextNevents(None, self.parseEvents(root), None)
        except RuntimeError:
            return "Error: Could not find the next event."
        liveXML = generateSchedule(profileID, metadata, events)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def convertUpdate(self, bxfXML, currentVideoUUID):
        """
        Create an updated playlist for a live event. Only includes videos that
        are pending after the currently streaming video.
        :param bxfXML: BXF file as a string.
        :param currentVideoUUID: UUID of the currently streaming video.
        :return: XML for a modified live event playlist.
        """
        root = self.iterateToSchedule(bxfXML)
        try:
            events = self.nextNevents(1, self.parseEvents(root), currentVideoUUID)
        except RuntimeError:
            return "Error: Could not find the next events."
        liveXML = generateUpdate(events)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def convertProfile(self, bxfXML, profileName):
        """
        Create a new profile for one event in a BXF playlist. The returned
        XML can be used for creating new profiles or updating old ones.
        :param bxfXML: BXF file as a string.
        :param profileName: Unique name for the profile.
        :return: XML for a live event profile.
        """
        liveXML = generateProfile(profileName)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

    def createRedirect(self, streamURL, deltaURL):
        """
        Create a live event that uses a UDP network input and an Apple HLS output to Delta.
        :param deltaURL: The URL for the master manifest file in Delta.
        :return: XML for a redirect live event as a string.
        """
        liveXML = genertateRedirect(deltaURL)
        return ET.tostring(liveXML.getroot(), encoding='UTF-8', method='xml')

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
            event["order"] = str(i)
            event["uri"] = xmlevent.find("./Content/Media/MediaLocation/Location/AssetServer/PathName").text
            event["startTime"] = xmlevent.find("./EventData/StartDateTime/SmpteDateTime/SmpteTimeCode").text
            event["duration"] = xmlevent.find("./EventData/LengthOption/Duration/SmpteDuration/SmpteTimeCode").text
            event["endTime"] = event["startTime"] + event["duration"]
            events.append(event)
            i += 1
        return events

    def nextEvent(self, events, currentVideoUUID):
        """
        Exclude all inputs except the next event after the currently streaming video.
        :param events: List of all inputs in the BXF file.
        :param currentVideoUUID: UUID of the currently streaming video. If set to None,
               the first video in the list is chosen.
        :return: A list of one event, the next event to stream.
        """
        if not currentVideoUUID:
            return [events[0]]
        for i in range(len(events)):
            if events[i]["uid"] == currentVideoUUID:
                if events[i+1]:
                    return [events[i+1]]
        return []

    def nextNevents(self, n, events, currentVideoUUID):
        """
        Exclude all inputs except the subsequent n after the currently streaming video.
        :param n: Number of inputs to include in the live XML. If this value is None,
               all events are returned.
        :param events: List of all inputs in the BXF file.
        :param currentVideoUUID: UUID of the currently streaming video.
        :return: A list of the next n events or fewer.
        """
        if not n:
            return events
        for i in range(len(events)):
            if events[i]["uid"] == currentVideoUUID:
                return [events[i + j] for j in range(1, n + 1) if (i + j) < len(events)]
        return []

    def elementsEqual(self, e1, e2):
        """
        Check if all elements in an ElementTree object are equal.
        :param e1: Root element of the first tree.
        :param e2: Root element of the second tree.
        :return: True - equal, False - not equal.
        """
        if e1.tag != e2.tag or e1.text != e2.text or e1.attrib != e2.attrib:
            return False
        return all(self.elementsEqual(c1, c2) for c1, c2 in zip(e1, e2))

    def validateXML(self, bxfXML):
        """
        Verify if a string has a well-formed xml structure.
        :param bxfXML: BXF file as a string.
        :return: Status code 200 for valid or 400 for not valid.
        """
        try:
            ET.fromstring(bxfXML)
        except ET.ParseError:
            return "StatusCode: 400: Not valid XML structure"
        return "StatusCode: 200"