# analyzer.py

from datetime import datetime

def analyze_log_data(events: list) -> dict:
    """
    Analyzes a list of parsed events to calculate high-level KPIs for a complete job cycle.
    """
    summary = {
        "operators": set(),
        "magazines": set(),
        "lot_id": "N/A",
        "panel_count": 0,
        "job_start_time": None,
        "job_end_time": None,
        "total_duration_sec": 0,
        "avg_cycle_time_sec": 0,
        "anomalies": [],
        "alarms": [],
    }

    if not events:
        return summary

    # --- START OF HIGHLIGHTED FIX ---

    # Step 1: Find the index of all LOADSTART commands.
    loadstart_indices = [i for i, event in enumerate(events) if event.get('details', {}).get('RCMD') == 'LOADSTART']

    job_found = False
    for start_index in loadstart_indices:
        loadstart_event = events[start_index]
        
        # Step 2: Search for the NEXT LoadToToolCompleted event AFTER this LOADSTART.
        end_index = -1
        for i in range(start_index + 1, len(events)):
            if events[i].get('details', {}).get('CEID') == 131:
                end_index = i
                break # Found the corresponding end event
        
        if end_index != -1: # A complete job cycle was found
            loadcomplete_event = events[end_index]
            
            summary['lot_id'] = loadstart_event['details'].get('LotID', 'N/A')
            summary['panel_count'] = loadstart_event['details'].get('PanelCount', 0)
            
            start_time_str = loadstart_event.get('timestamp')
            end_time_str = loadcomplete_event.get('timestamp')

            if start_time_str and end_time_str:
                summary['job_start_time'] = start_time_str
                summary['job_end_time'] = end_time_str
                
                try:
                    t_start = datetime.strptime(start_time_str, "%Y/%m/%d %H:%M:%S.%f")
                    t_end = datetime.strptime(end_time_str, "%Y/%m/%d %H:%M:%S.%f")
                    duration = (t_end - t_start).total_seconds()
                    
                    # Sanity check: duration should be positive and reasonable
                    if duration > 0:
                        summary['total_duration_sec'] = round(duration, 2)
                        
                        panel_count = summary['panel_count']
                        if isinstance(panel_count, str) and panel_count.isdigit():
                            panel_count = int(panel_count)

                        if isinstance(panel_count, int) and panel_count > 0:
                            cycle_time = duration / panel_count
                            summary['avg_cycle_time_sec'] = round(cycle_time, 2)
                
                        job_found = True
                        break # Stop after analyzing the first complete job found
                except (ValueError, TypeError):
                    continue # Try the next LOADSTART if there's a data format error
    
    # --- END OF HIGHLIGHTED FIX ---

    # Aggregate other data across all events (this part is correct)
    for event in events:
        details = event.get('details', {})
        if details.get('OperatorID'): summary['operators'].add(details['OperatorID'])
        if details.get('MagazineID'): summary['magazines'].add(details['MagazineID'])
        if details.get('Result', '').startswith("Failure"):
            event_name = event.get('details', {}).get('RCMD', 'Unknown Command')
            summary['anomalies'].append(f"{event['timestamp']}: Host command '{event_name}' failed.")
        if details.get('AlarmID'):
            summary['alarms'].append(f"{event['timestamp']}: Alarm {details['AlarmID']} occurred.")
            
    return summary
