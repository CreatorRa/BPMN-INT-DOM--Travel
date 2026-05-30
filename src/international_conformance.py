"""
This module evaluates how well the strict happy-path model represents
the full International Declarations event log. The model is
re-discovered with the Inductive Miner using the same
``noise_threshold`` as the discovery step, and the entire unfiltered
log is then replayed against it using token-based replay.

Fitness and precision scores are printed to the terminal.
"""

import os

import pandas as pd
import pm4py

# Must match the value used in international_discovery.py so that the
# model evaluated here is the same "happy path" model.
NOISE_THRESHOLD = 0.2


def load_log():
    """Load the International Declarations XES log as a DataFrame."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xes_path = os.path.join(script_dir, '..', 'Data', 'raw', 'InternationalDeclarations.xes')

    print("Loading International Declarations log...")
    log = pm4py.read_xes(xes_path)

    if not isinstance(log, pd.DataFrame):
        df = pm4py.convert_to_dataframe(log)
    else:
        df = log

    return df


def main():
    """Replay the full log against the strict model and report scores."""
    df = load_log()

    # ----------------------------------------------------------
    # Re-discover the strict happy-path model (same settings as
    # the discovery script).
    # ----------------------------------------------------------
    net, im, fm = pm4py.discover_petri_net_inductive(df, noise_threshold=NOISE_THRESHOLD)

    # ----------------------------------------------------------
    # Token-based replay of the entire unfiltered log
    # ----------------------------------------------------------
    fitness = pm4py.fitness_token_based_replay(df, net, im, fm)
    precision = pm4py.precision_token_based_replay(df, net, im, fm)

    print(f"\nAverage Trace Fitness: {fitness['average_trace_fitness']:.4f}")
    print(f"Precision Score: {precision:.4f}")

    print("\nConformance analysis complete.")


if __name__ == "__main__":
    main()
