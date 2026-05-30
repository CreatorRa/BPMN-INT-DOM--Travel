"""
This module covers the performance perspective of the International
Declarations event log:
  * Temporal analysis (case throughput times)
  * Variant analysis (most common end-to-end paths)
  * Bottleneck detection (slowest activity transitions)
  * Rejection / rework summary

Outputs CSV summaries and a duration histogram to the shared
``output/`` directory so the results can be compared side-by-side
with the Domestic Declarations analysis.
"""

import os

import pandas as pd
import matplotlib.pyplot as plt
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


def main():
    """Run the full performance analysis pipeline."""
    df = load_log()

    os.makedirs('output', exist_ok=True)

    # ----------------------------------------------------------
    # Basic statistics
    # ----------------------------------------------------------
    num_cases = df['case:concept:name'].nunique()
    print(f"\nTotal cases: {num_cases}")

    # ----------------------------------------------------------
    # Activity list
    # ----------------------------------------------------------
    activities = sorted(df['concept:name'].unique())
    activity_df = pd.DataFrame({
        'activity': activities
    })
    activity_df.index.name = 'index'
    activity_df.to_csv('output/international_activity_list.csv')
    print(f"Saved activity list ({len(activities)} activities)")

    # ----------------------------------------------------------
    # Variant analysis
    # ----------------------------------------------------------
    variants = pm4py.get_variants(df)
    # Sort variants by frequency (descending)
    sorted_variants = sorted(variants.items(), key=lambda x: len(x[1]) if isinstance(x[1], list) else x[1], reverse=True)

    total_cases = num_cases
    top_variants = []
    for rank, (variant, occ) in enumerate(sorted_variants[:5], start=1):
        count = len(occ) if isinstance(occ, list) else occ
        pct = 100.0 * count / total_cases
        sequence = ' -> '.join(variant) if isinstance(variant, tuple) else str(variant)
        top_variants.append({
            'Rank': rank,
            'Occurrences': count,
            'Percentage': round(pct, 2),
            'Activity Sequence': sequence
        })
    pd.DataFrame(top_variants).to_csv('output/international_top_variants.csv', index=False)
    print("Saved top 5 variants")

    # ----------------------------------------------------------
    # Bottleneck analysis (transition times)
    # ----------------------------------------------------------
    df_sorted = df.sort_values(['case:concept:name', 'time:timestamp'])
    df_sorted['next_activity'] = df_sorted.groupby('case:concept:name')['concept:name'].shift(-1)
    df_sorted['next_timestamp'] = df_sorted.groupby('case:concept:name')['time:timestamp'].shift(-1)
    df_sorted['transition_days'] = (
        df_sorted['next_timestamp'] - df_sorted['time:timestamp']
    ).dt.total_seconds() / 86400.0

    transitions = df_sorted.dropna(subset=['next_activity'])
    grouped = transitions.groupby(['concept:name', 'next_activity'])['transition_days'].agg(['mean', 'max', 'count'])
    grouped = grouped.sort_values('mean', ascending=False)
    grouped.head(5).to_csv('output/international_bottlenecks.csv')
    print("Saved top 5 bottlenecks")

    # ----------------------------------------------------------
    # Throughput time analysis
    # ----------------------------------------------------------
    case_durations = df.groupby('case:concept:name')['time:timestamp'].agg(['min', 'max'])
    case_durations['duration_days'] = (
        case_durations['max'] - case_durations['min']
    ).dt.total_seconds() / 86400.0

    avg_dur = case_durations['duration_days'].mean()
    min_dur = case_durations['duration_days'].min()
    max_dur = case_durations['duration_days'].max()

    print(f"\nAverage throughput: {avg_dur:.2f} days")
    print(f"Min throughput: {min_dur:.2f} days")
    print(f"Max throughput: {max_dur:.2f} days")

    # ----------------------------------------------------------
    # Duration histogram
    # ----------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.hist(case_durations['duration_days'], bins=50, edgecolor='black')
    plt.xlabel('Case Duration (days)')
    plt.ylabel('Number of Cases')
    plt.title('International Declarations - Case Duration Distribution')
    plt.tight_layout()
    plt.savefig('output/international_duration_histogram.png', dpi=150)
    plt.close()
    print("Saved duration histogram")

    # ----------------------------------------------------------
    # Rejection / rework summary
    # ----------------------------------------------------------
    df_sorted['prev_activity'] = df_sorted.groupby('case:concept:name')['concept:name'].shift(1)
    rejection_mask = df_sorted['concept:name'].str.contains('REJECTED', case=False, na=False)
    rejections = df_sorted[rejection_mask]
    print(f"\nTotal rejection events: {len(rejections)}")

    if len(rejections) > 0:
        preceding = rejections['prev_activity'].value_counts()
        print("Activities immediately preceding a rejection:")
        for act, cnt in preceding.items():
            print(f"  {act}: {cnt}")

    print("\nPerformance analysis complete.")


if __name__ == "__main__":
    main()
