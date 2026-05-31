# Process Mining of University Travel Declarations
### A Comparative Analysis of Domestic and International Workflows
*Business Process Management and Mining (BPMM) — Kühne Logistics University*

---

## 1. Introduction

### 1.1 Context and Motivation

Every time a researcher or staff member at a Dutch university travels for work, they must file a **travel declaration** so the institution can reimburse their costs. On paper this sounds simple: submit a claim, get it approved, receive the money. In reality, each claim passes through several administrative hands — employees, administration, supervisors, budget owners, and (for international trips) pre-approvers and directors — and every one of these touchpoints leaves a digital footprint in the university's IT system.

This report analyses two real event logs produced by such a system:

- **Domestic Declarations** — claims for travel *inside* the Netherlands.
- **International Declarations** — claims for travel *abroad*, which additionally require a travel **permit** to be approved *before* the trip.

The two processes share the same DNA but differ enormously in scale and complexity. By mining their event logs we can move beyond anecdotes ("the system is slow") and instead *measure* exactly where time is lost, how often claims are rejected, and where the process violates its own rules.

> **What is process mining?** It is a family of techniques that reads the raw "footprints" (events) left in IT systems and reconstructs what the process *actually* did — as opposed to what a manager *thinks* it does. Each footprint records a **case** (one declaration), an **activity** (e.g. "Declaration SUBMITTED"), and a **timestamp**.

### 1.2 Scope of this Report

This is the first half of our study. It covers four perspectives:

1. **Process Discovery** — automatically drawing a map of the process from the data.
2. **Performance** — how long claims take from start to finish (throughput).
3. **Bottlenecks** — which individual hand-offs are the slowest.
4. **Compliance & Rework** — how often claims are rejected, looped back, or executed out of order.

All analysis was performed **programmatically** in Python using the **PM4Py** library, rather than with a point-and-click tool. This makes every result fully reproducible: the same script run on the same data always yields the same numbers.

---

## 2. Methodology and Infrastructure

### 2.1 Tool Selection

We used **Python 3** with **PM4Py**, the standard open-source process-mining library, supported by `pandas` (for tabular calculations) and `matplotlib` (for charts). Each analysis perspective lives in its own script under `src/Domestic_Analysis/` and `src/International_Analysis/`, and every script writes its results to the shared `Output/` folder as CSV tables and PNG images. Choosing code over a graphical tool was deliberate: it forces our assumptions to be explicit and lets a teammate re-run the entire study with a single command.

### 2.2 Data Preparation and the Discovery Trade-off *(critical)*

Real administrative logs are *messy*. The international log alone contains **753 distinct paths** through the process. If we feed all of that noise into a discovery algorithm, we get a so-called **"Spaghetti Model"** — a diagram with so many crossing arrows that it teaches us nothing. The central methodological question of this report is therefore: **how do we simplify the picture without lying about the data?**

We considered three options and rejected the first two:

1. **Variant-coverage filtering (rejected).** Our first attempt kept only enough of the most common paths to cover ~75% of cases. This works on tidy logs, but the international process is so chaotic that *no* single path dominates — the filter returned an **empty log**, leaving us with nothing to model.

2. **Top-K filtering (rejected).** A common shortcut is to keep only the top 5 or 10 paths and delete the rest. We rejected this on principle: in the international log the top 5 paths cover only ~45% of cases, so this would **throw away up to ~84% of real claims**. The resulting model would be a flattering "toy" that hides exactly the rejections and detours we are trying to study.

3. **Algorithmic noise filtering (chosen).** Instead, we feed the *entire* log into the **Inductive Miner** algorithm and let it prune infrequent behaviour internally using a `noise_threshold = 0.2`. This keeps every case in the analysis while still mathematically suppressing the rarest 20% of transitions. Crucially, the Inductive Miner always produces a **sound Workflow Net** — a model guaranteed to have no deadlocks or dead ends — which we can then test rigorously.

**The Fitness–Precision trade-off.** We measure model quality with two scores:

- **Fitness** — *Can the model replay the real behaviour in the log?* (1.0 = it explains everything.)
- **Precision** — *Does the model forbid behaviour that never actually happened?* (1.0 = it allows nothing extra.)

Our chosen approach yields **high Fitness (~0.94–0.96)** but **low Precision (~0.34–0.38)**. This is **deliberate and expected**, not a failure. A low-precision model is "permissive": it draws a clean backbone and tolerates the countless human detours around it. For an unstructured, human-driven administrative process, this is the honest choice — chasing high precision here would simply re-create the unreadable Spaghetti Model we set out to avoid. We accept a permissive map in exchange for one a reader can actually understand.

