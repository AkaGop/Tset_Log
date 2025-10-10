# analyzer.py

from datetime import datetime

def analyze_log_data(events: list) -> dict:
    """
    Final, simplified, and robust analyzer. It performs a simple linear scan
    to find the first complete job cycle.
    """
    # Initialize with default "Not Found" values
    summary = {
        "operators": set(),
        "magazines": set(),
        "lot_id": "N/A",
        "panel_count": 0,
        "job_start_time": "N/A",
        "job_end_time": "N/A",
        "total_duration_sec": 0.0,
        "avg_cycle_time_sec": 0.0,
        "anomalies": [],
        "alarms": [],
        "job_status": "No Job Found"
    }

    if not events:
        return summary

    # --- START OF HIGHLIGHTED FINAL FIX ---

    start_event = None
    end_event = None

    # Find the first LOADSTART event in the entire log
    for event in events:
        if event.get('details', {}).get('RCMD') == 'LOADSTART':
            start_event = event
            break
    
    # If we found a start event, search for the first completion event AFTER it
    if start_event:
        summary['lot_id'] = start_event['details'].get('LotID', 'N/A')
        summary['panel_count'] = int(start_event['details'].get('PanelCount', 0))
        summary['job_start_time'] = start_event['timestamp']
        summary['job_status'] = "Started but did not complete"

        start_index = events.index(start_event)
        for i in range(start_index + 1, len(events)):
            event = events[i]
            if event.get('details', {}).get('CEID') == 131:
                end_event = event
                break
        
        # If we found both a start and an end, calculate the KPIs
        if end_event:
            summary['job_end_time'] = end_event['timestamp']
            summary['job_status'] = "Completed"
            
            try:
                t_start = datetime.strptime(summary['job_start_time'], "%Y/%m/%d %H:%M:%S.%f")
                t_end = datetime.strptime(summary['job_end_time'], "%Y/%m/%d %H:%M:%S.%f")
                duration = (t_end - t_start).total_seconds()

                if duration >= 0:
                    summary['total_duration_sec'] = round(duration, 2)
                    if summary['panel_count'] > 0:
                        summary['avg_cycle_time_sec'] = round(duration / summary['panel_count'], 2)
            except (ValueError, TypeError):
                 summary['job_status'] = "Error in Time Calculation"

    # --- END OF HIGHLIGHTED FINAL FIX ---

    # Aggregate other data across all events (this part is reliable)
    for event in events:
        details = event.get('details', {})
        if details.get('OperatorID'): summary['operators'].add(details['OperatorID'])
        if details.get('MagazineID'): summary['magazines'].add(details['MagazineID'])
        if str(details.get('Result', '')).startswith("Failure"):
             summary['anomalies'].append(f"{event['timestamp']}: Host command failed.")
        if details.get('AlarmID'):
            summary['alarms'].append(f"{event['timestamp']}: Alarm {details['AlarmID']} occurred.")
            
    return summary
