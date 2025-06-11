# root/priority_utils.py

import traci

PRIORITY_MAP = {
    "HV": 3,  # High Priority Ambulance / Fire
    "MV": 2,  # Medium priority 
    "LV": 1,  # Low priority
}

def get_highest_priority_vehicle_type(vehicles):
    highest_type = None
    highest_val = 0
    for vid in vehicles:
        try:
            vt = traci.vehicle.getTypeID(vid)
            val = PRIORITY_MAP.get(vt, 0)
            if val > highest_val:
                highest_val = val
                highest_type = vt
        except:
            pass
    return highest_type
