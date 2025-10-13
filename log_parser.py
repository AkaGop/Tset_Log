# log_parser.py

import re
from io import StringIO
from config import CEID_MAP, RPTID_MAP

def _parse_s6f11_report(full_text: str) -> dict:
    """
    Final, robust parser for S6F11. This version uses a comprehensive regex 
    to tokenize all data types and maps them correctly.
    """
    data = {}
    
    # --- START OF HIGHLIGHTED FINAL FIX ---

    # Step 1: A robust regex that captures all possible primitive types:
    # 1. Quoted strings (like timestamps or IDs): '([^']*)'
    # 2. Standalone alphanumeric words (like MIC, MOR): ([A-Za-z]+)
    # 3. Integers: (\d+)
    tokens = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|([A-Za-z]+)|(\d+))>", full_text)
    
    # The result is a list of tuples, e.g., [('2025...', '', ''), ('', 'MIC', '')]. Flatten it.
    flat_values = [s or w or n for s, w, n in tokens]

    if len(flat_values) < 3: return {}

    # Step 2: Identify CEID and RPTID by their standard positions.
    try:
        ceid = int(flat_values[1])
        rptid = int(flat_values[2])
    except (ValueError, IndexError):
        return {}

    # Step 3: Populate data and validate.
    if ceid in CEID_MAP:
        data['CEID'] = ceid
        if "Alarm" in CEID_MAP.get(ceid, ''): data['AlarmID'] = ceid
    
    if rptid in RPTID_MAP:
        data['RPTID'] = rptid
        # The payload is everything after the RPTID.
        data_payload = flat_values[3:]
        
        field_names = RPTID_MAP.get(rptid, [])
        for i, name in enumerate(field_names):
            if i < len(data_payload):
                data[name] = data_payload[i]
            
    # --- END OF HIGHLIGHTED FINAL FIX ---
            
    return data

# ... (The rest of the file, _parse_s2f49_command and parse_log_file, is correct and remains unchanged) ...
