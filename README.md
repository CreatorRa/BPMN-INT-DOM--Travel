# Process Mining of University Travel Declarations

This repository contains the replication package for the academic project: Analysis and Comparison of Domestic and International Travel Declarations. This project was conducted as part of the Business Process Management and Mining course at Kühne Logistics University (KLU).

## Project Overview

This analysis investigates the efficiency, compliance, and structural integrity of travel reimbursement workflows at a Dutch university. By employing a dual-tool methodology—combining Python (PM4Py) for mathematical rigor and Celonis (EMS) for visual process exploration—this study identifies systemic bottlenecks, rework loops, and non-conformance patterns.

## Repository Structure

    /Data: Contains the anonymized event logs in .xes format.

    /Scripts: Python notebooks (.ipynb) used for data pre-processing, inductive mining, and conformance checking.

    /Output: Exported visual artifacts, including Petri Net models, performance histograms, and bottleneck analyses.

    /Report: The final academic submission in PDF format.

## Methodology

This project utilizes a dual-lens approach to process mining:

    Programmatic Discovery (Python/PM4Py): Used to generate sound Workflow Nets and compute exact case-level metrics (Fitness/Precision). We employed the Inductive Miner with a noise_threshold = 0.2 to ensure model soundness while retaining the full dataset.

    Visual Discovery (Celonis): Used for interactive process mapping, variant exploration, and business-facing throughput visualization.

## Contact & Credits

This project  was conducted as an academic project at Kühne Logistics University (KLU). The data use was provided as part of the Business Process mining and management course. 