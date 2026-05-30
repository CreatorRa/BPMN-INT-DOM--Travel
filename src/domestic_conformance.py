"""
This script quantitatively verifies the quality of our discovered Petri Net. 
It re-generates the "Happy Path" model using the strict 25% filter, and then 
plays the ENTIRE unfiltered log (all 56,437 cases) through that simplified model 
using Token Replay to calculate the overall Fitness and Precision scores
"""

import pm4py
import os

def check_domestic_conformance(file_path):
    print("Loading event log...")
    log = pm4py.read_xes(file_path)

    print("\n--- Step 1: Re-Discover Strict Model ---")
    filtered_log = pm4py.filter_variants_by_coverage_percentage(log, 0.25)
    net, im, fm = pm4py.discover_petri_net_inductive(filtered_log)

    print("\n--- Step 2: Conformance Checking (Token Replay) ---")
    print("Evaluating the 'Happy Path' model against the entire unfiltered log...\n")

    # Fitness: How much of the actual log behavior can perfectly play through this model?
    print("Calculating Fitness (this may take a moment)...")
    fitness = pm4py.fitness_token_based_replay(log, net, im, fm)
    print(f"Average Trace Fitness: {fitness['average_trace_fitness']:.4f}")
    print(f"Percentage of perfectly fitting traces: {fitness['perc_fit_traces']:.2f}%")

    # Precision: Does the model allow for behavior that was NEVER seen in the log?
    print("\nCalculating Precision...")
    precision = pm4py.precision_token_based_replay(log, net, im, fm)
    print(f"Precision Score: {precision:.4f}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    file_path = os.path.join(project_root, 'Data', 'raw', 'DomesticDeclarations.xes')
    
    check_domestic_conformance(file_path)