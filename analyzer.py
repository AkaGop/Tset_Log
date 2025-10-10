# analyzer.py

from datetime import datetime

def analyze_log_data(events: list) -> dict:
    """
    Final, resilient analyzer. Calculates KPIs for the first complete job it finds.
    If no complete job is found, it still populates other available data.
    """
    summary = {
        "operators": set(),
        "magazines": set(),
        "lot_id": "N/A",
        "panel_count": 0,
        "job_start_time": "N/A",
        "job_end_time": "N/A",
        "total_duration_sec": 0,
        "avg_cycle_time_sec": 0,
        "anomalies": [],
        "alarms": [],
        "job_status": "No Complete Job Found"
    }

    if not events:
        return summary

    # --- START OF HIGHLIGHTED FIX ---

    # Find the index of the first LOADSTART command.
    start_index = -1
    for i, event in enumerate(events):
        if event.get('details', {}).get('RCMD') == 'LOADSTART':
            start_index = i
            break
    
    # If a LOADSTART was found, populate what we know.
    if start_index != -1:
        loadstart_event = events[start_index]
        summary['lot_id'] = loadstart_event['details'].get('LotID', 'N/A')
        summary['panel_count'] = loadstart_event['details'].get('PanelCount', 0)
        summary['job_start_time'] = loadstart_event.get('timestamp')
        summary['job_status'] = "Started but did not complete in this log."

        # Now, search FORWARD from that start point for the completion event.
        end_index = -1
        for i in range(start_index + 1, len(events)):
            if events[i].get('details', {}).get('CEID') == 131:
                end_index = i
                break
        
        # If a corresponding end event was found, calculate the duration.
        if end_index != -1:
            loadcomplete_event = events[end_index]
            summary['job_end_time'] = loadcomplete_event.get('timestamp')
            summary['job_status'] = "Completed"
            
            try:
                t_start = datetime.strptime(summary['job_start_time'], "%Y/%m/%d %H:%M:%S.%f")
                t_end = datetime.strptime(summary['job_end_time'], "%Y/%m/%d %H:%M:%S.%f")
                duration = (t_end - t_start).total_seconds()
                
                if duration >= 0:
                    summary['total_duration_sec'] = round(duration, 2)
                    panel_count = int(summary.get('panel_count', 0))
                    if panel_count > 0:
                        summary['avg_cycle_time_sec'] = round(duration / panel_count, 2)
            except (ValueError, TypeError):
                summary['job_status'] = "Completed (Error calculating duration)"

    # --- END OF HIGHLIGHTED FIX ---

    # Aggregate other data across all events.
    for event in events:
        details = event.get('details', {})
        if details.get('OperatorID'): summary['operators'].add(details['OperatorID'])
        if details.get('MagazineID'): summary['magazines'].add(details['MagazineID'])
        if details.get('Result', '').startswith("Failure"):
            summary['anomalies'].append(f"{event['timestamp']}: Host command failed.")
        if details.get('AlarmID'):
            summary['alarms'].append(f"{event['timestamp']}: Alarm {details['AlarmID']} occurred.")
            
    return summary
