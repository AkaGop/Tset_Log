# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file
from config import CEID_MAP

st.set_page_config(page_title="Hirata Log Analyzer", layout="wide")
st.title("Hirata Equipment Log Analyzer")

uploaded_file = st.file_uploader("Upload your Hirata Log File (.txt or .log)", type=['txt', 'log'])

if uploaded_file:
    with st.spinner("Analyzing log file..."):
        all_events = parse_log_file(uploaded_file)
    
    meaningful_events = [event for event in all_events if 'details' in event]
    
    st.header("Detailed Event Log")

    if meaningful_events:
        df = pd.json_normalize(meaningful_events)
        
        if 'details.CEID' in df.columns:
            df['EventName'] = df['details.CEID'].map(CEID_MAP).fillna("Unknown Event")
        else:
            df['EventName'] = df.get('details.RCMD', "Command")

        cols_in_order = [
            "timestamp", "msg_name", "EventName", "details.LotID", "details.PanelCount",
            "details.MagazineID", "details.OperatorID", "details.PortID", "details.PortStatus",
            "details.AlarmID"
        ]
        
        display_cols = [col for col in cols_in_order if col in df.columns]
        
        st.metric(label="Meaningful Events Found", value=len(df))
        st.dataframe(df[display_cols])

        with st.expander("Show Raw JSON Data (First 20 Events for Debugging)"):
            st.json(meaningful_events[:20])
    else:
        st.warning("No meaningful S6F11 or S2F49 messages were found in the log file.")
else:
    st.info("Please upload a log file to begin analysis.")
