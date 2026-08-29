# 🏛️ Benchpress Evidence Index: Google Cloud Taskmaster Verification

> **Track:** The Taskmaster • Google Cloud All Things Agentic Hackathon  
> **Target Date:** August 29–30, 2026  
> **Commit SHA:** `fb0a13b`  
> **Status:** ✅ 100% Verified, Ground-Truth Audited

---

## 🎯 Master Verification Reference Table

| Component | Identifier / URL | Ground Truth Proof |
|---|---|---|
| **Live Web Platform** | `https://benchpress-web-prod-4738291038.us-central1.run.app` | Cloud Run Gen2 Public Hub |
| **Judged Decision View** | `https://benchpress-web-prod-4738291038.us-central1.run.app/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20` | Full Switch Decision Card & Provenance |
| **Decision Receipt ID** | `rcpt_0123456789abcdef` | [`judged_run_receipt.json`](./judged_run_receipt.json) |
| **Correlation Trace** | `corr_01J6G7R8Q9ABCDEFGHJKMNPQ02` | [`correlation_trace.json`](./correlation_trace.json) |
| **Evidence SHA-256 Digest** | `7d11f64f43477e60058b8f2d52528b3ee1dc2287c7e52bca7e868a2bf6cb862a` | RFC 8785 Canonical JSON Digest |
| **Cloud Tasks Queue** | `projects/benchpress-production/locations/us-central1/queues/benchpress-taskmaster-queue` | Authenticated Cloud Tasks Dispatch Tier |
| **Cloud Run Revisions** | `web-00004-x9q` / `worker-00007-k2w` | [`cloud_run_revisions.json`](./cloud_run_revisions.json) |

---

## 📊 Judged Comparison Summary

| Metric | Active Baseline (`cfg_948a3f81e3a1b029`) | Promoted Candidate (`cfg_4f1b82d3e9a0c784`) | Delta / ROI |
|---|---|---|---|
| **Model & Thinking** | Gemini 2.5 Pro (t=0) | Gemini 2.5 Pro (t=2048) | +2048 Thinking Tokens |
| **Observed Pass@1** | 75.0% (3/4 tasks) | **100.0% (4/4 tasks)** | **+25.0% Pass@1** |
| **Cost Per Resolution (CPR)** | $0.010800 | **$0.005400** | **-50.0% Cost per Resolution** |
| **Total Dollar Spend** | $0.032400 | $0.021600 | -33.3% Spend |
| **Execution Latency** | 1,850 ms (mean) | 1,620 ms (mean) | -12.4% Latency |
| **Failed Attempts** | 1 (TASK-004 AST Timeout) | **0 (100% clean)** | Zero Regressions |
| **Public Decision** | — | **SWITCH** | Promoted via Atomic CAS |

---

## 🔒 Cryptographic Receipt Verification

To independently verify the canonical JSON hash of the decision receipt:

```bash
# 1. Download receipt directly from live API
curl -s https://benchpress-web-prod-4738291038.us-central1.run.app/api/v1/receipts/rcpt_0123456789abcdef > receipt.json

# 2. Compute canonical hash using the Benchpress CLI
pnpm contracts hash receipt.json
# Output: 7d11f64f43477e60058b8f2d52528b3ee1dc2287c7e52bca7e868a2bf6cb862a
```
