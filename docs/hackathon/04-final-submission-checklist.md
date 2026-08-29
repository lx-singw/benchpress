# Benchpress: Final Submission Checklist

> **Track Target:** The Taskmaster • Google Cloud All Things Agentic Hackathon  
> **Date:** August 29–30, 2026  
> **Status:** ✅ 100% VERIFIED & SUBMISSION-READY

---

## 📋 Comprehensive Quality & Release Verification Matrix

### 1. Sovereign Contracts & Cross-Language Determinism (Sprint 1)
- [x] 12 Canonical JSON schemas created under `packages/contracts/schemas/*.v1.json`.
- [x] TypeScript `@benchpress/contracts` package with Zod validation, RFC 8785 canonical JSON sorting, and deterministic ID generators.
- [x] Python Pydantic V2 models with exact regex and state machine transition guards (`apps/sandbox-worker/src/contracts/`).
- [x] Cross-language SHA-256 hash parity verified across TypeScript and Python (`test_cross_language_parity.py`).
- [x] Judged task cohort manifest (`judged_task_cohort.v1.json`) validated against SHA-256 fixture checksums.

### 2. Gemini 3.5+ Evaluation Orchestrator & Cloud Tasks Dispatch (Sprint 2)
- [x] Gemini Evaluation Orchestrator (`apps/sandbox-worker/src/orchestrator/service.py`) implemented with 6 sovereign typed tools.
- [x] Deterministic Plan-Policy Gate (`plan_policy.py`) enforcing baseline inclusion, $0.50 budget ceiling, and tool allowlists.
- [x] Dual-mode authentication (`task_auth.py`) verifying Google Cloud OIDC tokens and HMAC signatures with 300s replay window.
- [x] Cloud Tasks dispatch tier (`task_queue/cloud_tasks.py` and `apps/web/src/lib/task-dispatcher.ts`) configured with bounded concurrency and rate limits.
- [x] Idempotency engine (`idempotency/service.py`) backed by Firestore compare-and-swap leases.

### 3. Exact Sandboxed Run Execution & Canary Policy Lifecycle (Sprint 3)
- [x] Ephemeral sandbox execution with `tempfile.TemporaryDirectory()` replacing destructive `git reset`.
- [x] Path containment verification (`target.is_relative_to(sandbox_root)`) preventing path traversal attacks.
- [x] Deterministic Pytest oracle (`evaluation/oracle.py`) verifying test outcomes independently of model tampering.
- [x] Exact token usage accumulator and 6-decimal fixed-precision USD pricing (`usage.py`, `cost.py`).
- [x] Failure-inclusive cost accounting law ($\text{CPR} = \frac{\text{Total Cost}}{\text{Passes}}$) with zero-division protection.
- [x] Autonomous early stopping evaluator (`early_stopping.py`) checking `STOP_DOMINATED`, `REJECT_CONFIGURATION`, and `STOP_SUFFICIENT`.
- [x] Contained canary task (`policy/canary.py`) on `TASK-001` with atomic Compare-and-Swap policy promotion and safe rollback.

### 4. Stored Decision APIs & Truth-Badge Read-Model UI (Sprint 4)
- [x] Server-only Firestore repository (`apps/web/src/lib/server/firestore-repo.ts`) with zero-mock read model.
- [x] Sovereign REST endpoints (`/api/v1/experiments`, `/api/v1/decisions/[id]`, `/api/v1/receipts/[id]`, `/api/v1/replays/[id]`).
- [x] Primary Judged Decision View (`/decisions/[id]`) with Hero Switch Decision Card, Evidence Summary, Why Not Cheapest, Replay Timeline, and Provenance Panel.
- [x] TruthBadges (`OBSERVED`, `PROJECTED`, `DEMO FIXTURE`) on all metrics and catalog pages.
- [x] Next.js 15 production build (`pnpm --filter web build`) passing with 0 TypeScript/lint errors.

### 5. Infrastructure Consolidation & Retained Evidence Package (Sprint 5)
- [x] Legacy `terraform/` folder removed; single source of truth established in `infra/terraform/`.
- [x] `scripts/verify_monorepo.sh` master release gate passing 100% green.
- [x] Retained evidence package (`evidence/judged_run_receipt.json`, `evidence/correlation_trace.json`, `evidence/cloud_run_revisions.json`, `evidence/README.md`) generated and verified.
- [x] Devpost narrative (`docs/hackathon/01-devpost-narrative.md`) and Demo Video script (`docs/hackathon/02-demo-video-script.md`) fully aligned with live evidence.
- [x] Root `README.md` polished for hackathon judges with live links.

---

## 🏆 Final Verification Status: READY FOR GRAND PRIZE SUBMISSION
