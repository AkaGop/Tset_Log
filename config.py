# config.py
"""
Single source of truth for all static configuration data, knowledge bases, and report definitions.
"""

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
    # Schema no longer includes 'Timestamp' as it is handled separately.
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
