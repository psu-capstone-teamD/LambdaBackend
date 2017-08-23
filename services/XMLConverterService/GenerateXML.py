import xml.etree.ElementTree as ET
import re


def generateEventWithProfile(metadata, events, profile_id):
    """
    Generate an XML tree for a live event with a profile.
    :param events: A list of all inputs to include in the event.
    :param profileID: Unique profile identifier.
    :return: Element tree object for an event.
    """
    eventHeader = ET.Element("live_event")
    ET.SubElement(eventHeader, "name").text = metadata['name']
    ET.SubElement(eventHeader, "node_id").text = "3"
    ET.SubElement(eventHeader, "profile").text = profile_id
    input = ET.SubElement(eventHeader, "input")
    for event in events:
        ET.SubElement(input, "name").text = event['uid']
        ET.SubElement(input, "order").text = str(event['order'])
        fileInput = ET.SubElement(input, "file_input")
        ET.SubElement(fileInput, "uri").text = event['uri']
        ET.SubElement(fileInput, "certificate_file").text = event['uid']
    return ET.ElementTree(eventHeader)


def generateEvent(metadata, events, outputPath):
    """
    Generate an XML tree for a live event without a given profile.
    The output settings are set to UDP by default.
    :param events: A list of all inputs to include in the event.
    :param outputPath: Destination path for the output.
    :return: Element tree object for an event.
    """
    eventHeader = ET.Element("live_event")
    ET.SubElement(eventHeader, "name").text = metadata['name']
    ET.SubElement(eventHeader, "node_id").text = "3"
    input = ET.SubElement(eventHeader, "input")
    for event in events:
        ET.SubElement(input, "order").text = event['order']
        fileInput = ET.SubElement(input, "file_input")
        ET.SubElement(fileInput, "uri").text = event['uri']
        ET.SubElement(fileInput, "certificate_file").text = event['uid']
    failureRule = ET.SubElement(eventHeader, "failure_rule")
    ET.SubElement(failureRule, "priority").text = "50"
    ET.SubElement(failureRule, "restart_on_failure").text = "false"
    streamAssembly = ET.SubElement(eventHeader, "stream_assembly")
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
    outputGroup = ET.SubElement(eventHeader, "output_group")
    ET.SubElement(outputGroup, "type").text = "udp_group_settings"
    UDPgroupSettings = ET.SubElement(outputGroup, "udp_group_settings")
    ET.SubElement(UDPgroupSettings, "name").text = "UDPsettings"
    ET.SubElement(UDPgroupSettings, "on_input_loss").text = "drop_ts"
    output = ET.SubElement(outputGroup, "output")
    UDPsettings = ET.SubElement(output, "udp_settings")
    destination = ET.SubElement(UDPsettings, "destination")
    ET.SubElement(destination, "uri").text = "udp://127.0.0.1:4949"
    ET.SubElement(UDPsettings, "buffer_msec").text = "1000"
    ET.SubElement(UDPsettings, "max_ts_packet_count").text = "7"
    ET.SubElement(UDPsettings, "mpts_membership").text = "none"
    m2tsSettings = ET.SubElement(output, "m2ts_settings")
    ET.SubElement(m2tsSettings, "segmentation_markers").text = "none"
    ET.SubElement(m2tsSettings, "segmentation_style").text = "maintain_cadence"
    dvbSdtSettings = ET.SubElement(m2tsSettings, "dvb_sdt_settings")
    ET.SubElement(dvbSdtSettings, "output_sdt").text = "sdt_follow"
    ET.SubElement(dvbSdtSettings, "rep_interval").text = "500"
    ET.SubElement(output, "name_modifier").text = "output"
    ET.SubElement(output, "stream_assembly_name").text = "SA1"
    ET.SubElement(output, "container").text = "m2ts"
    return ET.ElementTree(eventHeader)

