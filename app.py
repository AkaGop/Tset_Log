# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file
from config import CEID_MAP
from analyzer import analyze_data

# --- START OF HIGHLIGHTED CHANGE ---
# Added a version number to the title to act as a "cache buster"
st.set_page_config(page_title="Hirata Log Analyzer v1.3", layout="wide")
st.title("Hirata Equipment Log Analyzer v1.3")
# --- END OF HIGHLIGHTED CHANGE ---

uploaded_file = st.file_uploader("Upload your Hirata Log File (.txt or .log)", type=['txt', 'log'])

if uploaded_file:
    with st.spinner("Analyzing log file..."):
        all_events = parse_log_file(uploaded_file)
    meaningful_events = [event for event in all_events if 'details' in event]
    summary_data = analyze_data(meaningful_events)
    
    st.header("Job Performance Dashboard")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Job Status", summary_data['job_status'])
    col2.metric("Lot ID", str(summary_data['lot_id']))
    col3.metric("Total Panels", int(summary_data['panel_count']))
    col4.metric("Job Duration (sec)", f"{summary_data['total_duration_sec']:.2f}")
    col5.metric("Avg Cycle Time (sec)", f"{summary_data['avg_cycle_time_sec']:.2f}")

    st.write("---")
    st.header("Detailed Event Log")
    if meaningful_events:
        df = pd.json_normalize(meaningful_events)
        if 'details.CEID' in df.columns:
            df['EventName'] = pd.to_numeric(df['details.CEID'], errors='coerce').map(CEID_MAP).fillna("Unknown")
        elif 'details.RCMD' in df.columns:
             df['EventName'] = df['details.RCMD']
        else:
             df['EventName'] = "Unknown"
        cols_in_order = [
            "timestamp", "msg_name", "EventName", "details.LotID", "details.PanelCount",
            "details.MagazineID", "details.OperatorID", "details.PortID", "details.PortStatus",
            "details.AlarmID"
        ]
        display_cols = [col for col in cols_in_order if col in df.columns]
        st.dataframe(df[display_cols])
        with st.expander("Show Raw JSON Data"):
            st.json(meaningful_events)
    else:
        st.warning("No meaningful parsed events were found.")
else:
    st.info("Please upload a log file to begin analysis.")
