"""
This script performs a targeted compliance and conformance analysis on the 'DomesticDeclarations.xes' log.
Specifically, it isolates all rejection events and identifies cases that get stuck in rework loops.

This script generates the empirical evidence needed to answer two of our key questions:
1. "How many applications get rejected? Can you find any reasons?"
2. "Can you find any unexpected behavior? / Are there any patterns that would suggest non-conformance?"

By exporting these findings into CSVs, we can easily format them into tables for the report and compare them 
against the International log once the Git branch is merged.
"""

import pm4py
import pandas as pd
import os

def analyze_domestic_compliance(file_path):
    # Read the XES file and convert it to a standard pandas dataframe for easier tabular manipulation
    log = pm4py.read_xes(file_path)
    df = pm4py.convert_to_dataframe(log)
    
    # Ensure the shared output directory exists for GitHub synchronization
    os.makedirs('output', exist_ok=True)

    print("\n--- Step 1: Rejection Summary ---")
    """
    While our performance script found the 87 automated 'MISSING' errors, we need a view 
    of organizational rejections to see which hierarchical layer is pushing back the most applications.
    This step isolates every activity containing the word 'REJECTED' to quantify friction.
    """
    # Filter the dataframe for any event where the activity name contains "REJECTED"
    rejections = df[df['concept:name'].str.contains('REJECTED', na=False)]
    
    # Count the total frequency of each specific rejection type
    rejection_summary = rejections['concept:name'].value_counts().reset_index()
    rejection_summary.columns = ['rejection_activity', 'frequency']
    
    print("Organizational Rejection Breakdown:")
    print(rejection_summary)
    rejection_summary.to_csv('output/domestic_rejection_summary.csv', index=False)
    print("-> Saved to output/domestic_rejection_summary.csv")


    print("\n--- Step 2: Rework / Loop Analysis ---")
    """
    The assignment asks us to find "unexpected behavior" and "patterns that would suggest non-conformance."
    In standard business process theory, a well-designed travel declaration should flow sequentially: 
    Submit -> Approve -> Pay. 
    
    If an activity is executed more than once within the exact same case, it indicates a rework loop.
    """
    # Group the data by Case ID and Activity Name, then count how many times that activity occurs per case
    activity_counts = df.groupby(['case:concept:name', 'concept:name']).size().reset_index(name='repeat_count')
    
    # Filter out standard behavior (activities executed exactly once). 
    # We only want activities where the count is strictly greater than 1 (meaning a loop occurred).
    rework_cases = activity_counts[activity_counts['repeat_count'] > 1].sort_values(by='repeat_count', ascending=False)
    
    print(f"\nFound {len(rework_cases)} instances of rework loops (unexpected behavior).")
    rework_cases.to_csv('output/domestic_rework_cases.csv', index=False)
    print("-> Saved to output/domestic_rework_cases.csv")

if __name__ == "__main__":
    # Dynamically locate the file to ensure compatibility across different machines in the shared GitHub repo
    # This prevents 'FileNotFound' errors when your project partner pulls the code.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up TWO levels: from Domestic_Analysis -> src -> Root
    project_root = os.path.dirname(os.path.dirname(script_dir))
    file_path = os.path.join(project_root, 'Data', 'raw', 'DomesticDeclarations.xes')
    
    analyze_domestic_compliance(file_path)