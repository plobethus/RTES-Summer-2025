# root/main.py
import traci
import os
from simulation import run_simulation

print("Library Importation Worked")

# Path to sumo or sumo-gui
SUMO_BINARY = "/usr/share/sumo/bin/sumo-gui"

# Name of SUMO config file
SUMO_CONFIG = "config.sumocfg"

if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = "/usr/share/sumo"

def main():
    try:
        traci.start([SUMO_BINARY, "-c", SUMO_CONFIG])
        
        # Uncomment one and comment the other to run EDF or FP:
        run_simulation(control_method="edf")
        #run_simulation(control_method="fixed")
    finally:
        traci.close()

if __name__ == "__main__":
    main()
