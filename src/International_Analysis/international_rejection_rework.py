"""
This script parses the International Declarations log to explicitly extract:
1. Rejection Summary: A count of all rejection types and the number of affected cases.
2. Rework Cases: Identifies process instances where activities were repeated 
   (e.g., submitting a declaration multiple times due to kickbacks).

Outputs two CSV files to Output/International/ to mirror the Domestic analysis.
"""

import os
import pandas as pd
import pm4py

def load_log():
    """Load the International Declarations XES log as a DataFrame."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up TWO levels: from International_Analysis -> src -> Root
    project_root = os.path.dirname(os.path.dirname(script_dir))
    xes_path = os.path.join(project_root, 'Data', 'raw', 'InternationalDeclarations.xes')

    print("Loading International Declarations log...")
    log = pm4py.read_xes(xes_path)

    if not isinstance(log, pd.DataFrame):
        df = pm4py.convert_to_dataframe(log)
    else:
        df = log

    return df, project_root

def main():
    df, project_root = load_log()
    
    # Ensure the output directory exists
    out_dir = os.path.join(project_root, 'Output', 'International')
    os.makedirs(out_dir, exist_ok=True)

    print("\n--- Step 1: Generating Rejection Summary ---")
    # Isolate all events that contain 'REJECTED'
    rejection_mask = df['concept:name'].str.contains('REJECTED', case=False, na=False)
    rejected_events = df[rejection_mask]
    
    # Count total occurrences of each rejection type
    rejection_summary = rejected_events['concept:name'].value_counts().reset_index()
    rejection_summary.columns = ['Rejection Activity', 'Total Occurrences']
    
    # Count unique cases affected by each rejection type
    case_counts = rejected_events.groupby('concept:name')['case:concept:name'].nunique().reset_index()
    case_counts.columns = ['Rejection Activity', 'Affected Cases']
    
    # Merge and save
    rejection_summary = pd.merge(rejection_summary, case_counts, on='Rejection Activity')
    rejection_path = os.path.join(out_dir, 'international_rejection_summary.csv')
    rejection_summary.to_csv(rejection_path, index=False)
    print(f"-> Saved: {rejection_path}")

    print("\n--- Step 2: Generating Rework Cases ---")
    # Rework occurs when an activity is executed more than once within the same case
    activity_counts_per_case = df.groupby(['case:concept:name', 'concept:name']).size().reset_index(name='count')
    
    # Filter only the activities that occurred > 1 time
    rework_activities = activity_counts_per_case[activity_counts_per_case['count'] > 1].copy()
    
    # Calculate how many "extra" redundant steps were taken
    rework_activities['extra_steps'] = rework_activities['count'] - 1
    
    # Summarize the rework per case
    rework_summary = rework_activities.groupby('case:concept:name').agg(
        Activities_Repeated=('concept:name', lambda x: ' | '.join(x)),
        Total_Extra_Steps=('extra_steps', 'sum')
    ).reset_index()
    
    # Sort by the most severe rework cases
    rework_summary = rework_summary.sort_values(by='Total_Extra_Steps', ascending=False)
    
    rework_path = os.path.join(out_dir, 'international_rework_cases.csv')
    rework_summary.to_csv(rework_path, index=False)
    print(f"-> Saved: {rework_path}")
    
    # Terminal Statistics for the Report
    total_cases = df['case:concept:name'].nunique()
    cases_with_rework = len(rework_summary)
    rework_rate = (cases_with_rework / total_cases) * 100
    
    print(f"\n--- Analysis Complete ---")
    print(f"Total Cases with Rework: {cases_with_rework} out of {total_cases} ({rework_rate:.1f}%)")
    if cases_with_rework > 0:
        print(f"Average Extra Steps per Reworked Case: {rework_summary['Total_Extra_Steps'].mean():.2f}")

if __name__ == "__main__":
    main()