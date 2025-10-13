# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _find_enclosed_list_and_rest(text):
    """
    A robust function to find the content of the first top-level <L[...]...> 
    block and the text that follows it. Returns a tuple of (body, rest).
    """
    match = re.search(r"<\s*L\s*\[\d+\]\s*", text)
    if not match:
        return None, None
    
    body_start = match.end()
    balance = 1
    for i in range(body_start, len(text)):
        if text[i] == '<':
            balance += 1
        elif text[i] == '>':
            balance -= 1
        
        if balance == 0:
            # Found the end of the list.
            body_end = i
            body = text[body_start:body_end]
            rest = text[body_end+1:]
            return body, rest
            
    return None, None

def _get_primitive_tokens(text_block):
    """Extracts all primitive <A...> and <U...> values from a block of text."""
    if not text_block: return []
    tokens = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", text_block)
    return [s if s else i for s, i in tokens]

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, robust, state-machine-based parser for S6F11.
    """
    data = {}
    
    # --- START OF FINAL, CORRECTED LOGIC ---

    # Step 1: Isolate the main <L,3> body of the S6F11 message.
    s6f11_body, _ = _find_enclosed_list(full_text)
    if not s6f11_body: return {}

    # Step 2: Extract the top-level items. We expect two primitives and one list.
    dataid_token = re.search(r"^\s*<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", s6f11_body)
    if not dataid_token: return {}
    
    # Find the text after the DATAID
    after_dataid = s6f11_body[dataid_token.end():]
    ceid_token = re.search(r"^\s*<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", after_dataid)
    if not ceid_token: return {}
    
    # The report list is everything after the CEID
    report_list_text = after_dataid[ceid_token.end():]
    
    try:
        ceid = int(ceid_token.group(1))
    except (ValueError, IndexError):
        return {}

    # Step 3: Parse the Report List block
    report_body, _ = _find_enclosed_list(report_list_text)
    if not report_body: return {}

    report_tokens = _get_primitive_tokens(report_body)
    if not report_tokens: return {}
    
    rptid = int(report_tokens[0])

    # Step 4: Populate data and validate against schemas.
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''): data['AlarmID'] = ceid
    
    if rptid in RPTID_MAP:
        data['RPTID'] = rptid
    else:
        return data

    # Step 5: The payload is all tokens in the report body AFTER the RPTID.
    data_payload = report_tokens[1:]
    
    # Step 6: Map the clean payload to the schema.
    field_names = RPTID_MAP.get(rptid, [])
    for i, name in enumerate(field_names):
        if i < len(data_payload):
            data[name] = data_payload[i]
            
    # --- END OF FINAL, CORRECTED LOGIC ---
            
    return data

def _parse_s2f49_command(full_text: str) -> dict:
    data = {}
    rcmd = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'", full_text)
    if rcmd: data['RCMD'] = rcmd.group(1)
    lotid = re.search(r"'LOTID'\s*>\s*<A\[\d+\]\s*'([^']*)'", full_text, re.IGNORECASE)
    if lotid: data['LotID'] = lotid.group(1)
    panels = re.search(r"'LOTPANELS'\s*>\s*<L\s\[(\d+)\]", full_text, re.IGNORECASE)
    if panels: data['PanelCount'] = int(panels.group(1))
    return data

def parse_log_file(uploaded_file):
    events = []
    if not uploaded_file: return events
    try: lines = StringIO(uploaded_file.getvalue().decode("utf-8")).readlines()
    except: lines = StringIO(uploaded_file.getvalue().decode("latin-1", errors='ignore')).readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not header: i += 1; continue
        ts, log_type, msg_part = header.groups()
        msg_match = re.search(r"MessageName=(\w+)|Message=.*?:\'(\w+)\'", msg_part)
        msg_name = (msg_match.group(1) or msg_match.group(2)) if msg_match else "N/A"
        event = {"timestamp": ts, "msg_name": msg_name}
        if ("Core:Send" in log_type or "Core:Receive" in log_type) and i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1; block = []
            while j < len(lines) and lines[j].strip() != '.': block.append(lines[j]); j += 1
            i = j
            if block:
                text = "".join(block)
                details = {}
                if msg_name == 'S6F11': details = _parse_s6f11_report(text)
                elif msg_name == 'S2F49': details = _parse_s2f49_command(text)
                if details: event['details'] = details
        if 'details' in event: events.append(event)
        i += 1
    return events
