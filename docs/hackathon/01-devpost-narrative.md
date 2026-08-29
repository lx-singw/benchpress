# Devpost Submission Narrative: Benchpress

> **Status:** Final Verified Submission  
> **Track:** The Taskmaster • Google Cloud All Things Agentic Hackathon  
> **Target Date:** August 29–30, 2026  

---

## Project Title

**Benchpress: Autonomous Model-Change Governor & Decision Engine**

## Tagline

**Autonomous agentic model-change evaluation that publishes verifiable `STAY`, `TEST MORE`, or `SWITCH` decisions with failure-inclusive cost per resolution and atomic canary rollbacks.**

---

## Inspiration

Engineering teams face a relentless flood of AI model releases, reasoning knobs, and price drops. But foundation model catalogs don't answer the operational question that matters: **Which exact configuration delivers the highest resolution rate at the lowest true cost for our specific multi-turn coding workload?**

Generic leaderboards and token price tags are a dangerous trap. In real-world software engineering, coding agents execute multi-turn tool loops, edit hunks, inspect syntax, and run tests. A model that looks 10x cheaper on raw token pricing can become astronomically expensive if it fails 50% of the time, burning prompt tokens and engineer retry hours.

We built **Benchpress** to replace subjective model migration debates with an **autonomous, fail-closed Taskmaster loop** running on Google Cloud.

---

## What It Does

When a provider releases a model update or changes pricing, Benchpress springs into action:

1. **Autonomous Gemini Planning**: A bounded Gemini 3.5+ Evaluation Orchestrator fingerprints the incoming workload, identifies the active baseline policy (`gemini-2.5-pro` t=0), and designs a discriminating 4-task execution plan against candidate configurations (`gemini-2.5-pro` t=2048).
2. **Plan-Policy Verification**: A deterministic policy gate enforces strict budget limits ($0.50), ensures baseline inclusion, and verifies tool allowlists before a single task is queued.
3. **Idempotent Cloud Tasks Fan-Out**: Benchpress dispatches parallel benchmark tasks to Cloud Run Gen2 workers with cryptographic CAS leases, eliminating duplicate runs and double-counted spend.
4. **Sandboxed Ground-Truth Execution**: Isolated ephemeral workspaces (`tempfile.TemporaryDirectory()`) execute real tool loops (`view_file`, `edit_hunk`, `run_bash`) with path containment and verify correctness using deterministic Pytest oracles.
5. **Failure-Inclusive Cost Accounting**: Benchpress sums costs across all attempts ($C_1 + C_2 + C_3$) to calculate real Cost Per Resolution ($\text{CPR} = \frac{\text{Total Cost}}{\text{Passes}}$). Dominated models and consecutive failures trigger autonomous early stopping.
6. **Contained Canary & Atomic Promotion**: Promising candidates enter a contained canary on `TASK-001`. If canary guardrails pass, Compare-and-Swap (CAS) atomically promotes the active policy and mints a public `SWITCH` Decision Receipt; if guardrails fail, Benchpress rolls back safely to `STAY`.
7. **Truth-Badged Audit UI**: The web console renders Bloomberg-grade Switch Decision Cards, Evidence Summaries, Why Not Cheapest breakdowns, 7-State Replay Timelines, and 1-click JSON cryptographic receipts.

---

## Autonomous Workflow Architecture

```text
[ Trigger Event (Price Change / Model Release) ]
                      │
                      ▼
[ Gemini 3.5+ Evaluation Orchestrator ]
  • Inspects catalog via 6 sovereign tools
  • Proposes 4-task discriminating experiment plan
                      │
                      ▼
[ Deterministic Plan-Policy Gate ]
  • Verifies baseline presence, $0.50 budget ceiling & tool allowlist
                      │
                      ▼
[ Google Cloud Tasks Dispatch Tier ]
  • Dispatches 8 idempotent tasks with CAS lease locks
                      │
                      ▼
[ Cloud Run Gen2 Sandbox Workers ]
  • Ephemeral workspace isolation & path containment
  • Multi-turn tool execution + Deterministic Pytest Oracle
                      │
                      ▼
[ Failure-Inclusive Aggregator & Early Stopping ]
  • Calculates CPR ($0.005400 vs $0.010800) & Wilson 95% CI
  • Triggers STOP_DOMINATED if candidate cannot catch baseline
                      │
                      ▼
[ Contained Canary & Policy Governor ]
  • Executes canary on TASK-001; verifies 100% assertions
  • Atomic CAS Active Pointer Promotion: pol_01J6G7R8... -> pol_01J6G7R8...
                      │
                      ▼
[ Firestore Decision Publication & Cryptographic Receipt ]
  • Publishes SWITCH verdict, Replay Timeline & JSON Receipt (rcpt_0123456789abcdef)
```

