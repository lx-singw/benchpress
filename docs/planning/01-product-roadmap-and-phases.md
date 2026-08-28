# Hackathon-to-startup product roadmap

> **Document ID:** `BP-PLAN-001`
> **Status:** Authoritative roadmap
> **Planning principle:** Prove one trustworthy loop, then expand coverage and control
> **Detailed execution plan:** See the [master build roadmap](./00-master-build-roadmap.md) for dated hackathon mini-sprints, the full 24-month sprint sequence, epics, release gates, controls, risks, and GTM timeline.

## 1. Product direction

Benchpress begins as an autonomous evaluation workflow and grows into an independent model and agent economics control layer.

The product has two mutually reinforcing surfaces rather than two competing directions:

1. **Publish:** keep provider facts, measured cohorts, methodology, recommendations, receipts, and replay free to browse on the Benchpress web.
2. **Decide at adoption time:** surface the relevant published or private evidence as `STAY`, `TEST MORE`, or `SWITCH` when a user, IDE, SDK, gateway, or policy owner considers changing models.

```text
Public provider facts
        +
Reproducible measured outcomes
        +
Configuration-aware recommendations
        +
Customer-specific policy deployment
```

The public catalog and aggregate explorer remain free to browse. Revenue comes from private evaluations, continuous monitoring, routing APIs, team controls, governed deployment, and enterprise support.

## 2. Durable product thesis

The long-term defensible asset is not a static leaderboard or a clever formula. It is a growing, consented, versioned dataset connecting:

- Exact provider, model, deployment, and native reasoning configuration.
- Task and repository characteristics.
- Prompt, tools, context, and harness version.
- All attempts, failures, retries, tokens, latency, and compute.
- Deterministic and delayed quality outcomes.
- The policy decision that followed and its production effect.

The startup becomes more valuable as it learns which configuration works for which segment under explicit quality, cost, latency, privacy, and reliability constraints.

## 3. Phase zero: hackathon proof

### Objective

Demonstrate one complete Taskmaster workflow with undeniable execution evidence.

### Deliverables

- One Gemini 3.5+ Evaluation Orchestrator using an allowed Google agent framework.
- Typed tools and deterministic approval boundaries.
- A small versioned Gemini model/configuration registry.
- The exact current configuration as the decision baseline.
- A versioned task fingerprint—including workflow phase—and Gemini-designed discriminating experiment.
- A 3–10 task coding cohort.
- Two or three real native thinking configurations.
- Authenticated, idempotent Cloud Tasks dispatch.
- Cloud Run worker execution.
- Actual provider usage and deterministic tests.
- Sequential stopping that retains all incurred attempts and costs.
- A deliberate cheapest-candidate rejection plus an honest abstention path.
- Persisted run ledger and versioned aggregate.
- A contained, versioned canary with deterministic promotion and automatic rollback.
- Public recommendation and Switch Decision Card with `STAY`, `TEST MORE`, or `SWITCH`, “Why not cheapest?”, “what would reverse this?”, evidence receipt, and replay timeline.
- Automatic staleness for model/price/tool/task/harness/oracle changes and delayed regressions.
- Fixture labels on all legacy static data.
- Root README, accurate architecture diagram, public repository, and sub-four-minute demo.

### Exit gate

The same correlation ID is visible from trigger through Gemini decision, worker jobs, tests, stopping decision, aggregate, policy canary/rollback, receipt, replay, and public recommendation.

### Optional hackathon bonus gate

Only after the phase-zero exit gate and reliability tests pass:

- Prefer one genuine Gemma integration as a low-cost task-fingerprint classifier or as a challenger configuration evaluated through the same harness.
- Retain its exact model ID, invocation, output, usage/cost, and workflow effect.
- Keep it within the single-orchestrator topology; an additional model does not imply an additional agent.
- Optionally publish qualifying public build content and a qualifying social post under the current official hackathon instructions.
- Do not add Veo, Lyria, voice, vision, or unrelated multimodal scope merely to collect a bonus.

The bonus is cut immediately if it reduces core reliability, demo clarity, or submission readiness.

## 4. Phase one: trustworthy public beta (0–3 months)

### Objective

Turn the demonstrated slice into a repeatable public measurement product.

### Product

