# Process Mining of Domestic University Travel Declarations
### A Dual-Tool Analysis: Programmatic Mining (Python / PM4Py) vs. Visual Mining (Celonis)
*Business Process Management and Mining (BPMM) — Kühne Logistics University*

---

## 1. Introduction

### 1.1 Context and Motivation

When a staff member at a Dutch university travels for work inside the Netherlands, they file a **domestic travel declaration** to be reimbursed. The idea is simple — submit a claim, get it approved, receive the money — but the reality involves several administrative actors (the employee, the administration office, a supervisor, and occasionally a budget owner or pre-approver). Every action they take is time-stamped and stored, producing an **event log**: a digital diary of what actually happened to each claim.

This report mines that domestic event log to understand how the process *really* behaves, rather than how the university *assumes* it behaves.

> **Process mining in one sentence:** it reconstructs the true process from the digital "footprints" left in IT systems. Each footprint records a **case** (one declaration), an **activity** (e.g. "Declaration SUBMITTED by EMPLOYEE"), and a **timestamp**.

### 1.2 Scope of this Report

This report covers the domestic process across four perspectives — **process discovery**, **performance/throughput**, **bottlenecks**, and **compliance/rework** — using a deliberate **dual-tool approach**:

- **Python (PM4Py)** — *programmatic* mining. It gives mathematical exactness: precise case-level metrics, structurally sound models (Petri Nets), and conformance scores computed by replaying every trace.
- **Celonis** — *visual* mining. It gives intuitive, business-facing dashboards (Variant Explorer, Process Explorer, throughput charts) that managers can read at a glance — but which struggle to show the *whole* picture without collapsing into an unreadable "spaghetti" diagram.

The recurring theme is the tension between these two lenses: **Python tells us exactly what is true; Celonis tells us what is easy to see.** As we will show, the two occasionally disagree — and those disagreements are themselves informative.

---

## 2. Methodology and Infrastructure

### 2.1 Tool Selection

The programmatic analysis uses **Python 3** with **PM4Py** (the standard open-source process-mining library), supported by `pandas` for tabular calculations and `matplotlib` for charts. Each perspective lives in its own reproducible script under `src/Domestic_Analysis/`, writing results to `Output/Domestic/`. The visual analysis was produced in **Celonis**, an industry-standard commercial process-mining platform, with screenshots stored in `Output/Celonis-Screenshots/Domestic/`.

### 2.2 Data Preparation and the Discovery Trade-off *(critical)*

The domestic log contains **10,500 cases** built from **56,437 events**, drawn from **17 distinct activities** that combine into **99 unique paths (variants)**. Even at this modest scale, showing all 99 paths at once produces a **"Spaghetti Model"** — a tangle of arrows that explains nothing. The core methodological question is therefore: *how do we simplify the picture without lying about the data?*

**Why we rejected Top-K filtering.** The tempting shortcut — and Celonis's visual default — is to keep only the top few variants and discard the rest. We rejected this as a *modelling* method. Arbitrarily deleting variants throws away exactly the rejections and detours we want to study; in our companion international log the same shortcut would erase up to **~84% of real cases**, producing a flattering "toy model." The domestic log is gentler (its top 5 variants happen to cover ~90% of cases), but the *principle* still holds: the interesting compliance failures live precisely in the long tail that Top-K hides.

**What we chose instead.** For the mathematical model we feed the *entire* log into the **Inductive Miner** and let it prune infrequent behaviour internally via `noise_threshold = 0.2`. This keeps every case in the analysis while suppressing the rarest ~20% of transitions, and — crucially — always yields a **sound Workflow Net** (no deadlocks, no dead ends) that we can rigorously test.

**The Fitness–Precision trade-off.** Model quality is judged on two axes:
- **Fitness** — *can the model replay the behaviour in the log?* (1.0 = explains everything).
- **Precision** — *does the model forbid behaviour that never happened?* (1.0 = allows nothing extra).

Our approach yields **high Fitness (0.9562)** but **low Precision (0.3758)**. This is **deliberate, not a defect.** A low-precision model is "permissive" — it draws a clean backbone and tolerates the many human detours around it. For a messy, human-driven administrative process, this is the honest choice; chasing high precision would simply recreate the spaghetti we set out to avoid.

---

## 3. Analysis of Domestic Travel Declarations

### 3.1 Process Discovery — Petri Net vs. Variant Explorer

**Python (mathematical structure).** The Inductive Miner produces a sound Petri Net capturing the backbone every claim is *supposed* to follow:
`SUBMITTED → APPROVED (Administration / Budget Owner) → FINAL_APPROVED by Supervisor → Request Payment → Payment Handled`.

