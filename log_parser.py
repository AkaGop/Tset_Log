# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, structurally-aware parser for S6F11.
    This version correctly parses the nested SECS-II list structure.
    """
    data = {}

    # Step 1: Find the top-level <L,3> structure of an S6F11 message.
    # We use a non-greedy capture `([\s\S]*?)` to get only the contents of the first L[3].
    top_level_match = re.search(r'<\s*L\s*\[3\]\s*([\s\S]*?)>', full_text, re.DOTALL)
    if not top_level_match:
        return {}

    body = top_level_match.group(1)

    # Step 2: Extract the top-level items: DATAID, CEID, and the Report List block.
    # This regex looks for two <U...> tags followed by a <L...> tag.
    items = re.findall(r"<\s*(U\d)\s*\[\d+\]\s*(\d+)\s*>|<\s*(L)\s*\[\d+\]\s*([\s\S]*?)>", body)
    
    if len(items) < 3:
        return {} # Must have DATAID, CEID, and Report List

    try:
        # Item 1 is DATAID (we ignore it for now)
        # Item 2 is CEID
        ceid = int(items[1][1])
        if ceid in CEID_MAP:
            data['CEID'] = ceid
            if "Alarm" in CEID_MAP.get(ceid, ''):
                data['AlarmID'] = ceid
        
        # Item 3 is the Report List block
        report_list_body = items[2][3]
        
    except (ValueError, IndexError):
        return {}

    # Step 3: Parse the Report List block. It contains one or more <L,2> reports.
    # Find the RPTID (the first U-integer in the report list)
    rptid_match = re.search(r'<\s*U\d\s*\[\d+\]\s*(\d+)\s*>', report_list_body)
    if not rptid_match:
        return data

    rptid = int(rptid_match.group(1))
    if rptid in RPTID_MAP:
        data['RPTID'] = rptid
    else:
        return data # We don't have a schema for this report.

    # Step 4: Isolate the final data payload list that follows the RPTID.
    rptid_tag = rptid_match.group(0) # The full tag, e.g., "<U4 [1] 141>"
    start_index = report_list_body.find(rptid_tag) + len(rptid_tag)
    payload_text = report_list_body[start_index:]
    
    # Step 5: Extract all primitive values from the payload.
    values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", payload_text)
    flat_values = [s if s else i for s, i in values]

    # Step 6: Map the payload values to the schema.
    field_names = RPTID_MAP.get(rptid, [])
    for i, name in enumerate(field_names):
        if i < len(flat_values):
            data[name] = flat_values[i]
            
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
