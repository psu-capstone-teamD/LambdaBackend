import xml.etree.ElementTree as ET
from StringIO import StringIO
from generateXML import XMLGenerator


class xmlConverterService:

    def __init__(self):
        self.xmlgenerator = XMLGenerator()

    def bxfToLive(self, bxf):
        # bxf string -> xml tree object
        tree = ET.ElementTree(ET.fromstring(bxf))
        root = self.iterateToSchedule(self.stripNamespace(self.fileToString(tree.getroot())))

        # extract metadata and events
        metadata = self.extractMetadata(root)
        events = self.extractEvents(root)

        # generate live XML with all the relevant information
        liveXML = self.xmlgenerator.generateLiveEvent(metadata, events)
        return self.fileToString(liveXML.getroot())

    def bxfToLiveUpdate(self, bxf, currentVideoUUID):
        # bxf string -> xml tree object
        tree = ET.ElementTree(ET.fromstring(bxf))
        root = self.iterateToSchedule(self.stripNamespace(self.fileToString(tree.getroot())))

        # extract metadata and the next two events after the currently streaming video
        metadata = self.extractMetadata(root)
        events = self.nextTwoEvents(self.extractEvents(root), currentVideoUUID)

        # generate live XML with all the relevant information
        liveXML = self.xmlgenerator.generateLiveEvent(metadata, events)
        return self.fileToString(liveXML.getroot())

    # Exclude all events except the subsequent two after a particular event.
    def nextTwoEvents(self, events, currentVideoUUID):
        next2Events = []
        for i in range(len(events)):
            if events[i]["name"] == currentVideoUUID:
                try:
                    next2Events.append(events[i+1])
                    next2Events.append(events[i+2])
                except IndexError:
                    return next2Events
        return next2Events

    def extractMetadata(self, root):
        metadata = {}
        metadata["name"] = root.find("./ScheduleName").text
        return metadata

    def extractEvents(self, root):
        events = []
        i = 1
        for xmlevent in root.findall("./ScheduledEvent"):
            event = {}
            event["name"] = xmlevent.find("./EventData/EventId/EventId").text
            event["order"] = i
            event["eventType"] = xmlevent.find("./EventData").attrib.get('eventType')
            event["uri"] = xmlevent.find("./Content/Media/MediaLocation/Location/AssetServer/PathName").text
            i += 1
            events.append(event)
        return events

    def iterateToSchedule(self, root):
        return root.find('.//BxfData/Schedule')

    def fileToString(self, root):
        return ET.tostring(root, encoding='utf8', method='xml')

    def stripNamespace(self, xmlstr):
        it = ET.iterparse(StringIO(xmlstr))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        return it.root
