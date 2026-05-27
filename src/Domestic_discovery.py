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
    
    print("\n--- Step 1: Strict Noise Filtering ---")
    print("Applying strict threshold (retaining only the top 25% of standard behavior)...")
    # Severely restrict the log to find the readable 'Happy Path'
    filtered_log = pm4py.filter_variants_by_coverage_percentage(log, 0.25)
    
    print(f"Original Log Size: {len(log)} cases")
    print(f"Filtered Log Size: {len(filtered_log)} cases")

    print("\n--- Step 2: Process Discovery ---")
    print("Discovering Petri Net using the Inductive Miner...")
    net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(filtered_log)
    
    print("\n--- Step 3: Visualization ---")
    os.makedirs('output', exist_ok=True)
    output_image = 'output/domestic_petri_net_strict.png'
    
    pm4py.save_vis_petri_net(net, initial_marking, final_marking, output_image)
    print(f"-> Strict Petri net successfully generated and saved to: {output_image}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    file_path = os.path.join(project_root, 'Data', 'raw', 'DomesticDeclarations.xes')
    
    discover_domestic_petri_net(file_path)