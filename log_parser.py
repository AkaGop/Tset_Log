# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _find_enclosed_list(text):
    """A helper function to find the content of a single, top-level <L[...]...> block."""
    match = re.search(r"<\s*L\s*\[\d+\]\s*([\s\S]*)", text, re.DOTALL)
    if not match:
        return ""
    
    body = match.group(1).strip()
    open_brackets = 1
    for i, char in enumerate(body):
        if char == '<':
            open_brackets += 1
        elif char == '>':
            open_brackets -= 1
        
        if open_brackets == 0:
            return body[:i]
    return ""

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, robust, and structurally-aware parser for S6f11.
    This version correctly isolates the data payload by navigating the list structure.
    """
    data = {}
    
    # --- START OF FINAL, CORRECTED LOGIC ---

    # Step 1: Isolate the main <L,3> body of the S6F11 message.
    main_body = _find_enclosed_list(full_text)
    if not main_body: return {}

    # Step 2: Extract the top-level items. We expect two <U...> tags and one <L...> block.
    # This regex is specific and robust for this task.
    top_items = re.findall(r"<\s*(?:U\d)\s*\[\d+\]\s*(\d+)\s*>|<\s*(L)\s*\[\d+\]\s*([\s\S]*)", main_body, re.DOTALL)
    
    if len(top_items) < 3: return {}

    try:
        ceid = int(top_items[1][0]) # Second item is the CEID
        
        # The third item is the report list block.
        report_list_body = top_items[2][2] 
    except (ValueError, IndexError):
        return {}
    
    # Find the RPTID within the report list block
    rptid_match = re.search(r'<\s*U\d\s*\[\d+\]\s*(\d+)\s*>', report_list_body)
    if not rptid_match: return {}
    rptid = int(rptid_match.group(1))

    # Step 3: Populate data and validate against schemas.
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''): data['AlarmID'] = ceid

    if rptid in RPTID_MAP:
        data['RPTID'] = rptid
    else:
        return data

    # Step 4: Isolate the final data payload. It's the list that FOLLOWS the RPTID.
    rptid_tag = rptid_match.group(0)
    start_index = report_list_body.find(rptid_tag) + len(rptid_tag)
    payload_text = report_list_body[start_index:]
    
    payload_body = _find_enclosed_list(payload_text)

    # Step 5: Tokenize ONLY the final, isolated payload.
    values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", payload_body)
    flat_values = [s if s else i for s, i in values]
    
    # Step 6: Map to schema.
    field_names = RPTID_MAP.get(rptid, [])
    for i, name in enumerate(field_names):
        if i < len(flat_values):
            data[name] = flat_values[i]
            
    # --- END OF FINAL, CORRECTED LOGIC ---

    return data

# The other functions remain the same.
def _parse_s2f49_command(full_text: str) -> dict:
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
