# config.py
"""
#Single source of truth for all static configuration data, knowledge bases, and report definitions.
"""
CEID_MAP = {
    11: "Equipment Offline", 12: "Control State Local", 13: "Control State Remote",
    16: "PP-SELECT Changed", 30: "Process State Change", 101: "Alarm Cleared",
    102: "Alarm Set", 120: "ID Read", 127: "Loaded To Tool", 131: "Load To Tool Completed",
    136: "Mapping Completed", 141: "Port Status Change", 151: "Magazine Docked",
    180: "Request Magazine Dock", 181: "Magazine Docked", 182: "Magazine Undocked",
    183: "Request Operator ID Check", 184: "Request Operator Login", 185: "Request Mapping Check",
}
RPTID_MAP = {
    152: ['Timestamp', 'OperatorID'], 150: ['Timestamp', 'MagazineID'],
    151: ['Timestamp', 'PortID', 'MagazineID', 'OperatorID'],
    141: ['Timestamp', 'PortID', 'PortStatus'],
    120: ['Timestamp', 'LotID', 'PanelID', 'Orientation', 'ResultCode', 'SlotID'],
    121: ['Timestamp', 'LotID', 'PanelID', 'SlotID'],
    122: ['Timestamp', 'LotID', 'SourcePortID', 'DestPortID', 'PanelList'],
    11:  ['Timestamp', 'ControlState'], 101: ['Timestamp', 'AlarmID'],
}

#**2. `log_parser.py` (Final, Simplified, and Corrected Parser)**

#This is the corrected parsing engine.
