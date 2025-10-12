# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, robust parser for S6F11, built on the principle that <A[16]> is a timestamp.
    """
    data = {}
    
    # --- START OF HIGHLIGHTED FINAL FIX ---

    # Step 1: Find all integer values to identify key markers.
    uints = [int(val) for val in re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)]
    if len(uints) < 3: return {}

    ceid, rptid = uints[1], uints[2]

    # Step 2: Populate initial data and validate schemas.
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''): data['AlarmID'] = ceid
    
    if rptid in RPTID_MAP:
        data['RPTID'] = rptid
    else:
        return data

    # Step 3: Isolate the report body following the RPTID tag.
    rptid_tag_match = re.search(r'(<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>)', full_text)
    if not rptid_tag_match: return data
    
    start_index = rptid_tag_match.end()
    report_body = full_text[start_index:]
    
    # Step 4: YOUR SUGGESTION - Handle Timestamp separately.
    # Find the timestamp if it exists.
    timestamp_match = re.search(r"<A\s\[16\]\s'([^']*)'>", report_body)
    if timestamp_match:
        data['ReportTimestamp'] = timestamp_match.group(1)

    # Step 5: Extract all OTHER primitive values (the real data).
    # This regex finds all A or U tags that are NOT <A[16]...>.
    data_values = re.findall(r"<(A)(?!\s\[16\])\s\[\d+\]\s'([^']*)'|<(U\d)\s\[\d+\]\s(\d+)>", report_body)
    
    # Flatten the regex result, which is a list of tuples with empty strings.
    flat_values = []
    for (a_tag, a_val, u_tag, u_val) in data_values:
        if a_tag: flat_values.append(a_val)
        if u_tag: flat_values.append(u_val)

    # Step 6: Map the clean data payload to our simplified schema.
    field_names = RPTID_MAP.get(rptid, [])
    for i, name in enumerate(field_names):
        if i < len(flat_values):
            data[name] = flat_values[i]
            
    # --- END OF HIGHLIGHTED FINAL FIX ---
            
    return data

def _parse_s2f49_command(full_text: str) -> dict:
    # This function is correct and does not need changes.
    # ... (code remains the same as previous step) ...

def parse_log_file(uploaded_file):
    # This function is correct and does not need changes.
    # ... (code remains the same as previous step) ...
