import pm4py
import pandas as pd
from pathlib import Path


# ============================================================
# INTERNATIONAL DECLARATIONS - DATA EXPLORATION SCRIPT
# ============================================================
# Purpose:
# This script explores the International Declarations event log.
# It produces ONE Excel workbook with multiple sheets.
#
# Main questions answered:
# 1. How many cases are in the log?
# 2. How many events are in the log?
# 3. What activities exist in the process?
# 4. What are the most frequent activities?
# 5. What are the most common variants?
# 6. What is the average throughput time?
# 7. Are there missing values in key columns?
# 8. What is the time coverage of the event log?
# 9. How many cases contain rejection-related activities?
# ============================================================


# ------------------------------------------------------------
# 1. Define file paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "Data" / "raw" / "InternationalDeclarations.xes"

OUTPUT_DIR = PROJECT_ROOT / "Output"
TABLES_DIR = OUTPUT_DIR / "tables"

TABLES_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT_PATH = TABLES_DIR / "international_data_exploration.xlsx"


# ------------------------------------------------------------
# 2. Load International Declarations event log
# ------------------------------------------------------------

print("=" * 70)
print("LOADING INTERNATIONAL DECLARATIONS EVENT LOG")
print("=" * 70)

if not DATA_PATH.exists():
    raise FileNotFoundError(f"File not found: {DATA_PATH}")

df = pm4py.read_xes(str(DATA_PATH))

print("\nInternational Declarations log loaded successfully.")
print("Object type:", type(df))


# ------------------------------------------------------------
# 3. Inspect columns
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("COLUMN CHECK")
print("=" * 70)

print("\nColumns in the dataset:")
print(df.columns.tolist())


# ------------------------------------------------------------
# 4. Standardize timestamp column
# ------------------------------------------------------------

df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True)


# ------------------------------------------------------------
# 5. Basic event log statistics
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("BASIC EVENT LOG STATISTICS")
print("=" * 70)

total_events = len(df)
total_cases = df["case:concept:name"].nunique()
total_activities = df["concept:name"].nunique()

start_date = df["time:timestamp"].min()
end_date = df["time:timestamp"].max()

basic_stats = {
    "Log": "International Declarations",
    "Total Events": total_events,
    "Total Cases": total_cases,
    "Unique Activities": total_activities,
    "Start Date": str(start_date),
    "End Date": str(end_date)
}

for key, value in basic_stats.items():
    print(f"{key}: {value}")

basic_stats_df = pd.DataFrame([basic_stats])


# ------------------------------------------------------------
# 6. Preview first rows
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FIRST 10 ROWS")
print("=" * 70)

print(df.head(10))

first_20_rows = df.head(20).copy()

# Remove timezone from timestamp column for Excel export
if "time:timestamp" in first_20_rows.columns:
    first_20_rows["time:timestamp"] = first_20_rows["time:timestamp"].dt.tz_localize(None)


# ------------------------------------------------------------
# 7. Missing values check
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MISSING VALUES CHECK")
print("=" * 70)

missing_values = df.isna().sum().reset_index()
missing_values.columns = ["Column", "Missing Values"]
missing_values["Missing Percentage"] = round(
    (missing_values["Missing Values"] / len(df)) * 100, 2
)

print(missing_values)


# ------------------------------------------------------------
# 8. Activity frequency
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ACTIVITY FREQUENCY")
print("=" * 70)

activity_frequency = (
    df["concept:name"]
    .value_counts()
    .reset_index()
)

activity_frequency.columns = ["Activity", "Frequency"]
activity_frequency["Percentage"] = round(
    (activity_frequency["Frequency"] / total_events) * 100, 2
)

print(activity_frequency)


# ------------------------------------------------------------
# 9. Events per case
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EVENTS PER CASE")
print("=" * 70)

events_per_case = (
    df.groupby("case:concept:name")
    .size()
    .reset_index(name="Number of Events")
)