def genertateRedirect(deltaURL):
    """
    Generate XML for a redirect event.
    :param deltaURL: The URL for the master manifest file in Delta.
    :return: XML tree for a redirect live event.
    """

    deltaURL = re.sub(".m3u8", "", deltaURL)              # remove file type

    eventHeader = ET.Element("live_event")
    ET.SubElement(eventHeader, "name").text = "Redirect"
    ET.SubElement(eventHeader, "node_id").text = "3"
    input = ET.SubElement(eventHeader, "input")
    networkInput = ET.SubElement(input, "network_input")
    ET.SubElement(networkInput, "uri").text = "udp://127.0.0.1:4949"
    failureRule = ET.SubElement(eventHeader, "failure_rule")
    ET.SubElement(failureRule, "priority").text = "50"
    ET.SubElement(failureRule, "restart_on_failure").text = "false"
    streamAssembly = ET.SubElement(eventHeader, "stream_assembly")
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
    outputGroup = ET.SubElement(eventHeader, "output_group")
    ET.SubElement(outputGroup, "type").text = "apple_live_group_settings"
    ALGsettings = ET.SubElement(outputGroup, "apple_live_group_settings")
    ET.SubElement(ALGsettings, "cdn").text = "Basic_PUT"
    destination = ET.SubElement(ALGsettings, "destination")
    ET.SubElement(destination, "uri").text = deltaURL
    output = ET.SubElement(outputGroup, "output")
    ET.SubElement(output, "name_modifier").text = "output"
    ET.SubElement(output, "stream_assembly_name").text = "SA1"
    ET.SubElement(output, "container").text = "m3u8"
    return ET.ElementTree(eventHeader)


def generateSchedule(profileID, metadata, events):
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
    ET.SubElement(eventHeader, "start_time").text = metadata['startTime']
    ET.SubElement(eventHeader, "end_time").text = metadata['endTime']
    for event in events:
        inputHeader = ET.SubElement(eventHeader, "input")
        ET.SubElement(inputHeader, "order").text = str(event['order'])
        fileHeader = ET.SubElement(inputHeader, "file_input")
        ET.SubElement(fileHeader, "certificate_file").text = event['uid']
        ET.SubElement(fileHeader, "uri").text = event['uri']
    return ET.ElementTree(eventHeader)


def generateUpdate(inputs):
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
        ET.SubElement(audioSelector, "name").text = "audio_selector1"
        ET.SubElement(audioSelector, "default_selection").text = "false"
        ET.SubElement(audioSelector, "order").text = "1"
        ET.SubElement(audioSelector, "program_selection").text = "1"
        ET.SubElement(audioSelector, "unwrap_smpte337").text = "true"
        i += 1
    return ET.ElementTree(eventHeader)


def generateProfile(profileName):
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
    ET.SubElement(outputGroup, "type").text = "udp_group_settings"
    UDPgroupSettings = ET.SubElement(outputGroup, "udp_group_settings")
    ET.SubElement(UDPgroupSettings, "name").text = "UDPsettings"
    ET.SubElement(UDPgroupSettings, "on_input_loss").text = "drop_ts"
    output = ET.SubElement(outputGroup, "output")
    UDPsettings = ET.SubElement(output, "udp_settings")
    destination = ET.SubElement(UDPsettings, "destination")
    ET.SubElement(destination, "uri").text = "udp://127.0.0.1:4949"
    ET.SubElement(UDPsettings, "buffer_msec").text = "1000"
    ET.SubElement(UDPsettings, "max_ts_packet_count").text = "7"
    ET.SubElement(UDPsettings, "mpts_membership").text = "none"
    m2tsSettings = ET.SubElement(output, "m2ts_settings")
    ET.SubElement(m2tsSettings, "segmentation_markers").text = "none"
    ET.SubElement(m2tsSettings, "segmentation_style").text = "maintain_cadence"
    dvbSdtSettings = ET.SubElement(m2tsSettings, "dvb_sdt_settings")
    ET.SubElement(dvbSdtSettings, "output_sdt").text = "sdt_follow"
    ET.SubElement(dvbSdtSettings, "rep_interval").text = "500"
    ET.SubElement(output, "name_modifier").text = "output"
    ET.SubElement(output, "stream_assembly_name").text = "SA1"
    ET.SubElement(output, "container").text = "m2ts"
    return ET.ElementTree(profileHeader)
