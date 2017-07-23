import xml.etree.ElementTree as ET

class XMLGenerator:

    def generateLiveEvent(self, metadata, events):
        eventRoot = ET.Element("live_event")
        nameHeader = ET.SubElement(eventRoot, "name").text = metadata['name']
        for event in events:
            inputHeader = ET.SubElement(eventRoot, "input")
            nameTag = ET.SubElement(inputHeader, "name").text = event['name']
            orderTag = ET.SubElement(inputHeader, "order").text = str(event['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            uriInfo = ET.SubElement(fileHeader, "uri").text = event['uri']
        nodeInfo = ET.SubElement(eventRoot, "node_id").text = "3"
        profileInfo = ET.SubElement(eventRoot, "profile").text = "11"

        return ET.ElementTree(eventRoot)


    def generateSchedule(self, metadata, events):
        eventRoot = ET.Element("schedule")
        nameHeader = ET.SubElement(eventRoot, "name").text = metadata[0]['name']
        for event in events:
            inputHeader = ET.SubElement(eventRoot, "input")
            nameTag = ET.SubElement(fileHeader, "uri").text = event['name']
            orderTag = ET.SubElement(inputHeader, "order").text = str(event['order'])
            fileHeader = ET.SubElement(inputHeader, "file_input")
            uriInfo = ET.SubElement(fileHeader, "uri").text = event['uri']
        nodeInfo = ET.SubElement(eventRoot, "node_id").text = "3"
        profileInfo = ET.SubElement(eventRoot, "profile").text = "11"
        # TODO add timing tags

        return ET.ElementTree(eventRoot)
