# G0 audit-remediation implementation plan

> **Document ID:** `BP-PLAN-007`
> **Status:** Local implementation complete; live rehearsal and submission freeze pending
> **Scope:** Close every blocker found in the 2026-08-29 audit of `BP-PLAN-006`
> **Release target:** One truthful, deployed, replayable, evidence-backed Taskmaster G0 path
> **Predecessor:** [Submission-critical implementation plan](./06-submission-critical-implementation-plan.md)
> **Release gate:** [Final submission checklist](../hackathon/04-final-submission-checklist.md)
> **Rule:** This document defines required work. Completion evidence and remaining gates are recorded in the [implementation status](../00-implementation-status.md) and [release rehearsal runbook](../implementation/07-release-verification-and-rehearsal.md).

## 1. Outcome

Implement and prove one correlated workflow:

```text
change/replay event
  -> eligible Gemini planner invocation
  -> deterministic plan approval
  -> authenticated Cloud Tasks fan-out
  -> idempotent, bounded provider executions
  -> deterministic oracles
  -> durable failure-inclusive aggregation
  -> sufficiency/stopping decision
  -> contained canary
  -> atomic promotion or exact rollback
  -> immutable decision receipt and replay
  -> public decision card sourced only from stored evidence
```

Completion means an independent reviewer can start with one `correlation_id`, reconstruct every state transition from Firestore and Cloud Logging, verify the receipt hash locally, open the deployed decision page, and match all public measured claims to provider-returned usage and deterministic test results.

## 2. Audit baseline and release decision

At the start of the 2026-08-29 audit, the repository was **NO-GO** for a truthful G0 submission. The table below is the audit-time baseline that this plan was written to remediate; it is retained for traceability and must not be read as the current implementation inventory. Current closure and remaining live proof are tracked in the authoritative implementation status.

| ID | Blocker | Audit-time evidence | Required closure |
|---|---|---|---|
| B-01 | Public claims exceed evidence | Root and evidence documentation claim production verification while named production URLs return `404` | Remove or quarantine unsupported claims before further release work |
| B-02 | Evidence is generated from constants | `scripts/generate_evidence_package.py` embeds receipt, trace, revision, and result values | Export actual immutable records and cryptographically verify them |
| B-03 | Gemini eligibility is not proved | Planner defaults to Gemini 2.5 and silently simulates when initialization fails | Require an exact eligible Gemini 3.5+ model and retain a genuine call |
| B-04 | Operational state is in memory | Ledger and policy repositories use process-local singletons | Implement transactional Firestore repositories and restart-safe state |
| B-05 | Cloud Tasks path is inconsistent | Queue and URL defaults mismatch deployed resources; OIDC is incomplete; fallback hides failures | Use one queue contract, explicit handler URLs, OIDC on every task, and fail closed |
| B-06 | Task authentication is incomplete | Token verification does not bind audience, issuer, and expected service-account identity | Verify all required claims and reject missing/invalid identity |
| B-07 | Run manifests are not honored exactly | Execution substitutes a default model and omits the thinking control | Resolve immutable configurations and reject unsupported substitutions |
| B-08 | Execution safety and budget controls are incomplete | Shell execution permits compound-command risk; budgets are not enforced incrementally; destructive Git fallback remains | Use argument-vector execution, hard ceilings, and non-destructive cleanup |
| B-09 | Aggregation and governance are disconnected | Aggregate, canary, promotion, rollback, and receipt services do not form an automated persisted chain | Wire transactional state transitions and terminal publication |
| B-10 | Web read model can silently serve fixtures | Firestore failures can seed or return measured-looking defaults | Separate fixture mode and make measured routes fail closed |
| B-11 | Deployed revisions do not match source claims | Actual state is a development deployment with older routes and mutable image tags | Build immutable images from the release SHA and deploy/verify the exact revision |
| B-12 | Full validation and submission proof are incomplete | Combined Python collection fails; no retained real cohort, tag, video URL, or completed release checklist | Fix test isolation and produce a signed-off evidence bundle |

No blocker may be closed by prose, a fixture, a mocked provider response, a generated identifier, or the existence of source code alone.

## 3. Non-negotiable implementation rules

1. Production and evidence modes fail closed. They never fall back to mocks, local HTTP, seeded fixtures, default models, or in-memory state.
2. Every externally visible measured value must be traceable to an immutable run result.
3. Cloud Tasks may deliver more than once; provider spend and policy effects occur at most once per logical key.
4. Only deterministic policy may approve plans, aggregate outcomes, promote, roll back, or publish.
5. A planner model may explain decisions but may not fabricate metrics or override policy.
6. Configuration identifiers resolve to immutable native provider settings; unknown or unsupported settings are rejected.
7. A task handler returns `2xx` only after its owned durable state transition is committed.
8. Provider/model failures are durable experiment outcomes. Retryable infrastructure failures remain task failures until retried successfully.
9. Rejection and early stopping cancel only unstarted work and retain all incurred cost.
10. No automatic path executes destructive Git commands, installs packages, pushes changes, or changes customer traffic.
11. Infrastructure uses dedicated identities, least privilege, immutable artifacts, and explicit environment configuration.
12. “Implemented,” “deployed,” “measured,” and “verified” remain separate statuses until their individual gates pass.

## 4. Target architecture and ownership

