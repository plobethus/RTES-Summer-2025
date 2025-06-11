# root/control.py
import traci
from priority_utils import PRIORITY_MAP, get_highest_priority_vehicle_type

PHASE_MAP = {
    "E0": 0,     
    "-E2": 0,
    "-E1": 2,    
    "-E3": 2,
}
DEFAULT_PHASE = 0

def get_phase_for_edge(edge):
    """Return the traffic light phase index for the chosen edge."""
    return PHASE_MAP.get(edge, DEFAULT_PHASE)

###############################################################################
# FIXED PRIORITY (FP)
###############################################################################
def fp_pick_edge(edge_vehicles):
    """
    Among edges that have vehicles, pick the one with the highest priority 
    (HV=3 > MV=2 > LV=1), then use queue length to break ties.
    If no vehicles, pick the largest queue anyway.
    """
    best_edge = None
    best_score = -1

    for edge, vehicles in edge_vehicles.items():
        veh_type = get_highest_priority_vehicle_type(vehicles)
        prio_val = PRIORITY_MAP.get(veh_type, 0)
        # Weighted sum: prio * 100 + queue length
        score = prio_val * 100 + len(vehicles)
        if score > best_score:
            best_score = score
            best_edge = edge

    if not best_edge:
        # fallback if no vehicles
        best_edge = max(edge_vehicles, key=lambda e: len(edge_vehicles[e]))
    return best_edge

###############################################################################
# EARLIEST DEADLINE FIRST (EDF)
###############################################################################
def edf_pick_edge(edge_vehicles, current_time):
    """
    Among edges that have vehicles with deadlines, pick the earliest.
    If no deadlines, fallback to largest queue.
    """
    best_edge = None
    best_remain = float('inf')

    for edge, vehicles in edge_vehicles.items():
        min_deadline = None
        for vid in vehicles:
            try:
                d_str = traci.vehicle.getParameter(vid, "deadline")
                if d_str:
                    deadline = float(d_str)
                    remain = deadline - current_time
                    if (min_deadline is None) or (remain < min_deadline):
                        min_deadline = remain
            except traci.TraCIException:
                pass

        if (min_deadline is not None) and (min_deadline < best_remain):
            best_remain = min_deadline
            best_edge = edge

    if not best_edge:
        # no deadlines found, pick largest queue
        best_edge = max(edge_vehicles, key=lambda e: len(edge_vehicles[e]))

    return best_edge