- Versioned provider registry for Google, OpenAI, and Anthropic.
- Official-source collection with freshness and deprecation monitoring.
- Provider-native configuration adapters.
- Stable coding task taxonomy and run manifests.
- Progressive smoke, screening, promotion, and certification cohorts.
- Adaptive experiment selection and sequential evidence acquisition.
- Public model/configuration pages and task-segment comparisons.
- Versioned decision receipts, replay, rejection/abstention reasons, and observed counterfactual cost.
- A current-versus-candidate Switch Decision Card consumable on the web and through a stable API/SDK contract.
- Visible `OBSERVED`, `PROJECTED`, and `ILLUSTRATIVE` economic labels with auditable assumptions.
- Workflow-phase segmentation for planning, specification, execution, review, refinement, and whole-workflow evidence.
- Downloadable aggregate snapshots and methodology.
- Stale, experimental, community, measured, official, and fixture badges.
- Budget, retry, timeout, and concurrency controls.

### Engineering

- Replace the simulated harvester with provider-backed adapters.
- Replace static model metrics with registry and aggregate reads.
- Consolidate Terraform.
- Harden authentication, idempotency, durable task ownership, and negative tests.
- Add immutable model/price/harness/task versions.
- Add automatic staleness and targeted refresh on model alias, price, tool-schema, task, harness, oracle, and delayed-regression changes.
- Export CDN-ready JSON/Parquet snapshots so public browsing does not query the warehouse.
- Replace the hard-coded ROI calculator and routing response with measured aggregates plus explicitly labelled projections.
- Add continuous integration for build, tests, formatting, IaC validation, and secret scanning.

### Evidence gate

- At least three coding task segments.
- Published raw methodology and cohort manifests.
- Confidence-aware results with no fixture contamination.
- Repeatable refresh after one model or pricing change.
- Verified rejection, abstention, and stale-result behavior without forced winners.

## 5. Phase two: private customer evaluation (3–6 months)

### Objective

Prove willingness to pay by evaluating the customer's own workflows safely.

### Customer product

- Private task and repository ingestion.
- Customer-defined success tests and constraints.
- Bring-your-own-provider-key or customer-cloud execution.
- Private dashboards for quality, CPR, latency, failures, and drift.
- Recommended model/reasoning configuration by workload segment.
- Scheduled regression runs on provider/model/harness changes.
- Audit receipts for every recommendation.

### Trust requirements

- Explicit data-processing and learning consent.
- Tenant isolation, retention, deletion, encryption, and access controls.
- Redaction before persistence.
- Source and license provenance.
- Customer-controlled exclusions from aggregate learning.
- Human approval before production policy changes.

### Commercial test

- Design partners with repeatable evaluation pain.
- Time-to-first-value measured in days, not quarters.
- Demonstrated savings or quality improvement after accounting for failures and review.
- Pricing validated before building a broad enterprise appliance.

## 6. Phase three: routing and policy control (6–12 months)

### Objective

Move from recommendation to governed operational control.

### Product

- Routing recommendation API and supported SDKs.
- Gateway/framework adapters rather than replacement of every platform layer.
- Task classification from explicit prompts/events and approved workspace metadata.
- Phase-aware route policies that can map planning, execution, and review to different exact configurations.
- End-to-end policy evaluation including handoff tokens, repeated context, replanning, escalation, and failure costs.
- Versioned customer policy templates; no claim that “frontier plans, cheap model executes” is universally optimal.
- Confidence-aware fallback to a customer baseline.
- Versioned policy artifacts.
- Shadow evaluation and randomized/interleaved canaries.
- Bounded traffic rollout, cooldown, drift monitoring, and automatic rollback.
- Cost, quality, latency, and failure SLOs.
- Per-PR or per-workflow FinOps receipts.

### Promotion gate

A new policy may receive production traffic only when:

- Minimum sample and confidence thresholds are met.
- Quality is non-inferior under customer constraints.
- Security and data policy allow the route.
- Expected value exceeds switching and integration costs.
- Rollback is tested and automatic.

## 7. Phase four: enterprise control plane (12–24 months)

### Objective

Support regulated, multi-team deployment after demand and product-market fit are demonstrated.

### Product

- Organization/tenant policy hierarchy.
- Model/provider allowlists and data-residency routing.
- Customer-managed keys and private-network deployment options.
- Identity-scoped tools and credentials.
- Long-term audit records and deletion workflows.
- Agent/configuration registry for approved internal workflows.
- Enterprise observability integrations.
- Package, license, vulnerability, secret, and PII policy gates.
- Private marketplace or appliance only where customer demand justifies it.

Formal compliance claims require audited controls and evidence; documentation alone is not certification.