events_per_case_summary = events_per_case["Number of Events"].describe().reset_index()
events_per_case_summary.columns = ["Statistic", "Value"]

print(events_per_case_summary)


# ------------------------------------------------------------
# 10. Throughput time per case
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("THROUGHPUT TIME ANALYSIS")
print("=" * 70)

case_times = (
    df.groupby("case:concept:name")["time:timestamp"]
    .agg(["min", "max"])
    .reset_index()
)

case_times.columns = ["Case ID", "Start Time", "End Time"]

case_times["Throughput Time"] = case_times["End Time"] - case_times["Start Time"]
case_times["Throughput Days"] = (
    case_times["Throughput Time"].dt.total_seconds() / 86400
)

throughput_summary = case_times["Throughput Days"].describe().reset_index()
throughput_summary.columns = ["Statistic", "Throughput Days"]

print(throughput_summary)

# Excel cannot handle timezone-aware datetime values.
# So we create an Excel-safe copy of the throughput table.
case_times_excel = case_times.copy()
case_times_excel["Start Time"] = case_times_excel["Start Time"].dt.tz_localize(None)
case_times_excel["End Time"] = case_times_excel["End Time"].dt.tz_localize(None)

# Convert timedelta to readable text for Excel
case_times_excel["Throughput Time"] = case_times_excel["Throughput Time"].astype(str)


# ------------------------------------------------------------
# 11. Variant analysis
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VARIANT ANALYSIS")
print("=" * 70)

df_sorted = df.sort_values(
    by=["case:concept:name", "time:timestamp"]
)

variants_per_case = (
    df_sorted.groupby("case:concept:name")["concept:name"]
    .apply(lambda activities: " -> ".join(activities))
    .reset_index()
)

variants_per_case.columns = ["Case ID", "Variant"]

variant_frequency = (
    variants_per_case["Variant"]
    .value_counts()
    .reset_index()
)

variant_frequency.columns = ["Variant", "Frequency"]
variant_frequency["Percentage"] = round(
    (variant_frequency["Frequency"] / total_cases) * 100, 2
)

variant_frequency["Cumulative Percentage"] = variant_frequency["Percentage"].cumsum()

print("\nTotal unique variants:", len(variant_frequency))
print("\nTop 10 variants:")
print(variant_frequency.head(10))


# ------------------------------------------------------------
# 12. Start and end activity analysis
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("START AND END ACTIVITY ANALYSIS")
print("=" * 70)

first_last_activities = (
    df_sorted.groupby("case:concept:name")
    .agg(
        Start_Activity=("concept:name", "first"),
        End_Activity=("concept:name", "last")
    )
    .reset_index()
)

start_activity_frequency = (
    first_last_activities["Start_Activity"]
    .value_counts()
    .reset_index()
)

start_activity_frequency.columns = ["Start Activity", "Frequency"]
start_activity_frequency["Percentage"] = round(
    (start_activity_frequency["Frequency"] / total_cases) * 100, 2
)

end_activity_frequency = (
    first_last_activities["End_Activity"]
    .value_counts()
    .reset_index()
)

end_activity_frequency.columns = ["End Activity", "Frequency"]
end_activity_frequency["Percentage"] = round(
    (end_activity_frequency["Frequency"] / total_cases) * 100, 2
)

print("\nStart activity frequency:")
print(start_activity_frequency)

print("\nEnd activity frequency:")
print(end_activity_frequency)


# ------------------------------------------------------------
# 13. Rejection check
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("REJECTION ACTIVITY CHECK")
print("=" * 70)

all_activities = df["concept:name"].unique()

possible_rejection_activities = [
    activity for activity in all_activities
    if "reject" in str(activity).lower()
]

