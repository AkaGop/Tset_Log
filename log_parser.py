# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_s6f11_report(full_text: str) -> dict:
    data = {}
    uints = [int(val) for val in re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)]
    if len(uints) < 3: return {}
    try:
        ceid, rptid = uints[1], uints[2]
    except (ValueError, IndexError): return {}
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''): data['AlarmID'] = ceid
    if rptid in RPTID_MAP:
        data['RPTID'] = rptid
        try:
            rptid_tag_match = re.search(r'(<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>)', full_text)
            if not rptid_tag_match: return data
            start_index = rptid_tag_match.end()
            report_body = full_text[start_index:]
            timestamp_match = re.search(r"<A\s\[16\]\s'([^']*)'>", report_body)
            if timestamp_match: data['ReportTimestamp'] = timestamp_match.group(1)
            data_values = re.findall(r"<(A)(?!\s\[16\])\s\[\d+\]\s'([^']*)'|<(U\d)\s\[\d+\]\s(\d+)>", report_body)
            flat_values = []
            for (a_tag, a_val, u_tag, u_val) in data_values:
                if a_tag: flat_values.append(a_val)
                if u_tag: flat_values.append(u_val)
            field_names = RPTID_MAP.get(rptid, [])
            for i, name in enumerate(field_names):
                if i < len(flat_values): data[name] = flat_values[i]
        except (ValueError, IndexError): pass
    return data

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
    try: lines = StringIO(uploaded_file.getvalue().decode("utf-8")).readlines()
    except UnicodeDecodeError: lines = StringIO(uploaded_file.getvalue().decode("latin-1", errors='ignore')).readlines()
    lines = [line for line in lines if line.strip()]
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