| Component | Owns | Must not own |
|---|---|---|
| Next.js web | Request validation, public read model, decision/replay presentation | Provider calls, policy decisions, fixture substitution in measured mode |
| Orchestrator handler | Gemini plan request, typed-tool interaction, proposed plan persistence | Budget approval, result fabrication, promotion |
| Plan policy | Schema, baseline, cohort, budget, threshold, and allowlist approval | Provider execution |
| Cloud Tasks dispatcher | Deterministic task names, OIDC, queue routing, scheduling | Business-state mutation beyond dispatch records |
| Run handler | Transactional claim, exact native invocation, tool loop, oracle, durable result | Cohort aggregation or policy promotion |
| Aggregate handler | Eligible-run selection, failure-inclusive metrics, sufficiency and stopping | New provider spend without a persisted approved plan |
| Canary handler | Contained validation of a frozen candidate policy | Direct public publication |
| Publisher | CAS promotion/rollback, receipt minting, replay projection | Recomputing hidden metrics or accepting fixtures |
| Firestore | System of record for workflow state and immutable evidence | Large analytics scans |
| BigQuery | Append-only analytical events and cost/query support | Transactional ownership or policy pointers |

The only allowed state progression is:

```text
RECEIVED -> PLANNING -> PLAN_PROPOSED -> PLAN_APPROVED
         -> DISPATCHED -> RUNNING -> AGGREGATING
         -> ABSTAINED | REJECTED | CANARY_RUNNING
         -> ROLLED_BACK | PROMOTED
         -> RECEIPT_PUBLISHED
```

Each transition records `from_state`, `to_state`, `actor`, `occurred_at`, `correlation_id`, `causation_id`, `attempt`, and a hash of the material input. Invalid or repeated transitions are rejected transactionally or returned as an idempotent replay of the existing result.

## 5. Delivery sequence

The work is divided into sixteen work packages. Dependencies are strict.

| Order | Work package | Depends on | Primary gate |
|---:|---|---|---|
| 0 | WP-00 Truth quarantine | None | No unsupported production/measured claim remains |
| 1 | WP-01 Release configuration and eligible-model preflight | WP-00 | Production cannot start with ineligible or incomplete settings |
| 2 | WP-02 Firestore system of record | WP-01 | State survives restart and duplicate delivery |
| 3 | WP-03 Task dispatch and workload identity | WP-01, WP-02 | Authenticated deterministic task reaches the intended handler |
| 4 | WP-04 Genuine Gemini orchestrator | WP-01, WP-02 | Retained eligible planning call and approved bounded plan |
| 5 | WP-05 Exact configuration registry | WP-02, WP-04 | Every run resolves without substitution |
| 6 | WP-06 Bounded execution and sandbox hardening | WP-02, WP-03, WP-05 | Duplicate-safe real run with enforced ceilings |
| 7 | WP-07 Durable aggregation and stopping | WP-02, WP-06 | Versioned failure-inclusive aggregate is persisted |
| 8 | WP-08 Canary, promotion, rollback, and publication | WP-07 | Exactly one terminal decision receipt is published |
| 9 | WP-09 Truthful web read model | WP-02, WP-08 | Public pages render stored evidence only |
| 10 | WP-10 Telemetry and observability | WP-02 through WP-09 | One correlation ID joins all retained events |
| 11 | WP-11 Infrastructure and immutable deployment | WP-01, WP-03, WP-10 | Deployed revisions match release SHA/digest |
| 12 | WP-12 Evidence exporter and verifier | WP-08, WP-10, WP-11 | Bundle is derived from cloud records and verifies offline |
| 13 | WP-13 Test and CI closure | All code packages | Clean build/test/security/infrastructure gates |
| 14 | WP-14 Real rehearsal and measured cohort | WP-11 through WP-13 | Successful end-to-end run and negative-path replay |
| 15 | WP-15 Submission freeze | WP-14 | Checklist, tag, video, URLs, and claims are internally consistent |

## 6. WP-00 — Quarantine unsupported claims

### Objective

Make the repository truthful before adding new proof. This prevents old fixture values from being mistaken for results produced by later work.

### Files

- `README.md`
- `evidence/README.md`
- existing files under `evidence/`
- `docs/00-implementation-status.md`
- `docs/hackathon/01-devpost-narrative.md`
- `docs/hackathon/02-demo-video-script.md`
- `docs/hackathon/04-final-submission-checklist.md`
- UI components and data files containing measured-looking numbers

### Tasks

1. Replace “100% Production Reality,” “100% Verified,” “zero regressions,” production URLs, exact savings, pass rates, latency, and revision claims with the current audited status.
2. Mark every historical generated bundle `DEMO_FIXTURE` or move it under `evidence/fixtures/`. Preserve it only if useful for schema/UI tests.
3. Add a machine-readable provenance field to fixture documents: `truth_status: DEMO_FIXTURE`, `source: synthetic`, and `eligible_for_publication: false`.
4. Remove fixture IDs from default decision links and metadata.
5. Inventory exact empirical claims with `rg`; classify each as `OBSERVED`, `OFFICIAL_SPECIFICATION`, `PROJECTED`, `ILLUSTRATIVE`, or `DEMO_FIXTURE`.
6. Update the implementation-status table with the audit’s concrete gaps and the date/commit reviewed.
7. Keep the final checklist unchecked until a linked artifact closes an item.

### Tests and exit gate

- Add a documentation/fixture linter that rejects forbidden phrases and measured fields lacking provenance.
- Search the built web output as well as source files.
- Exit only when all public URLs work or are explicitly labeled unavailable, and no synthetic record is eligible for publication.

### Rollback

Reverting claim corrections is prohibited unless a newly exported evidence bundle independently verifies the restored claim.

## 7. WP-01 — Release configuration and eligible-model preflight

### Objective

Define one validated configuration contract for local test, development, rehearsal, and production/evidence modes.

### Files

- `apps/sandbox-worker/src/config.py`
- `.env.example`
- `infra/terraform/variables.tf`
- `infra/terraform/environments/dev.tfvars`
- `infra/terraform/environments/prod.tfvars`
- `infra/terraform/cloud_run.tf`
- deployment scripts under `scripts/`

