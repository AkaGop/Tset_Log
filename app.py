# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file
from config import KNOWLEDGE_BASE

st.set_page_config(page_title="Hirata Log Analyzer", layout="wide")
st.title("Hirata Equipment Log Analyzer")

uploaded_file = st.file_uploader("Upload your Hirata Log File (.txt or .log)", type=['txt', 'log'])

if uploaded_file:
    with st.spinner("Analyzing log file..."):
        all_events = parse_log_file(uploaded_file)
    
    meaningful_events = [event for event in all_events if 'details' in event]
    
    st.header("Detailed Event Log")

    if meaningful_events:
        # --- START OF FIX ---
        # Manually create the data for the DataFrame to ensure correctness.
        
        display_data = []
        for event in meaningful_events:
            details = event.get('details', {})
            ceid = details.get('CEID')
            
            # Determine the event name
            event_name = "Unknown Event"
            if ceid in KNOWLEDGE_BASE['ceid_map']:
                event_name = KNOWLEDGE_BASE['ceid_map'][ceid]
            elif 'RCMD' in details:
                event_name = details['RCMD']

            row = {
                'timestamp': event['timestamp'],
                'msg_name': event['msg_name'],
                'EventName': event_name,
                'LotID': details.get('LotID'),
                'PanelCount': details.get('PanelCount'),
                'MagazineID': details.get('MagazineID'),
                'OperatorID': details.get('OperatorID'),
                'PortID': details.get('PortID'),
                'PortStatus': details.get('PortStatus'),
                'AlarmID': details.get('AlarmID'),
            }
            display_data.append(row)
        
        df = pd.DataFrame(display_data)
        
        st.metric(label="Meaningful Events Found", value=len(df))
        st.dataframe(df) # Display the cleaned DataFrame

        with st.expander("Show Raw JSON Data (First 20 Events)"):
            st.json(meaningful_events[:20])
        # --- END OF FIX ---
            
    else:
        st.warning("No meaningful S6F11 or S2F49 messages were found in the log file.")

else:
    st.info("Please upload a log file to begin analysis.")
