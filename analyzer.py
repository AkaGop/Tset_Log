# analyzer.py

from datetime import datetime

def analyze_log_data(events: list) -> dict:
    """
    Analyzes a list of parsed events to calculate high-level KPIs.

    Args:
        events: A list of event dictionaries from the parser.

    Returns:
        A dictionary containing the calculated KPIs and summary data.
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

    # Find the main LOADSTART job
    loadstart_event = next((e for e in events if e.get('details', {}).get('RCMD') == 'LOADSTART'), None)

    # Find the corresponding LoadToToolCompleted event
    loadcomplete_event = next((e for e in events if e.get('details', {}).get('CEID') == 131), None)

    # Calculate Job KPIs if a job was found
    if loadstart_event and loadcomplete_event:
        summary['lot_id'] = loadstart_event['details'].get('LotID', 'N/A')
        summary['panel_count'] = loadstart_event['details'].get('PanelCount', 0)
        
        start_time_str = loadstart_event.get('timestamp')
        end_time_str = loadcomplete_event.get('timestamp')

        if start_time_str and end_time_str:
            summary['job_start_time'] = start_time_str
            summary['job_end_time'] = end_time_str
            
            try:
                # Convert timestamps to datetime objects to calculate duration
                t_start = datetime.strptime(start_time_str, "%Y/%m/%d %H:%M:%S.%f")
                t_end = datetime.strptime(end_time_str, "%Y/%m/%d %H:%M:%S.%f")
                duration = (t_end - t_start).total_seconds()
                summary['total_duration_sec'] = round(duration, 2)
                
                if summary['panel_count'] > 0:
                    cycle_time = duration / summary['panel_count']
                    summary['avg_cycle_time_sec'] = round(cycle_time, 2)
            except ValueError:
                # Handle cases where timestamp format might be different
                pass # Keep default 0 values

    # Aggregate other data across all events
    for event in events:
        details = event.get('details', {})
        if details.get('OperatorID'):
            summary['operators'].add(details['OperatorID'])
        if details.get('MagazineID'):
            summary['magazines'].add(details['MagazineID'])
        if details.get('Result', '').startswith("Failure"):
            summary['anomalies'].append(f"{event['timestamp']}: {event.get('EventName', 'Unknown Event')} failed.")
        if details.get('AlarmID'):
            summary['alarms'].append(f"{event['timestamp']}: Alarm {details['AlarmID']} occurred.")
            
    return summary