### Tasks

1. Introduce an explicit runtime mode enum: `local_mock`, `development`, `rehearsal`, `production`.
2. Require `PLANNER_MODEL`, project, region, queue name, worker audience, invoker service-account email, collection prefix, and budget defaults outside `local_mock`.
3. Set the judged planner model to the exact eligible Gemini 3.5-or-newer identifier confirmed by the target Vertex AI/GenAI account. Do not encode an assumed alias before a preflight call proves availability.
4. Add startup validation that rejects:
   - Gemini model IDs below the eligibility boundary;
   - mock mode in rehearsal/production;
   - `0.0.0.0` or localhost service URLs;
   - missing OIDC audience/identity;
   - mutable or missing release identifiers;
   - missing Firestore configuration;
   - budgets or ceilings outside frozen policy bounds.
5. Expose a sanitized `/readyz` response showing runtime mode, release SHA, model ID, repository backend, queue, and dependency status without secrets.
6. Add `scripts/preflight_release.py` to check GenAI model access, Firestore read/write transaction, Cloud Tasks queue existence, service URLs, IAM identity, and BigQuery dataset/table access.
7. Record the preflight output as evidence only when every check is live and its timestamp/release SHA is retained.

### Tests and exit gate

- Unit-test every invalid configuration class.
- Container startup must fail in production when any required setting is absent or ineligible.
- Preflight must execute a minimal eligible model request and retain the provider response model/version and usage.

## 8. WP-02 — Transactional Firestore system of record

### Objective

Replace process-local state with restart-safe, transactionally owned records.

### Files

- Replace `apps/sandbox-worker/src/ledger/firestore.py` with an interface plus real implementation.
- Replace the singleton behavior in `apps/sandbox-worker/src/policy/repository.py`.
- Add `apps/sandbox-worker/src/ledger/repository.py` and `firestore_repository.py` if separation improves testability.
- Add emulator/integration tests under `tests/ledger/` and `tests/policy/`.
- Add indexes/rules/configuration to `infra/terraform/` where required.

### Collections

Use an environment-prefixed root or separate GCP projects. Store timestamps in UTC and money as fixed-point decimal strings or integer micros.

| Collection | Key | Required immutable/material fields |
|---|---|---|
| `change_events` | `event_id` | source, received time, replay pointer, payload hash |
| `task_fingerprints` | `fingerprint_id` | phase, suite, repository, harness, oracle and schema versions |
| `native_configurations` | `configuration_id` | provider, exact model, native controls, price version, content hash |
| `experiment_plans` | `experiment_id` | baseline, candidates, tasks, ceilings, stopping rules, planner invocation |
| `run_manifests` | `run_key` | frozen plan/config/task/tool/harness inputs and expected attempt policy |
| `run_claims` | `run_key` | lease owner, lease expiry, attempt, invocation fence, terminal pointer |
| `run_results` | `run_key` | provider metadata, usage, costs, latency, oracle, failure taxonomy |
| `aggregates` | `aggregate_id` | eligible run keys, exclusions, costs, CPR, uncertainty, sufficiency |
| `policy_versions` | `policy_version_id` | immutable routing/configuration, predecessor, state, content hash |
| `policy_pointers` | scope key | active version, generation, updated time, receipt pointer |
| `canary_results` | `canary_id` | baseline/candidate runs, boundaries, result, prior version |
| `decision_receipts` | `receipt_id` | canonical decision body, digest, publication status |
| `replay_events` | sequence key | transition data and material-input hash |
| `dispatches` | deterministic task name | target, schedule, task response, attempt, related record |

### Transaction semantics

1. `claim_run(run_key)` creates or renews a bounded lease and increments an invocation fence.
2. A terminal result is create-only. Same-content duplicates return the existing result; conflicting results raise a permanent integrity error.
3. Lease expiry permits recovery but not a second provider call if an invocation fence already has a stored provider response.
4. Plan approval freezes manifests before dispatch.
5. Aggregate creation uses a stable sorted set of terminal eligible run keys and produces a content-addressed ID.
6. Policy promotion uses a Firestore transaction comparing the expected active version and generation.
7. Receipt creation is create-only and unique per terminal policy decision.
8. Replay events are append-only and never used as the sole system of record.

### Migration

1. Introduce repository protocols and retain in-memory implementations only for unit tests.
2. Select the backend through dependency injection; production cannot choose memory.
3. Seed only immutable configuration/task definitions, never measured results.
4. Run Firestore emulator integration tests, then a development-project restart test.
5. Delete no old data during G0; label legacy records and exclude them by schema/version/provenance.

### Exit gate

A workflow may be interrupted between every state, restarted on a new instance, and resumed without losing state, duplicating provider spend, or changing a terminal result.

## 9. WP-03 — Cloud Tasks dispatch and fail-closed authentication

### Objective

Make Cloud Tasks the sole durable asynchronous transport for the judged workflow.

### Files

- `apps/sandbox-worker/src/task_queue/cloud_tasks.py`
- `apps/web/src/lib/task-dispatcher.ts`
- `apps/web/src/lib/gcp-tasks.ts`
- `apps/sandbox-worker/src/security/task_auth.py`
- task handlers in `apps/sandbox-worker/src/main.py`
- `infra/terraform/cloud_tasks.tf`
- `infra/terraform/service_accounts.tf`
- `infra/terraform/cloud_run.tf`

### Tasks

