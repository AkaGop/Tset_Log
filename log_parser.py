# In log_parser.py, replace the _parse_event_report function

def _parse_event_report(data_block_lines: list) -> dict:
    """
    Parses S6F11 Event Reports based on their RPTID.
    Expects a list of strings as input.
    """
    full_text = "".join(data_block_lines)
    data = {}
    
    ceid_map = KNOWLEDGE_BASE['ceid_map']
    rptid_map = KNOWLEDGE_BASE['rptid_map']

    uints = re.findall(r'<U\d\s\[\d+\]\s(\d+)>', full_text)
    if len(uints) < 2:
        return {} 

    ceid = int(uints[1])
    if ceid in ceid_map:
        data['CEID'] = ceid
        if "Alarm" in ceid_map[ceid]:
            data['AlarmID'] = ceid

    if len(uints) >= 3:
        rptid = int(uints[2])
        if rptid in rptid_map:
            data['RPTID'] = rptid
            
            # --- START OF THE FIX ---
            # This regex is now more specific. It looks for the RPTID, then captures the content
            # of the VERY NEXT <L [...]> block. This prevents it from grabbing outer timestamps.
            report_body_match = re.search(
                r'<\s*U\d\s*\[\d+\]\s*' + str(rptid) + r'\s*>\s*'  # Find the RPTID
                r'<\s*L\s*\[\d+\]\s*([\s\S]*)',  # Capture everything inside the list that follows
                full_text
            )
            # --- END OF THE FIX ---
            
            if report_body_match:
                report_body = report_body_match.group(1)
                
                values = re.findall(r"<(?:A|U\d)\s\[\d+\]\s(?:'([^']*)'|(\d+))>", report_body)
                flat_values = [s if s else i for s, i in values]
                
                field_names = rptid_map.get(rptid, [])
                for i, field_name in enumerate(field_names):
                    if i < len(flat_values):
                        data[field_name] = flat_values[i]
    return data
