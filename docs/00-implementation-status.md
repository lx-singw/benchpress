# Benchpress implementation status

> **Status:** Authoritative
> **Verified against repository:** 2026-08-29
> **Purpose:** Separate implemented code, prototypes, fixtures, and roadmap claims.

## 1. Executive assessment

Benchpress is a substantial product prototype, not an empty concept and not yet a proven production platform. The repository contains a polished web surface, API routes, SDKs, a Python worker, a formal trajectory state machine, safeguard components, telemetry contracts, tests, and Google Cloud infrastructure definitions.

The principal gap is evidence-to-claim alignment. Several execution paths are hard-coded or simulated, model metrics are embedded as fixtures, and cloud/security capabilities documented as operating systems have not all been demonstrated end to end.

The hackathon objective is to make one complete path real and preserve everything else as clearly labelled prototype or roadmap material.

## 2. Status by product area

| Product area | Current status | Repository evidence | Required next proof |
|---|---|---|---|
| Next.js product UI | **Prototype** | `apps/web`, model pages, compare view, trajectories, custom evals, arbitrage and live routes | Build, deploy, and connect the judged path to persisted real results |
| Public model catalog | **Demo fixture** | `apps/web/src/lib/models-data.ts` contains static profiles and metrics | Versioned provider registry with source URLs and retrieval dates |
| Benchmark leaderboard API | **Demo fixture** | `apps/web/src/app/api/v1/benchmarks/route.ts` contains static rows | Query materialized measured aggregates |
| Routing recommendation API and SDK | **Prototype** | Zod validation, `ParetoRouter`, and TypeScript request/response types exist | Replace fixture rules with a measured contract that requires the current baseline and returns `STAY`, `TEST MORE`, or `SWITCH` plus receipt/replay links |
| “Why Switch?” and ROI surfaces | **Demo fixture/prototype** | `why-switch-roi-calculator.tsx` and the IDE rationale wireframe express the original decision-time UX | Replace hard-coded models, quality, latency, and savings with the versioned Switch Decision Card; label values `OBSERVED`, `PROJECTED`, or `ILLUSTRATIVE` |
| Trajectory submission API | **Prototype** | Persists initial state and dispatches through a queue abstraction | Prove authenticated Cloud Tasks dispatch, durable completion, retry, and idempotency |
| Python worker service | **Prototype** | FastAPI health, task, and WebSocket endpoints exist | Run the complete cloud path with required authentication and retained logs |
| FSM runtime | **Prototype** | Formal states, transitions, budget hooks, tools, telemetry hooks | Replace hard-coded plan/tool sequence and estimated usage with real Gemini structured tool decisions and actual usage |
| Gemini integration | **Declared, not demonstrated** | `google-genai` dependency and model identifiers exist | Capture a genuine Gemini 3.5+ request, response model metadata, usage, and correlated result |
| Harvester | **Demo fixture** | `scripts/run_continuous_harvester.py` derives outcomes from predefined rates and formulas | Replace with provider adapters and immutable real-run manifests |
| Deterministic evaluation | **Prototype** | Pytest runner, task fixtures, and evaluation tests exist | Freeze a small task cohort and demonstrate hidden or independent assertions |
| Adaptive experiment and policy lifecycle | **Proposed** | Authoritative submission, architecture, evaluation, demo, and checklist documents define fingerprinting, early stopping, reject/abstain, contained canary, rollback, receipt, replay, and staleness | Implement each state and retain one correlated end-to-end decision record; documentation is not execution evidence |
| Phase-aware planner/executor/reviewer policy | **Experimental hypothesis** | ADR-003, the FSM concept, trajectory UI, and prototype router describe hybrid choreography | Keep outside the judged core unless executed end to end; include handoff/context/replanning/failure costs and never reuse the historical percentage claims as measured evidence |
| Additional Google-model bonus | **Proposed/optional** | Gemma is identified as a possible task-fingerprint classifier or measured challenger | Attempt only after the core passes; retain exact model invocation, usage/cost, output, and workflow effect before claiming the bonus |
| Telemetry | **Prototype** | Shared types and BigQuery streamer abstractions exist | Persist request, turns, usage, outcome, and aggregate under one correlation ID |
| Cloud infrastructure | **Implemented, not cloud-verified** | Terraform exists in both `infra/terraform` and `terraform` | Choose one source of truth, deploy it, and retain Cloud Run/Tasks/data-plane evidence |
| Security safeguards | **Prototype** | HMAC, secret-scanner, prompt-armor, kill-switch and rollback tests/components exist | Enforce authentication on every non-mock request, remove the destructive `git reset --hard` fallback, and demonstrate negative paths |
| gVisor isolation | **Unverified claim** | Runner and documentation exist | Show an actual `runsc`/managed isolation boundary or describe the worker accurately as a subprocess/container demo |
| GitHub crash-to-PR | **Prototype** | Webhook route and remediation-related components/tests exist | Authenticate, edit an authorized demo repo, test, push, and open a real PR; never auto-merge |
| Multimodal voice/vision | **Prototype/demo** | UI routes and Playwright specs exist | Connect a genuine session and demonstrate recovery; otherwise omit from judged core |
| Trajectory distillation | **Proposed/prototype** | Package and exporter tests exist | Add consent, provenance, licensing, privacy, and reliable outcome gates before product use |
| Enterprise appliance/governance | **Proposed** | Terraform modules and detailed governance documents exist | Treat as post-hackathon target state until controls are deployed and audited |

