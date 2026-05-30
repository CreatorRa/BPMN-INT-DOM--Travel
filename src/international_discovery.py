"""
This module discovers a process model from the International
Declarations event log. Instead of pre-filtering variants (which is
unreliable on a log with no single dominant variant), we rely on the
Inductive Miner's built-in infrequent-behaviour filtering via the
``noise_threshold`` parameter. This isolates the dominant "happy path"
behaviour, avoids an unreadable spaghetti model, and still guarantees
a sound, block-structured Workflow Net.

The resulting Petri net is saved as a PNG to the shared ``output/``
directory.
"""

import os

import pandas as pd
import pm4py

# Fraction of infrequent behaviour the Inductive Miner is allowed to
# filter out. Higher -> simpler / stricter "happy path" model.
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
    """Discover a strict happy-path Petri net and save it."""
    df = load_log()

    os.makedirs('output', exist_ok=True)

    # ----------------------------------------------------------
    # Discover a sound Workflow Net with the Inductive Miner.
    # noise_threshold filters infrequent behaviour internally so the
    # model focuses on the dominant happy path.
    # ----------------------------------------------------------
    net, im, fm = pm4py.discover_petri_net_inductive(df, noise_threshold=NOISE_THRESHOLD)

    # ----------------------------------------------------------
    # Save the visual representation
    # ----------------------------------------------------------
    pm4py.save_vis_petri_net(net, im, fm, 'output/international_petri_net_strict.png')
    print(f"Saved strict Petri net visualization (noise_threshold={NOISE_THRESHOLD})")

    print("\nDiscovery complete.")


if __name__ == "__main__":
    main()
