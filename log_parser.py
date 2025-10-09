# log_parser.py

import re
from io import StringIO
from config import KNOWLEDGE_BASE  # Import from the central config file

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
                if 'AlarmID' not in data:
                    data['AlarmID'] = val
            else:
                if 'CEID' not in data:
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
        
        event = {
            "timestamp": timestamp_str,
            "log_type": log_type,
            "msg_name": msg_name,
        }

        if data_block_lines:
            parsed_details = _parse_secs_data_block(data_block_lines)
            if parsed_details:
                 event['details'] = parsed_details
        
        events.append(event)
        i += 1
            
    return events
