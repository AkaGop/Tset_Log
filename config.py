# config.py
"""
Single source of truth for static configuration, knowledge bases, and report definitions.
"""

# Maps SECS message names to human-readable descriptions
SECS_MAP = {
    "S1F1": "Are You There Request", "S1F2": "Are You There Data",
    "S1F3": "Selected Equipment Status Request", "S1F4": "Selected Equipment Status Data",
    "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
    "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
}

# Maps Collection Event IDs (CEID) to human-readable names
CEID_MAP = {
    11: "GemEquipmentOFFLINE", 12: "GemControlStateLOCAL", 13: "GemControlStateREMOTE",
    14: "GemMsgRecognition", 16: "GemPPChangeEvent", 30: "GemProcessStateChange",
    101: "AlarmClear", 102: "AlarmSet", 18: "AlarmSet", 113: "AlarmSet", 114: "AlarmSet", 
    120: "IDRead", 121: "UnloadedFromMag/LoadedToTool", 127: "LoadedToTool",
    131: "LoadToToolCompleted", 132: "UnloadFromToolCompleted", 136: "MappingCompleted",
    141: "PortStatusChange", 151: "MagazineDocked", 180: "RequestMagazineDock",
    181: "MagazineDocked", 182: "MagazineUndocked", 183: "RequestOperatorIdCheck",
    184: "RequestOperatorLogin", 185: "RequestMappingCheck",
}

# Defines the structure of each Report ID (RPTID)
# This is the key to reliable parsing. It maps the position of data to a name.
RPTID_MAP = {
    152: ['Timestamp', 'OperatorID'],        # For RequestOperatorLogin
    150: ['Timestamp', 'MagazineID'],        # For RequestMagazineDock
    151: ['Timestamp', 'PortID', 'MagazineID', 'OperatorID'], # For MagazineDocked/Undocked
    141: ['Timestamp', 'PortID', 'PortStatus'], # For PortStatusChange
    120: ['Timestamp', 'LotID', 'PanelID', 'Orientation', 'ResultCode', 'SlotID'], # For IDRead
    121: ['Timestamp', 'LotID', 'PanelID', 'SlotID'], # For UnloadedFromMag/LoadedToTool
    122: ['Timestamp', 'LotID', 'SourcePortID', 'DestPortID', 'PanelList'], # For LoadToToolCompleted
    11:  ['Timestamp', 'ControlState'],
    101: ['Timestamp', 'AlarmID'],
}
