"""
Description:
This script combines Step 1 and Step 2 of our exploratory process analysis. 
It loads the domestic travel logs, creates a master list of all unique activities (Step 1), 
and identifies the top 5 most common end-to-end paths or "variants" (Step 2).
Both outputs are saved as clean, Excel-ready CSV files inside the output folder.
"""

import os
import pm4py
import pandas as pd
from pm4py.statistics.traces.generic.log import case_statistics

# We wrap the entire execution in a try-except block to catch any file loading issues as we are working together and we mght store our data in different places.
try:
    # --- SETUP & LOG LOADING ---
    # Load the raw event log file. Think of a log as a big database of digital footprints.
    log = pm4py.read_xes("C:\\Users\\Carter\\OneDrive\\Documents\\KLU\\KLU Studies\\Business Process Mining\\BPMN-INT-DOM--Travel\\Data\\raw\\DomesticDeclarations.xes")
    
    # Convert the log into a standard data table (DataFrame) so we can easily count things.
    df = pm4py.convert_to_dataframe(log)
    
    # Create the output directory if it doesn't exist yet on our computer.
    os.makedirs("output", exist_ok=True)


    # =========================================================================
    # STEP 1: ACTIVITY INVENTORY (Listing all unique actions)
    # =========================================================================
    
    # Count the total number of unique travel requests (Cases).
    total_cases = len(log) 
    
    # Count every single individual step recorded across all requests (Events).
    total_events = len(df)
    
    # Get a list of all the unique activity names used in this process.
    # This helps us see exactly what administrative steps exist (like approvals or rejections).
    activities = df['concept:name'].unique()
    sorted_activities = sorted(activities)
    
    # Put this list of unique activities into a clean table structure.
    activity_table = pd.DataFrame({
        "Index": range(1, len(sorted_activities) + 1),
        "Domestic Process Activity Name": sorted_activities
    })
    
    # Save the activity list as a CSV file. 
    # Index=False keeps Pandas from adding a redundant row-number column.
    activity_csv_path = "output/domestic_activity_list.csv"
    activity_table.to_csv(activity_csv_path, index=False)


    # =========================================================================
    # STEP 2: VARIANT ANALYSIS (Finding the top 5 most common paths)
    # =========================================================================
    
    # Calculate all the unique paths (variants) that people take from start to finish.
    variants = pm4py.get_variants(log)
    total_variants = len(variants)
    
    # Extract the top 5 most frequent paths using pm4py's built-in statistics module.
    top_variants = case_statistics.get_variant_statistics(log)
    top_variants = sorted(top_variants, key=lambda x: x['count'], reverse=True)[:5]
    
    # Format the variant data into rows for our final table.
    # We use a horizontal arrow " → " to visually show the flow of steps in the path.
    variant_rows = []
    for i, v in enumerate(top_variants):
        full_sequence = " → ".join(v['variant'])
        variant_rows.append([
            f"Variant {i+1}",
            v['count'],
            f"{round((v['count'] / total_cases) * 100, 2)}%",
            full_sequence
        ])
        
    # Turn our variant calculations into a structured data table.
    variant_table = pd.DataFrame(
        variant_rows, 
        columns=["Rank", "Occurrences", "Percentage", "Activity Sequence"]
    )
    
    # Save the top variants data as a separate clean CSV file.
    variant_csv_path = "output/domestic_top_variants.csv"
    variant_table.to_csv(variant_csv_path, index=False)


    # --- TERMINAL CONFIRMATION LOGS ---
    # These printouts give us an immediate summary of the data health right in the console.
    print("--- COMBINED EXECUTION SUCCESS ---")
    print(f"Total Cases Analyzed: {total_cases:,}")
    print(f"Total Events Processed: {total_events:,}")
    print(f"Unique Activity Types Found: {len(activities)}")
    print(f"Total Unique Paths (Variants) in Data: {total_variants:,}")
    print(f"\nSaved Step 1 output to: {activity_csv_path}")
    print(f"Saved Step 2 output to: {variant_csv_path}")

except FileNotFoundError:
    print("Execution Error: The file 'DomesticDeclarations.xes' was not found. Please double-check the path.")
except Exception as e:
    print(f"Execution Error: An unexpected error occurred: {e}")