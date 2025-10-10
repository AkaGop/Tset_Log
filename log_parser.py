# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, robust, and structurally-aware parser for S6F11 reports.
    This version correctly isolates the data payload associated with an RPTID.
    """
    data = {}
    
    # --- START OF HIGHLIGHTED FIX ---
    
    # Step 1: Extract all unsigned integers to find key markers.
    # This is a reliable way to get all potential numeric IDs.
    all_uints = re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)
    
    if len(all_uints) < 3:
        # Not a valid S6F11 for our purposes if it's missing CEID or RPTID.
        return {}

    # Step 2: Identify CEID and RPTID based on their standard positions within the S6F11 structure.
    # The first U-integer in the top-level list is DATAID, the second is CEID.
    # The first U-integer inside the nested report list is the RPTID.
    try:
        ceid = int(all_uints[1])
        rptid = int(all_uints[2])
    except (ValueError, IndexError):
        return {} # Malformed message.

    # Step 3: Populate initial data and check if we have a schema for this report.
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''):
            data['AlarmID'] = ceid
    
    if rptid not in RPTID_MAP:
        return data # We found a CEID but don't know how to parse this specific report.
    data['RPTID'] = rptid

    # Step 4: This is the CRITICAL FIX.
    # We create a regex pattern that specifically finds the RPTID tag,
    # and then captures ONLY the content of the list that immediately follows it.
    # `[\s\S]*?` is a non-greedy match for any character including newlines.
    pattern = r'<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>\s*<L\s*\[\d+\]\s*([\s\S]*?)'
    
    match = re.search(pattern, full_text)
    if not match:
        return data # Could not find the data payload for this RPTID.

    report_body = match.group(1)
    
    # Step 5: Tokenize ONLY the isolated report body. This prevents contamination from other parts of the message.
    values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", report_body)
    flat_values = [s if s else i for s, i in values]
    
    # Step 6: Map the clean payload to the field names from our config schema.
    field_names = RPTID_MAP.get(rptid, [])
    for i, name in enumerate(field_names):
        if i < len(flat_values):
            data[name] = flat_values[i]

    # --- END OF HIGHLIGHTED FIX ---
            
    return data

def _parse_s2f49_command(full_text: str) -> dict:
    """Parses S2F49 Remote Commands (This function is correct)."""
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
    lines = [line for line in stringio.readlines() if line.strip()]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header_match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not header_match: i += 1; continue
        
        timestamp, log_type, message_part = header_match.groups()
        msg_match = re.search(r"MessageName=(\w+)|Message=.*?:\'(\w+)\'", message_part)
        msg_name = (msg_match.group(1) or msg_match.group(2)) if msg_match else "N/A"
        
        event = {"timestamp": timestamp, "log_type": log_type, "msg_name": msg_name}
        
        data_block_lines = []
        if ("Core:Send" in log_type or "Core:Receive" in log_type) and i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1
            while j < len(lines) and lines[j].strip() != '.':
                data_block_lines.append(lines[j]); j += 1
            i = j
            
            if data_block_lines:
                full_data_block_text = "".join(data_block_lines)
                details = {}
                if msg_name == 'S6F11': details = _parse_s6f11_report(full_data_block_text)
                elif msg_name == 'S2F49': details = _parse_s2f49_command(full_data_block_text)
                if details: event['details'] = details
        
        if 'details' in event:
            events.append(event)
        i += 1
            
    return events
