# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, robust parser for S6F11, built on the user-provided rules.
    1. A[16] is always the timestamp.
    2. PortID is always a small integer.
    3. PortStatus is always alphabetic.
    """
    data = {}
    
    # --- START OF HIGHLIGHTED FINAL FIX ---

    # Universal Step 1: Find all integer values to identify key markers.
    uints = [int(val) for val in re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)]
    if len(uints) < 3: return {}
    
    try:
        ceid, rptid = uints[1], uints[2]
    except (ValueError, IndexError):
        return {}

    # Universal Step 2: Populate base data.
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''): data['AlarmID'] = ceid
    
    if rptid not in RPTID_MAP: return data
    data['RPTID'] = rptid

    # Universal Step 3: Isolate the report body (everything after the RPTID tag).
    rptid_tag_match = re.search(r'(<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>)', full_text)
    if not rptid_tag_match: return data
    start_index = rptid_tag_match.end()
    report_body = full_text[start_index:]
    
    # Step 4: Rule #1 - Extract the Timestamp based on the A[16] pattern.
    timestamp_match = re.search(r"<A\s\[16\]\s'([^']*)'>", report_body)
    if timestamp_match:
        data['ReportTimestamp'] = timestamp_match.group(1)

    # Step 5: Extract all OTHER primitive values (the real data payload).
    # This regex finds all A or U tags that are NOT <A[16]...>.
    data_tokens = re.findall(r"<(A)(?!\s\[16\])\s\[\d+\]\s'([^']*)'|<(U\d)\s\[\d+\]\s(\d+)>", report_body)
    
    flat_payload = []
    for (a_tag, a_val, u_tag, u_val) in data_tokens:
        if a_tag: flat_payload.append(a_val)
        if u_tag: flat_payload.append(u_val)

    # Step 6: Map the clean data payload to our simplified schema from config.
    field_names = RPTID_MAP.get(rptid, [])
    for i, name in enumerate(field_names):
        if i < len(flat_payload):
            value = flat_payload[i]
            
            # Step 7: Rule #2 & #3 - Validate data types before assigning.
            if name == 'PortID' and value.isdigit() and len(value) < 3:
                data[name] = value
            elif name == 'PortStatus' and value.isalpha():
                data[name] = value
            elif name not in ['PortID', 'PortStatus']:
                # For all other fields, assign directly.
                data[name] = value

    # --- END OF HIGHLIGHTED FINAL FIX ---
            
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
        if ("Core:Send" in log_type or "Core:Receive" in log_type) and i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1
            data_block_lines = []
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