1. Define handler paths for `orchestrate`, `execute-run`, `aggregate`, `canary`, and `publish`.
2. Use the Terraform output queue name everywhere; eliminate hard-coded `trajectory-execution-queue` and localhost defaults outside local mode.
3. Generate deterministic Cloud Tasks names from the transition type and logical object ID.
4. Configure OIDC on every task with the dedicated invoker service account and exact worker service audience.
5. Verify token signature, issuer, audience, expiry, issued-at, and expected service-account email. Optionally require a signed task payload hash as defense in depth, but never make HMAC presence optional.
6. Require Cloud Run IAM invocation by the same dedicated identity.
7. Remove production fallback to direct HTTP, mock task IDs, or best-effort success.
8. Classify handler responses:
   - `2xx`: transition durably committed or idempotent terminal replay;
   - `4xx`: permanent schema/auth/policy failure, recorded where safe;
   - `409`: conflicting immutable state, alert and no retry loop;
   - `429/5xx`: retryable infrastructure failure.
9. Remove `BackgroundTasks` from the judged path. Keep legacy endpoints disabled outside local mode or delete them after callers migrate.

### Tests and exit gate

- Unit tests for missing, expired, wrong-audience, wrong-issuer, wrong-email, malformed, and valid tokens.
- Emulator/fake tests for deterministic task names and `AlreadyExists` idempotency.
- Live development smoke test shows Cloud Tasks identity in worker logs and the expected durable dispatch/result records.
- Kill the worker after dispatch and prove a retry resumes safely.

## 10. WP-04 — Genuine eligible Gemini orchestrator

### Objective

Use one genuine eligible Gemini call to propose a bounded experiment through typed tools, with no silent simulation.

### Files

- `apps/sandbox-worker/src/orchestrator/gemini_client.py`
- `apps/sandbox-worker/src/orchestrator/planner.py`
- `apps/sandbox-worker/src/orchestrator/service.py`
- `apps/sandbox-worker/src/orchestrator/tools.py`
- `apps/sandbox-worker/src/orchestrator/prompts.py`
- `apps/sandbox-worker/src/orchestrator/plan_policy.py`
- `tests/orchestrator/`

### Tasks

1. Make client initialization errors fatal outside local mock mode.
2. Remove default Gemini 2.5 identifiers from judged execution.
3. Define strict typed tools for reading the active policy, fingerprint, configuration registry, task catalog, price version, and budget remaining; tools are read-only during planning.
4. Require structured output matching the experiment-plan schema, including baseline, candidate set, task subset, rationale, stopping rules, cost upper bound, and requested native controls.
5. Bound planner turns, tool calls, output tokens, wall time, and planner cost.
6. Persist a sanitized invocation record containing exact model, SDK/library version, request hash, tool call names/arguments, finish reason, provider response ID/version, usage metadata, latency, and errors. Do not retain hidden chain-of-thought.
7. Run the deterministic plan policy after the model response. Invalid plans are rejected or produce a bounded replan; they are never repaired silently.
8. Map exhausted planning/replanning to `TEST MORE` with a precise reason.
9. Preserve a test-only fake client behind explicit dependency injection.

### Exit gate

A retained development run proves an eligible model created a schema-valid proposed plan, deterministic policy approved it, and the exact invocation metadata can be found by `correlation_id`.

## 11. WP-05 — Immutable native configuration registry

### Objective

Ensure every run executes the configuration named by its manifest exactly.

### Files

- configuration contracts in `packages/contracts/` and worker models
- `apps/sandbox-worker/src/execution/run_service.py`
- `apps/sandbox-worker/src/execution/gemini_adapter.py`
- `apps/sandbox-worker/src/execution/provider_adapter.py`
- Firestore configuration repository
- tests under `tests/execution/` and `tests/contracts/`

### Tasks

1. Define immutable configurations with provider, exact model ID, API surface, temperature, top-p/top-k where supported, max output, native reasoning/thinking control, safety configuration, tool schema version, and price version.
2. Derive `configuration_id` from canonical content. Reject attempts to mutate an existing ID.
3. Resolve the manifest’s ID before claiming spend; remove all execution defaults.
4. Build provider requests from an allowlisted mapping and pass the native thinking/reasoning field explicitly.
5. Validate requested controls against a capability matrix. Unsupported controls are permanent plan/configuration failures, not dropped fields.
6. Persist both requested and provider-acknowledged configuration, plus provider-returned usage.
7. Freeze the baseline before planning and preserve its exact version through canary and rollback.
8. Version provider prices with source URL, currency, effective/retrieved dates, token units, and input/output/cached categories.

### Exit gate

Contract tests prove two configurations with different thinking budgets create distinct IDs and provider requests; a captured live request confirms the intended field is sent and the recorded model matches the manifest.

## 12. WP-06 — Bounded, idempotent execution and sandbox hardening

### Objective

Execute real runs safely, once per logical key, with actual usage and enforceable ceilings.

### Files

- `apps/sandbox-worker/src/execution/run_service.py`
- `apps/sandbox-worker/src/execution/gemini_adapter.py`
- `apps/sandbox-worker/src/execution/cost.py`
- `apps/sandbox-worker/src/execution/usage.py`
- `apps/sandbox-worker/src/sandbox/runner.py`
- `apps/sandbox-worker/src/sandbox/gvisor_runner.py`
- `apps/sandbox-worker/src/sandbox/git_saga.py`
- `apps/sandbox-worker/src/tools/terminal_ops.py`
- `apps/sandbox-worker/src/tools/registry.py`
- `apps/sandbox-worker/src/evaluation/oracle.py`

### Tasks

