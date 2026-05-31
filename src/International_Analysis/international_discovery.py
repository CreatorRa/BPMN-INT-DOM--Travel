"""
This module discovers a simplified happy-path process model from the
International Declarations event log.

The full International Declarations log contains many variants, rejections,
loops, and exceptional paths. Discovering directly from the full log creates
an unreadable spaghetti-like Petri net. Therefore, this script first filters
the log to the dominant expected happy path and then applies the Inductive
Miner to the filtered log.

The resulting Petri net is saved as a PNG to:
output/International/international_petri_net_happy_path.png
"""

import os
import pandas as pd
import pm4py


# ============================================================
# SETTINGS
# ============================================================

# Since we filter to the happy path first, no additional noise filtering is needed.
NOISE_THRESHOLD = 0.0

# Expected happy path for International Declarations
HAPPY_PATH = [
    "Permit SUBMITTED by EMPLOYEE",
    "Permit APPROVED by ADMINISTRATION",
    "Permit FINAL_APPROVED by SUPERVISOR",
    "Start trip",
    "End trip",
    "Declaration SUBMITTED by EMPLOYEE",
    "Declaration APPROVED by ADMINISTRATION",
    "Declaration FINAL_APPROVED by SUPERVISOR",
    "Request Payment",
    "Payment Handled",
]


# ============================================================
# LOAD LOG
# ============================================================

def load_log():
    """Load the International Declarations XES log as a DataFrame."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up TWO levels: from International_Analysis -> src -> Root
    project_root = os.path.dirname(os.path.dirname(script_dir))

    xes_path = os.path.join(
        project_root,
        "Data",
        "raw",
        "InternationalDeclarations.xes"
    )

    print("=" * 70)
    print("Loading International Declarations log...")
    print("=" * 70)
    print(f"Log path: {xes_path}")

    if not os.path.exists(xes_path):
        raise FileNotFoundError(f"File not found: {xes_path}")

    log = pm4py.read_xes(xes_path)

    if not isinstance(log, pd.DataFrame):
        df = pm4py.convert_to_dataframe(log)
    else:
        df = log.copy()

    required_columns = ["case:concept:name", "concept:name", "time:timestamp"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True)

    df = df.sort_values(
        by=["case:concept:name", "time:timestamp"]
    ).copy()

    print("\nLog loaded successfully.")
    print(f"Total events: {len(df):,}")
    print(f"Total cases: {df['case:concept:name'].nunique():,}")
    print(f"Unique activities: {df['concept:name'].nunique():,}")

    return df


# ============================================================
# HAPPY PATH FILTER
# ============================================================

def filter_happy_path_cases(df):
    """
    Keep only cases whose activity sequence exactly matches the expected
    International Declarations happy path.
    """
    print("\n" + "=" * 70)
    print("Filtering happy-path cases...")
    print("=" * 70)

    variants_per_case = (
        df.groupby("case:concept:name")["concept:name"]
        .apply(list)
        .reset_index()
    )

    variants_per_case.columns = ["Case ID", "Activity Sequence"]

    variants_per_case["Variant"] = variants_per_case["Activity Sequence"].apply(
        lambda activities: " -> ".join(activities)
    )

    happy_path_string = " -> ".join(HAPPY_PATH)

    happy_cases = variants_per_case.loc[
        variants_per_case["Variant"] == happy_path_string,
        "Case ID"
    ]

    print("\nExpected happy path:")
    print(happy_path_string)

    print(f"\nHappy-path cases found: {len(happy_cases):,}")

    if len(happy_cases) == 0:
        print("\nNo exact happy-path cases were found.")
        print("Below are the top 10 variants in the log. Check whether one activity name differs.")
        print("-" * 70)

        top_variants = (
            variants_per_case["Variant"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        top_variants.columns = ["Variant", "Frequency"]
        print(top_variants.to_string(index=False))

        raise ValueError(
            "No exact happy-path cases found. "
            "Update HAPPY_PATH using the exact activity names from the top variants above."
        )

    filtered_df = df[df["case:concept:name"].isin(happy_cases)].copy()

    print(f"Filtered events: {len(filtered_df):,}")
    print(f"Filtered cases: {filtered_df['case:concept:name'].nunique():,}")
    print(f"Filtered activities: {filtered_df['concept:name'].nunique():,}")

    return filtered_df


# ============================================================
# DISCOVER AND SAVE PETRI NET
# ============================================================

def discover_happy_path_petri_net(df):
    """Discover and save a happy-path Petri net as PNG."""
    print("\n" + "=" * 70)
    print("Discovering happy-path Petri net...")
    print("=" * 70)

    os.makedirs("output/International", exist_ok=True)

    output_path = "output/International/international_petri_net_happy_path.png"

    formatted_df = pm4py.format_dataframe(
        df,
        case_id="case:concept:name",
        activity_key="concept:name",
        timestamp_key="time:timestamp"
    )

    net, im, fm = pm4py.discover_petri_net_inductive(
        formatted_df,
        noise_threshold=NOISE_THRESHOLD
    )

    pm4py.save_vis_petri_net(
        net,
        im,
        fm,
        output_path
    )

    print(f"\nSaved happy-path Petri net visualization:")
    print(output_path)


# ============================================================
# MAIN
# ============================================================

def main():
    """Load log, filter happy path, discover Petri net, and save PNG."""
    df = load_log()

    happy_path_df = filter_happy_path_cases(df)

    discover_happy_path_petri_net(happy_path_df)

    print("\n" + "=" * 70)
    print("Discovery complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()