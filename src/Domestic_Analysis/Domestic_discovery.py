"""
This script applies process discovery algorithms to the 'DomesticDeclarations.xes' event log.
It filters out 20% of the most infrequent behavior (noise) to ensure visual simplicity. 
It then applies the Inductive Miner algorithm to guarantee the discovery of a sound, 
block-structured Workflow Net. Finally, it exports the resulting Petri Net as a PNG visualization.
"""

import pm4py
import os

import pm4py
import os

def discover_domestic_petri_net(file_path):
    print("Loading event log...")
    log = pm4py.read_xes(file_path)
    
    print("\n--- Step 1: Strict Noise Filtering (Inductive Miner) ---")
    print("Using the Inductive Miner's noise_threshold to isolate the 'Happy Path'...")
    # The Inductive Miner filters infrequent behaviour internally via noise_threshold. 
    # This is robust even on logs with no single dominant variant (a variant-coverage filter would empty such logs entirely).
    print(f"Original Log Size: {len(log)} cases")

    print("\n--- Step 2: Process Discovery ---")
    print("Discovering Petri Net using the Inductive Miner (noise_threshold=0.2)...")
    net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)
    
    print("\n--- Step 3: Visualization ---")
    os.makedirs('output', exist_ok=True)
    output_image = 'output/domestic_petri_net_strict.png'
    
    pm4py.save_vis_petri_net(net, initial_marking, final_marking, output_image)
    print(f"-> Strict Petri net successfully generated and saved to: {output_image}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # script now lives in src/Domestic_Analysis/, so go up two levels to the project root
    project_root = os.path.dirname(os.path.dirname(script_dir))
    file_path = os.path.join(project_root, 'Data', 'raw', 'DomesticDeclarations.xes')
    
    discover_domestic_petri_net(file_path)