1. Derive `run_key` from experiment, task, configuration, repetition, harness, and oracle versions.
2. Claim the run transactionally before provider invocation; record an invocation fence and provider request ID when available.
3. Enforce ceilings before and after every turn: input/output tokens, estimated/actual spend, turns, tool calls, wall clock, output bytes, process count, and retry count.
4. Reserve worst-case spend transactionally at experiment level; reconcile actual cost after each terminal attempt.
5. Make provider retries explicit and bounded. Retry transport/429/eligible 5xx conditions with jitter; do not retry deterministic model output, policy rejection, test failure, or unsupported parameters as infrastructure.
6. Replace `shell=True` with argument-vector execution. Allowlist executable plus normalized arguments; reject shell operators, redirection, command substitution, environment interpolation, and traversal.
7. Restrict reads/writes to the ephemeral task workspace and reject symlink escapes.
8. Remove `git reset --hard`. Restore by discarding the temporary workspace/worktree, or use non-destructive file restoration inside an isolated copy.
9. Choose an accurate isolation claim:
   - prove `runsc`/managed gVisor with runtime evidence; or
   - call the implementation a restricted subprocess inside Cloud Run and remove gVisor claims.
10. Run deterministic tests from the frozen manifest, capturing command vector, exit code, duration, stdout/stderr hashes, assertion counts, and oracle version.
11. Persist terminal result before returning `2xx`; include failed and budget-exhausted attempts.

### Exit gate

Live tests prove exact configuration, actual usage, deterministic oracle output, duplicate delivery without duplicate spend, hard budget stop, timeout, invalid tool rejection, path escape rejection, and restart recovery.

## 13. WP-07 — Durable aggregation, sufficiency, and early stopping

### Objective

Turn stored terminal runs into one reproducible, versioned decision input.

### Files

- `apps/sandbox-worker/src/aggregation/aggregator.py`
- `apps/sandbox-worker/src/aggregation/early_stopping.py`
- `apps/sandbox-worker/src/aggregation/sufficiency.py`
- aggregate handler and Firestore repository
- tests under `tests/aggregation/`

### Tasks

1. Trigger aggregation only after terminal-run updates or a declared deadline.
2. Select eligible runs by frozen plan, schema, task, configuration, harness, oracle, and provenance versions.
3. Store exclusions with machine-readable reasons. Never delete or omit failed attempts from incurred cost.
4. Compute per configuration: attempts, verified successes, failure categories, input/output tokens, provider cost, tool/compute cost, total cost, latency distribution, pass rate, uncertainty, and CPR.
5. Define CPR as total incurred cost divided by verified successes. When successes are zero, store `value: null`, `defined: false`, and `reason: ZERO_VERIFIED_SUCCESSES`; do not use numeric zero.
6. Version all formulas, confidence methods, quality/safety floors, dominance margins, maximum failure rate, and minimum sample rules.
7. Evaluate `CONTINUE`, `STOP_DOMINATED`, `REJECT_CONFIGURATION`, `STOP_SUFFICIENT`, and `ABSTAIN` using only frozen thresholds.
8. Cancel only undispatched/unclaimed future work. Preserve dispatched, running, failed, cancelled, and completed records.
9. Make aggregate IDs content-addressed from sorted eligible runs and policy version.
10. Ensure incomplete or stale aggregates cannot replace a valid published recommendation.

### Exit gate

Golden tests cover no successes, partial failures, ties, cheapest-but-failing rejection, dominance, insufficient evidence, stale inputs, duplicate results, and late-arriving runs. Recomputing from the same records produces byte-identical canonical aggregate content.

## 14. WP-08 — Canary, promotion, rollback, receipt, and replay

### Objective

Connect aggregate outcomes to a contained policy lifecycle and exactly one public terminal decision.

### Files

- `apps/sandbox-worker/src/policy/canary.py`
- `apps/sandbox-worker/src/policy/promotion.py`
- `apps/sandbox-worker/src/policy/rollback.py`
- `apps/sandbox-worker/src/policy/repository.py`
- relevant handler wiring in `apps/sandbox-worker/src/main.py`
- receipt/hash contracts in worker and `packages/contracts/`
- policy tests under `tests/policy/`

### Tasks

1. Persist immutable baseline and candidate policy versions before canary dispatch.
2. Use distinct baseline and candidate run keys. Never place one run in both cohorts.
3. Restrict the canary to the frozen demo scope; it cannot change customer traffic.
4. Evaluate canary pass/fail with deterministic pre-versioned boundaries.
5. On pass, promote by CAS against the exact prior active version and generation.
6. On failure, retain the active baseline and record a rollback/containment event referencing the exact prior version.
7. If promotion succeeds but the post-promotion verification fails, CAS back to the exact predecessor and prove it is active.
8. Map terminal outcomes:
   - insufficient/stale/tied -> `TEST_MORE`;
   - rejected candidate or failed canary -> `STAY`;
   - sufficient aggregate plus passing canary and successful CAS -> `SWITCH`.
9. Mint exactly one canonical receipt containing trigger, fingerprint, baseline, candidate, selected cohort, eligible/excluded runs, failures, successes, total cost, CPR status/value, uncertainty, aggregate/policy versions, decision, approval boundary, canary, rollback, release SHA, and timestamps.
10. Canonicalize with the shared RFC 8785 implementation and compute SHA-256 from the receipt body excluding the digest field according to the frozen contract.
11. Append replay events for every transition and expose material inputs without secrets or hidden reasoning.
12. Reject a second conflicting receipt for the same terminal decision.

### Exit gate

Tests and a live development run prove `STAY`, `TEST_MORE`, and `SWITCH`, concurrent promotion conflict, failed canary containment, post-promotion rollback, exact receipt digest, and deterministic replay ordering.

## 15. WP-09 — Truthful web read model and public decision surface

### Objective

Serve public decisions only from stored published records, while keeping synthetic demos visibly isolated.

### Files

- `apps/web/src/lib/server/firestore-repo.ts`
- `apps/web/src/lib/task-dispatcher.ts`
- API routes under `apps/web/src/app/api/v1/`
- decision components under `apps/web/src/components/decision/`
- decision page `apps/web/src/app/decisions/[id]/page.tsx`
- fixture files under `apps/web/src/lib/`

