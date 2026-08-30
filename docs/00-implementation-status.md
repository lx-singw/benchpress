# Benchpress implementation status

> **Status:** Authoritative
> **Verified against working tree:** 2026-08-30
> **Release decision:** **LOCAL IMPLEMENTATION COMPLETE; G0 RELEASE NO-GO UNTIL LIVE REHEARSAL**
> **Purpose:** Separate implemented code, local proof, deployed proof, measured evidence, fixtures, and roadmap claims.

## 1. Executive assessment

Benchpress now contains the complete local implementation for the bounded G0 Taskmaster workflow: fail-closed configuration, transactional Firestore repositories, deterministic authenticated Cloud Tasks, genuine nonlocal Gemini adapters, immutable native configurations, bounded duplicate-safe execution, failure-inclusive aggregation, early stopping, canary governance, atomic receipt publication, a measured-only web read model, correlated telemetry, immutable deployment infrastructure, and an offline evidence verifier.

The repository is not yet a verified G0 release. No authorized cloud deployment and rehearsal from the current release SHA has been completed, no eligible Gemini 3.5-or-newer call from that deployment has been retained, and no measured evidence bundle from one real correlation ID exists. Consequently, the public claim remains “implemented and locally verified,” not “deployed,” “measured,” or “production verified.”

Historical numbers and files directly under `evidence/` remain `DEMO_FIXTURE`. They cannot support public model recommendations.

## 2. Work-package status

| Work package | Implementation state | Local proof | Remaining release proof |
|---|---|---|---|
| WP-00 Truth quarantine | Implemented | Root/evidence status labels, disabled synthetic measured generator, fixture badges, truth-boundary scan | Final submission-document claim audit after measured export |
| WP-01 Release configuration/preflight | Implemented | Strict runtime settings and preflight tests | Authorized spend-producing preflight with exact eligible model |
| WP-02 Firestore system of record | Implemented | Transactional repository, immutable records, replay, and passing Firestore emulator restart/CAS suite | Deployed restart rehearsal |
| WP-03 Cloud Tasks/authentication | Implemented | Deterministic names, exact OIDC claims, negative tests | Live valid/invalid delivery and forced redelivery evidence |
| WP-04 Gemini orchestrator | Implemented | Nonlocal adapter fails closed; structured-plan tests | Genuine Gemini 3.5+ invocation and retained response metadata |
| WP-05 Native configuration registry | Implemented | Cross-contract deterministic IDs and substitution rejection | Captured provider request from a deployed run |
| WP-06 Bounded execution | Implemented | Cost/turn/tool/timeout ceilings, argument-vector subprocesses, duplicate-safe claims | Live duplicate delivery with one provider charge; container health proof |
| WP-07 Aggregation/stopping | Implemented | Failure-inclusive deterministic aggregates, undefined zero-success CPR, atomic pending cancellation | Real cohort recomputation from exported records |
| WP-08 Governance/publication | Implemented | Deterministic canary, CAS promotion/rollback, atomic single publication | Contained live canary plus promotion or rollback evidence |
| WP-09 Web read model | Implemented | Fixture/measured repositories are separate; invalid or unpublished receipts fail closed; 8 API/read-model tests | Deployed decision, receipt, replay, and routing URL checks |
| WP-10 Telemetry/observability | Implemented | Versioned sanitized events, deterministic event IDs, BigQuery schema, alerts, reconstruction script | BigQuery/Logging records joined by the rehearsal correlation ID |
| WP-11 Infrastructure/deployment | Implemented, not applied | Terraform format/validate and 14 semantic tests; dedicated identities and immutable images | Build, push, apply, smoke-test, and prove revisions match the release SHA |
| WP-12 Evidence exporter/verifier | Implemented | Fail-closed exporter, checksums, schema/digest/lineage verifier, negative tests | Export one live bundle and obtain offline `PASS` from a clean clone |
| WP-13 Test/CI closure | Implemented locally | Full Python suite, contracts, web tests/build, SDK/telemetry builds, Terraform validation, CI workflow | Clean-checkout CI run and retained reports for the frozen SHA |
| WP-14 Real rehearsal | Not performed | Procedure documented | Authorized deployment, primary run, redelivery/restart and negative-path run |
| WP-15 Submission freeze | Not performed | Handoff checklist and runbook prepared | Human/account items, evidence-linked docs, video, public URLs, tag and freeze |

## 3. Current local verification snapshot

Observed in the current workspace on 2026-08-30:

| Gate | Result |
|---|---|
| Full Python collection | **129 passed** with the Firestore emulator enabled; durable terminal-result replay and policy CAS restart paths included |
| Web/API/read-model tests | **8 passed** |
| Contracts tests and build | **Pass** |
| Next.js production build | **Pass** |
| Production dependency audit | **Pass; no known vulnerabilities** |
| Telemetry and TypeScript SDK builds | **Pass** |
| Terraform semantic tests | **14 passed** |
| Terraform `fmt -check -recursive` and `validate` | **Pass** using the Windows Terraform binary |
| Critical Ruff scan | **Pass** |
| Truth/provenance boundary scan | **Pass** |

These observations are local development evidence. They are not a substitute for a clean CI run, container build, cloud deployment, live provider invocation, or independently verified measured bundle.

Current live-readiness check on 2026-08-30: Docker and Terraform are available, but the WSL environment has no active `gcloud` account, no selected Google Cloud project, no exact `PLANNER_MODEL`, and the working tree is not clean. Live preflight and deployment must remain blocked until an authorized operator supplies those inputs and freezes a release SHA.

## 4. Implemented G0 boundary

The implemented path is:

```text
ChangeEvent
  -> deterministic experiment identity and durable state
  -> eligible-model Gemini planner request in nonlocal modes
  -> deterministic plan approval
  -> OIDC-authenticated deterministic Cloud Tasks
  -> exact immutable provider configurations
  -> bounded idempotent runs and deterministic oracles
  -> failure-inclusive aggregates and early stopping
  -> contained canary and policy compare-and-swap
  -> atomic STAY / TEST MORE / SWITCH receipt publication
  -> measured-only public decision, receipt, replay, and routing reads
  -> correlated sanitized logs and BigQuery workflow events
```

Local fixture mode remains available for development and is visibly classified `DEMO_FIXTURE`. Nonlocal modes reject fixture fallback, missing cloud configuration, ineligible planner models, invalid task identity, unknown native configurations, and unpublished or invalid-digest receipts.

## 5. Explicitly unverified or out of scope

The following must not be presented as current demonstrated capabilities:

- Any exact cost reduction, pass-rate gain, latency improvement, scale, or accuracy figure not linked to a verified measured bundle.
- A production-ready or generally secure sandbox. The active runner is a bounded subprocess runner; `runsc` detection is not gVisor integration.
- eBPF enforcement, SEV-SNP, VPC Service Controls, CMEK, Model Armor, BigQuery Storage Write, WebRTC, autonomous pull-request creation, enterprise compliance, or customer production-traffic control.
- Universal model superiority or a recommendation beyond the exact frozen task/configuration cohort.
- A deployed release, genuine eligible Gemini call, measured cohort, successful canary, public video, or completed Devpost submission until the corresponding artifact exists.

## 6. Definition of measured evidence

A value may be labelled `BENCHPRESS_MEASURED` only when the evidence bundle retains:

- the provider-returned exact model version and native configuration;
- provider usage, observed latency, attempts, failures, oracle output, and all incurred cost;
- task, repository, harness, oracle, prompt, tool-schema, policy, and code versions;
- deterministic logical run keys and immutable manifests/results;
- a failure-inclusive aggregate and its source-result digest;
- the approved plan, trigger, fingerprint, canary/governance result, terminal receipt, publication pointer, and replay;
- Cloud Tasks, Cloud Run, Firestore, Logging, Terraform, Git, public API, and test-report provenance; and
- a successful offline run of `scripts/verify_evidence_package.py`.

Everything else is an official specification, projection, historical hypothesis, community result, prototype, or demo fixture.

## 7. Next release actions

Follow [Release verification and rehearsal](./implementation/07-release-verification-and-rehearsal.md). In order:

1. Commit the implementation and obtain a clean CI pass for the full release SHA.
2. Confirm an account-available exact Gemini 3.5-or-newer model and run the live preflight.
3. Build immutable web/worker images, apply `infra/terraform`, and verify the deployed revisions.
4. Run the primary measured cohort plus duplicate-delivery, restart, invalid-auth, budget-stop, and canary-containment proofs.
5. Export the correlation-scoped evidence bundle and verify it offline from a clean clone.
6. Only then update measured claims, record the video, complete Devpost, tag, and freeze the submission.

## 8. Documentation precedence

This file and the following documents are authoritative in order:

1. [G0 remediation implementation plan](./planning/07-g0-remediation-implementation-plan.md)
2. [Release verification and rehearsal](./implementation/07-release-verification-and-rehearsal.md)
3. [Final submission checklist](./hackathon/04-final-submission-checklist.md)
4. [Submission-critical implementation plan](./planning/06-submission-critical-implementation-plan.md)

Architecture, governance, research, and earlier audit documents are retained as design or historical material unless a claim is explicitly linked to current measured evidence.
