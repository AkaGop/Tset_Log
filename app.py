# app.py

# app.py

import streamlit as st
import pandas as pd
from log_parser import parse_log_file, KNOWLEDGE_BASE

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
    
    # Filter for events that have the 'details' key, which means our parser found something.
    meaningful_events = [event for event in all_events if 'details' in event]
    
    st.header("Analysis Results")
    
    if meaningful_events:
        st.metric(label="Meaningful Events with SECS Data", value=len(meaningful_events))

        # Use pandas json_normalize to flatten the nested 'details' dictionary
        df = pd.json_normalize(meaningful_events)
        
        # Define the desired column order
        cols_in_order = [
            "timestamp", "msg_name", "details.CEID", "details.RCMD", 
            "details.OperatorID", "details.MagazineID", "details.LotID", 
            "details.Result", "details.PortStatus", "log_type"
        ]
        
        # Filter the DataFrame to show only existing columns from our desired list
        display_cols = [col for col in cols_in_order if col in df.columns]
        st.dataframe(df[display_cols])

        # --- DEBUGGING SECTION ---
        with st.expander("Show Raw Parsed Data for Debugging"):
            st.write("First 20 meaningful events found:")
            st.json(meaningful_events[:20])
            st.write("All parsed events (including those without details):")
            st.metric(label="Total Log Lines Parsed", value=len(all_events))
            st.json(all_events[:20])

    else:
        st.warning("No meaningful SECS data blocks were found in the log file.")
        # --- DEBUGGING SECTION ---
        with st.expander("Show Raw Parser Output (Debugging)"):
             st.write(f"Total log lines parsed: {len(all_events)}. No lines contained parsable SECS data.")
             st.write("First 50 raw parsed events:")
             st.json(all_events[:50])

else:
    st.info("Please upload a log file to begin analysis.")