### Tasks

1. Split repositories into `FirestoreMeasuredRepository` and `FixtureDemoRepository`; select explicitly by runtime mode.
2. Remove unconditional `seedDefaultFixtures()` from the measured repository.
3. In production, Firestore initialization/query failure returns an unavailable/error state and logs a correlation-safe error; it never substitutes fixture values.
4. Require `publication_status=PUBLISHED`, valid provenance, and a verified receipt digest for public measured routes.
5. Keep fixtures under an explicit `/demo` path or persistent `DEMO FIXTURE` banner and exclude them from recommendations/leaderboards.
6. Make decision, experiment, receipt, replay, and recommendation endpoints read the same stored identifiers.
7. Display exact model/configuration, sample counts, exclusions, failed attempts, actual usage/cost, uncertainty, freshness, “why this decision,” “what would reverse it,” and canary outcome.
8. Show CPR as undefined with reason when there are no verified successes.
9. Mark projections separately from observed values and display assumptions.
10. Add cache headers/invalidations so a prior fixture or stale decision cannot remain after publication.

### Exit gate

Route/component tests cover published, unpublished, invalid-digest, missing, stale, zero-success, `STAY`, `TEST_MORE`, `SWITCH`, and Firestore-unavailable states. The deployed page’s JSON and rendered values match the exported receipt exactly.

## 16. WP-10 — Telemetry, cost lineage, and observability

### Objective

Make the workflow diagnosable and evidence-exportable without treating logs as the sole database.

### Files

- `apps/sandbox-worker/src/telemetry/bq_streamer.py`
- `apps/sandbox-worker/src/telemetry/metrics_calculator.py`
- web/worker structured loggers
- `infra/terraform/bigquery.tf`
- dashboards/queries or evidence query scripts

### Tasks

1. Define a versioned event envelope with correlation, causation, object ID, transition, attempt, service, release SHA, severity, timestamp, and sanitized details.
2. Emit events for receipt, planning, plan policy, dispatch, claim, provider call, tool call, oracle, aggregate, canary, promotion, rollback, and publication.
3. Use provider-returned usage as the source for token costs and versioned price records for derived currency cost.
4. Reconcile experiment reservation, incurred provider cost, tool/compute cost, and remaining budget.
5. Make BigQuery writes append-only and retry-safe through deterministic event IDs.
6. Exclude prompts, source content, credentials, tokens, and raw sensitive output from public/log evidence; store hashes or approved sanitized excerpts.
7. Add alerts for authentication failures, conflicting immutable writes, duplicate invocation fences, budget breach, failed rollback, invalid receipt digest, and publication mismatch.
8. Provide one saved query or script that reconstructs the chronological workflow from a `correlation_id`.

### Exit gate

The same correlation ID returns a complete ordered event set, Firestore objects, Cloud Task names, Cloud Run revisions, provider usage, aggregate, canary, and receipt. Cost totals reconcile within the documented rounding rule.

## 17. WP-11 — Infrastructure, identities, and immutable deployment

### Objective

Deploy the source under review with reproducible artifacts and least-privilege identities.

### Files

- `infra/terraform/*.tf`
- `infra/terraform/environments/*.tfvars`
- `scripts/gcp_deploy_all.sh`
- `scripts/deploy_production.sh`
- `scripts/gcp_smoke_test.sh`
- container definitions for web and worker

### Tasks

1. Keep `infra/terraform` as the sole Terraform root and remove documentation/references to deleted legacy state.
2. Create dedicated web runtime, worker runtime, and Cloud Tasks invoker service accounts.
3. Grant only required roles: task creation, service invocation, scoped Firestore access, telemetry append, model invocation, logs, and secret access as appropriate.
4. Run web and worker under their dedicated runtime identities, not the default compute account.
5. Build images from a clean release commit and deploy by digest or immutable full Git SHA tag; prohibit environment-only tags as release evidence.
6. Inject explicit runtime mode, release SHA, exact planner model, queue, audience, invoker identity, collection namespace, and budget controls.
7. Reconcile Cloud Run ingress with IAM: the worker may be network-reachable only as required, but all non-health handlers require authenticated invocation.
8. Configure Cloud Tasks retry/rate limits to match handler idempotency and provider quotas.
9. Add required Firestore indexes and BigQuery schemas through versioned infrastructure/migrations.
10. Emit Terraform outputs for actual service URLs, revisions, service accounts, queue, project, region, and image digests.
11. Make deployment scripts consume outputs rather than construct assumed URLs.
12. Deploy development first, run gates, then production/rehearsal. Do not label development resources production.

### Rollback

- Preserve the prior web/worker image digests and Cloud Run revisions.
- Roll back traffic to those exact revisions if health, auth, persistence, or publication smoke tests fail.
- Do not roll back Firestore data destructively; new readers must tolerate prior schema versions or the release must stop before write migration.

### Exit gate

Cloud Run reports the same release SHA and image digests as the evidence manifest; current receipt routes return `200`; task authentication works; old/unauthenticated task calls fail; and no service uses the default compute identity.

## 18. WP-12 — Evidence exporter and independent verifier

### Objective

Replace generated claims with a bundle exported from actual cloud and repository state.

### Files

- replace `scripts/generate_evidence_package.py`
- add `scripts/export_evidence_package.py`
- add `scripts/verify_evidence_package.py`
- version an evidence manifest schema under `packages/contracts/`
- generated output under `evidence/runs/<correlation_id>/`

### Export requirements

The exporter accepts `correlation_id`, environment, and output directory. It reads, rather than invents:

