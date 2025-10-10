# log_parser.py

import re
from io import StringIO
from config import KNOWLEDGE_BASE

def _parse_event_report(full_text: str) -> dict:
    data = {}
    ceid_map = KNOWLEDGE_BASE['ceid_map']
    rptid_map = KNOWLEDGE_BASE['rptid_map']

    uints = re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)
    if len(uints) < 2: return {}

    ceid = int(uints[1])
    if ceid in ceid_map:
        data['CEID'] = ceid
        if "Alarm" in ceid_map[ceid]: data['AlarmID'] = ceid

    if len(uints) >= 3:
        rptid = int(uints[2])
        if rptid in rptid_map:
            data['RPTID'] = rptid
            # Corrected Regex: Makes the capture non-greedy and looks for the list structure.
            report_body_match = re.search(r'<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>\s*<L\s\[\d+\]\s*([\s\S]*?)>\s*>', full_text)
            if report_body_match:
                report_body = report_body_match.group(1)
                values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", report_body)
                flat_values = [s if s else i for s, i in values]
                field_names = rptid_map.get(rptid, [])
                for i, field_name in enumerate(field_names):
                    if i < len(flat_values):
                        data[field_name] = flat_values[i]
    return data

def _parse_remote_command(full_text: str) -> dict:
    data = {}
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'", full_text)
    if rcmd_match: data['RCMD'] = rcmd_match.group(1)
    lotid_match = re.search(r"'LOTID'\s*>\s*<A\[\d+\]\s*'([^']*)'", full_text, re.IGNORECASE)
    if lotid_match: data['LotID'] = lotid_match.group(1)
    lotpanels_match = re.search(r"'LOTPANELS'\s*>\s*<L\s\[(\d+)\]", full_text, re.IGNORECASE)
    if lotpanels_match: data['PanelCount'] = int(lotpanels_match.group(1))
    return data

def parse_log_file(uploaded_file):
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
        timestamp_str, log_type, message_part = header_match.groups()
        msg_name_match = re.search(r"MessageName=(\w+)|Message=.*?:\'(\w+)\'", message_part)
        msg_name = (msg_name_match.group(1) or msg_name_match.group(2)) if msg_name_match else "N/A"
        data_block_lines = []
        if ("Core:Send" in log_type or "Core:Receive" in log_type) and i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1
            while j < len(lines) and lines[j].strip() != '.':
                data_block_lines.append(lines[j]); j += 1
            i = j
        event = {"timestamp": timestamp_str, "log_type": log_type, "msg_name": msg_name}
        if data_block_lines:
            # The input to the parsers must be a single string.
            full_data_block_text = "".join(data_block_lines)
            details = {}
            if msg_name == 'S6F11': details = _parse_event_report(full_data_block_text)
            elif msg_name == 'S2F49': details = _parse_remote_command(full_data_block_text)
            if details: event['details'] = details
        events.append(event)
        i += 1
    return events
