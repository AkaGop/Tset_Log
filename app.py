# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file # Import our new function

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

# This is the updated section
if uploaded_file is not None:
    st.success(f"Successfully uploaded: **{uploaded_file.name}**")
    st.write("---")

    # Call the parsing function
    with st.spinner("Parsing log file..."):
        events = parse_log_file(uploaded_file)
    
    st.header("Initial Parsing Results")
    st.metric(label="Total Events Parsed", value=len(events))

    # Display the first 5 events as a sanity check
    st.subheader("Sample of Parsed Events (First 5)")
    st.json(events[:5]) # Show first 5 items from our list of events

else:
    st.info("Please upload a log file to begin analysis.")