- Firestore change event, fingerprint, configurations, plan, manifests, claims, results, aggregate, policies, canary, receipt, and replay records;
- Cloud Tasks task names/status metadata;
- filtered Cloud Logging entries;
- Cloud Run service/revision/image digest and runtime identities;
- exact Git commit and clean/dirty status;
- Terraform output/state identifiers without secrets;
- public API responses and URLs;
- sanitized Gemini invocation metadata and usage;
- test/build/security reports.

The exporter must stop on missing objects, conflicting IDs, invalid provenance, digest mismatch, an unrelated commit/revision, or fixture participation.

### Bundle layout

```text
evidence/runs/<correlation_id>/
  manifest.json
  README.md
  firestore/
  cloud-tasks/
  cloud-run/
  logs/
  provider/
  public-api/
  tests/
  screenshots/
  checksums.sha256
  verification-report.json
```

### Verification requirements

1. Validate every JSON document against the shared schema.
2. Recompute canonical IDs, run keys, aggregate ID, policy hashes, and receipt digest.
3. Check referential integrity and chronological/state-machine validity.
4. Recalculate attempt counts, successes, failures, spend, CPR, confidence values, and decision mapping.
5. Confirm no fixture is eligible or referenced.
6. Verify Git commit existence and exact full SHA; reject padded short hashes.
7. Confirm deployed release SHA/image digest and public URL responses match the manifest.
8. Hash every exported file and write `checksums.sha256` last.
9. Produce a machine-readable pass/fail report and nonzero exit status on any discrepancy.
10. Make the verifier work offline except for optional URL freshness checks.

### Exit gate

A newly cloned repository can verify the committed bundle using documented commands and obtain `PASS` without credentials. The old hard-coded generator is deleted or limited to explicitly named fixture generation.

## 19. WP-13 — Test, build, security, and CI closure

### Objective

Turn the release gate into repeatable automation and fix the broader Python collection failure.

### Tasks

1. Resolve the `tests/security` package shadowing `apps/sandbox-worker/src/security` through explicit package layout/import strategy; do not rely on test order.
2. Define one supported build environment. If Windows and WSL are both retained, document separate dependency/install paths and prove both only where required.
3. Expand `scripts/verify_monorepo.sh` to run:
   - secret and claim/provenance scans;
   - contract generation/parity/schema tests;
   - full Python tests with the production import layout;
   - worker type/lint checks;
   - web lint, typecheck, unit/API tests, and production build;
   - SDK tests/builds;
   - Terraform format, validate, and semantic tests;
   - evidence verifier tests.
4. Add integration suites using Firestore emulator, fake Cloud Tasks transport, and fake provider client.
5. Keep a small opt-in live suite for GenAI, Cloud Tasks, Cloud Run, Firestore, and public URLs; never run spend-producing tests implicitly.
6. Add negative-path tests for auth, duplicate delivery, restart, stale data, malformed provider usage, budget breach, unsupported controls, zero successes, CAS conflicts, rollback failure, invalid receipt, and fixture leakage.
7. Add a CI workflow with required jobs and retained reports. Live release gates run in the authorized GCP environment.

### Canonical local commands

```bash
bash scripts/verify_monorepo.sh
PYTHONPATH=apps/sandbox-worker/src:. python -m pytest tests apps/sandbox-worker/tests -q
pnpm build
cd infra/terraform && terraform fmt -check -recursive && terraform validate
python scripts/verify_evidence_package.py evidence/runs/<correlation_id>
```

### Exit gate

All commands pass twice from a clean checkout, no test depends on order or stale generated state, and reports identify the full release SHA.

## 20. WP-14 — Real rehearsal and measured cohort

### Objective

Produce the first valid end-to-end evidence without contaminating it with prior fixtures.

### Rehearsal procedure

1. Freeze a clean commit, task suite, oracle, prompt/tool schema, configurations, price record, and deterministic policy thresholds.
2. Run release preflight and record exact eligible Gemini model availability.
3. Submit a clearly labeled replay/change event through the deployed public/authorized entry point.
4. Observe the planner call and approved bounded plan.
5. Observe Cloud Tasks fan-out and unique logical run keys.
6. Intentionally redeliver at least one task and verify no duplicate provider spend.
7. Execute at least the minimum frozen baseline/candidate cohort required by the submission plan.
8. Preserve one failed or rejected case if it occurs naturally; do not engineer or relabel a provider failure as observed. A deterministic negative-path rehearsal may be recorded separately.
9. Observe aggregation and, if sufficient, the contained canary and CAS policy action.
10. Verify receipt/replay/public page consistency.
11. Restart a worker or replay a completed task and verify durable/idempotent behavior.
12. Export and independently verify the bundle.

### Decision handling

- Accept the genuine terminal outcome. Do not tune thresholds after observing results to force `SWITCH`.
- A valid `STAY` or `TEST_MORE` is submission-worthy if it proves the autonomous governed loop.
- If evidence is insufficient, correct defects or execute only additional work authorized by the frozen stopping policy; retain prior spend and attempts.
- Do not manually edit measured records.

### Exit gate

One correlation ID passes the offline verifier, live URL checks, and the complete release checklist’s technical sections. A separate negative-path run proves failed auth, duplicate delivery, budget stop, and canary containment without altering the primary result.

## 21. WP-15 — Submission freeze and handoff

### Objective

Freeze a coherent release in which code, deployment, evidence, documentation, and video all describe the same system.

### Tasks

