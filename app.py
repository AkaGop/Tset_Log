# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file

st.set_page_config(page_title="Hirata Log Analyzer", layout="wide")
st.title("Hirata Equipment Log Analyzer")
st.write(
    "This tool parses and analyzes Hirata equipment log files (.txt or .log) "
    "to provide key performance indicators and an operational summary."
)

uploaded_file = st.file_uploader(
    "Upload your Hirata Log File",
    type=['txt', 'log'],
    accept_multiple_files=False
)

if uploaded_file is not None:
    st.success(f"Successfully uploaded: **{uploaded_file.name}**")
    st.write("---")

    with st.spinner("Parsing log file for detailed events..."):
        all_events = parse_log_file(uploaded_file)
    
    # Filter for events that have the 'details' key we added
    meaningful_events = [event for event in all_events if "details" in event]
    
    st.header("Detailed Event Log")
    
    if meaningful_events:
        df = pd.json_normalize(meaningful_events)
        
        # Reorder columns for better readability
        cols = ["timestamp", "msg_name", "log_type", "details.CEID", "details.RCMD", "details.OperatorID", "details.MagazineID", "details.LotID", "details.Result", "details.PortStatus"]
        existing_cols = [col for col in cols if col in df.columns]
        
        st.metric(label="Total Meaningful Events Found", value=len(df))
        st.dataframe(df[existing_cols])

        st.subheader("Raw Data of First 5 Meaningful Events")
        st.json(meaningful_events[:5])
    else:
        st.warning("No meaningful SECS data blocks were found in the log file.")

else:
    st.info("Please upload a log file to begin analysis.")
