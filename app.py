# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file
from config import CEID_MAP
from analyzer import analyze_log_data # Import our new analysis function

st.set_page_config(page_title="Hirata Log Analyzer", layout="wide")
st.title("Hirata Equipment Log Analyzer")

uploaded_file = st.file_uploader("Upload your Hirata Log File (.txt or .log)", type=['txt', 'log'])

if uploaded_file:
    with st.spinner("Analyzing log file..."):
        all_events = parse_log_file(uploaded_file)
        meaningful_events = [event for event in all_events if 'details' in event]
        
        # --- NEW: Perform analysis to get KPIs ---
        summary_data = analyze_log_data(meaningful_events)

    # --- NEW: Display the KPI Dashboard ---
    st.header("Job Performance Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Lot ID", value=summary_data['lot_id'])
    with col2:
        st.metric(label="Total Panels Processed", value=summary_data['panel_count'])
    with col3:
        st.metric(label="Total Job Duration (sec)", value=f"{summary_data['total_duration_sec']:.2f}")
    with col4:
        st.metric(label="Avg. Cycle Time / Panel (sec)", value=f"{summary_data['avg_cycle_time_sec']:.2f}")

    st.write("---")

    # --- Display the detailed event log (as before) ---
    st.header("Detailed Event Log")
    if meaningful_events:
        df = pd.json_normalize(meaningful_events)
        if 'details.CEID' in df.columns:
            df['EventName'] = df['details.CEID'].map(CEID_MAP).fillna("Unknown Event")
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

        with st.expander("Show Raw JSON Data (First 20 Events for Debugging)"):
            st.json(meaningful_events[:20])
    else:
        st.warning("No meaningful S6F11 or S2F49 messages were found in the log file.")

else:
    st.info("Please upload a log file to begin analysis.")
