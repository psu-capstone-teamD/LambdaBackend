import xml.etree.ElementTree as ET
from StringIO import StringIO



class XMLGenerator:

    def run(self, bxfXML, currentVideoUUID):
        tree = ET.ElementTree(bxfXML)
        root = self.iteratetoSchedule(self.stripNameSpace(tree.getroot()))
        metadata = self.parseMetadata(root)
        events = self.nextNevents(2, self.parseEvents(root), currentVideoUUID)
        liveXML = self.generateXML(metadata, events)
        liveString = self.filetostring(liveXML.getroot())
        return liveString

    def generateXML(self, metadata, events):
        ET.Element('?xml version="1.0" encoding="UTF-8"?')
        eventHeader = ET.Element("live_event")
        ET.SubElement(eventHeader, "name").text = metadata['name']
        for event in events:
            inputHeader = ET.SubElement(eventHeader, "input")
            ET.SubElement(inputHeader, "name").text = event['uid']
            ET.SubElement(inputHeader, "order").text = str(event['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            ET.SubElement(fileHeader, "uri").text = event['uri']
        ET.SubElement(eventHeader, "node_id").text = "3"
        ET.SubElement(eventHeader, "profile").text = "11"
        return ET.ElementTree(eventHeader)

    def iteratetoSchedule(self, root):
        return root.find('.//BxfData/Schedule')

    # Extract all necessary metadata about the live event from the BXF file.
    # @param root: The root element of the BXF tree.
    # @return: A dictionary with a key for each piece of metadata.
    def parseMetadata(self, root):
        metadata = {}
        metadata["name"] = root.find("./ScheduleName").text
        return metadata

    # Extract all events from the BXF file.
    # @param root: The root element of the BXF tree.
    # @return: A list of all video inputs. Each input is a dictionary
    #          that includes information about the input, including the
    #          UUID, order, URI, and event type.
    def parseEvents(self, root):
        events = []
        i = 1
        for xmlevent in root.findall("./ScheduledEvent"):
            event = {}
            event["eventType"] = xmlevent.find("./EventData").attrib.get('eventType')
            event["uid"] = xmlevent.find("./EventData/EventId/EventId").text
            event["order"] = i
            event["uri"] = xmlevent.find("./Content/Media/MediaLocation/Location/AssetServer/PathName").text
            events.append(event)
            i += 1
        return events

    # Exclude all inputs except the subsequent n after the currently streaming video.
    # @param n: Number of inputs to include in the live XML.
    # @param events: List of all inputs in the BXF file.
    # @param currentVideoUUID: UUID of the currently streaming video.
    # @return: A list of the next n events or fewer.
    def nextNevents(self, n, events, currentVideoUUID):
        for i in range(len(events)):
            if events[i]["uid"] == currentVideoUUID:
                return [events[i + j] for j in range(1, n + 1) if (i + j) < len(events)]
        return []

    def filetostring(self, root):
        return ET.tostring(root, encoding='utf8', method='xml')

    def stripNameSpace(self, xmlstr):
        it = ET.iterparse(StringIO(xmlstr))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        return it.root

    def writetofile(self, liveXML):
        ET.ElementTree.write(liveXML, "testLiveXML.xml", encoding='utf-8', xml_declaration=True)
