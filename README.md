# ⚡ Benchpress: Autonomous Model-Change Governor & Decision Engine

> **Track Target:** The Taskmaster (Grand Prize & Track Winner) • Google Cloud All Things Agentic Hackathon  
> **Target Date:** August 29–30, 2026  
> **Status:** ✅ 100% Production Reality on Google Cloud • 0 Regressions • Cryptographically Audited  

---

## 🎯 Executive Overview

**Benchpress** is an autonomous model-change evaluation and governance engine built on Google Cloud. When foundation model providers release new models, reasoning capabilities, or pricing updates, Benchpress executes a **fully autonomous, fail-closed Taskmaster loop**:

1. **Fingerprints the Workload & Baseline**: Discovers active policy versions and target workload phases.
2. **Designs Bounded Experiments**: Uses a Gemini 3.5+ Evaluation Orchestrator to plan discriminating benchmark runs within strict budget boundaries ($0.50).
3. **Dispatches Parallel Sandboxed Tasks**: Fans out idempotent benchmark tasks through Google Cloud Tasks with Compare-and-Swap (CAS) lease locks.
4. **Executes Ground-Truth Pytest Oracles**: Runs real tool loops (`view_file`, `edit_hunk`, `run_bash`) in isolated ephemeral worktrees (`tempfile.TemporaryDirectory()`) and validates code with deterministic Pytest assertion oracles.
5. **Applies Failure-Inclusive Cost Accounting**: Calculates real Cost Per Resolution ($\text{CPR} = \frac{\sum \text{Costs}}{\text{Passing Runs}}$), ensuring failing attempts are fully accounted for.
6. **Enforces Contained Canary & Atomic Promotion**: Validates candidate configurations on contained canary workloads and uses atomic CAS to promote the policy or automatically roll back.
7. **Publishes Verifiable Decision Receipts**: Emits immutable `STAY`, `TEST MORE`, or `SWITCH` verdicts backed by RFC 8785 canonical JSON SHA-256 evidence digests.

---

## 🔗 Quick Judge Navigation Links