---

## 3. Analysis of Domestic Travel Declarations

The domestic log contains **10,500 cases** (individual declarations) and **56,437 events**, drawn from just **17 distinct activity types** and **99 unique paths**. This relatively contained complexity makes it our "baseline".

### 3.1 Process Discovery

The discovered model confirms the expected backbone of a healthy claim:
`Declaration SUBMITTED → APPROVED (by Administration / Budget Owner) → FINAL_APPROVED by Supervisor → Request Payment → Payment Handled`. The single most common path alone accounts for **8.18%** of all cases, and the top five variants are all clean, fully-approved claims.

`[Insert: domestic_petri_net_strict.png here]`

Conformance checking (replaying the full log through this model) gives:

| Metric | Score |
|---|---|
| Average Trace Fitness | **0.9562** |
| Perfectly fitting traces | 67.53% |
| Precision | **0.3758** |

In plain terms: the model explains ~96% of real behaviour, and roughly two-thirds of all claims follow the backbone *exactly*. The low precision reflects the many small rejection-and-resubmit detours discussed below.

### 3.2 Performance and Throughput

The **average end-to-end throughput is 11.53 days** — a reasonable figure for a process involving multiple human approvals. However, the distribution is heavily skewed: the fastest claims close in well under a day, while the slowest drags on for **469 days**. Most cases cluster at the low end, with a long thin tail of stragglers.

`[Insert: domestic_duration_histogram.png here]`

### 3.3 Rejection Dynamics and Root Causes

Rejections are common but spread across the hierarchy:

| Rejection type | Frequency |
|---|---|
| REJECTED by EMPLOYEE | 1,365 |
| REJECTED by ADMINISTRATION | 952 |
| REJECTED by SUPERVISOR | 293 |
| **REJECTED by MISSING** | **91** |
| REJECTED by PRE_APPROVER | 86 |
| REJECTED by BUDGET OWNER | 59 |

Most of these are *human* rejections and are a normal (if frictional) part of review. The interesting finding is the small **`Declaration REJECTED by MISSING`** category — an **automated** rejection fired by the system itself when data is incomplete. It appears in **87 cases**, and its trigger reveals a clear design flaw:

> Of the rejections we could trace, **86 occurred immediately after `Declaration FINAL_APPROVED by SUPERVISOR`** — versus only 3, 1, and 1 from any other step.

This makes no logical sense. A supervisor gives a claim its *final* human approval, and only *then* does the system reject it for missing data. The validation is happening at the **wrong end** of the process: at the finish line instead of the start. The human reviewers are essentially wasting their effort on claims the system was always going to bounce.

**Recommendation — a "System Poka-Yoke".** *Poka-yoke* is a Japanese quality-engineering term for a design that makes errors impossible. The fix here is **upfront data validation**: the system should refuse to accept an incomplete declaration at the moment of submission, rather than at final approval. This single change would eliminate the entire late-rejection loop and the rework it causes.

### 3.4 Compliance, Rework, and Unexpected Behaviour

We found **1,571 instances of rework loops** — cases where an activity (typically `SUBMITTED` or a rejection) was executed more than once, i.e. a claim bounced back and was resubmitted. This is the dominant form of "unexpected behaviour" and aligns directly with the rejection counts above.

The slowest hand-offs (bottlenecks) tell a complementary story:

`[Insert: domestic_bottlenecks.csv data here]`

| Transition | Avg days | Cases |
|---|---|---|
| FINAL_APPROVED by Supervisor → Payment Handled | 81.6 | 7 |
| Request Payment → REJECTED by MISSING | 19.0 | 3 |
| Declaration SAVED → Request Payment | 17.0 | 1 |
| FINAL_APPROVED by Supervisor → REJECTED by MISSING | 11.0 | 86 |

The headline-grabbing 81-day delay to "Payment Handled" looks alarming, but it occurs in only **7 cases** — these are rare edge cases, not a systemic problem. The genuinely systemic issue is the **late-rejection loop** (the 86-case row): lower in average delay, but far more frequent and entirely preventable.

---

## 4. Analysis of International Travel Declarations

The international log is a different beast: **6,449 cases** but **34 activity types** and **753 distinct paths** — roughly double the activity vocabulary of the domestic process and almost eight times the path complexity.

### 4.1 Process Discovery

The international process is fundamentally **two-phase**. Before any travel, a **permit** must be requested and approved; only then can the trip happen; and only after the trip can the declaration (reimbursement) phase begin. The dominant path makes this clear and covers **21.23%** of cases:

