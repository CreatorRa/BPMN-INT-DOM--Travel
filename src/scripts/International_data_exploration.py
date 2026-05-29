import pm4py
import pandas as pd
from pathlib import Path


# ============================================================
# INTERNATIONAL DECLARATIONS - FULL PYTHON ANALYSIS SCRIPT
# ============================================================
# Purpose:
# This script analyzes the International Declarations event log for the
# BPMM assignment.
#
# It answers the International Declarations part of the assignment:
#
# 1. Describe and visualize the general underlying process flow.
# 2. How long do the different process instances take?
# 3. Are there any bottlenecks?
# 4. How many applications get rejected?
# 5. Can we find unexpected behavior, e.g. missing permits?
# 6. Are there patterns that suggest non-conformance?
# 7. Prepare International results for later comparison with Domestic.
# 8. What is missing to provide more detailed insights?
# 9. Where could supervised/unsupervised ML help?
# 10. Useful KPIs.
# 11. Recommendations for process improvement.
#
# Output:
# ONE CSV file:
# Output/tables/international_declarations_analysis_summary.csv
#
# Note:
# CSV files cannot contain multiple sheets like Excel workbooks.
# Therefore, this script saves one structured report-style CSV with
# columns: Question, Section, Metric, Value, Interpretation.
# ============================================================


# ============================================================
# 1. PATH SETTINGS
# ============================================================

def find_project_root() -> Path:
    """
    Finds the project root by searching upward for the Data/raw folder.
    This makes the script more robust if it is placed inside scripts/.
    """
    current = Path(__file__).resolve()

    for parent in [current.parent] + list(current.parents):
        possible_data_path = parent / "Data" / "raw" / "InternationalDeclarations.xes"
        if possible_data_path.exists():
            return parent

    # fallback: use two levels up, similar to the previous script
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = find_project_root()

DATA_PATH = PROJECT_ROOT / "Data" / "raw" / "InternationalDeclarations.xes"

OUTPUT_DIR = PROJECT_ROOT / "Output"
TABLES_DIR = OUTPUT_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

CSV_OUTPUT_PATH = TABLES_DIR / "international_declarations_analysis_summary.csv"


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

report_rows = []


def add_row(question, section, metric, value, interpretation=""):
    """
    Adds one row to the final report-style CSV.
    """
    report_rows.append({
        "Question": question,
        "Section": section,
        "Metric": metric,
        "Value": value,
        "Interpretation": interpretation
    })