1. Update the implementation status from exported evidence, not intention.
2. Rewrite README architecture, URLs, results, and status to match the verified bundle exactly.
3. Update Devpost narrative and demo script with only verified numbers and resource names.
4. Complete each checklist item with an adjacent link or artifact path; leave human/account items for their authorized owner.
5. Record public web, decision, receipt, replay, repository, video, and evidence URLs.
6. Capture the demo from the frozen deployed revisions, keeping secrets and personal data out of frame.
7. Run the full verifier and URL smoke tests after video capture.
8. Create an annotated release tag only after the final clean commit passes all gates. Record the full commit and tag object IDs.
9. Freeze deployment/repository changes for the judging window according to competition rules.
10. Prepare a rollback/contact note for availability incidents without changing evidence claims.

### Exit gate

An independent reviewer can follow README links, reproduce receipt verification, see the same decision in the public UI/API, confirm the deployed SHA/revisions, and find no unchecked technical G0 item.

## 22. File-level change map

| Area | Modify | Add | Remove/disable |
|---|---|---|---|
| Configuration | `config.py`, `.env.example`, Terraform variables | release preflight | implicit production defaults |
| Persistence | ledger and policy repositories | Firestore implementations, emulator tests | production in-memory singletons |
| Queue/auth | queue clients, dispatcher, handlers, IAM | shared routing/task-name helpers | production direct/mock fallback, optional auth |
| Planner | Gemini client/planner/tools/policy | persisted invocation repository | silent simulated planner in nonlocal modes |
| Execution | run service, adapter, tools, sandbox | exact config resolver, spend reservation | default config substitution, `shell=True`, destructive Git fallback |
| Aggregation | aggregator/stopping/sufficiency | durable aggregate service | zero CPR for no successes |
| Governance | canary/promotion/rollback | publisher/receipt coordinator | disconnected in-memory state changes |
| Web | Firestore repo, APIs, cards | explicit fixture repository/demo path | measured-route fixture seeding |
| Telemetry | BigQuery/logging | correlation query and alerts | generated event/revision claims |
| Infrastructure | Cloud Run/Tasks/IAM/deploy scripts | immutable release outputs | default compute identities, mutable release tags |
| Evidence | evidence docs/scripts | exporter, verifier, manifest schema | hard-coded measured package generator |
| CI | verification script and test layout | required CI jobs/reports | order-dependent combined test collection |

## 23. Acceptance matrix

| Requirement | Automated proof | Live proof | Retained artifact |
|---|---|---|---|
| Eligible Gemini call | client/schema/policy tests | preflight and planner invocation | sanitized provider metadata/usage |
| Durable workflow | emulator restart/transaction tests | instance restart during run | Firestore objects and replay |
| Authenticated tasks | token/claims tests | valid and invalid task calls | IAM config and filtered logs |
| Idempotent spend | duplicate/concurrency tests | forced task redelivery | one provider invocation/result per run key |
| Exact configuration | request-construction tests | captured native request metadata | configuration and result records |
| Budget/safety | ceiling/tool/path tests | bounded negative-path run | result/failure records |
| Failure-inclusive aggregation | golden recomputation | real aggregate | aggregate JSON and verifier report |
| Canary/governance | CAS/rollback tests | contained canary | policy versions, canary, receipt |
| Truthful web | API/component tests | deployed page/API checks | saved responses/screenshots |
| Immutable deploy | Terraform/deploy tests | revision/digest inspection | release manifest |
| Evidence integrity | verifier unit/tamper tests | export from live run | checksums and PASS report |
| Full repository quality | clean-checkout pipeline | release pipeline | test/build/security reports |

## 24. Definition of done

G0 is done only when all statements below are true:

- The root documentation contains no unsupported current-state claim.
- A genuine eligible Gemini 3.5-or-newer planning call is in the judged path and retained.
- Every nonlocal transition is durable in Firestore.
- Every Cloud Task is deterministically named and OIDC-authenticated.
- Missing or invalid auth fails closed.
- Every run uses the exact immutable configuration in its manifest.
- Actual provider usage, failure, latency, and cost lineage are stored.
- Budgets, turns, tools, timeouts, concurrency, and retries are enforced.
- No judged path uses `shell=True`, destructive Git cleanup, or unproved gVisor claims.
- Aggregation is failure-inclusive, reproducible, and explicit when CPR is undefined.
- Sufficiency, stopping, rejection, staleness, and abstention are versioned.
- Canary, promotion, rollback, receipt, replay, and publication form one automated chain.
- The public UI and APIs read verified published records and never silently seed fixtures.
- Deployed Cloud Run revisions identify the exact release SHA and immutable image digests.
- The evidence exporter reads real systems; the offline verifier rejects tampering.
- Full Python, JavaScript/TypeScript, SDK, Terraform, security, and evidence gates pass from a clean checkout.
- One real correlation ID reconstructs the complete workflow.
- README, Devpost, video, checklist, public URLs, release tag, and evidence bundle agree.

Anything less remains **implemented but not verified**, **prototype**, or **demo fixture**—never “production proven.”

## 25. Immediate implementation queue

Start with this exact order:

1. Complete WP-00 and commit the truth-only documentation/fixture boundary separately.
2. Implement WP-01 startup validation and live eligibility preflight.
3. Implement WP-02 Firestore repositories and restart/idempotency tests.
4. Implement WP-03 task routing, OIDC, and handler response semantics.
5. Complete WP-04 and WP-05 before spending on any cohort.
6. Complete WP-06 through WP-08 with fake-provider integration tests.
7. Connect WP-09 and WP-10, then deploy WP-11 to development by immutable digest.
8. Build WP-12 and WP-13 before treating any live run as submission evidence.
9. Execute WP-14 once, accept its honest outcome, and remediate only observed defects.
10. Complete WP-15 and freeze the release.

The first implementation commit should therefore correct truth boundaries, not add another success claim. The first spend-producing operation should be the eligible-model preflight, and the first measured cohort should occur only after persistence, identity, exact-configuration, budget, aggregation, governance, and evidence-verifier gates are green.
