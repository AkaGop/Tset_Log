# app.py
import streamlit as st
import pandas as pd
from log_parser import parse_log_file
from config import CEID_MAP
from analyzer import analyze_data

st.set_page_config(page_title="Hirata Log Analyzer vFINAL-4", layout="wide")
st.title("Hirata Equipment Log Analyzer vFINAL-4")

uploaded_file = st.file_uploader("Upload your Hirata Log File (.txt or .log)", type=['txt', 'log'])
if uploaded_file:
    with st.spinner("Analyzing log file..."):
        events = parse_log_file(uploaded_file)
        summary = analyze_data(events)
    st.header("Job Performance Dashboard")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Job Status", summary['job_status'])
    c2.metric("Lot ID", str(summary['lot_id']))
    c3.metric("Total Panels", int(summary['panel_count']))
    c4.metric("Job Duration (sec)", f"{summary['total_duration_sec']:.2f}")
    c5.metric("Avg Cycle Time (sec)", f"{summary['avg_cycle_time_sec']:.2f}")
    st.write("---")
    st.header("Detailed Event Log")
    if events:
        df = pd.json_normalize(events)
        if 'details.CEID' in df.columns:
            df['EventName'] = pd.to_numeric(df['details.CEID'], errors='coerce').map(CEID_MAP).fillna("Unknown")
        elif 'details.RCMD' in df.columns: df['EventName'] = df['details.RCMD']
        else: df['EventName'] = "N/A"
        cols = [
            "timestamp", "msg_name", "EventName", "details.LotID", "details.PanelCount",
            "details.MagazineID", "details.OperatorID", "details.PortID", "details.PortStatus", "details.AlarmID"
        ]
        display_cols = [col for col in cols if col in df.columns]
        st.dataframe(df[display_cols])
        with st.expander("Show Raw JSON Data"): st.json(events)
    else:
        st.warning("No meaningful events were found.")
else:
    st.info("Please upload a log file to begin analysis.")
