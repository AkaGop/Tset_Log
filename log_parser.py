# log_parser.py

# log_parser.py

import re
from io import StringIO

# --- KNOWLEDGE BASE (Derived from Hirata Manuals) ---
# This helps us translate IDs into human-readable names.
KNOWLEDGE_BASE = {
    "ceid_map": {
        11: "GemEquipmentOFFLINE",
        12: "GemControlStateLOCAL",
        13: "GemControlStateREMOTE",
        14: "GemMsgRecognition",
        16: "GemPPChangeEvent",
        30: "GemProcessStateChange",
        101: "AlarmClear",
        102: "AlarmSet",
        121: "UnloadedFromMag_OR_LoadedToTool", # Note: This ID is used for multiple events
        131: "LoadToToolCompleted",
        132: "UnloadFromToolCompleted",
        136: "MappingCompleted",
        141: "PortStatusChange",
        151: "MagazineDocked",
        181: "MagazineDocked", # Duplicate entry is fine, maps to same event
        182: "MagazineUndocked",
        183: "RequestOperatorIdCheck",
        184: "RequestOperatorLogin",
        185: "RequestMappingCheck",
    },
    "secs_map": {
        "S1F1": "Are You There Request", "S1F2": "Are You There Data",
        "S1F3": "Selected Equipment Status Request", "S1F4": "Selected Equipment Status Data",
        "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
        "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
    }
}

def _parse_secs_data_block(raw_data_block):
    """Parses a raw SECS-II data block string to extract key values."""
    if not raw_data_block:
        return {}

    extracted_data = {}

    # Pattern to find any Unsigned Integer and check if it's a known CEID
    # <U4 [1] 181> -> finds 181
    ceid_matches = re.findall(r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", raw_data_block)
    for potential_ceid in ceid_matches:
        if int(potential_ceid) in KNOWLEDGE_BASE["ceid_map"]:
            extracted_data['CEID'] = int(potential_ceid)
            # Once we find the CEID, we can stop looking for it.
            break
    
    # Pattern to find a Remote Command (RCMD)
    # <A [9] 'LOADSTART'> -> finds LOADSTART
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'\s*>", raw_data_block)
    if rcmd_match:
        extracted_data['RCMD'] = rcmd_match.group(1)

    # Dictionary of specific patterns to find common data points
    patterns = {
        'OperatorID': r"'OPERATORID'>\s*<A\s*\[\d+\]\s*'(\w+)'",
        'MagazineID': r"'MAGAZINEID'>\s*<A\s*\[\d+\]\s*'([\w-]+)'",
        'Result': r"'RESULT'>\s*<U1\s*\[\d+\]\s*(\d+)>",
        'LotID': r"'LOTID'>\s*<A\s*\[\d+\]\s*'([\d\.]+)'",
        'PortStatus': r"<A\s*\[3\]\s*'(\w+)'", # For events like PortStatusChange
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw_data_block, re.IGNORECASE) # Ignore case for robustness
        if match:
            value = match.group(1)
            if key == 'Result':
                # Translate result code into human-readable format
                extracted_data[key] = "Success" if value == '0' else f"Failure({value})"
            else:
                extracted_data[key] = value

    return extracted_data


def parse_log_file(uploaded_file):
    """
    Reads an uploaded file and parses it into a structured list of events.
    """
    events = []
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    lines = stringio.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header_match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        
        if not header_match:
            i += 1
            continue
        
        timestamp_str, log_type, message_part = header_match.groups()
        
        msg_name_match = re.search(r"MessageName=(\w+)", message_part) or \
                         re.search(r"Message=.*?:\'(\w+)\'", message_part)
        msg_name = msg_name_match.group(1) if msg_name_match else "N/A"

        data_block_lines = []
        if "Core:Send" in log_type or "Core:Receive" in log_type:
            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                j = i + 1
                while j < len(lines) and lines[j].strip() != '.':
                    data_block_lines.append(lines[j])
                    j += 1
                i = j
        
        raw_data_block = "".join(data_block_lines)
        
        # --- NEW PART ---
        # Parse the raw data block to get structured data
        parsed_data = _parse_secs_data_block(raw_data_block)
event_data = {
    "timestamp": timestamp_str,
    "log_type": log_type,
    "msg_name": msg_name,
}

# If a data block was found and parsed, add the details to the event.
if raw_data_block:
    parsed_data = _parse_secs_data_block(raw_data_block)
    # We only add the details key if the parser found something meaningful
    if parsed_data:
         event_data["details"] = parsed_data

events.append(event_data)


        
        i += 1
        
    return events
