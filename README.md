# Benchpress

Benchpress is an autonomous model-evaluation and routing intelligence platform. It is designed to detect relevant model or pricing changes, evaluate supported model and reasoning configurations on reproducible tasks, and publish evidence-backed recommendations before engineering teams spend money on production agent runs.

The repository currently contains a substantial product prototype: a Next.js web experience, a Python worker and finite-state runtime, SDKs, telemetry contracts, evaluation fixtures, tests, and Google Cloud infrastructure definitions. Some paths still use simulated execution or static demonstration data. The documentation distinguishes those paths from measured results.

## Current hackathon objective

The Google Cloud All Things Agentic submission is a narrow, real Taskmaster workflow:

```text
Model or configuration change
        -> Gemini evaluation orchestrator
        -> budget-bounded benchmark plan
        -> parallel Cloud Tasks workers
        -> deterministic tests and usage capture
        -> persisted aggregate
        -> public Benchpress recommendation
```

The intended architecture is **one autonomous Gemini orchestrator with many controlled benchmark workers**. Parallel workers are execution jobs, not a swarm of independent agents.

Read these documents in order:

1. [Implementation status](./docs/00-implementation-status.md)
2. [Authoritative hackathon submission plan](./docs/hackathon/00-authoritative-submission-plan.md)
3. [Master build roadmap](./docs/planning/00-master-build-roadmap.md)
4. [Agent and worker architecture](./docs/architecture/06-agent-orchestration-and-swarm-topology.md)
5. [Model registry and evaluation methodology](./docs/evals/04-multi-model-continuous-harvester-and-deep-profiles.md)
6. [Hackathon-to-startup roadmap summary](./docs/planning/01-product-roadmap-and-phases.md)
7. [Complete documentation index](./docs/README.md)

## Repository layout

```text
apps/web                 Next.js web application and API routes
apps/sandbox-worker      Python worker, FSM, tools, telemetry, and safeguards
packages/sdk-python      Python client and CLI
packages/sdk-ts          TypeScript client
packages/telemetry       Shared telemetry contracts
packages/integrations    Integration scaffolding
packages/distillation    Experimental post-hackathon pipeline
infra/terraform          Primary Google Cloud infrastructure definitions
terraform                Legacy/alternate Terraform definitions pending consolidation
docs                     Product, architecture, methodology, and submission documentation
tests                    Cross-cutting prototype and safeguard tests
```

## Local development

Prerequisites:

- Node.js compatible with Next.js 15
- `pnpm` 10
- Python 3.12+
- Google Cloud credentials only for real cloud execution

Install JavaScript dependencies:

```bash
pnpm install
```

Create a local environment file from `.env.example`. Keep `USE_LOCAL_MOCK=true` for fixture-backed development; set it to `false` only after configuring real credentials and secured worker endpoints.

Run the web application:

```bash
pnpm dev
```

Run the worker from `apps/sandbox-worker` after installing its Python package:

```bash
python -m pip install -e .
python src/main.py
```

Useful verification commands:

```bash
pnpm build
python -m pytest tests apps/sandbox-worker/tests
python -m pip install -e packages/sdk-python
python -m pytest packages/sdk-python/tests
```

The exact judged cloud path, proof requirements, and known gaps are tracked in the [submission plan](./docs/hackathon/00-authoritative-submission-plan.md).

## Data and claims policy

Benchpress separates four kinds of information:

- **Official specification:** sourced from a provider API or official provider documentation.
- **Benchpress measured:** produced by a reproducible Benchpress run with a stored manifest and deterministic outcome.
- **Community verified:** submitted with provenance and independently reproduced.
- **Demo fixture:** synthetic data used to exercise the interface or tests.

No fixture value should be presented as an empirical benchmark. Every public recommendation should show its source, configuration, task cohort, sample count, harness version, evaluation date, and confidence or limitations.

## Product direction

The public web catalog and measured leaderboard are intended to remain free to browse. The startup business is built around private evaluations, continuous regression monitoring, routing APIs, policy deployment, team economics, and enterprise governance—not charging users merely to view public model facts.

## Hackathon eligibility note

The official submission requires Gemini 3.5 or newer, a Google agent framework, and at least one Google Cloud infrastructure service. The project is targeting **The Taskmaster**. Any pre-existing work incorporated into the entry must be disclosed according to the official rules and FAQ.
