"""
This module documents domain-specific compliance rules for the
International Declarations process and counts how often each rule is
violated. The rules encode the expected ordering of the trip, permit
approval and payment steps in the declaration workflow.

Outputs the violation counts as terminal output so they can be
documented directly in the report.
"""

import os

import pandas as pd
import pm4py


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


def first_index(seq, activity):
    """Return the position of an activity in a sequence, or None if absent."""
    return seq.index(activity) if activity in seq else None


def first_index_prefix(seq, prefix):
    """Return the position of the first activity matching a prefix, or None."""
    for i, act in enumerate(seq):
        if act.startswith(prefix):
            return i
    return None


def main():
    """Identify and count non-compliant cases."""
    df = load_log()

    # Order events within each case chronologically
    df_sorted = df.sort_values(['case:concept:name', 'time:timestamp'])

    # Build a per-case ordered list of activities
    case_sequences = df_sorted.groupby('case:concept:name')['concept:name'].apply(list)

    total_cases = len(case_sequences)
    print(f"\nTotal cases analysed: {total_cases}")

    # ----------------------------------------------------------
    # Compliance rules
    # ----------------------------------------------------------
    violations = {}

    # Rule 1: Payment must not be handled before the trip ends
    payment_before_end = 0
    # Rule 2: The trip must not start before the permit is finally approved
    start_before_permit = 0

    for seq in case_sequences:
        payment_idx = first_index(seq, 'Payment Handled')
        end_idx = first_index(seq, 'End trip')
        if payment_idx is not None and end_idx is not None and payment_idx < end_idx:
            payment_before_end += 1

        start_idx = first_index(seq, 'Start trip')
        permit_idx = first_index_prefix(seq, 'Permit FINAL_APPROVED')
        if start_idx is not None and permit_idx is not None and start_idx < permit_idx:
            start_before_permit += 1

    violations['Payment Handled before End trip'] = payment_before_end
    violations['Start trip before Permit Final Approval'] = start_before_permit

    print(f"\nNon-compliant cases:")
    for rule, count in violations.items():
        print(f"  {rule}: {count}")

    print("\nCompliance analysis complete.")


if __name__ == "__main__":
    main()