def print_section(title):
    """
    Prints a clear section heading in the terminal.
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def format_number(value, decimals=2):
    """
    Formats numeric values for readable CSV output.
    """
    if pd.isna(value):
        return ""
    if isinstance(value, (int,)):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    return str(value)


def activity_contains(activity_set, search_text):
    """
    Checks whether any activity in a case-level set contains a search text.
    """
    return any(search_text.lower() in str(activity).lower() for activity in activity_set)


def first_time(case_df, activity_text, activity_col="concept:name", time_col="time:timestamp"):
    """
    Finds the first timestamp of an activity containing the given text.
    """
    rows = case_df[
        case_df[activity_col].str.contains(activity_text, case=False, na=False)
    ]
    if rows.empty:
        return None
    return rows[time_col].min()


def last_time(case_df, activity_text, activity_col="concept:name", time_col="time:timestamp"):
    """
    Finds the last timestamp of an activity containing the given text.
    """
    rows = case_df[
        case_df[activity_col].str.contains(activity_text, case=False, na=False)
    ]
    if rows.empty:
        return None
    return rows[time_col].max()


def interval_summary(df_sorted, from_activity, to_activity, label, question, section):
    """
    Calculates duration statistics between two activities.
    Uses first occurrence of the start activity and last occurrence of the end activity.
    Only positive / valid durations are summarized.
    Invalid sequence cases are counted separately.
    """
    durations = []
    invalid_order_count = 0
    missing_pair_count = 0

    for case_id, case_df in df_sorted.groupby("case:concept:name"):
        start = first_time(case_df, from_activity)
        end = last_time(case_df, to_activity)

        if start is None or end is None:
            missing_pair_count += 1
            continue

        duration_days = (end - start).total_seconds() / 86400

        if duration_days >= 0:
            durations.append(duration_days)
        else:
            invalid_order_count += 1

    if durations:
        series = pd.Series(durations)
        summary = {
            "Cases included": len(durations),
            "Average days": series.mean(),
            "Median days": series.median(),
            "Minimum days": series.min(),
            "Maximum days": series.max()
        }
    else:
        summary = {
            "Cases included": 0,
            "Average days": None,
            "Median days": None,
            "Minimum days": None,
            "Maximum days": None
        }

    add_row(question, section, f"{label} - Cases included", summary["Cases included"],
            "Cases where both activities exist and the sequence has a non-negative duration.")
    add_row(question, section, f"{label} - Average days",
            round(summary["Average days"], 2) if summary["Average days"] is not None else "",
            "Average duration for this process interval.")
    add_row(question, section, f"{label} - Median days",
            round(summary["Median days"], 2) if summary["Median days"] is not None else "",
            "Median duration for this process interval.")
    add_row(question, section, f"{label} - Minimum days",
            round(summary["Minimum days"], 2) if summary["Minimum days"] is not None else "",
            "Shortest observed valid duration.")
    add_row(question, section, f"{label} - Maximum days",
            round(summary["Maximum days"], 2) if summary["Maximum days"] is not None else "",
            "Longest observed valid duration.")
    add_row(question, section, f"{label} - Invalid order cases", invalid_order_count,
            "Cases where the end activity timestamp occurred before the start activity timestamp.")
    add_row(question, section, f"{label} - Missing pair cases", missing_pair_count,
            "Cases where at least one of the two selected activities was missing.")

    return summary


# ============================================================
# 3. LOAD EVENT LOG
# ============================================================

print_section("LOADING INTERNATIONAL DECLARATIONS EVENT LOG")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"InternationalDeclarations.xes was not found at:\n{DATA_PATH}\n\n"
        "Please check that your file is saved in Data/raw/InternationalDeclarations.xes"
    )

log_object = pm4py.read_xes(str(DATA_PATH))

# pm4py may return a DataFrame directly or an EventLog object depending on version
if isinstance(log_object, pd.DataFrame):
    df = log_object.copy()
else:
    df = pm4py.convert_to_dataframe(log_object)

print("International Declarations log loaded successfully.")
print("Object type after loading:", type(df))
print("Rows:", len(df))
print("Columns:", df.columns.tolist())


# ============================================================
# 4. VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = ["case:concept:name", "concept:name", "time:timestamp"]

missing_required_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_required_columns:
    raise ValueError(
        f"The following required columns are missing: {missing_required_columns}\n"
        "The script expects case:concept:name, concept:name, and time:timestamp."
    )

df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")

if df["time:timestamp"].isna().any():
    print("Warning: Some timestamps could not be converted and are missing after conversion.")


# Sort the event log for sequence-based analysis
df_sorted = df.sort_values(["case:concept:name", "time:timestamp"]).copy()


# ============================================================
# 5. BASIC EVENT LOG STATISTICS
# ============================================================

print_section("BASIC EVENT LOG STATISTICS")

total_events = len(df_sorted)
total_cases = df_sorted["case:concept:name"].nunique()
unique_activities = df_sorted["concept:name"].nunique()
start_date = df_sorted["time:timestamp"].min()
end_date = df_sorted["time:timestamp"].max()

print(f"Total events: {total_events:,}")
print(f"Total cases: {total_cases:,}")
print(f"Unique activities: {unique_activities:,}")
print(f"Time coverage: {start_date} to {end_date}")

add_row("General data overview", "Basic statistics", "Total cases", total_cases,
        "Number of international declaration process instances.")
add_row("General data overview", "Basic statistics", "Total events", total_events,
        "Number of recorded events in the International Declarations log.")
add_row("General data overview", "Basic statistics", "Unique activities", unique_activities,
        "Number of different activity names in the process.")
add_row("General data overview", "Basic statistics", "Start date", start_date,
        "Earliest timestamp in the event log.")
add_row("General data overview", "Basic statistics", "End date", end_date,
        "Latest timestamp in the event log.")


# ============================================================
# 6. MISSING VALUES CHECK
# ============================================================

print_section("MISSING VALUES CHECK")

missing_values = df_sorted.isna().sum().reset_index()
missing_values.columns = ["Column", "Missing Values"]
missing_values["Missing Percentage"] = round(
    (missing_values["Missing Values"] / len(df_sorted)) * 100, 2
)

print(missing_values)

for _, row in missing_values.iterrows():
    add_row(
        "Data quality",
        "Missing values",
        row["Column"],
        f"{row['Missing Values']} missing values ({row['Missing Percentage']}%)",
        "Missing values may limit deeper business interpretation if they occur in important columns."
    )


# ============================================================
# 7. ACTIVITY FREQUENCY
# ============================================================

print_section("ACTIVITY FREQUENCY")

activity_frequency = (
    df_sorted["concept:name"]
    .value_counts()
    .reset_index()
)
activity_frequency.columns = ["Activity", "Frequency"]
activity_frequency["Percentage"] = round(
    activity_frequency["Frequency"] / total_events * 100, 2
)

print(activity_frequency)

for _, row in activity_frequency.head(20).iterrows():
    add_row(
        "1. Describe and visualize the general process flow",
        "Most frequent activities",
        row["Activity"],
        f"{row['Frequency']} events ({row['Percentage']}%)",
        "Frequently occurring activities help describe the dominant process behavior."
    )


# ============================================================
# 8. EVENTS PER CASE
# ============================================================

print_section("EVENTS PER CASE")

events_per_case = (
    df_sorted.groupby("case:concept:name")
    .size()
    .reset_index(name="Number of Events")
)

events_summary = events_per_case["Number of Events"].describe()

print(events_summary)

for stat_name, stat_value in events_summary.items():
    add_row(
        "Process complexity",
        "Events per case",
        stat_name,
        round(stat_value, 2),
        "Shows how many activities are typically recorded per case."
    )


# ============================================================
# 9. CASE THROUGHPUT TIME FROM FIRST EVENT TO LAST EVENT
# ============================================================

print_section("CASE THROUGHPUT TIME: FIRST EVENT TO LAST EVENT")

case_times = (
    df_sorted.groupby("case:concept:name")["time:timestamp"]
    .agg(["min", "max"])
    .reset_index()
)
case_times.columns = ["Case ID", "Start Time", "End Time"]
case_times["Throughput Days"] = (
    (case_times["End Time"] - case_times["Start Time"]).dt.total_seconds() / 86400
)

throughput_summary = case_times["Throughput Days"].describe()

print(throughput_summary)

for stat_name, stat_value in throughput_summary.items():
    add_row(
        "2. How long do the different process instances take?",
        "Full case duration from first event to last event",
        stat_name,
        round(stat_value, 2),
        "General case duration based on first and last recorded event in each case."
    )


# ============================================================
# 10. VARIANT ANALYSIS
# ============================================================

print_section("VARIANT ANALYSIS")

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
    variant_frequency["Frequency"] / total_cases * 100, 2
)
variant_frequency["Cumulative Percentage"] = variant_frequency["Percentage"].cumsum()

total_variants = len(variant_frequency)
top1_variant_coverage = variant_frequency.head(1)["Percentage"].sum()
top5_variant_coverage = variant_frequency.head(5)["Percentage"].sum()
top10_variant_coverage = variant_frequency.head(10)["Percentage"].sum()

print(f"Total unique variants: {total_variants}")
print("Top 10 variants:")
print(variant_frequency.head(10))

add_row("1. Describe and visualize the general process flow",
        "Variant analysis",
        "Total unique variants",
        total_variants,
        "High number of variants indicates process variability and complexity.")

add_row("1. Describe and visualize the general process flow",
        "Variant analysis",
        "Top 1 variant coverage",
        f"{round(top1_variant_coverage, 2)}%",
        "Shows how much of the log follows the most common process path.")

add_row("1. Describe and visualize the general process flow",
        "Variant analysis",
        "Top 5 variant coverage",
        f"{round(top5_variant_coverage, 2)}%",
        "Shows how concentrated or fragmented the process is.")

add_row("1. Describe and visualize the general process flow",
        "Variant analysis",
        "Top 10 variant coverage",
        f"{round(top10_variant_coverage, 2)}%",
        "Additional measure of process standardization.")

for index, row in variant_frequency.head(10).iterrows():
    add_row(
        "1. Describe and visualize the general process flow",
        "Top 10 variants",
        f"Variant {index + 1}",
        f"{row['Frequency']} cases ({row['Percentage']}%)",
        row["Variant"]
    )


# ============================================================
# 11. START AND END ACTIVITY ANALYSIS
# ============================================================

print_section("START AND END ACTIVITY ANALYSIS")

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
    start_activity_frequency["Frequency"] / total_cases * 100, 2
)

end_activity_frequency = (
    first_last_activities["End_Activity"]
    .value_counts()
    .reset_index()
)
end_activity_frequency.columns = ["End Activity", "Frequency"]
end_activity_frequency["Percentage"] = round(
    end_activity_frequency["Frequency"] / total_cases * 100, 2
)

print("\nStart activities:")
print(start_activity_frequency)

print("\nEnd activities:")
print(end_activity_frequency)

for _, row in start_activity_frequency.iterrows():
    add_row(
        "1. Describe and visualize the general process flow",
        "Start activities",
        row["Start Activity"],
        f"{row['Frequency']} cases ({row['Percentage']}%)",
        "Shows how cases begin in the log."
    )

for _, row in end_activity_frequency.iterrows():
    add_row(
        "1. Describe and visualize the general process flow",
        "End activities",
        row["End Activity"],
        f"{row['Frequency']} cases ({row['Percentage']}%)",
        "Shows how cases end in the log."
    )


# ============================================================
# 12. PROCESS FLOW INTERPRETATION
# ============================================================

expected_flow = (
    "Permit submitted by employee -> Permit approved -> Permit final approved -> "
    "Start trip -> End trip -> Declaration submitted -> Declaration approved -> "
    "Declaration final approved -> Request payment -> Payment handled"
)

add_row(
    "1. Describe and visualize the general process flow",
    "Expected high-level flow",
    "International declaration process",
    expected_flow,
    "The international process includes a permit phase before travel and a declaration/payment phase after travel."
)


# ============================================================
# 13. DETAILED THROUGHPUT INTERVALS
# ============================================================

print_section("DETAILED THROUGHPUT INTERVALS")

# These intervals correspond to the analysis used in the report.
intervals = [
    (
        "Permit SUBMITTED by EMPLOYEE",
        "Payment Handled",
        "Permit Submitted by Employee -> Payment Handled",
        "Full international process duration"
    ),
    (
        "End trip",
        "Payment Handled",
        "End Trip -> Payment Handled",
        "Post-trip duration until final payment"
    ),
    (
        "Declaration SUBMITTED by EMPLOYEE",
        "Payment Handled",
        "Declaration Submitted by Employee -> Payment Handled",
        "Reimbursement processing duration"
    ),
    (
        "End trip",
        "Declaration SUBMITTED by EMPLOYEE",
        "End Trip -> Declaration Submitted by Employee",
        "Employee delay before submitting declaration"
    ),
    (
        "Request Payment",
        "Payment Handled",
        "Request Payment -> Payment Handled",
        "Payment processing duration"
    )
]

for from_activity, to_activity, label, interpretation in intervals:
    summary = interval_summary(
        df_sorted=df_sorted,
        from_activity=from_activity,
        to_activity=to_activity,
        label=label,
        question="2. How long do the different process instances take?",
        section="Throughput time intervals"
    )
    print(f"\n{label}")
    print(summary)


# ============================================================
# 14. BOTTLENECK ANALYSIS
# ============================================================

print_section("BOTTLENECK ANALYSIS")

bottleneck_intervals = [
    (
        "Permit SUBMITTED by EMPLOYEE",
        "Permit APPROVED by ADMINISTRATION",
        "Permit Submitted -> Permit Approved by Administration"
    ),
    (
        "Permit APPROVED by ADMINISTRATION",
        "Permit FINAL_APPROVED by SUPERVISOR",
        "Permit Approved by Administration -> Permit Final Approved by Supervisor"
    ),
    (
        "End trip",
        "Declaration SUBMITTED by EMPLOYEE",
        "End Trip -> Declaration Submitted by Employee"
    ),
    (
        "Declaration SUBMITTED by EMPLOYEE",
        "Declaration APPROVED by ADMINISTRATION",
        "Declaration Submitted -> Declaration Approved by Administration"
    ),
    (
        "Declaration FINAL_APPROVED by SUPERVISOR",
        "Request Payment",
        "Declaration Final Approved by Supervisor -> Request Payment"
    ),
    (
        "Request Payment",
        "Payment Handled",
        "Request Payment -> Payment Handled"
    )
]

bottleneck_summaries = []

for from_activity, to_activity, label in bottleneck_intervals:
    summary = interval_summary(
        df_sorted=df_sorted,
        from_activity=from_activity,
        to_activity=to_activity,
        label=label,
        question="3. Are there any bottlenecks?",
        section="Bottleneck intervals"
    )
    bottleneck_summaries.append((label, summary))
    print(f"\n{label}")
    print(summary)

# Identify bottleneck based on highest median duration among valid intervals
valid_bottlenecks = [
    (label, summary["Median days"], summary["Average days"])
    for label, summary in bottleneck_summaries
    if summary["Median days"] is not None
]

if valid_bottlenecks:
    main_bottleneck = max(valid_bottlenecks, key=lambda x: x[1])
    add_row(
        "3. Are there any bottlenecks?",
        "Main bottleneck",
        "Largest median delay interval",
        main_bottleneck[0],
        f"This interval has the largest median duration among the checked bottleneck intervals. "
        f"Median days: {round(main_bottleneck[1], 2)}; Average days: {round(main_bottleneck[2], 2)}."
    )


# ============================================================
# 15. REJECTION ANALYSIS
# ============================================================

print_section("REJECTION ANALYSIS")

rejection_events = df_sorted[
    df_sorted["concept:name"].str.contains("REJECTED", case=False, na=False)
].copy()

rejected_cases = rejection_events["case:concept:name"].nunique()
rejection_rate = round((rejected_cases / total_cases) * 100, 2)

print(f"Rejected cases: {rejected_cases:,}")
print(f"Rejection rate: {rejection_rate}%")

add_row(
    "4. How many applications get rejected?",
    "Rejection summary",
    "Rejected cases",
    rejected_cases,
    "Number of unique cases with at least one rejection-related activity."
)

add_row(
    "4. How many applications get rejected?",
    "Rejection summary",
    "Rejection rate",
    f"{rejection_rate}%",
    "Rejected cases divided by total cases."
)

rejection_activity_event_count = (
    rejection_events["concept:name"]
    .value_counts()
    .reset_index()
)
rejection_activity_event_count.columns = ["Rejection Activity", "Event Count"]

rejection_activity_case_count = (
    rejection_events
    .groupby("concept:name")["case:concept:name"]
    .nunique()
    .sort_values(ascending=False)
    .reset_index()
)
rejection_activity_case_count.columns = ["Rejection Activity", "Case Count"]

print("\nRejection activities by event count:")
print(rejection_activity_event_count)

print("\nRejection activities by case count:")
print(rejection_activity_case_count)

for _, row in rejection_activity_case_count.iterrows():
    add_row(
        "4. How many applications get rejected?",
        "Rejection activities by case count",
        row["Rejection Activity"],
        row["Case Count"],
        "Case count is preferred because one case can contain repeated rejection events."
    )

for _, row in rejection_activity_event_count.iterrows():
    add_row(
        "4. How many applications get rejected?",
        "Rejection activities by event count",
        row["Rejection Activity"],
        row["Event Count"],
        "Event count can be higher than case count because one case may contain repeated rejection activities."
    )


# ============================================================
# 16. CASE-LEVEL ACTIVITY SETS
# ============================================================

case_activities = (
    df_sorted.groupby("case:concept:name")["concept:name"]
    .apply(lambda x: set(x))
)


# ============================================================
# 17. UNEXPECTED BEHAVIOR / MISSING PERMIT CHECK
# ============================================================

print_section("UNEXPECTED BEHAVIOR / MISSING PERMIT CHECK")

declaration_without_permit = case_activities[
    case_activities.apply(lambda acts:
        activity_contains(acts, "Declaration SUBMITTED by EMPLOYEE")
        and not activity_contains(acts, "Permit SUBMITTED by EMPLOYEE")
    )
]

payment_without_permit = case_activities[
    case_activities.apply(lambda acts:
        activity_contains(acts, "Payment Handled")
        and not activity_contains(acts, "Permit SUBMITTED by EMPLOYEE")
    )
]

payment_without_final_permit = case_activities[
    case_activities.apply(lambda acts:
        activity_contains(acts, "Payment Handled")
        and not activity_contains(acts, "Permit FINAL_APPROVED")
    )
]

payment_without_final_declaration = case_activities[
    case_activities.apply(lambda acts:
        activity_contains(acts, "Payment Handled")
        and not activity_contains(acts, "Declaration FINAL_APPROVED")
    )
]

unexpected_checks = [
    (
        "Declaration submitted but no permit submitted",
        len(declaration_without_permit),
        "Possible missing permit record before declaration submission."
    ),
    (
        "Payment handled but no permit submitted",
        len(payment_without_permit),
        "Possible payment despite missing permit record."
    ),
    (
        "Payment handled but no permit final approval",
        len(payment_without_final_permit),
        "Possible payment without completed permit approval."
    ),
    (
        "Payment handled but no declaration final approval",
        len(payment_without_final_declaration),
        "Important approval-control check before payment."
    )
]

for metric, value, interpretation in unexpected_checks:
    print(f"{metric}: {value:,}")
    add_row(
        "5. Can you find unexpected behavior, e.g. missing permits?",
        "Missing permit / approval checks",
        metric,
        value,
        interpretation
    )


# ============================================================
# 18. SEQUENCE / NON-CONFORMANCE CHECKS
# ============================================================

print_section("SEQUENCE / NON-CONFORMANCE CHECKS")

payment_before_end_trip = 0
start_trip_after_payment = 0
start_trip_before_permit_final_approval = 0
declaration_before_end_trip = 0
payment_before_request_payment = 0

for case_id, case_df in df_sorted.groupby("case:concept:name"):
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

sequence_checks = [
    (
        "Payment Handled before End trip",
        payment_before_end_trip,
        "Payment appears before trip completion. This may suggest non-conformance or timestamp/data-quality issues."
    ),
    (
        "Start trip after Payment Handled",
        start_trip_after_payment,
        "Trip appears to start after payment is already handled. This is an abnormal sequence."
    ),
    (
        "Start trip before Permit Final Approval",
        start_trip_before_permit_final_approval,
        "Trip appears to start before permit approval is fully completed."
    ),
    (
        "Declaration Submitted before End trip",
        declaration_before_end_trip,
        "Declaration appears before trip completion. This may be allowed only if policy permits early submission."
    ),
    (
        "Payment Handled before Request Payment",
        payment_before_request_payment,
        "Payment appears before the payment request event."
    )
]

for metric, value, interpretation in sequence_checks:
    print(f"{metric}: {value:,}")
    add_row(
        "5. Can you find unexpected behavior, e.g. missing permits?",
        "Sequence/order checks",
        metric,
        value,
        interpretation
    )
    add_row(
        "6. Are there patterns that would suggest non-conformance?",
        "Non-conformance indicators",
        metric,
        value,
        interpretation
    )

add_row(
    "6. Are there patterns that would suggest non-conformance?",
    "Positive conformance check",
    "Payment handled without declaration final approval",
    len(payment_without_final_declaration),
    "A value of 0 suggests that payment does not bypass declaration final approval."
)


# ============================================================
# 19. INTERNATIONAL RESULTS FOR LATER COMPARISON
# ============================================================

print_section("INTERNATIONAL RESULTS FOR LATER COMPARISON")

comparison_metrics = [
    ("Total cases", total_cases, "International log size."),
    ("Total events", total_events, "Total number of recorded events."),
    ("Unique activities", unique_activities, "Number of activities in the international process."),
    ("Unique variants", total_variants, "Number of unique process paths identified by Python."),
    ("Top 1 variant coverage", f"{round(top1_variant_coverage, 2)}%", "Share of cases following the most common variant."),
    ("Top 5 variant coverage", f"{round(top5_variant_coverage, 2)}%", "Share of cases covered by the five most common variants."),
    ("Rejected cases", rejected_cases, "Cases with at least one rejection activity."),
    ("Rejection rate", f"{rejection_rate}%", "Rejected cases divided by total cases."),
    ("Main bottleneck", main_bottleneck[0] if valid_bottlenecks else "", "Based on largest median delay among checked intervals."),
    ("Main non-conformance indicator", "Start trip before Permit Final Approval", f"{start_trip_before_permit_final_approval} cases.")
]

for metric, value, interpretation in comparison_metrics:
    add_row(
        "7. International results prepared for later comparison",
        "International-only comparison metrics",
        metric,
        value,
        interpretation
    )


# ============================================================
# 20. MISSING INFORMATION FOR DEEPER INSIGHTS
# ============================================================

missing_insight_items = [
    ("Rejection reasons", "Needed to identify exact causes of rejection."),
    ("Document status", "Needed to know whether receipts or attachments were missing."),
    ("Travel purpose", "Needed to explain why some cases require more approvals."),
    ("Destination country", "Needed to analyze risk or complexity by destination."),
    ("Claim amount or amount category", "Needed to assess whether high-value trips follow different paths."),
    ("Department or faculty", "Needed to detect department-specific bottlenecks."),
    ("Approver ID or workload", "Needed to identify workload-related delays."),
    ("Official SLA targets", "Needed to judge whether observed durations are acceptable."),
    ("Official conformance rules", "Needed to distinguish real violations from legitimate exceptions."),
    ("Actual vs planned travel dates", "Needed to interpret sequence anomalies around trip start/end.")
]

for metric, interpretation in missing_insight_items:
    add_row(
        "8. What is missing to provide more detailed insights?",
        "Missing data / context",
        metric,
        "Missing or not explicit in the log",
        interpretation
    )


# ============================================================
# 21. MACHINE LEARNING OPPORTUNITIES
# ============================================================

supervised_ml_items = [
    ("Predict rejection risk", "Use case features to predict whether a declaration is likely to be rejected."),
    ("Predict long-running cases", "Predict cases likely to exceed 60/90 days or SLA thresholds."),
    ("Predict late declaration submission", "Identify employees/cases likely to delay submission after trip end."),
    ("Predict missing permit risk", "Flag cases likely to have missing permit-related records."),
    ("Predict payment delay", "Identify cases likely to take long after payment request.")
]

unsupervised_ml_items = [
    ("Cluster process variants", "Group similar variants into standard, approval-heavy, rejection-heavy, or anomalous paths."),
    ("Anomaly detection", "Detect unusual sequences such as payment before trip end."),
    ("Outlier detection", "Identify extremely long-running cases."),
    ("Sequence clustering", "Group cases based on activity order."),
    ("Rework pattern discovery", "Identify repeated rejection or correction loops.")
]

for metric, interpretation in supervised_ml_items:
    add_row(
        "9. Reflect on where supervised / unsupervised ML could help",
        "Supervised machine learning",
        metric,
        "Potential use case",
        interpretation
    )

for metric, interpretation in unsupervised_ml_items:
    add_row(
        "9. Reflect on where supervised / unsupervised ML could help",
        "Unsupervised machine learning",
        metric,
        "Potential use case",
        interpretation
    )


# ============================================================
# 22. USEFUL KPIS
# ============================================================

kpi_items = [
    ("Average full throughput time", "Average time from permit submission to payment handled."),
    ("Median full throughput time", "Typical full process duration less affected by outliers."),
    ("End Trip -> Declaration Submitted duration", "Measures employee submission delay after travel."),
    ("Declaration Submitted -> Payment Handled duration", "Measures reimbursement processing time."),
    ("Request Payment -> Payment Handled duration", "Measures finance/payment handling speed."),
    ("Rejection rate", "Percentage of cases with at least one rejection activity."),
    ("Rework rate", "Percentage of cases with repeated rejection or repeated approval loops."),
    ("Missing permit rate", "Percentage of cases with declaration/payment but no recorded permit."),
    ("Start trip before permit final approval rate", "Measures possible travel authorization non-conformance."),
    ("Payment before trip end rate", "Measures abnormal payment timing."),
    ("Number of variants", "Measures process complexity."),
    ("Top 5 variant coverage", "Measures process standardization."),
    ("Cases exceeding SLA threshold", "Tracks cases requiring escalation.")
]

for metric, interpretation in kpi_items:
    add_row(
        "10. Can you think of useful KPIs?",
        "Recommended KPIs",
        metric,
        "Recommended KPI",
        interpretation
    )


# ============================================================
# 23. RECOMMENDATIONS
# ============================================================

recommendations = [
    (
        "Introduce post-trip declaration reminders",
        "Send reminders 3, 7, and 14 days after trip end to reduce late employee submissions."
    ),
    (
        "Add mandatory declaration submission checks",
        "Require receipts, dates, cost category, amount information, and permit reference before submission."
    ),
    (
        "Add automatic permit validation",
        "Flag or block cases where payment is requested without a valid permit submission and permit final approval."
    ),
    (
        "Monitor trips starting before permit final approval",
        "Trigger alerts when Start trip occurs before Permit Final Approval."
    ),
    (
        "Escalate long-running cases",
        "Create escalation rules for cases open longer than 30, 60, 90, or 180 days."
    ),
    (
        "Add rejection-reason fields",
        "Require users or approvers to record why a permit or declaration was rejected."
    ),
    (
        "Review rare and complex variants",
        "Investigate low-frequency variants to determine whether they are legitimate exceptions or unnecessary deviations."
    ),
    (
        "Improve timestamp reliability",
        "Clarify whether trip start/end dates are planned or actual dates and validate impossible sequences."
    ),
    (
        "Create a process monitoring dashboard",
        "Monitor throughput time, rejection rate, missing permits, non-conformance patterns, and long-running cases."
    )
]

for metric, interpretation in recommendations:
    add_row(
        "11. Make specific recommendations for improving the process",
        "Recommendations",
        metric,
        "Recommended action",
        interpretation
    )


# ============================================================
# 24. PYTHON AND CELONIS COMPARISON NOTES
# ============================================================

tool_comparison_items = [
    (
        "Python strength",
        "Exact case-level calculations, rejection rates, sequence checks, missing-permit checks, and reproducibility."
    ),
    (
        "Celonis strength",
        "Visual process maps, Variant Explorer, Process Explorer, Throughput Time Explorer, and communication through screenshots."
    ),
    (
        "Python limitation",
        "Less visually intuitive unless additional plotting or PM4Py visualization is added."
    ),
    (
        "Celonis limitation",
        "Some case-level filtering can be difficult or misleading if filters use all-activity logic instead of any-activity logic."
    ),
    (
        "Combined value",
        "Celonis makes the process understandable visually, while Python confirms the findings with exact numbers."
    )
]

for metric, interpretation in tool_comparison_items:
    add_row(
        "Tool comparison",
        "Python vs Celonis",
        metric,
        "Observation",
        interpretation
    )


# ============================================================
# 25. EXPORT TO ONE CSV FILE
# ============================================================

print_section("EXPORTING RESULTS TO ONE CSV FILE")

report_df = pd.DataFrame(report_rows)

# Convert timestamps and complex objects to string-safe format
for col in report_df.columns:
    report_df[col] = report_df[col].astype(str)

report_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding="utf-8-sig")

print(f"CSV file saved here:\n{CSV_OUTPUT_PATH}")


# ============================================================
# 26. FINAL TERMINAL SUMMARY
# ============================================================

print_section("FINAL SUMMARY")

print(f"Total cases: {total_cases:,}")
print(f"Total events: {total_events:,}")
print(f"Unique activities: {unique_activities:,}")
print(f"Unique variants: {total_variants:,}")
print(f"Top 1 variant coverage: {round(top1_variant_coverage, 2)}%")
print(f"Top 5 variant coverage: {round(top5_variant_coverage, 2)}%")
print(f"Rejected cases: {rejected_cases:,}")
print(f"Rejection rate: {rejection_rate}%")
print(f"Payment Handled before End trip: {payment_before_end_trip:,}")
print(f"Start trip after Payment Handled: {start_trip_after_payment:,}")
print(f"Start trip before Permit Final Approval: {start_trip_before_permit_final_approval:,}")
print(f"Declaration Submitted before End trip: {declaration_before_end_trip:,}")
print(f"Payment Handled before Request Payment: {payment_before_request_payment:,}")
print(f"Payment handled without declaration final approval: {len(payment_without_final_declaration):,}")

print("\nAnalysis completed successfully.")
print("Only ONE CSV file was created.")