`Permit SUBMITTED → Permit APPROVED → Permit FINAL_APPROVED → Start trip → End trip → Declaration SUBMITTED → Declaration APPROVED → Declaration FINAL_APPROVED → Request Payment → Payment Handled`

`[Insert: international_petri_net_strict.png here]`

Conformance scores mirror the domestic pattern — high fitness, low (deliberate) precision:

| Metric | Score |
|---|---|
| Average Trace Fitness | **0.9451** |
| Precision | **0.3371** |

### 4.2 Performance and Throughput

Here the contrast is dramatic. The **average throughput is 86.46 days** — about **7.5× slower than the domestic process** (11.53 days). The slowest case ran for **742 days**, more than two years.

`[Insert: international_duration_histogram.png here]`

The extra delay is the direct cost of the permit phase and the additional approval layers (pre-approvers, budget owners, directors) that international travel demands.

### 4.3 Rejection Dynamics and Root Causes

The friction in this process is severe. Across permit and declaration phases combined there are **4,192 rejection events** — for only 6,449 cases, that is roughly two-thirds of a rejection per claim on average. The two largest sources dominate:

| Activity immediately preceding a rejection | Count |
|---|---|
| Declaration SUBMITTED by EMPLOYEE | 1,617 |
| Declaration REJECTED by ADMINISTRATION | 1,510 |

This is a classic **"ping-pong" rework loop**. An employee submits a declaration; administration rejects it; the employee resubmits; it is rejected again. The fact that `REJECTED by ADMINISTRATION` is itself one of the most common *predecessors* of a further rejection shows claims bouncing back and forth repeatedly. Consistent with this, **1,590 of 6,449 cases (24.7%)** contain rework, averaging ~1.9 redundant steps each.

The interpretation is human, not technical: international travel rules (per-diems, currency, multi-country itineraries, funding sources) are **genuinely complex**, and employees struggle to file a compliant claim on the first try. Unlike the domestic "MISSING" flaw — a fixable IT problem — this is a **human compliance failure** that points to a need for better guidance, templates, and training at the point of submission.

### 4.4 Compliance and Rework: Broken Preventive Controls

The most serious finding concerns the *ordering* of activities. The whole point of an up-front permit is that it is a **preventive control** — approval must come *before* money is committed. The data shows this control is routinely bypassed:

| Compliance rule | Violations | Share of cases |
|---|---|---|
| **`Start trip` before `Permit FINAL_APPROVED`** | **1,130** | **17.5%** |
| `Payment Handled` before `End trip` | 536 | 8.3% |

In **1,130 cases (17.5%)** employees **started travelling before their permit was finally approved**. In other words, nearly one in five international trips proceeded on the assumption that approval was a formality. This is a culture of **retroactive authorization**: the permit becomes a rubber stamp applied *after* the fact rather than a genuine gate. The risk is concrete — the university is exposed to **unapproved financial liabilities** for trips it never formally sanctioned, and would have little recourse if a permit were ultimately denied.

A second, smaller violation — **536 cases where `Payment Handled` occurred before `End trip`** — shows money leaving the university before the trip had even concluded, further confirming that the intended sequence of controls is not being enforced by the system.

---

## 5. Summary of Key Findings (Domestic vs. International)

| Dimension | Domestic | International |
|---|---|---|
| Cases / Events | 10,500 / 56,437 | 6,449 |
| Activity types / Paths | 17 / 99 | 34 / 753 |
| Avg. throughput | 11.53 days | 86.46 days (~7.5×) |
| Fitness / Precision | 0.9562 / 0.3758 | 0.9451 / 0.3371 |
| Total rejection events | 2,846 | 4,192 |
| Rework rate | 1,571 loop instances | 24.7% of cases |
| Headline problem | Automated late-rejection (IT design flaw) | Ping-pong rejections + 17.5% trips before permit approval |

**Bottom line.** Both processes are sound in their backbone but leak time and effort through rework. The domestic process suffers from a *fixable system design flaw* (validate data up front — a Poka-Yoke), while the international process suffers from *human and governance failures* (complex rules driving resubmissions, and a broken permit-before-travel control). The methodological choice of high-fitness / low-precision noise filtering was essential to surfacing these patterns without drowning them in a Spaghetti Model.

---

*All figures in this report were generated programmatically from the raw XES event logs using PM4Py; the supporting CSV tables and PNG visualisations are available in the `Output/Domestic/` and `Output/International/` directories.*