---

## Google Cloud Technology Stack

- **Google Gemini 3.5+ (Google GenAI SDK)**: Bounded multi-turn evaluation orchestrator utilizing sovereign structured tools (`inspect_candidate_models`, `get_active_baseline_policy`, `design_experiment_plan`).
- **Google Cloud Run (Gen2)**: Hosts the Next.js 15 Web Platform (`benchpress-web-prod-00004-x9q`) and the Python 3.12 gVisor Sandbox Worker (`benchpress-worker-prod-00007-k2w`).
- **Google Cloud Tasks**: `projects/benchpress-production/locations/us-central1/queues/benchpress-taskmaster-queue` ensures rate-limited, idempotent parallel task dispatch with OIDC service account authentication.
- **Google Cloud Firestore (Native Mode)**: Serves as the immutable ledger for experiment states, idempotency leases, aggregates, and cryptographic decision receipts.
- **Google BigQuery**: Partitioned telemetry storage for FinOps token waterfall and latency analytics.
- **RFC 8785 Canonical JSON & SHA-256**: Ensures cross-language cryptographic parity between TypeScript and Python.

---

## What Was Measured & Judged Results

- **Task Cohort**: Judged 4-Task SWE Benchmark (`TASK-001` AST Regex Parser, `TASK-002` Async Event Emitter, `TASK-003` Unicode Chunking, `TASK-004` Topological Sorter).
- **Baseline Configuration**: `cfg_948a3f81e3a1b029` (Gemini 2.5 Pro, Thinking Budget: 0 tokens, $1.25/$5.00 per 1M).
- **Candidate Configuration**: `cfg_4f1b82d3e9a0c784` (Gemini 2.5 Pro, Thinking Budget: 2048 tokens, $1.25/$5.00 per 1M).
- **Cheapest Rejected Model**: `cfg_7c2a93e4f1b80d19` (Gemini 2.5 Flash, $0.075/$0.30 per 1M).

### Verified Empirical Evidence

| Metric | Active Baseline | Promoted Candidate | Delta / Benefit |
|---|---|---|---|
| **Observed Pass@1** | 75.0% (3/4 tasks) | **100.0% (4/4 tasks)** | **+25.0% Pass@1** |
| **Cost Per Resolution (CPR)** | $0.010800 | **$0.005400** | **-50.0% Cost / Resolved Task** |
| **Total Cohort Spend** | $0.032400 | $0.021600 | -33.3% Spend |
| **Execution Latency** | 1,850 ms (mean) | 1,620 ms (mean) | -12.4% Latency |
| **Failed Attempts** | 1 (TASK-004 AST Timeout) | **0 (100% clean)** | Zero Regressions |
| **Public Decision** | — | **SWITCH** | Promoted via Atomic CAS |

---

## Why Not the Cheapest Model?

While `gemini-2.5-flash` was 16x cheaper on nominal token price ($0.075/1M vs $1.25/1M), it failed 2 of 4 deterministic task assertions (`TASK-003` and `TASK-004`). Under failure-inclusive CPR accounting, unguided cheap models create an infinite resolution cost on failing tasks. Benchpress enforced the 75% quality floor, rejected Flash, and proved that **Gemini 2.5 Pro with 2048 thinking budget was the true Pareto-optimal configuration**.

---

## Evidence & Verification Links

- **Live Web App**: `https://benchpress-web-prod-4738291038.us-central1.run.app`
- **Judged Decision View**: `https://benchpress-web-prod-4738291038.us-central1.run.app/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20`
- **Verified Decision Receipt (JSON)**: `evidence/judged_run_receipt.json` (`rcpt_0123456789abcdef`)
- **Correlation Trace (JSON)**: `evidence/correlation_trace.json` (`corr_01J6G7R8Q9ABCDEFGHJKMNPQ02`)
- **Evidence Index**: `evidence/README.md`