if possible_rejection_activities:
    print("\nPossible rejection activities found:")
    for activity in possible_rejection_activities:
        print("-", activity)

    # Keep only events where the activity name contains rejection-related wording
    rejection_events = df[
        df["concept:name"].isin(possible_rejection_activities)
    ].copy()

    # Total number of unique cases that contain at least one rejection activity
    rejected_cases = rejection_events["case:concept:name"].nunique()

    # Rejection rate based on cases, not events
    rejection_rate = round((rejected_cases / total_cases) * 100, 2)

    rejection_summary = {
        "Rejected Cases": rejected_cases,
        "Total Cases": total_cases,
        "Rejection Rate (%)": rejection_rate
    }

    print("\nRejection summary:")
    print(rejection_summary)

    print("\nRejection activities by event count:")
    rejection_activity_event_count = (
        rejection_events["concept:name"]
        .value_counts()
        .reset_index()
    )
    rejection_activity_event_count.columns = ["Rejection Activity", "Event Count"]
    print(rejection_activity_event_count)

    print("\nRejection activities by case count:")
    rejection_activity_case_count = (
        rejection_events
        .groupby("concept:name")["case:concept:name"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
    )
    rejection_activity_case_count.columns = ["Rejection Activity", "Case Count"]
    print(rejection_activity_case_count)

else:
    print("No activity containing the word 'reject' was found.")

    rejection_summary = {
        "Rejected Cases": 0,
        "Total Cases": total_cases,
        "Rejection Rate (%)": 0
    }

    rejection_activity_event_count = pd.DataFrame(
        columns=["Rejection Activity", "Event Count"]
    )

    rejection_activity_case_count = pd.DataFrame(
        columns=["Rejection Activity", "Case Count"]
    )

print("\nFinal rejection summary:")
print(rejection_summary)

rejection_summary_df = pd.DataFrame([rejection_summary])


# ============================================================
# 15. UNEXPECTED BEHAVIOR / MISSING PERMIT CHECK
# ============================================================

activity_col = "concept:name"
case_col = "case:concept:name"
time_col = "time:timestamp"

# Sort data by case and timestamp
df_sorted = df.sort_values([case_col, time_col]).copy()

# Create case-level activity sets
case_activities = (
    df_sorted.groupby(case_col)[activity_col]
    .apply(lambda x: set(x))
)

def has_activity(activity_set, text):
    return any(text.lower() in act.lower() for act in activity_set)

total_cases = df_sorted[case_col].nunique()

# 1. Declaration submitted but no permit submitted
declaration_without_permit = case_activities[
    case_activities.apply(lambda acts:
        has_activity(acts, "Declaration SUBMITTED by EMPLOYEE")
        and not has_activity(acts, "Permit SUBMITTED by EMPLOYEE")
    )
]

# 2. Payment handled but no permit submitted
payment_without_permit = case_activities[
    case_activities.apply(lambda acts:
        has_activity(acts, "Payment Handled")
        and not has_activity(acts, "Permit SUBMITTED by EMPLOYEE")
    )
]

# 3. Payment handled but no permit final approval
payment_without_final_permit = case_activities[
    case_activities.apply(lambda acts:
        has_activity(acts, "Payment Handled")
        and not has_activity(acts, "Permit FINAL_APPROVED")
    )
]

# 4. Payment handled but no declaration final approval
payment_without_final_declaration = case_activities[
    case_activities.apply(lambda acts:
        has_activity(acts, "Payment Handled")
        and not has_activity(acts, "Declaration FINAL_APPROVED")
    )
]

# Helper function for sequence/order checks
def first_time(case_df, activity_text):
    rows = case_df[case_df[activity_col].str.contains(activity_text, case=False, na=False)]
    if rows.empty:
        return None
    return rows[time_col].min()

# Sequence checks
payment_before_end_trip = 0
start_trip_after_payment = 0
start_trip_before_permit_final_approval = 0
declaration_before_end_trip = 0
payment_before_request_payment = 0

for case_id, case_df in df_sorted.groupby(case_col):
    start_trip_time = first_time(case_df, "Start trip")
    end_trip_time = first_time(case_df, "End trip")
    payment_time = first_time(case_df, "Payment Handled")
    request_payment_time = first_time(case_df, "Request Payment")
    permit_final_time = first_time(case_df, "Permit FINAL_APPROVED")
    declaration_submit_time = first_time(case_df, "Declaration SUBMITTED by EMPLOYEE")

    if payment_time is not None and end_trip_time is not None and payment_time < end_trip_time:
        payment_before_end_trip += 1

    if start_trip_time is not None and payment_time is not None and start_trip_time > payment_time:
        start_trip_after_payment += 1

    if start_trip_time is not None and permit_final_time is not None and start_trip_time < permit_final_time:
        start_trip_before_permit_final_approval += 1

    if declaration_submit_time is not None and end_trip_time is not None and declaration_submit_time < end_trip_time:
        declaration_before_end_trip += 1

    if payment_time is not None and request_payment_time is not None and payment_time < request_payment_time:
        payment_before_request_payment += 1

print("\n================ UNEXPECTED BEHAVIOR CHECK ================")
print(f"Total cases: {total_cases}")

print("\nMissing permit / approval checks:")
print(f"Cases with declaration submitted but no permit submitted: {len(declaration_without_permit)}")
print(f"Cases with payment handled but no permit submitted: {len(payment_without_permit)}")
print(f"Cases with payment handled but no permit final approval: {len(payment_without_final_permit)}")
print(f"Cases with payment handled but no declaration final approval: {len(payment_without_final_declaration)}")

print("\nSequence/order checks:")
print(f"Cases with Payment Handled before End trip: {payment_before_end_trip}")
print(f"Cases with Start trip after Payment Handled: {start_trip_after_payment}")
print(f"Cases with Start trip before Permit Final Approval: {start_trip_before_permit_final_approval}")
print(f"Cases with Declaration Submitted before End trip: {declaration_before_end_trip}")
print(f"Cases with Payment Handled before Request Payment: {payment_before_request_payment}")


# ------------------------------------------------------------
# 14. Save all outputs into ONE Excel workbook
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EXPORTING RESULTS TO ONE EXCEL FILE")
print("=" * 70)

with pd.ExcelWriter(EXCEL_OUTPUT_PATH, engine="openpyxl") as writer:
    basic_stats_df.to_excel(writer, sheet_name="Basic Statistics", index=False)
    first_20_rows.to_excel(writer, sheet_name="First 20 Rows", index=False)
    missing_values.to_excel(writer, sheet_name="Missing Values", index=False)
    activity_frequency.to_excel(writer, sheet_name="Activity Frequency", index=False)
    events_per_case_summary.to_excel(writer, sheet_name="Events Case Summary", index=False)
    events_per_case.to_excel(writer, sheet_name="Events Per Case", index=False)
    case_times_excel.to_excel(writer, sheet_name="Case Throughput", index=False)
    throughput_summary.to_excel(writer, sheet_name="Throughput Summary", index=False)
    variant_frequency.to_excel(writer, sheet_name="Variant Frequency", index=False)
    variants_per_case.to_excel(writer, sheet_name="Variants Per Case", index=False)
    first_last_activities.to_excel(writer, sheet_name="Start End Per Case", index=False)
    start_activity_frequency.to_excel(writer, sheet_name="Start Activities", index=False)
    end_activity_frequency.to_excel(writer, sheet_name="End Activities", index=False)
    rejection_summary_df.to_excel(writer, sheet_name="Rejection Summary", index=False)
    rejection_activity_event_count.to_excel(writer, sheet_name="Rejection Event Count", index=False)
    rejection_activity_case_count.to_excel(writer, sheet_name="Reject Case Count", index=False)


# ------------------------------------------------------------
# 15. Final confirmation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("DATA EXPLORATION COMPLETED")
print("=" * 70)

print(f"\nExcel file saved here: {EXCEL_OUTPUT_PATH}")
print("\nOnly one Excel workbook is created. No separate CSV files are created.")