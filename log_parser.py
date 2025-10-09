# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_event_report(full_text):
    """Parses S6F11 Event Reports based on their RPTID."""
    data = {}
    
    # 1. Extract the CEID - this is always the second U4 in an S6F11
    uints = re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)
    if len(uints) >= 2:
        ceid = int(uints[1])
        if ceid in CEID_MAP:
            data['CEID'] = ceid
            if "Alarm" in CEID_MAP[ceid]:
                data['AlarmID'] = ceid # Use CEID as AlarmID for alarm events
    else:
        return {} # Not a valid S6F11

    # 2. Extract the RPTID - this is the third U4
    if len(uints) >= 3:
        rptid = int(uints[2])
        if rptid in RPTID_MAP:
            data['RPTID'] = rptid
            
            # 3. Extract all data values within the report list
            # Find the list that follows the RPTID
            report_body_match = re.search(r'<U\d\s\[\d+\]\s' + str(rptid) + r'>\s*<L\s\[(\d+)\]\s*([\s\S]*)', full_text)
            if report_body_match:
                num_items = int(report_body_match.group(1))
                report_body = report_body_match.group(2)
                
                # Extract all ASCII '<A...>' and Unsigned Int '<U...>' values in order
                values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", report_body)
                
                # The regex returns tuples of (string_match, int_match). Combine them.
                flat_values = [s if s else i for s, i in values]

                # 4. Map values to names using our RPTID_MAP
                field_names = RPTID_MAP[rptid]
                for i in range(min(len(field_names), len(flat_values))):
                    data[field_names[i]] = flat_values[i]
    return data

def _parse_remote_command(full_text):
    """Parses S2F49 Remote Commands."""
    data = {}
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'", full_text)
    if rcmd_match:
        data['RCMD'] = rcmd_match.group(1)
        
    lotid_match = re.search(r"'LOTID'\s*>\s*<A\[\d+\]\s*'([^']*)'", full_text, re.IGNORECASE)
    if lotid_match:
        data['LotID'] = lotid_match.group(1)
        
    # Count how many panel IDs are listed in the 'LOTPANELS' list
    lotpanels_match = re.search(r"'LOTPANELS'\s*>\s*<L\s\[(\d+)\]", full_text, re.IGNORECASE)
    if lotpanels_match:
        data['PanelCount'] = int(lotpanels_match.group(1))

    return data

def parse_log_file(uploaded_file):
    events = []
    if not uploaded_file: return events

    try: stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    except Exception: stringio = StringIO(uploaded_file.getvalue().decode("latin-1", errors='ignore'))
    
    lines = stringio.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header_match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        
        if not header_match: i += 1; continue
        
        timestamp_str, log_type, message_part = header_match.groups()
        
        msg_name_match = re.search(r"MessageName=(\w+)|Message=.*?:\'(\w+)\'", message_part)
        msg_name = msg_name_match.group(1) or msg_name_match.group(2) if msg_name_match else "N/A"

        data_block_lines = []
        if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1
            while j < len(lines) and lines[j].strip() != '.':
                data_block_lines.append(lines[j]); j += 1
            i = j
        
        event = {"timestamp": timestamp_str, "log_type": log_type, "msg_name": msg_name}

        if data_block_lines:
            details = {}
            if msg_name == 'S6F11':
                details = _parse_event_report(data_block_lines)
            elif msg_name == 'S2F49':
                details = _parse_remote_command(data_block_lines)
            
            if details: event['details'] = details
        
        events.append(event)
        i += 1
            
    return events
