# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file
from config import KNOWLEDGE_BASE # Import config separately

st.set_page_config(page_title="Hirata Log Analyzer", layout="wide")
st.title("Hirata Equipment Log Analyzer")

uploaded_file = st.file_uploader(
    "Upload your Hirata Log File",
    type=['txt', 'log']
)

if uploaded_file is not None:
    st.success(f"Successfully uploaded: **{uploaded_file.name}**")
    st.write("---")

    with st.spinner("Parsing log file..."):
        all_events = parse_log_file(uploaded_file)
    
    meaningful_events = [event for event in all_events if 'details' in event]
    
    st.header("Detailed Event Log")
    
    if meaningful_events:
        df = pd.json_normalize(meaningful_events)
        
        # Use the imported KNOWLEDGE_BASE to add a human-readable description
        if 'details.CEID' in df.columns:
            df['Event Name'] = df['details.CEID'].map(KNOWLEDGE_BASE['ceid_map'])

        cols_in_order = [
            "timestamp", "msg_name", "Event Name", "details.CEID", "details.RCMD", 
            "details.OperatorID", "details.MagazineID", "details.LotID", 
            "details.Result", "details.PortStatus"
        ]
        
        display_cols = [col for col in cols_in_order if col in df.columns]
        
        st.metric(label="Meaningful Events with SECS Data", value=len(df))
        st.dataframe(df[display_cols])

        with st.expander("Show Raw Parsed Data for Debugging"):
            st.json(meaningful_events[:20])
    else:
        st.warning("No meaningful SECS data blocks were found in the log file.")

else:
    st.info("Please upload a log file to begin analysis.")
