import xml.etree.ElementTree as ET
from StringIO import StringIO

class XMLGenerator:

    def run(self, bxfXML):
        tree = ET.ElementTree(bxfXML)
        firstroot = tree.getroot()
        root = self.iteratetoSchedule(self.stripNameSpace(firstroot))
        events = self.parse(root)
        liveXML = self.generateXML(events)
        liveString = self.filetostring(liveXML.getroot())
        return liveString

    def generateXML(self, events):
        xmlInfo = '?xml version="1.0" encoding="UTF-8"?'
        infoHeader = ET.Element(xmlInfo)
        eventHeader = ET.Element("live_event")
        nameHeader = ET.SubElement(eventHeader, "name").text = events[0]
        for event in events[1:]:
            inputHeader = ET.SubElement(eventHeader, "input")
            orderTag = ET.SubElement(inputHeader, "order").text = str(event['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            uriInfo = ET.SubElement(fileHeader, "uri").text = event['uri']
            uidInfo = ET.SubElement(fileHeader, "certificate_file").text = event['uid']
        nodeInfo = ET.SubElement(eventHeader, "node_id").text = "3"
        profileInfo = ET.SubElement(eventHeader, "profile").text = "11"

        liveXML = ET.ElementTree(eventHeader)
        return liveXML

    def writetofile(self, liveXML):
        ET.ElementTree.write(liveXML, "testliveXML.xml")

    def iteratetoSchedule(self, root):
        return root.find('.//BxfData/Schedule')

    def parse(self, root):
        events = []
        events.append(root.find("./ScheduleName").text)
        i = 1
        for xmlevent in root.findall("./ScheduledEvent"):
            event = {}
            event["order"] = i
            event["eventType"] = xmlevent.find("./EventData").attrib.get('eventType')
            event["uri"] = xmlevent.find("./Content/Media/MediaLocation/Location/AssetServer/PathName").text
            event["uid"] = xmlevent.find("./EventData/EventId/EventId").text
            i = i + 1
            events.append(event)
        return events

    def filetostring(self, aroot):
        xmlstr = ET.tostring(aroot, encoding='utf8', method='xml')
        return xmlstr

    def stripNameSpace(self, xmlstr):
        it = ET.iterparse(StringIO(xmlstr))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        root = it.root
        return root

    def writetofile(self, liveXML):
        ET.ElementTree.write(liveXML, "testbxfXML.xml")
