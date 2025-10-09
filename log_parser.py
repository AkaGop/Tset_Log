# log_parser.py

# log_parser.py

import re
from io import StringIO

KNOWLEDGE_BASE = {
    "ceid_map": {
        11: "GemEquipmentOFFLINE", 12: "GemControlStateLOCAL", 13: "GemControlStateREMOTE",
        14: "GemMsgRecognition", 16: "GemPPChangeEvent", 30: "GemProcessStateChange",
        101: "AlarmClear", 102: "AlarmSet", 113: "AlarmSet", 114: "AlarmSet", 18: "AlarmSet",
        120: "IDRead", 121: "UnloadedFromMag_OR_LoadedToTool", 127: "LoadedToTool",
        131: "LoadToToolCompleted", 132: "UnloadFromToolCompleted", 136: "MappingCompleted",
        141: "PortStatusChange", 151: "MagazineDocked", 180: "RequestMagazineDock",
        181: "MagazineDocked", 182: "MagazineUndocked", 183: "RequestOperatorIdCheck",
        184: "RequestOperatorLogin", 185: "RequestMappingCheck",
    },
    "secs_map": {
        "S1F1": "Are You There Request", "S1F2": "Are You There Data",
        "S1F3": "Selected Equipment Status Request", "S1F4": "Selected Equipment Status Data",
        "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
        "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
    }
}

def _parse_secs_data_block(raw_data_block):
    """A more robust parser for the raw SECS-II data block string."""
    if not raw_data_block:
        return {}

    data = {}
    full_text = "".join(raw_data_block)

    # Find all Unsigned Integers and check if they are a known CEID or AlarmID
    uint_matches = re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)
    for val_str in uint_matches:
        val = int(val_str)
        if val in KNOWLEDGE_BASE["ceid_map"]:
            if "Alarm" in KNOWLEDGE_BASE["ceid_map"][val]:
                if 'AlarmID' not in data: # Grab the first one we see
                    data['AlarmID'] = val
            else:
                if 'CEID' not in data: # Grab the first one we see
                    data['CEID'] = val

    # Find Remote Commands
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'", full_text)
    if rcmd_match:
        data['RCMD'] = rcmd_match.group(1)

    # Find specific key-value pairs
    patterns = {
        'OperatorID': r"'OPERATORID'\s*>\s*<A\[\d+\]\s*'([^']*)'",
        'MagazineID': r"'MAGAZINEID'\s*>\s*<A\[\d+\]\s*'([^']*)'",
        'Result': r"'RESULT'\s*>\s*<U1\[\d+\]\s*(\d)",
        'LotID': r"'LOTID'\s*>\s*<A\[\d+\]\s*'([^']*)'",
        'PortStatus': r"<A\s\[3\]\s*'(\w+)'"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            if key == 'Result':
                data[key] = "Success" if value == '0' else f"Failure({value})"
            else:
                data[key] = value
                
    return data

def parse_log_file(uploaded_file):
    events = []
    if not uploaded_file:
        return events

    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        lines = stringio.readlines()
    except Exception:
        stringio = StringIO(uploaded_file.getvalue().decode("latin-1", errors='ignore'))
        lines = stringio.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header_match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        
        if not header_match:
            i += 1
            continue
        
        timestamp_str, log_type, message_part = header_match.groups()
        
        msg_name_match = re.search(r"MessageName=(\w+)", message_part) or re.search(r"Message=.*?:\'(\w+)\'", message_part)
        msg_name = msg_name_match.group(1) if msg_name_match else "N/A"

        data_block_lines = []
        if ("Core:Send" in log_type or "Core:Receive" in log_type):
            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                j = i + 1
                while j < len(lines) and lines[j].strip() != '.':
                    data_block_lines.append(lines[j])
                    j += 1
                i = j
        
        # We process every line now, but only add 'details' if something is parsed.
        event = {
            "timestamp": timestamp_str,
            "log_type": log_type,
            "msg_name": msg_name,
        }

        if data_block_lines:
            parsed_details = _parse_secs_data_block(data_block_lines)
            if parsed_details: # Only add the 'details' key if the dictionary is not empty
                event['details'] = parsed_details
        
        events.append(event)
        i += 1
            
    return events

