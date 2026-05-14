import pm4py
import pandas as pd
import os

class ProcessAnalyzer:
    def __init__(self, file_path, output_dir="../output"):
        """Initializes the analyzer with the XES log and output directory."""
        self.file_path = file_path
        self.output_dir = output_dir
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Load data
        print(f"--- Loading Log: {os.path.basename(file_path)} ---")
        self.log = pm4py.read_xes(file_path)
        self.df = pm4py.convert_to_dataframe(self.log)
        
        # Standardize timestamp format
        self.df['time:timestamp'] = pd.to_datetime(self.df['time:timestamp'], utc=True)

    def get_summary_statistics(self):
        """Returns core descriptive statistics for the report[cite: 53, 56]."""
        case_count = len(self.log)
        event_count = len(self.df)
        variants = pm4py.get_variants(self.log)
        
        # Calculate Average Throughput Time in days
        all_durations = pm4py.get_all_case_durations(self.log)
        avg_duration = (sum(all_durations) / len(all_durations)) / 86400 
        
        stats = {
            "Total Cases": case_count,
            "Total Events": event_count,
            "Unique Variants": len(variants),
            "Avg Throughput (Days)": round(avg_duration, 2)
        }
        return stats

    def export_bpmn(self, filename="process_map.png", noise_threshold=0.2):
        """Discovers and saves a BPMN model with a specific level of abstraction[cite: 55, 56]."""
        # Inductive Miner is used to ensure a sound model 
        tree = pm4py.discover_process_tree_inductive(self.log, noise_threshold=noise_threshold)
        bpmn_graph = pm4py.convert_to_bpmn(tree)
        
        path = os.path.join(self.output_dir, filename)
        pm4py.save_vis_bpmn(bpmn_graph, path)
        print(f"BPMN exported to: {path}")

    def analyze_rejections(self, rejection_activity_name="Declaration Rejected"):
        """Calculates the frequency and percentage of rejected applications."""
        # Filter cases that contain the rejection activity
        rejected_cases = pm4py.filter_log_by_activity_presence(self.log, [rejection_activity_name])
        rejection_rate = (len(rejected_cases) / len(self.log)) * 100
        
        return {
            "Rejected Cases": len(rejected_cases),
            "Rejection Rate (%)": round(rejection_rate, 2)
        }