## 3. What is reusable

The following work remains strategically useful:

- The web information architecture and visual identity.
- Model comparison, trajectory replay, and Pareto visualizations.
- The two-service monorepo boundary.
- API request validation and SDK shapes.
- The FSM concept, once model decisions replace the canned sequence.
- Tool validation, budget ceilings, rollback concepts, and deterministic test execution.
- Telemetry schemas and the correlation-ID model.
- Terraform as deployment scaffolding after consolidation.
- Evaluation methodology, provided all empirical language is linked to real runs.
- Governance documents as product requirements rather than compliance attestations.

## 4. Claims that must not be presented as current fact

Until supported by retained evidence, Benchpress must not claim:

- A specific percentage cost reduction, pass-rate gain, compression rate, or self-healing rate.
- Thousands or hundreds of completed empirical evaluations.
- Zero loss, perfect accuracy, complete compliance, or guaranteed secret prevention.
- Predictive outage detection before provider errors.
- Production gVisor, eBPF, SEV-SNP, VPC-SC, CMEK, Model Armor, WebRTC, or BigQuery Storage Write operation merely because code or Terraform mentions it.
- Continuous self-tuning based on real provider data.
- That a generated test independently proves a generated patch is correct.

## 5. Hackathon conversion rule

Every judged component must satisfy all four conditions:

1. **Real invocation:** the required provider or cloud service is genuinely called.
2. **Observable evidence:** logs, identifiers, usage, state changes, or external results are visible.
3. **Reproducible path:** setup instructions and deterministic validation exist.
4. **Truthful boundary:** anything outside the path is visibly marked prototype, fixture, or roadmap.

## 6. Documentation disposition

| Documentation family | Disposition |
|---|---|
| Root README and `docs/README.md` | Current entry points |
| `docs/hackathon/00-04` | Submission truth; update with the demonstrated build |
| Competition readiness report | Retain as an internal audit and risk register |
| Architecture and implementation documents | Retain; reconcile diagrams with the demonstrated boundary |
| ADRs with unsupported empirical results | Treat as proposed hypotheses until validated |
| Research papers with generated numbers | Label synthetic or revise after real measurement |
| Governance and enterprise documents | Retain as target-state requirements, not certifications |
| Multimodal, distillation, swarm, and appliance designs | Preserve as post-hackathon options unless implemented and demonstrated |

## 7. Definition of “measured”

A value may be labelled **Benchpress measured** only when the following are stored:

- Provider and exact model or immutable model snapshot.
- Provider-native configuration, including reasoning controls.
- Task version, repository commit, harness version, and prompt/tool-schema hashes.
- Start/end time, attempts, turns, token usage, tool costs, compute costs, and failures.
- Deterministic outcome evidence such as test results.
- A run ID that can be traced from invocation through aggregation.
- Evaluation date, sample count, exclusions, and known limitations.

Anything else is an official specification, community submission, experiment, or demo fixture—not an empirical Benchpress result.

## 8. Verification snapshot

Commands were run from the Windows-mounted workspace on 2026-08-28 after the documentation changes. Documentation changes did not modify application code.

| Check | Observed result | Interpretation/action |
|---|---|---|
| Authoritative local Markdown links | **Pass** | All checked relative links resolve. |
| `pnpm build` | **Environment-blocked** | The bundled pnpm dependency check failed while traversing the existing WSL-backed `node_modules/typescript` path (`EISDIR`). Recreate/install dependencies consistently in one environment before using this as a release gate. |
| `python -m pytest tests apps/sandbox-worker/tests -q` | **57 passed, 1 failed** | `test_git_tree_snapshot_and_atomic_rollback` fails on the Windows temporary Git path. The rollback implementation also falls back to `git reset --hard`; remove that fallback and make worktree/path handling explicit. |
| `python -m pytest packages/sdk-python/tests -q` without package install | **Collection blocked** | The active Python environment lacks `rich`; install `packages/sdk-python` (and its development dependencies where needed) before running the suite. |

These results are pre-existing implementation/environment issues and remain release blockers until rerun successfully in the intended build environment.
