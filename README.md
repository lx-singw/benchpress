# Benchpress

Benchpress is a prototype autonomous model-change evaluation and governance engine. The repository contains a Next.js decision surface, a Python Cloud Run worker, shared contracts, deterministic evaluation fixtures, policy and aggregation components, and Terraform for Google Cloud.

> **Current status (2026-08-29):** the bounded G0 path is implemented and locally verified, but it is not yet cloud-rehearsed or supported by a measured release bundle. Local mock mode and demo fixtures remain intentionally separate. Do not treat fixture metrics or historical generated evidence as provider measurements.

## Target workflow

Benchpress is being implemented to:

1. fingerprint a workload and its active model configuration;
2. use an eligible Gemini orchestrator to propose a bounded experiment;
3. approve the plan with deterministic budget and safety policy;
4. dispatch idempotent runs through authenticated Google Cloud Tasks;
5. execute exact native model configurations and deterministic test oracles;
6. aggregate every incurred attempt with failure-inclusive cost accounting;
7. run a contained canary and atomically promote or retain the active policy; and
8. publish a verifiable `STAY`, `TEST MORE`, or `SWITCH` receipt and replay.

This is the target architecture. The judged path is complete only after one real correlation ID reconstructs the entire deployed workflow from retained records.

## Current release decision

The project is **NO-GO for a verified G0 release claim** until the live rehearsal and submission freeze are complete. The remaining blockers are:

- the retained files under `evidence/` are synthetic UI/schema fixtures;
- no eligible Gemini 3.5-or-newer planning call from the release deployment has yet been retained;
- the current source revision has not been built, deployed, and proved through the live preflight;
- Firestore-emulator tests were skipped in the current local environment and must pass in the release environment;
- no real duplicate-delivery/restart/canary rehearsal has been retained; and
- no real measured cohort currently supports the historical savings and pass-rate examples.

## Authoritative documents

Read these in order:

1. [Current implementation status](./docs/00-implementation-status.md)
2. [G0 audit-remediation implementation plan](./docs/planning/07-g0-remediation-implementation-plan.md)
3. [Submission-critical implementation specification](./docs/planning/06-submission-critical-implementation-plan.md)
4. [Release verification and rehearsal](./docs/implementation/07-release-verification-and-rehearsal.md)
5. [Final submission checklist](./docs/hackathon/04-final-submission-checklist.md)
6. [Documentation index](./docs/README.md)

## Repository structure

```text
benchpress/
├── apps/
│   ├── web/                     # Next.js decision UI and API routes
│   └── sandbox-worker/          # Python orchestration and execution worker
├── packages/
│   ├── contracts/               # Shared schemas, types, and canonical hashing
│   └── sdk/                     # Client SDK packages
├── infra/terraform/             # Current Google Cloud infrastructure root
├── evidence/                    # Fixtures now; verified runs will use evidence/runs/
├── scripts/                     # Validation, deployment, and evidence tooling
├── tests/                       # Cross-component and integration tests
└── docs/                        # Architecture, methodology, planning, and submission docs
```

## Local verification

Run the scoped repository gate:

```bash
bash scripts/verify_monorepo.sh
```

Individual checks:

```bash
pnpm --filter @benchpress/contracts test
pnpm --filter web test
pnpm --filter web build
python scripts/validate_demo_manifest.py
PYTHONPATH=apps/sandbox-worker/src:. python -m pytest tests apps/sandbox-worker/tests -q
cd infra/terraform && terraform fmt -check -recursive && terraform validate
```

Current local observations are 127 passed/2 Firestore-emulator skips for the combined Python suite and 8 passed for the web/API/read-model suite; contracts, web production build, SDK/telemetry builds, critical Ruff checks, Terraform validation, and truth-boundary checks pass. These results must be reproduced from the clean release commit and retained by CI.

## Evidence policy

Every empirical value must be labeled as one of:

- `BENCHPRESS_MEASURED` or `OBSERVED`: derived from a retained real run;
- `OFFICIAL_SPECIFICATION`: sourced from a provider or authoritative specification;
- `PROJECTED`: calculated from explicit assumptions;
- `ILLUSTRATIVE` or `DEMO_FIXTURE`: synthetic data used for design or testing.

Files currently stored directly under [`evidence/`](./evidence/README.md) are `DEMO_FIXTURE` artifacts and are ineligible for public recommendations. Future verified bundles will be exported from actual Firestore, Cloud Tasks, Cloud Run, provider, and repository state into `evidence/runs/<correlation_id>/` and must pass an independent verifier.

## Deployment

Terraform and the fail-closed deployment/preflight/smoke tooling are implemented but have not been applied for the current release SHA. Do not infer a live production URL, model invocation, or revision from an example variable or generated fixture. Follow the [release rehearsal runbook](./docs/implementation/07-release-verification-and-rehearsal.md).

## Contributing

Changes that touch the judged workflow should include tests for durable state, duplicate delivery, authentication, exact provider configuration, budget enforcement, failure-inclusive accounting, policy compare-and-swap, and fixture exclusion as applicable. Public claims must link to a verifiable artifact.