## 8. Proactive capability disposition

The earlier “zero-ask superpowers” are retained, but their scope and sequence are corrected.

| Capability | Decision | Phase | Correct product form |
|---|---|---:|---|
| Model and thinking prescriber | **Core** | 0–1 | Recommend exact native configuration after intent/event, with confidence and measured evidence |
| Switch Decision Card | **Core delivery surface** | 0–1 | Publish and surface `STAY`, `TEST MORE`, or `SWITCH` against an explicit current baseline |
| Phase-aware routing choreography | **Core startup extension** | 1–3 | Evaluate complete planner/executor/reviewer policies, including handoff and failure economics |
| Runaway loop and budget breaker | **Core safeguard** | 0–1 | Deterministic spend/turn/retry/time ceilings; pause or halt safely |
| Context bloat reduction | **Research then opt-in** | 2–3 | Measure prompt/context variants; never strip code/comments with assumed zero loss |
| Prompt-cache optimization | **Useful optimization** | 2–3 | Provider-specific cache policy with measured net cost, not a universal discount promise |
| Provider outage failover | **Later reliability feature** | 3 | Health-aware bounded fallback with compatibility tests and customer policy; no prediction claim |
| Secret and PII controls | **Required safeguard** | 1–4 | Redact before persistence/dispatch, preserve mapping only within approved trust boundary, test leakage paths |
| Legacy model migration scanner | **Good acquisition feature** | 2–3 | Inventory model calls, estimate alternatives, create a reviewable plan; never open or merge changes without approval |
| Regression-test assistance | **Selective feature** | 2–3 | Suggest tests and run independent existing/hidden tests; generated tests do not certify their own patch |
| Cross-developer semantic caching | **High-risk research** | 3–4 | Tenant-scoped, authorization-aware verified artifacts with freshness; no cross-tenant reuse |
| Hyperparameter tuning | **Core extension** | 1–3 | Provider-native controlled sweeps; do not rely on universal temperature folklore |
| PR receipts and compliance notes | **Strong product feature** | 2–3 | Actual model/usage/test/cost/provenance receipt; compliance language limited to implemented controls |
| License and CVE gate | **Enterprise policy feature** | 3–4 | Policy-configurable package/license/vulnerability checks; legal review for license decisions |
| Polyglot toolchain selection | **Execution infrastructure** | 2–3 | Reproducible pinned toolchain images selected from repository manifests |
| Trajectory distillation | **Conditional later feature** | 4 | Only with consent, provenance, licensing, privacy, reliable labels, and demonstrated need |

## 9. Capabilities explicitly rejected in their original form

- Automatic `git reset --hard` against user work.
- Guaranteed zero-loss context pruning.
- “Predictive” provider outage detection without evidence.
- Automatic substitution of supposedly equivalent models across incompatible tools or semantics.
- Universal cross-team answer caching without authorization and freshness boundaries.
- Treating generated tests as independent proof.
- Describing copyleft licensing as automatic “infection.”
- Exporting customer trajectories for training by default.
- Exact savings or compliance guarantees without measurement or audit.
- Passive workspace surveillance before clear user or organizational authorization.

The desired experience is **zero unnecessary configuration after the user or system expresses intent**, not hidden action before intent exists.

## 10. Agent architecture evolution

### Hackathon and early product

- One Evaluation Orchestrator.
- Typed deterministic tools.
- Parallel worker jobs.
- Deterministic aggregation and policy.

### Add specialists only when justified

Potential later roles:

- Catalog Intelligence Agent.
- Benchmark Design Agent.
- Security/Policy Agent.
- Recommendation Explanation Agent.

A specialist is added only when it has distinct permissions/context, an independently testable contract, and measured benefit. Worker concurrency remains separate from agent count.

## 11. Data flywheel

### Required inputs

- Consent and provenance.
- Exact model/configuration/harness versions.
- Deterministic and delayed outcome labels.
- Full attempts and economic accounting.
- Contamination-resistant holdouts.
- Customer segment descriptors.

### Learning loop

```text
Observe candidate change
  -> evaluate on frozen cohort
  -> estimate segment-level effect
  -> shadow or canary policy
  -> observe quality/cost/latency and delayed regressions
  -> promote, hold, or roll back
  -> update policy evidence
```

Historical correlation alone never authorizes a production policy change.

## 12. Public-free and commercial boundary

### Free public surface