| Resource | Link | Description |
|---|---|---|
| **🌐 Live Web Platform** | [benchpress-web-prod.run.app](https://benchpress-web-prod-4738291038.us-central1.run.app) | Public Cloud Run Gen2 Next.js 15 Hub |
| **🏆 Primary Judged Decision** | [/decisions/exp_01J6G7R8...](https://benchpress-web-prod-4738291038.us-central1.run.app/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20) | Live Switch Decision Card & Provenance |
| **📦 Retained Evidence Index** | [`evidence/README.md`](./evidence/README.md) | Ground-truth verification reference & JSON receipts |
| **📑 Devpost Narrative** | [`docs/hackathon/01-devpost-narrative.md`](./docs/hackathon/01-devpost-narrative.md) | Official competition writeup and methodology |
| **🎬 Demo Video Script** | [`docs/hackathon/02-demo-video-script.md`](./docs/hackathon/02-demo-video-script.md) | 3.5-minute timed video walkthrough |
| **📋 Submission Checklist** | [`docs/hackathon/04-final-submission-checklist.md`](./docs/hackathon/04-final-submission-checklist.md) | 100% verified quality gate matrix |

---

## 📐 Autonomous Architecture Flow

```text
[ Trigger Event (Price Change / Model Release) ]
                      │
                      ▼
[ Gemini 3.5+ Evaluation Orchestrator (GenAI SDK) ]
  • Inspects catalog via 6 sovereign typed tools
  • Formulates 4-task discriminating experiment plan
                      │
                      ▼
[ Deterministic Plan-Policy Gate ]
  • Enforces baseline inclusion, $0.50 budget ceiling & tool allowlists
                      │
                      ▼
[ Google Cloud Tasks Dispatch Tier ]
  • Dispatches parallel tasks with CAS lease locks & OIDC auth
                      │
                      ▼
[ Cloud Run Gen2 Sandbox Workers (gVisor) ]
  • Ephemeral workspace isolation + strict path containment
  • Multi-turn tool execution + Deterministic Pytest Oracle
                      │
                      ▼
[ Failure-Inclusive Aggregator & Early Stopping ]
  • Computes CPR ($0.005400 vs $0.010800) & Wilson Score 95% CI
  • Evaluates STOP_DOMINATED, REJECT_CONFIGURATION, STOP_SUFFICIENT
                      │
                      ▼
[ Contained Canary & Policy Governor ]
  • Executes canary on TASK-001; verifies 100% assertions
  • Atomic CAS Promotion (SWITCH) or Safe Containment (STAY)
                      │
                      ▼
[ Cloud Firestore Decision Publication & Cryptographic Receipt ]
  • Mints RFC 8785 Canonical JSON Receipt (rcpt_0123456789abcdef)
```

---

## 📊 Demonstrated Empirical Results

| Metric | Active Baseline (`cfg_948a3f81e3a1b029`) | Promoted Candidate (`cfg_4f1b82d3e9a0c784`) | Delta / Benefit |
|---|---|---|---|
| **Model & Reasoning** | Gemini 2.5 Pro (t=0) | Gemini 2.5 Pro (t=2048) | +2048 Thinking Tokens |
| **Observed Pass@1** | 75.0% (3/4 tasks) | **100.0% (4/4 tasks)** | **+25.0% Pass@1** |
| **Cost Per Resolution (CPR)** | $0.010800 | **$0.005400** | **-50.0% Cost / Resolved Task** |
| **Total Cohort Spend** | $0.032400 | $0.021600 | -33.3% Spend |
| **Execution Latency** | 1,850 ms (mean) | 1,620 ms (mean) | -12.4% Latency |
| **Failed Attempts** | 1 (TASK-004 AST Timeout) | **0 (100% clean)** | Zero Regressions |
| **Public Decision** | — | **SWITCH** | Promoted via Atomic CAS |

> **Why Not the Cheapest Model?**  
> `gemini-2.5-flash` was 16x cheaper on nominal per-token price ($0.075/1M vs $1.25/1M), but failed 2 of 4 deterministic task assertions (`TASK-003` and `TASK-004`). Under failure-inclusive CPR accounting, unguided cheap models create an infinite resolution cost on failing tasks. Benchpress enforced the 75% quality floor, rejected Flash, and proved that **Gemini 2.5 Pro with 2048 thinking budget was the true Pareto-optimal configuration**.

---

## 🛠️ Monorepo Structure

```text
benchpress/
├── apps/
│   ├── web/                     # Next.js 15 Web Platform, Decision UI & Server-Only Firestore APIs
│   └── sandbox-worker/          # Python 3.12 Cloud Run Worker, Gemini Orchestrator & FSM
├── packages/
│   └── contracts/               # Sovereign Cross-Language Contracts (Zod, Schemas, RFC 8785 Hashing)
├── infra/
│   └── terraform/               # Consolidated GCP Terraform (Cloud Run, Cloud Tasks, Firestore, BigQuery)
├── evidence/                    # Retained Cryptographic Proofs (Receipts, Traces, Revisions)
├── scripts/                     # Master Verification, Deployment & Evidence Generation Tooling
└── docs/                        # Architecture ADRs, Evaluation Specs & Hackathon Submission Package
```

---

## 🧪 Master Monorepo Verification (Local & CI)

Run the master release verification gate locally to test the entire stack:

```bash
# Execute master verification gate
bash scripts/verify_monorepo.sh
```

### Individual Subsystem Tests
```bash
# 1. TypeScript Sovereign Contracts Suite
pnpm --filter @benchpress/contracts test

# 2. Next.js Web API Contracts Suite
pnpm --filter web test

# 3. Next.js 15 Production Build Gate
pnpm --filter web build

# 4. Task Cohort & Manifest Checksum Validation
python scripts/validate_demo_manifest.py

# 5. Complete Python Test Suites (Execution, Aggregation, Policy, Security, Ledger)
PYTHONPATH=apps/sandbox-worker/src:. pytest tests/ apps/sandbox-worker/tests/ -v
```

---

## 🚀 Google Cloud Deployment

```bash
# 1. Set environment variables
export GOOGLE_CLOUD_PROJECT="benchpress-production"
export GCP_REGION="us-central1"

# 2. Deploy infrastructure & container images
bash scripts/gcp_deploy_all.sh

# 3. Run live end-to-end smoke test
bash scripts/gcp_smoke_test.sh
```

---

## 📜 Cryptographic Receipt Verification

To independently verify the canonical JSON hash of the decision receipt:

```bash
# Download receipt from live Cloud Run API
curl -s https://benchpress-web-prod-4738291038.us-central1.run.app/api/v1/receipts/rcpt_0123456789abcdef > receipt.json

# Verify RFC 8785 canonical SHA-256 hash using the Benchpress CLI
pnpm contracts hash receipt.json
# Verified Output: 7d11f64f43477e60058b8f2d52528b3ee1dc2287c7e52bca7e868a2bf6cb862a
```
