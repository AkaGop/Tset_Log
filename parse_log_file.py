# log_parser.py

import re
from io import StringIO

def parse_log_file(uploaded_file):
    """
    Reads an uploaded file and parses it into a structured list of events.
    
    Args:
        uploaded_file: The file object provided by st.file_uploader.
    
    Returns:
        A list of dictionaries, where each dictionary represents a parsed log event.
    """
    events = []
    
    # Streamlit's uploaded file is a bytes-like object. We need to decode it into a string.
    # StringIO makes it behave like a file on disk, which is easy to iterate over.
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    lines = stringio.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # This is the main regex to capture the timestamp, log type, and the rest of the message.
        header_match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        
        if not header_match:
            i += 1
            continue # Skip lines that don't match the primary log format
        
        timestamp_str, log_type, message_part = header_match.groups()
        
        # Extract the message name (e.g., S6F11, S2F49)
        msg_name_match = re.search(r"MessageName=(\w+)", message_part) or \
                         re.search(r"Message=.*?:\'(\w+)\'", message_part)
        msg_name = msg_name_match.group(1) if msg_name_match else "N/A"

        # Check if this line is followed by a SECS-II data block (starts with '<')
        data_block_lines = []
        if "Core:Send" in log_type or "Core:Receive" in log_type:
            # Look ahead to the next lines to find the data block
            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                j = i + 1
                # Read lines until we hit the end of the block, marked by a '.'
                while j < len(lines) and lines[j].strip() != '.':
                    data_block_lines.append(lines[j])
                    j += 1
                i = j # Move the main loop index past the data block we just consumed
        
        # Store the extracted information
        event_data = {
            "timestamp": timestamp_str,
            "log_type": log_type,
            "msg_name": msg_name,
            "raw_data_block": "".join(data_block_lines) # Join the lines into a single string
        }
        events.append(event_data)
        
        i += 1
        
    return events