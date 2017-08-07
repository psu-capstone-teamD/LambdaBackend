import xml.etree.ElementTree as ET
from StringIO import StringIO


class XMLGenerator:

    def run(self, bxfXML, currentVideoUUID = None):
        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        metadata = self.parseMetadata(root)
        events = self.nextNevents(2, self.parseEvents(root), currentVideoUUID)
        liveXML = self.generateXML(metadata, events)
        liveString = self.filetostring(liveXML.getroot())
        return liveString

    def generateXML(self, metadata, events):
        eventHeader = ET.Element("live_event")
        ET.SubElement(eventHeader, "name").text = metadata['name']
        for event in events:
            inputHeader = ET.SubElement(eventHeader, "input")
            ET.SubElement(inputHeader, "name").text = event['uid']
            ET.SubElement(inputHeader, "order").text = str(event['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            ET.SubElement(fileHeader, "uri").text = event['uri']

            # Need to know exactly how the following information is used in the live XML. For now just adding it as
            # a subelement of each individual input.

            ET.SubElement(inputHeader, "screen_resolution").text = event['screenRes']
            ET.SubElement(inputHeader, "aspect_ratio").text = event['aspectRatio']
            ET.SubElement(inputHeader, "start_mode").text = event['startMode']
            ET.SubElement(inputHeader, "end_mode").text = event['endMode']
        ET.SubElement(eventHeader, "node_id").text = "3"
        ET.SubElement(eventHeader, "profile").text = "11"
        return ET.ElementTree(eventHeader)

    def iteratetoSchedule(self, root):
        return root.find('.//BxfData/Schedule')

    def parseMetadata(self, root):
        """
        Extract all necessary metadata about the live event from the BXF file.
        :param root: The root element of the BXF tree.
        :return: A dictionary with a key for each piece of metadata.
        """
        metadata = {}
        metadata["name"] = root.find("./ScheduleName").text
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
            event["uid"] = xmlevent.find("./EventData/EventId/EventId").text
            event["order"] = i
            event["uri"] = xmlevent.find("./Content/Media/MediaLocation/Location/AssetServer/PathName").text
            event["screenRes"] = xmlevent.find("./Content/Media/PrecompressedTS/TSVideo/Format").text
            event["aspectRatio"] = xmlevent.find("./Content/Media/PrecompressedTS/TSVideo/AspectRatio").text
            event["startMode"] = xmlevent.find("./EventData/StartMode").text
            event["endMode"] = xmlevent.find("./EventData/EndMode").text
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
        if currentVideoUUID is not None:
            for i in range(len(events)):
                if events[i]["uid"] == currentVideoUUID:
                    return [events[i + j] for j in range(1, n + 1) if (i + j) < len(events)]
            return []
        else:
            return events

    def filetostring(self, root):
        """Returns a string representation of an XML tree element.
        :param root: the root element of the xml file.
        :return The element tree in string format
        """
        return ET.tostring(root, encoding='utf8', method='xml')

    def stripNameSpace(self, xmlstr):
        """Removes the namespace code preceding every line of the XML document.
        :param xmlstr: string representation of xml.
        :return it.root: the root of the xml tree without the namespaces attached.
        """
        it = ET.iterparse(StringIO(xmlstr))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        return it.root

    def writetofile(self, liveXML):
        ET.ElementTree.write(liveXML, "testLiveXML.xml", encoding='utf-8', xml_declaration=True)