`[Insert: domestic_petri_net_strict.png here]`

**Celonis (visual variants).** Celonis's Variant Explorer renders the same backbone far more intuitively and even ranks the variants by frequency — but it does so by *showing only a handful of paths at a time*.

`[Insert: domestic_happy_path.png here]`

`[Insert: 1-5_variant_analysis.png here]`

This contrast exposes the key difference between the tools — and a genuine **data discrepancy worth flagging**:

| | Python (PM4Py CSV) | Celonis Variant Explorer |
|---|---|---|
| Happy path (Variant #1) — case count | 4,618 | 4,618 (4.62K) |
| Happy path — **share of cases** | reported as **8.18%** ❌ | **43.98%** ✅ |
| Top-5 variant coverage | (not shown directly) | **~90%** of 10,500 cases |

Both tools agree on the absolute count (4,618 cases follow the happy path). But the Python script's *percentage* is wrong: it divided 4,618 by the **event** count (56,437) instead of the **case** count (10,500), yielding a misleading 8.18%. Celonis, working natively in cases, correctly reports **43.98%**. This is a perfect illustration of the dual-tool value: **Celonis's visual cross-check caught a units bug in the Python output.** The corrected reading is that a single dominant path carries ~44% of all claims, and the top five cover ~90% — confirming the process is, at its core, quite well-behaved.

The flip side is equally important: Celonis reaches 90% coverage only by *hiding* the remaining ~9,500-case tail of 94 rarer variants. The Python Petri Net, by contrast, mathematically folds *all* behaviour into one sound model. **Celonis is easier to read; Python is harder to fool.**

**Conformance scores (Python):**

| Metric | Score |
|---|---|
| Average Trace Fitness | **0.9562** |
| Perfectly fitting traces | **67.53%** |
| Precision | **0.3758** |

### 3.2 Performance and Throughput

**Python (exact distribution).** The mean end-to-end throughput is **11.53 days**, but the distribution is heavily right-skewed: the fastest claims close in under a day while the slowest runs to **469 days**. The histogram peaks sharply in the 5–8 day band and then trails off into a long thin tail.

`[Insert: domestic_duration_histogram.png here]`

**Celonis (business framing).** Celonis visualises the same distribution but headlines a *different* number depending on the view:

`[Insert: variant_throughput_analysis.png here]`

`[Insert: avg_throughput_analysis.png here]`

| Source / view | Reported average |
|---|---|
| Python — raw mean (all cases) | **11.53 days** |
| Celonis — Process start → Process end | **12 days** |
| Celonis — SUBMITTED → Payment Handled | **11 days** |
| Celonis — Performance Overview (*excluding extreme outliers*) | **9 days** |

`[Insert: performance_overview.png here]`

The tools do not contradict each other — they answer slightly different questions. Python reports the honest arithmetic mean, which the 469-day tail inflates toward ~11.5 days. Celonis's headline "**9 days**" deliberately strips extreme outliers to show a typical experience. A critical reader must know *which* number they are quoting: ~9 days is the typical case, ~11.5 days is the true average including the slow tail. **Python is exact; Celonis is digestible — but its convenience can quietly hide the outliers Python forces you to confront.**

### 3.3 Rejection Dynamics and Root Causes — a Systemic IT Design Flaw

**Python (exact counts).** Across the full log, rejections are spread across the hierarchy:

| Rejection type | Frequency |
|---|---|
| REJECTED by EMPLOYEE | 1,365 |
| REJECTED by ADMINISTRATION | 952 |
| REJECTED by SUPERVISOR | 293 |
| **REJECTED by MISSING** | **91** |
| REJECTED by PRE_APPROVER | 86 |
| REJECTED by BUDGET OWNER | 59 |

Most are ordinary *human* rejections. The revealing one is the small, **automated** `Declaration REJECTED by MISSING` — fired by the system itself when required data is absent. Python finds it in **87 cases**, and pinpoints the trigger exactly:

> **86 of these rejections occur immediately after `Declaration FINAL_APPROVED by SUPERVISOR`** — versus only 3, 1, and 1 from any other step.

This is illogical. A supervisor grants a claim its *final* human approval, and only *then* does the system bounce it for missing data. The validation is at the **wrong end of the process** — at the finish line instead of the entrance — so reviewers waste effort on claims the system was always going to reject.

**Celonis (visual proof).** Celonis makes this loop visible. Filtering the Process Explorer to the affected cases shows the offending edge `FINAL_APPROVED by SUPERVISOR → REJECTED by MISSING` and the rework loop back to `SUBMITTED by EMPLOYEE` (≈82 cases), exactly mirroring Python's finding:

`[Insert: non-conformance_exploration.png here]`

`[Insert: rejection_analysis.png here]`

`[Insert: rejection_rework_analysis.png here]`

Here the tools are complementary: **Python proves the pattern numerically (86 of 87); Celonis makes it instantly legible to a manager** as a visible loop on the map.

**Recommendation — a "System Poka-Yoke".** *Poka-yoke* is a quality-engineering term for a design that makes an error impossible. The fix is **upfront data validation**: the system should refuse an incomplete declaration at the moment of submission, not at final approval. This single change would eliminate the entire late-rejection loop and the rework it generates.

### 3.4 Compliance, Rework, and Unexpected Behaviour

**Rework.** Python identifies **1,571 instances of rework loops** — activities repeated within a single case (typically a rejection followed by resubmission). Celonis frames the same phenomenon through its conformance lens:

`[Insert: conformance_overview.png here]`

| Conformance metric (Celonis) | Value |
|---|---|
| Conforming cases | **44%** (4.62K conforming vs. 5.88K non-conforming) |
| Distinct violations | 19 |
| Throughput: violating vs. conforming | **13.2 vs. 9.4 days** |
| Steps per case: violating vs. conforming | **5.7 vs. 5.0** |

This yields a subtle but important lesson about how the two tools define "conformance" differently. Python's **fitness of 0.9562** measures *how much* of each trace fits (a partial-credit score), and reports **67.53%** of traces fitting *perfectly*. Celonis instead labels only **44%** of *cases* as fully conforming to its reference model. The numbers differ because they measure different things — Python scores partial replay against an Inductive-Miner model, Celonis scores binary conformance against its own reference. A naïve reader could quote "96%" or "44%" and tell opposite stories; the disciplined approach is to report **both and explain the definitions.** Celonis also adds a business insight Python does not surface directly: non-conforming cases take **~4 days longer** and **~0.7 extra steps** — rework is measurably expensive.

**Bottlenecks.** Finally, the slowest hand-offs:

`[Insert: domestic_bottlenecks.csv data here]`

| Transition (Python) | Avg days | Cases |
|---|---|---|
| FINAL_APPROVED by Supervisor → Payment Handled | **81.6** | **7** |
| FINAL_APPROVED by Supervisor → REJECTED by MISSING | 11.0 | 86 |
| REJECTED by MISSING → SUBMITTED by EMPLOYEE | 8.6 | 61 |

`[Insert: longest_throughput_delay.png here]`

`[Insert: bottlenecks.png here]`

The eye-catching **81.6-day** delay to "Payment Handled" looks alarming, but Python shows it affects only **7 cases** — a severe but *rare* edge case. Celonis's bottleneck view agrees, ranking the high-*frequency* hand-offs (`Request Payment → Payment Handled`, ~4 days, affecting 96% of cases) as the operationally relevant ones. The genuinely *systemic* problem is not the rare 81-day outlier but the **high-frequency late-rejection loop** of Section 3.3, which is lower in average delay yet entirely preventable.

---

## 4. Conclusion (Domestic)

The domestic declaration process is fundamentally sound — a single happy path carries ~44% of cases and the top five cover ~90% — yet it leaks effort through a preventable design flaw. The combined analysis shows:

- **A fixable IT flaw:** ~87 claims are auto-rejected for *missing data* only *after* a supervisor's final approval (86 of them immediately after), wasting human review. The remedy is an upfront-validation **Poka-Yoke**.
- **Honest performance numbers:** typical claims close in ~9 days, but the true mean is ~11.5 days once the long tail (up to 469 days) is included.
- **Rework is costly:** ~1,571 rework instances; non-conforming cases run ~4 days and ~0.7 steps longer.

Methodologically, the dual-tool approach proved its worth: **Python supplied the exact, structurally sound truth (and Celonis caught a units bug in its variant percentages), while Celonis supplied the intuitive visual context that makes those truths legible to decision-makers.** Neither tool alone would have told the full story — Python risks being unreadable, Celonis risks hiding the tail. Used together, they are far stronger than either in isolation.

---

*All quantitative figures were generated programmatically from the raw `DomesticDeclarations.xes` log using PM4Py; all visual figures are Celonis screenshots. Supporting CSVs and PNGs reside in `Output/Domestic/` and `Output/Celonis-Screenshots/Domestic/`.*
