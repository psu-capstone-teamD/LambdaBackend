import xml.etree.ElementTree as ET
from StringIO import StringIO
import xml.dom.minidom as minidom
from generateXML import XMLGenerator


def main():
    xmlService = xmlConverterService()

    with open('test_BXF/BXFshort.xml', 'r') as infile:
        bxf = infile.read()

    xmlService.bxfToLive(bxf)

def main2():
    xmlService = xmlConverterService()

    with open('test_BXF/BXFshort.xml', 'r') as infile:
        bxf = infile.read()

    xmlService.bxfToLiveUpdate(bxf, "urn:uuid:e618de18-9787-445f-ab4f-f0f7764ad1a7")

class xmlConverterService:

    def bxfToLive(self, bxf):

        # bxf string -> xml tree object
        tree = ET.ElementTree(ET.fromstring(bxf))
        root = self.iterateToSchedule(self.stripNamespace(self.fileToString(tree.getroot())))

        # extract metadata and events
        metadata = self.extractMetadata(root)
        events = self.extractEvents(root)

        # generate live XML with all the relevant information
        xmlgenerator = XMLGenerator()
        liveXML = xmlgenerator.generateLiveEvent(metadata, events)
        liveXML.write('test_LiveXML/liveXML.xml', encoding='utf-8', xml_declaration=True)

        # print converted live XML
        roughString = ET.tostring(liveXML.getroot(), 'utf-8')
        reparsed = minidom.parseString(roughString)
        print reparsed.toprettyxml(indent="\t")

        return self.fileToString(liveXML.getroot())

    def bxfToLiveUpdate(self, bxf, currentVideoUUID):

        # bxf string -> xml tree
        tree = ET.ElementTree(ET.fromstring(bxf))
        root = self.iterateToSchedule(self.stripNamespace(self.fileToString(tree.getroot())))

        # extract metadata and events
        metadata = self.extractMetadata(root)
        events = self.nextTwoEvents(self.extractEvents(root), currentVideoUUID)

        # generate live XML with all the relevant information
        xmlgenerator = XMLGenerator()
        liveXML = xmlgenerator.generateLiveEvent(metadata, events)
        liveXML.write('test_LiveXML/liveXMLUpdate.xml', encoding='utf-8', xml_declaration=True)

        # print converted live XML
        roughString = ET.tostring(liveXML.getroot(), 'utf-8')
        reparsed = minidom.parseString(roughString)
        print reparsed.toprettyxml(indent="\t")

        return self.fileToString(liveXML.getroot())

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

    def iterateToSchedule(self, root):
        return root.find('.//BxfData/Schedule')

    def fileToString(self, aroot):
        return ET.tostring(aroot, encoding='utf8', method='xml')

    def stripNamespace(self, xmlstr):
        it = ET.iterparse(StringIO(xmlstr))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        return it.root


if __name__ == '__main__':
    #main()
    main2()