- Provider facts and sources.
- Model/configuration explorer.
- Public measured cohorts.
- Methodology and limitations.
- Aggregate downloads.
- Basic recommendation explorer.
- Published Switch Decision Cards and historical `STAY`, `TEST MORE`, or `SWITCH` receipts for public cohorts.

### Paid product

- Private repositories/tasks and custom outcome oracles.
- Continuous customer-specific regression evaluation.
- BYOK or customer-cloud execution.
- Routing API and team policy.
- Spend/quality alerts and audit receipts.
- Governed rollout and rollback.
- Enterprise privacy, identity, residency, and support.

Avoid paywalling basic facts that are already public. Charge for customer-specific evidence and operational control.

## 13. Go-to-market sequence

1. **Public credibility:** publish a small transparent benchmark and useful free explorer.
2. **Design partners:** recruit teams already running multiple coding models or gateways.
3. **Private evaluation:** prove value on real workflows without changing production routing.
4. **Recommendation integration:** deliver the same published/private Switch Decision Card through an API, SDK, PR receipt, IDE, or existing gateway.
5. **Controlled deployment:** add shadow traffic and canaries.
6. **Enterprise expansion:** sell governance only after the core outcome economics are trusted.

Initial ideal customers:

- AI-native development teams with meaningful model spend.
- Platform teams operating multiple providers or agent frameworks.
- Engineering leaders unable to connect token spend to verified outcomes.
- FinOps teams that need workload-level evidence rather than aggregate billing charts.

## 14. Business model hypotheses

Validate rather than assume:

- Free public catalog and benchmark explorer.
- Usage- or run-based private evaluation.
- Team subscription for continuous monitoring and receipts.
- Enterprise annual contract for private execution, policy control, governance, and support.
- Sponsored model evaluation only with independence and disclosure.

Pricing figures in earlier planning documents are hypotheses until customer interviews and paid pilots establish willingness to pay.

## 15. Product metrics

### Trust

- Percentage of public results with complete provenance.
- Stale-result detection time.
- Reproduction success rate.
- Fixture contamination incidents.

### Evaluation quality

- Cohort coverage by task segment.
- Confidence and sample sufficiency.
- Hidden/delayed regression rate.
- Infrastructure-failure rate separated from model-failure rate.

### Customer value

- Time to first customer-specific recommendation.
- Quality-adjusted cost reduction.
- Recommendation acceptance and override rates.
- Production rollback rate.
- Net savings after evaluation and integration cost.

### Business

- Design-partner conversion.
- Paid pilot conversion.
- Expansion from evaluation to monitoring/routing.
- Gross margin after provider and compute costs.

## 16. Milestone gates

| Gate | Required evidence | Unlocks |
|---|---|---|
| G0: Hackathon proof | One real end-to-end correlated workflow | Public prototype claim |
| G1: Trusted beta | Multi-provider registry, real cohorts, provenance and refresh | Public measurement product |
| G2: Customer proof | Repeatable private evaluation and paid/design-partner value | Private evaluation business |
| G3: Safe routing | Shadow/canary evidence, policy versions, rollback | Production recommendation/control |
| G4: Enterprise readiness | Tenant isolation, identity, privacy, audit and operational evidence | Enterprise contracts |
| G5: Data advantage | Large consented outcome-labelled corpus with causal policy evaluation | Defensible learning loop |

## 17. Immediate execution order

1. Freeze the Taskmaster story and demonstrated architecture.
2. Add the real Gemini orchestrator call and typed tools.
3. Define the current baseline plus immutable task fingerprints, workflow phase, configurations, run manifests, evidence thresholds, and stop rules.
4. Make task dispatch authenticated, durable, idempotent, and bounded.
5. Run a small adaptive cohort with deterministic tests and actual usage.
6. Prove cheapest-candidate rejection, sequential stopping, and honest abstention.
7. Persist and aggregate under one correlation ID.
8. Add the contained versioned canary, guardrail verification, and automatic rollback test.
9. Connect the public recommendation and Switch Decision Card (`STAY`, `TEST MORE`, or `SWITCH`) to the evidence receipt, replay, “Why not cheapest?” card, and staleness state.
10. Label all fixtures and remove unsupported submission claims.
11. Deploy and retain Google Cloud proof.
12. Build and test the entire path.
13. Only then consider one evidenced Gemma integration and qualifying public content/social bonus.
14. Record, submit, tag, and freeze.

Only after that sequence should Benchpress expand providers, task suites, additional models, proactive features, or enterprise architecture.
