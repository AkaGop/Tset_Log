# config.py

# --- START OF HIGHLIGHTED CHANGE ---
# RPTID_MAP is now simpler and does not include the 'Timestamp' field,
# as it will be handled separately based on your A[16] insight.

SECS_MAP = {
    "S1F1": "Are You There Request", "S1F2": "Are You There Data",
    "S1F3": "Selected Equipment Status Request", "S1F4": "Selected Equipment Status Data",
    "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
    "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
}

CEID_MAP = {
    11: "Equipment Offline", 12: "Control State Local", 13: "Control State Remote",
    16: "PP-SELECT Changed", 30: "Process State Change", 101: "Alarm Cleared",
    102: "Alarm Set", 18: "AlarmSet", 113: "AlarmSet", 114: "AlarmSet", 
    120: "IDRead", 121: "UnloadedFromMag/LoadedToTool", 127: "LoadedToTool",
    131: "LoadToToolCompleted", 132: "UnloadFromToolCompleted", 136: "MappingCompleted",
    141: "PortStatusChange", 151: "MagazineDocked", 180: "RequestMagazineDock",
    181: "MagazineDocked", 182: "MagazineUndocked", 183: "RequestOperatorIdCheck",
    184: "RequestOperatorLogin", 185: "RequestMappingCheck",
}

RPTID_MAP = {
    152: ['OperatorID'],
    150: ['MagazineID'],
    151: ['PortID', 'MagazineID', 'OperatorID'],
    141: ['PortID', 'PortStatus'],
    120: ['LotID', 'PanelID', 'Orientation', 'ResultCode', 'SlotID'],
    121: ['LotID', 'PanelID', 'SlotID'],
    122: ['LotID', 'SourcePortID', 'DestPortID', 'PanelList'],
    11:  ['ControlState'],
    101: ['AlarmIDValue'],
}
# --- END OF HIGHLIGHTED CHANGE ---
