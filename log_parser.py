# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_secs_data(msg_name, data_block_lines):
    """
    Master function to delegate parsing based on the SECS message name.
    """
    full_text = "".join(data_block_lines)
    
    if msg_name == 'S6F11':
        return _parse_s6f11_report(full_text)
    elif msg_name == 'S2F49':
        return _parse_s2f49_command(full_text)
    
    return {} # Return empty dict for message types we don't parse

def _parse_s6f11_report(full_text: str) -> dict:
    """Parses S6F11 Event Reports based on their RPTID."""
    data = {}
    uints = re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)
    
    if len(uints) < 2: return {}

    ceid = int(uints[1])
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP[ceid]: data['AlarmID'] = ceid

    if len(uints) >= 3:
        rptid = int(uints[2])
        if rptid in RPTID_MAP:
            data['RPTID'] = rptid
            # Simplified, non-greedy regex to find the data list following the RPTID
            match = re.search(r'<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>\s*<L\[\d+\]\s*([\s\S]*?)>\s*>', full_text)
            if match:
                body = match.group(1)
                values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", body)
                flat_values = [s if s else i for s, i in values]
                field_names = RPTID_MAP.get(rptid, [])
                for i, name in enumerate(field_names):
                    if i < len(flat_values):
                        data[name] = flat_values[i]
    return data

def _parse_s2f49_command(full_text: str) -> dict:
    """Parses S2F49 Remote Commands."""
    data = {}
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'", full_text)
    if rcmd_match: data['RCMD'] = rcmd_match.group(1)
        
    lotid_match = re.search(r"'LOTID'\s*>\s*<A\[\d+\]\s*'([^']*)'", full_text, re.IGNORECASE)
    if lotid_match: data['LotID'] = lotid_match.group(1)
    
    panels_match = re.search(r"'LOTPANELS'\s*>\s*<L\s\[(\d+)\]", full_text, re.IGNORECASE)
    if panels_match: data['PanelCount'] = int(panels_match.group(1))
        
    return data

def parse_log_file(uploaded_file):
    """Main parsing function. Iterates through the log file line by line."""
    events = []
    if not uploaded_file: return events
    
    try: stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    except UnicodeDecodeError: stringio = StringIO(uploaded_file.getvalue().decode("latin-1", errors='ignore'))
    
    lines = stringio.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header_match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not header_match: i += 1; continue
        
        timestamp, log_type, message_part = header_match.groups()
        
        msg_match = re.search(r"MessageName=(\w+)|Message=.*?:\'(\w+)\'", message_part)
        msg_name = (msg_match.group(1) or msg_match.group(2)) if msg_match else "N/A"
        
        event = {"timestamp": timestamp, "log_type": log_type, "msg_name": msg_name}
        
        if ("Core:Send" in log_type or "Core:Receive" in log_type) and i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1
            data_block_lines = []
            while j < len(lines) and lines[j].strip() != '.':
                data_block_lines.append(lines[j]); j += 1
            i = j
            
            if data_block_lines:
                details = _parse_secs_data(msg_name, data_block_lines)
                if details: event['details'] = details
        
        events.append(event)
        i += 1
    return events
