# Benchpress documentation

This directory contains both current product documentation and earlier design material. The files listed under **Authoritative documents** define the present implementation truth and take precedence over older claims, diagrams, ADR statuses, or performance figures.

## Status vocabulary

All product capabilities should use one of these labels:

| Status | Meaning |
|---|---|
| **Implemented and demonstrated** | The path executes end to end and has retained evidence. |
| **Implemented, not cloud-verified** | Code exists, but the required deployed path has not yet been evidenced. |
| **Prototype** | The component exists but depends on mocks, fixtures, hard-coded behavior, or incomplete controls. |
| **Demo fixture** | Data or behavior is intentionally synthetic for UI or test development. |
| **Proposed** | Design or roadmap material; not implemented. |
| **Historical** | Superseded planning material retained for context. |

When another document conflicts with the status inventory, the [implementation status](./00-implementation-status.md) is authoritative.

## Authoritative documents

Read in this order:

1. [Current implementation status](./00-implementation-status.md) — what exists, what is simulated, and what is missing.
2. [Hackathon submission plan](./hackathon/00-authoritative-submission-plan.md) — the exact judged scope and definition of done.
3. [Master build roadmap](./planning/00-master-build-roadmap.md) — complete hackathon and 24-month execution plan, sprint schedule, gates, epics, controls, and commercialization sequence.
4. [Agent orchestration architecture](./architecture/06-agent-orchestration-and-swarm-topology.md) — one Gemini orchestrator and parallel controlled workers.
5. [Model registry and evaluation methodology](./evals/04-multi-model-continuous-harvester-and-deep-profiles.md) — how provider facts and measured results are acquired and published.
6. [Hackathon-to-startup roadmap](./planning/01-product-roadmap-and-phases.md) — concise staged product and commercial summary.

## Core proof crosswalk

The strengthened judged workflow is documented once at the level where it is authoritative:

| Concern | Authoritative document |
|---|---|
| Judged scope, policy lifecycle, build order, and definition of done | [Hackathon submission plan](./hackathon/00-authoritative-submission-plan.md) |
| One orchestrator, typed tools, early stopping, canary, rollback, and replay state | [Agent orchestration architecture](./architecture/06-agent-orchestration-and-swarm-topology.md) |
| Task fingerprints, adaptive experiment design, rejection, abstention, cost accounting, and staleness | [Evaluation methodology](./evals/04-multi-model-continuous-harvester-and-deep-profiles.md) |
| Published `STAY`, `TEST MORE`, or `SWITCH` API envelope | [Model Router Integration](./api/02-model-router-integration.md) |
| Current-versus-candidate adoption-time UX | [User journeys and wireframes](./design/03-user-journeys-and-wireframes.md) |
| Four-minute visible proof | [Demo script](./hackathon/02-demo-video-script.md) |
| Submission and optional-bonus release gates | [Final checklist](./hackathon/04-final-submission-checklist.md) |
| Full build timeline, sprints, epics, release gates, controls, and post-hackathon sequence | [Master build roadmap](./planning/00-master-build-roadmap.md) |
| Concise post-hackathon product sequence | [Roadmap summary](./planning/01-product-roadmap-and-phases.md) |

## Hackathon submission documents

- [Authoritative submission plan](./hackathon/00-authoritative-submission-plan.md)
- [Devpost narrative](./hackathon/01-devpost-narrative.md)
- [Four-minute demo script](./hackathon/02-demo-video-script.md)
- [Judging criteria analysis](./hackathon/03-judging-criteria-deep-dive.md) — supporting analysis; validate claims against the authoritative plan.
- [Final submission checklist](./hackathon/04-final-submission-checklist.md)
- [Competition readiness report](./hackathon/05-competition-readiness-report.md) — audit and risk evidence, not marketing copy.

## Detailed reference domains

- `architecture/` — system boundaries, runtime, data flow, infrastructure, and ADRs.
- `api/` — API and SDK contracts.
- `community/` — contribution and future benchmark-verification processes.
- `design/` — UI system, journeys, and multimodal concepts.
- `evals/` — datasets, task schemas, contamination controls, and model evaluation.
- `governance/` — security and compliance requirements; many are target-state controls.
- `implementation/` — development, deployment, testing, and operations.
- `methodology/` — CPR, trajectory metrics, and task-suite definitions.
- `planning/` — roadmap, backlog, risks, budgets, and commercialization.
- `research/` — hypotheses and research narratives; empirical wording requires measured evidence.
- `telemetry/` — event semantics, cost queries, and monitoring design.

## Documentation rules

1. Never describe a fixture, mock, formula-generated result, or local simulation as a measured provider result.
2. Never use exact savings, success, latency, compression, or compliance percentages without a linked run manifest or external source.
3. Distinguish code existence from deployed proof.
4. Use exact provider-native model and reasoning parameters in measurement records.
5. Mark roadmap components visually and textually; do not place them inside the demonstrated boundary of an architecture diagram.
6. Preserve source URLs, effective dates, and retrieval timestamps for provider facts and prices.
7. Treat destructive actions, external writes, and production policy changes as approval-boundary events.

## Current product statement

> **Benchpress autonomously detects AI model, reasoning, capability, and pricing changes; designs the smallest experiment needed to compare them with a team’s current configuration; rejects candidates that fail real workflows; and publishes a verifiable `STAY`, `TEST MORE`, or `SWITCH` decision—with contained canary promotion and rollback before engineering teams risk production quality or spend.**

Publication and decision-time delivery are complementary parts of one product:

- The free public web publishes provider facts, measured cohorts, methodology, historical receipts, and current recommendations.
- The decision surface brings the relevant published evidence into the moment a user, IDE, agent framework, gateway, or policy owner is considering a change.
- The autonomous evaluation loop creates new evidence when the existing public or private evidence is stale, incompatible, or insufficient.

Benchpress is therefore neither only a benchmark website nor only an opaque router. It is the evidence and policy-decision layer connecting model change detection to safe adoption.

For the hackathon, this is implemented as one bounded Taskmaster workflow. Post-hackathon, the same registry, run ledger, evaluation harness, and public web surface become the foundation for a multi-provider startup.
