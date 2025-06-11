# root/simulation.py

import traci
import random
from control import edf_pick_edge, fp_pick_edge, get_phase_for_edge
from priority_utils import PRIORITY_MAP

# Traffic Light ID
TLS_ID = "J1"

# Edges that have routes
INCOMING_EDGES = ["E0", "-E1", "-E2", "-E3"]

# The route IDs from routes.rou.xml, keyed by each edge
ROUTE_MAP = {
    "E0":  ["r_0", "r_1", "r_2"],
    "-E1": ["r_6", "r_7", "r_8"],
    "-E2": ["r_3", "r_4", "r_5"],
    "-E3": ["r_9", "r_10", "r_11"]
}

# Weighted priority distribution 
PRIORITY_DISTRIBUTION = {
    "HV": 0.05,
    "MV": 0.15,
    "LV": 0.80
}

# Minimum green time so traffic lights don't flip every step
MIN_GREEN = 8

def run_simulation(control_method="edf"):
    """
    Runs the simulation using either Earliest Deadline First (EDF) or Fixed Priority (FP).
    Spawns vehicles, checks deadlines and then selects an incoming edge based on the chosen algorithm.
    A final summary report is printed at the end.
    """
    step = 0
    max_steps = 2000

    current_phase_edge = None
    time_in_phase = 0

    # Track how many vehicles of each type are spawned/missed
    priority_counts = {
        "HV": {"spawned": 0, "missed": 0},
        "MV": {"spawned": 0, "missed": 0},
        "LV": {"spawned": 0, "missed": 0},
    }

    # Keep a set of vehicles we’ve already flagged as missed
    already_missed = set()

    while step < max_steps:
        traci.simulationStep()

        spawn_vehicles(step, priority_counts)
        check_missed_deadlines(step, priority_counts, already_missed)

        # Gather vehicles on each incoming edge
        edge_vehicles = {
            e: traci.edge.getLastStepVehicleIDs(e)
            for e in INCOMING_EDGES
        }

        # Change phase if no phase chosen yet or if we have fulfilled the minimum green time
        if (current_phase_edge is None) or (time_in_phase >= MIN_GREEN):
            if control_method == "edf":
                chosen_edge = edf_pick_edge(edge_vehicles, step)
            elif control_method == "fixed":
                chosen_edge = fp_pick_edge(edge_vehicles)
            else:
                raise ValueError("Unknown control method: choose 'edf' or 'fixed'")

            phase_idx = get_phase_for_edge(chosen_edge)
            traci.trafficlight.setPhase(TLS_ID, phase_idx)

            current_phase_edge = chosen_edge
            time_in_phase = 0
        else:
            # Remain in the current phase until MIN_GREEN is reached
            pass

        time_in_phase += 1
        step += 1

    # Simulation is finished
    traci.close()
    print_final_report(priority_counts)

def spawn_vehicles(step, priority_counts):
    """
    Every 10 steps, spawn 1 vehicle on each edge.
    Vehicle type is chosen via a weighted distribution (HV < MV < LV).
    A random route is chosen from ROUTE_MAP for the given edge.
    """
    if step % 10 == 0:
        for edge in INCOMING_EDGES:
            veh_id = f"{edge}_{step}"
            vtype = weighted_priority_choice()
            route_list = ROUTE_MAP[edge]
            route_id = random.choice(route_list)

            try:
                traci.vehicle.add(vehID=veh_id, routeID=route_id, typeID=vtype)
                priority_counts[vtype]["spawned"] += 1

                # Set deadlines based on vehicle type
                if vtype == "HV":
                    dl = step + 60
                elif vtype == "MV":
                    dl = step + 80
                else:  # "LV"
                    dl = step + 100

                traci.vehicle.setParameter(veh_id, "deadline", str(dl))

            except traci.TraCIException as e:
                print(f"[Spawn Error] {veh_id}: {e}")

def weighted_priority_choice():
    """
    Returns 'HV', 'MV', or 'LV' based on the distribution in PRIORITY_DISTRIBUTION.
    """
    r = random.random()  # Uniform random in [0, 1)
    cumulative = 0.0
    for ptype, prob in PRIORITY_DISTRIBUTION.items():
        cumulative += prob
        if r < cumulative:
            return ptype
    return "LV"  # fallback

def check_missed_deadlines(current_time, priority_counts, already_missed):
    """
    Count a vehicle’s missed deadline only once.
    If current_time > deadline, increment the missed counter for that vehicle type and flag it.
    """
    for vid in traci.vehicle.getIDList():
        if vid in already_missed:
            continue
        try:
            ds = traci.vehicle.getParameter(vid, "deadline")
            if ds:
                dl = float(ds)
                if current_time > dl:
                    vtype = traci.vehicle.getTypeID(vid)
                    if vtype in priority_counts:
                        priority_counts[vtype]["missed"] += 1
                    already_missed.add(vid)
        except Exception:
            pass

def print_final_report(priority_counts):
    """
    Print a summary of how many vehicles of each priority were spawned and missed,
    along with the overall percentage of missed deadlines.
    """
    print("\n=== FINAL REPORT: Deadline Misses by Priority ===")
    total_spawned = 0
    total_missed = 0

    for ptype in ["HV", "MV", "LV"]:
        s = priority_counts[ptype]["spawned"]
        m = priority_counts[ptype]["missed"]
        total_spawned += s
        total_missed += m

        pct = 100.0 * m / s if s > 0 else 0.0
        print(f"  {ptype}: spawned = {s}, missed = {m}, {pct:.2f}% missed")

    overall_pct = 100.0 * total_missed / total_spawned if total_spawned > 0 else 0.0
    print(f"  Overall: spawned = {total_spawned}, missed = {total_missed}, {overall_pct:.2f}% missed")
    print("=====================================================\n")
