# Authoritative hackathon submission plan

> **Project:** Benchpress
> **Track:** The Taskmaster
> **Status:** Build and submission source of truth
> **Last verified:** 2026-08-29
> **Deadline:** 2026-08-31 17:00 PDT / 2026-09-01 02:00 SAST

## 1. Submission thesis

> **Benchpress autonomously detects AI model, reasoning, capability, and pricing changes; designs the smallest experiment needed to compare them with a team’s current configuration; rejects candidates that fail real workflows; and publishes a verifiable `STAY`, `TEST MORE`, or `SWITCH` decision—with contained canary promotion and rollback before engineering teams risk production quality or spend.**

Short spoken version:

> **Benchpress autonomously tests AI model and reasoning changes before teams adopt them, rejects configurations that fail real workflows, and publishes the safest cost-effective choice with verifiable evidence.**

The hackathon entry proves one narrow version of that thesis. It does not attempt to prove universal provider coverage, production enterprise compliance, a complete autonomous coding platform, or every proactive feature in the long-term roadmap.

The restored decision-time experience adds strength without replacing publication. The autonomous loop produces trustworthy evidence; the public Benchpress web publishes it; and a Switch Decision Card surfaces the relevant published result when a user is deciding whether to adopt a change.

## 2. User and problem

Primary user:

- An engineer, platform lead, or FinOps owner choosing a model and reasoning configuration for an agentic coding workload.

Current friction:

- Provider catalogs and controls change quickly.
- Reasoning controls differ across providers and models.
- Teams choose configurations by intuition or generic leaderboards.
- List price does not reveal cost per successful workflow.
- Higher reasoning settings may add cost and latency without improving a particular task.
- Failed attempts, retries, tools, and worker compute are often excluded from cost comparisons.

Desired outcome:

- Before a production run, the user receives `STAY`, `TEST MORE`, or `SWITCH` against their declared current configuration, with measured cost, quality, latency, sample size, provenance, freshness, limitations, and a published decision receipt.
- A user who is only researching can still browse the complete public catalog, methodology, cohorts, and historical decisions for free.

## 3. Why Taskmaster

The official Taskmaster resources describe an event-driven workflow with autonomous routing: the system watches for a change, determines what must happen, interacts with other systems, and finishes the job without the user directing every step.

Benchpress matches that shape:

```text
change detected
  -> task fingerprinted
  -> adaptive evaluation plan created
  -> budget approved
  -> jobs dispatched
  -> weak configurations stopped early
  -> outcomes and evidence sufficiency verified
  -> reject, abstain, or canary
  -> verify and promote or roll back
  -> evidence receipt and recommendation published
```

The Collaborative Partner track emphasizes stateful adaptive dialogue, which is not the core product. The Fortified Enterprise Fleet emphasizes multi-agent orchestration, discovery, long-term institutional memory, identity, gateways, and enterprise security posture; choosing it would require unjustified scope.

Official sources:

- [Rules](https://allthingsagentichackathon.devpost.com/rules)
- [Track resources](https://allthingsagentichackathon.devpost.com/resources)
- [FAQ](https://allthingsagentichackathon.devpost.com/details/faqs)

## 4. Mandatory requirements

The submission must visibly use:

1. Gemini 3.5 or newer through the Gemini API or Vertex AI.
2. At least one Google agent framework: Google ADK, GenAI SDK, Antigravity SDK, or Genkit.
3. At least one Google Cloud infrastructure service.

Benchpress target implementation:

- **Model:** Gemini 3.5+ for the Evaluation Orchestrator and/or evaluated Gemini configurations.
- **Framework:** Google GenAI SDK or ADK with structured tools.
- **Cloud:** Cloud Run, Cloud Tasks, and BigQuery or Firestore.
- **Proof:** model metadata and usage, Cloud Run revision/logs, Cloud Tasks jobs, persisted records, deployed UI, and a shared correlation ID.

The repository must include reproducible setup instructions and an architecture diagram. The public video must be no longer than four minutes and show unedited proof of action plus visible Google Cloud deployment.

### Optional bonus, only after the core passes

The [official hackathon overview](https://allthingsagentichackathon.devpost.com/) lists three optional bonus paths: publish qualifying public build content, publish a qualifying social post, and successfully integrate an additional Google AI model such as Gemma, Veo, or Lyria. None replaces a mandatory requirement or repairs an incomplete core workflow.

Benchpress's preferred technical bonus is **one genuinely integrated Gemma role** because it can reinforce the product without distorting it:

- Low-cost task-fingerprint/classification before the Gemini orchestrator designs the experiment; or
- A clearly labelled challenger configuration evaluated by the same worker, oracle, ledger, and receipt path.

The bonus is accepted only if its invocation, output, cost, and effect on the workflow are visible in retained evidence. It does not become a second autonomous agent. Veo, Lyria, or unrelated multimodal features are excluded unless a real product need appears after submission readiness.

## 5. Product boundary

### In the judged build

- One Gemini-powered Evaluation Orchestrator.
- One event source: manual trigger, catalog change, price change, or clearly labelled replay.
- The exact current model/configuration or policy version as a mandatory decision baseline.
- Provider/model registry slice sufficient for the demo.
- Native model/thinking configuration enumeration.
- A task fingerprint covering workload, repository, tool, risk, and latency characteristics.
- Workflow phase in the fingerprint: research/planning, specification, execution, review, refinement, or whole workflow.
- Gemini-generated adaptive experiment design rather than an unconditional full matrix.
- Deterministic run-budget calculation.
- Cloud Tasks matrix dispatch.
- Controlled benchmark workers.
- A 3–10 task frozen coding cohort.
- At least two or three real thinking configurations.
- Actual provider usage, cost, latency, and test evidence.
- Sequential early stopping for invalid or clearly dominated configurations.
- A deliberate quality guardrail capable of rejecting the cheapest candidate.
- An explicit abstention path when evidence is insufficient.
- Persisted run and aggregate records.
- A versioned, contained demo-canary policy lifecycle with promotion and automatic rollback.
- Public model/configuration recommendation page, evidence receipt, and decision replay.
- A Switch Decision Card that expresses the published policy outcome as `STAY`, `TEST MORE`, or `SWITCH`.
- Automatic staleness when a model alias, price, tool schema, task suite, harness, or delayed regression changes.
- Provenance and fixture labels.
- Hard spend, turn, retry, timeout, and concurrency boundaries.

### Reused prototype surfaces

- Existing Next.js UI, charts, model pages, compare experience, trajectory views, types, SDK shapes, worker service, FSM concepts, safeguards, tests, and Terraform.
- These components may be shown only to the degree connected to the demonstrated path.

### Outside the judged build

- Universal coverage of all models and providers.
- Cross-provider production routing.
- Automatic IDE, gateway, or production-traffic policy deployment. The judged canary is confined to a contained demo route.
- Full multi-model planner/executor/reviewer choreography. Phase-aware route policies remain the immediate extension after the single-configuration loop is proven.
- Predictive outage detection.
- Automatic destructive Git rollback.
- Unproven context pruning or caching guarantees.
- Cross-developer semantic result reuse.
- Autonomous dependency license decisions.
- Trajectory distillation for customer data.
- Multimodal voice/vision unless genuinely connected and stable.
- Enterprise appliance, formal compliance, and long-term institutional memory.
- A peer-agent swarm.

## 6. Agent decision

Use **one autonomous Gemini Evaluation Orchestrator with many parallel controlled workers**.

The orchestrator:

- Interprets the change.
- Uses the task fingerprint to choose a bounded, discriminating evaluation cohort.
- Calls typed tools.
- Monitors completion.
- Decides whether the deterministic evidence permits rejection, abstention, or a contained canary.
- Explains the result and publishes a replayable receipt.

Deterministic services:

- Validate supported configurations.
- Calculate costs and budgets.
- Enforce idempotency and policy.
- Execute tests.
- Calculate metrics, confidence, and Pareto membership.

Workers execute one immutable manifest each. They are not independent agents and cannot publish or alter global policy.

See [Evaluation orchestrator and worker topology](../architecture/06-agent-orchestration-and-swarm-topology.md).

## 7. End-to-end judged workflow

### Step 1: Receive a change event

Input includes:

- Source snapshot or explicit evaluation request.
- Exact target model or family.
- Exact current model/configuration or active policy version.
- Task category and repository segment.
- Workflow phase or `whole_workflow`.
- Maximum spend and time.

For a replayed external event, the UI and video must say **REPLAY EVENT**. The resulting Gemini planning, Cloud Tasks execution, provider calls, persistence, and publication must still be real.

### Step 2: Fingerprint the task and create an adaptive proposal

The orchestrator calls typed tools to:

- Inspect the change.
- List supported native configurations.
- Build a task fingerprint: language/framework, task type, workflow phase, repository and context size, input/output intensity, required tools, risk, and latency sensitivity.
- Select the configurations and tasks most likely to distinguish meaningful tradeoffs.
- Include the current configuration as the baseline, or reuse only fresh, compatible baseline evidence with an explicit provenance link.
- Produce an evaluation plan, maximum spend, stopping rules, and rationale.

The agent cannot claim results at this stage.

Illustrative plan copy—never a measured claim—is:

> Six configurations are supported. Testing all of them could cost up to $1.42. Benchpress selected four configurations and three discriminating tasks, with a maximum approved spend of $0.48.

### Step 3: Deterministic policy approves the plan

Validation checks:

- Model and configuration exist.
- Native parameters are supported.
- Task and harness versions are frozen.
- Estimated worst-case spend is below the budget.
- Concurrency and rate limits are within policy.
- Logical run keys do not already exist.
- Stop rules and evidence thresholds are declared before dispatch.

### Step 4: Dispatch parallel workers

Cloud Tasks receives one job per configuration, task, and repetition. Each job carries a correlation ID and immutable run manifest. Authentication, retries, and idempotency are enforced.

### Step 5: Execute, verify, and stop safely

Each worker:

- Invokes the declared model/configuration.
- Uses only approved tools and workspace paths.
- Runs deterministic tests.
- Records actual usage and latency.
- Persists pass/fail and failure taxonomy.
- Includes all failed attempts in economics.

After each eligible result, deterministic policy may:

- Reject a configuration after repeated invalid tool calls or a declared safety/quality failure.
- Stop a dominated configuration when it cannot beat the baseline under the remaining budget.
- Stop buying evidence once the confidence threshold is reached.
- Halt undispatched work at the fixed matrix budget.

The cheapest candidate must not win merely because it is cheap. A planned demo branch should show a low-thinking configuration failing a security or correctness boundary and being marked `REJECT`, while a more capable configuration remains eligible. Final numbers must come from retained runs.

### Step 6: Aggregate and determine evidence sufficiency

Deterministic aggregation produces:

- Resolution rate.
- Cost per verified resolution.
- P50/P95 latency when sample size permits.
- Token and reasoning usage.
- Tool failure distribution.
- Sample count, confidence, and exclusions.
- Pareto membership under declared constraints.

If the sample is too small, results are statistically tied, the tasks are unrepresentative, provider responses are incomplete, infrastructure failures are excessive, or the model/price changes during the run, the system publishes `ABSTAIN` with the reason. It must not force a winner.

### Step 7: Create a versioned candidate policy

The policy lifecycle is:

```text
CHANGE_DETECTED
  -> EXPERIMENTAL
  -> EVALUATING
  -> REJECT | ABSTAIN | CANARY
  -> VERIFY
  -> ROLLBACK | RECOMMENDED
```

Only a complete, current, sufficient aggregate can reach `CANARY`. The policy record includes the previous baseline and an immutable candidate version.

### Step 8: Verify a contained canary and promote or roll back

The candidate handles one contained demo task or a fixed demo traffic slice. Deterministic quality, cost, latency, and infrastructure guardrails compare it with the baseline:

- Passing canary: promote the candidate recommendation version.
- Failing or incomplete canary: automatically restore the prior version and record `ROLLBACK`.

This is evidence of a safe policy lifecycle, not authorization to change customer production traffic.

### Step 9: Publish the receipt, replay, and switch decision

The orchestrator explains the evidence in plain language. The publisher writes a versioned decision receipt and, when permitted, a recommendation such as:

> For the measured Python bug-fix cohort, configuration A is the current cost-constrained recommendation. It resolved X of Y eligible runs at observed CPR Z. Configuration B achieved higher/lower quality at a different cost/latency tradeoff. These results apply only to cohort and harness version N.

Use actual values only after the run completes.

The receipt must retain policy version, trigger, task fingerprint, baseline, candidate, selected tasks/configurations, eligible runs, failures, verified successes, total experiment cost, observed CPR, uncertainty, decision, approval boundary, and canary/rollback outcome. A replay timeline lets a judge reconstruct every state transition without exposing hidden chain-of-thought.

Every terminal outcome is published:

| Internal evidence/policy outcome | User-facing decision | Meaning |
|---|---|---|
| Candidate rejected, dominated, or rolled back; current baseline remains eligible | `STAY` | Keep the current configuration and show why the candidate lost |
| Evidence insufficient, tied, stale, or incompatible | `TEST MORE` | Do not switch; publish the missing evidence and bounded next experiment |
| Candidate passes evidence thresholds and the contained canary | `SWITCH` | Publish the eligible candidate and its safe adoption receipt |

The Switch Decision Card is one delivery surface for this published record. The free public model/configuration page, aggregate export, and historical replay remain part of the core product.

## 8. Data shown on the public page

### Official specification panel

- Provider and exact model ID.
- Lifecycle status.
- Context/output limits.
- Supported tools/modalities.
- Native reasoning controls.
- Current price and effective/retrieval date.
- Official source link.

### Benchpress measured panel

- Exact native configuration.
- Task category and cohort version.
- Sample count and repetitions.
- Resolution rate and outcome evidence.
- Total cost and CPR.
- Median/tail latency where justified.
- Evaluation date and harness version.
- Confidence, exclusions, and limitations.
- Current policy state and version.
- Staleness causes and superseding evidence, when applicable.

### Decision explanation panel

- The headline decision: `STAY`, `TEST MORE`, or `SWITCH`.
- Current baseline and candidate, including exact native settings and policy versions.
- Task and workflow-phase match.
- A **Why not cheapest?** card naming the failed test or risk boundary and the observed price difference.
- Observed counterfactual cost: recommended route versus the cheapest failed route and a higher-reasoning route, using actual recorded costs only.
- “Why this decision?” and “What would reverse it?” explanations.
- An evidence receipt with baseline, candidate, decision, approval boundary, and canary result.
- A replayable timeline from change detection through promotion, rollback, rejection, or abstention.

### Required badges

- Official specification
- Benchpress measured
- Community verified
- Experimental
- Stale
- Demo fixture

Fixture and measured data must never share an indistinguishable visual treatment.

## 9. Build-now backlog

### P0: eligibility and proof

1. Add a genuine Gemini 3.5+ structured-tool call to the worker or dedicated orchestrator.
2. Replace the hard-coded judged tool sequence with Gemini decisions for the selected workflow.
3. Record provider model metadata, request ID when available, and actual usage.
4. Create the bounded configuration/run manifest schema.
5. Dispatch idempotent authenticated Cloud Tasks jobs.
6. Persist run states, usage, tests, cost, and result under one correlation ID.
7. Aggregate at least one real cohort.
8. Make the current configuration a mandatory baseline and include workflow phase in its task fingerprint.
9. Implement adaptive cohort selection and deterministic sequential stopping.
10. Demonstrate a cheap configuration rejected by a correctness or safety guardrail.
11. Implement evidence sufficiency and an explicit abstention outcome.
12. Implement a contained canary policy, promotion, and tested rollback to the previous version.
13. Publish `STAY`, `TEST MORE`, or `SWITCH` through the recommendation, Switch Decision Card, evidence receipt, and replay page.
14. Implement staleness invalidation for the declared change types.
15. Deploy the web and worker path to Google Cloud.
16. Capture Cloud Run, Cloud Tasks, data-store, and model-call proof.
17. Label every remaining synthetic metric and simulator state.
18. Ensure the root README reproduces the demonstrated path.

### P1: reliability

1. Reject missing/invalid worker authentication outside mock mode.
2. Fix asynchronous acknowledgment so accepted work has durable ownership.
3. Enforce unique logical run keys.
4. Add negative tests for duplicate delivery, invalid configuration, budget exhaustion, timeout, and malformed tool calls.
5. Consolidate the Terraform source of truth.
6. Make CORS and credential scope explicit.
7. Add a terminal partial-failure state and prevent incomplete promotion.
8. Verify fixture data cannot enter measured aggregates.
9. Verify early stopping cannot hide incurred cost or bias the eligible denominator.
10. Test reject, abstain, canary promotion, stale-policy, and automatic rollback paths.

### P2: presentation

1. Export a readable architecture diagram with demonstrated services solid and roadmap services dashed.
2. Prepare the four-minute video from the final deployed build.
3. Capture a raw run manifest and aggregate for repository evidence.
4. Finalize the Devpost narrative with only demonstrated claims.
5. Tag/freeze the submission commit and preserve deployment evidence.
6. If and only if P0 and P1 are complete, add one justified, evidenced Gemma integration and/or qualifying public content/social bonus.

## 10. Definition of done

The submission is ready only when all are true:

- A judge can identify the user problem in one sentence.
- The selected track is Taskmaster and only one track is claimed.
- Gemini 3.5+ makes a genuine bounded agent decision.
- An allowed Google agent framework is visible in code and dependency metadata.
- At least one Google Cloud service is deployed and shown; target path uses Cloud Run and Cloud Tasks.
- Multiple configurations execute through real provider calls.
- The user's current configuration is the explicit baseline or is represented by demonstrably fresh, compatible retained evidence.
- Gemini chooses a smaller discriminating experiment from the supported domain and explains why.
- Tests provide deterministic outcome evidence.
- Actual usage and latency are stored.
- At least one cheapest-but-failing configuration is rejected by a declared guardrail.
- Sequential stopping preserves all incurred usage and its decision rationale.
- Insufficient evidence results in `ABSTAIN`, not a fabricated winner.
- A versioned contained canary is either promoted or automatically rolled back under deterministic guardrails.
- The same correlation ID is visible across the workflow.
- The public result, evidence receipt, and replay timeline update from stored records.
- Every terminal path publishes exactly one user-facing decision: `STAY`, `TEST MORE`, or `SWITCH`.
- Stale evidence cannot remain the current recommendation silently.
- Synthetic data is unmistakably labelled.
- README setup steps work from a clean environment or limitations are explicit.
- The video is under four minutes and contains unedited action.
- The architecture diagram matches the deployed path.
- No unsupported exact performance or compliance claims remain in submission-facing material.

## 11. Four-minute narrative

The submission story is deliberately singular:

1. Teams guess model and reasoning settings.
2. Benchpress receives a relevant change.
3. Gemini determines the bounded evaluation plan.
4. Deterministic policy approves the cost and stopping rules.
5. Cloud Tasks performs parallel real evaluations and stops wasteful branches.
6. A cheap but unsafe/incorrect option is rejected; insufficient evidence can cause abstention.
7. A contained canary is promoted or rolled back under guardrails.
8. Benchpress publishes a replayable evidence receipt and a `STAY`, `TEST MORE`, or `SWITCH` recommendation.
9. The same pipeline becomes the startup's multi-provider intelligence layer.

See [demo video script](./02-demo-video-script.md).

## 12. Evidence package

Retain:

- Submission commit hash and repository URL.
- Deployed Cloud Run revisions/URLs.
- Cloud Tasks queue/job screenshot or recording.
- Model/API request metadata and usage.
- Persisted run and aggregate records.
- Policy versions, canary comparison, and rollback evidence.
- Evidence receipt and decision replay record.
- Correlation-ID trace.
- Test output.
- Architecture image.
- Exact demo input/event.
- Public recommendation URL.
- Known limitations.
- Disclosure of incorporated pre-existing work.

## 13. Claim language

Preferred:

- “Benchpress measured…”
- “In this frozen cohort…”
- “The current cost-constrained recommendation is…”
- “Benchpress published `STAY`, `TEST MORE`, or `SWITCH` against the declared current baseline.”
- “This result includes failed attempts…”
- “This value is observed/projected/illustrative…”
- “The architecture is designed to expand to…”
- “This component is a prototype/roadmap item…”

Avoid:

- “Unbeatable,” “flawless,” “zero loss,” “100% compliant,” or “industry first” without proof.
- Exact savings derived from fixture data.
- Projected annual savings presented without observed inputs, volume, horizon, price version, evaluation/switching costs, and uncertainty.
- “Production-grade” based only on Terraform or tests.
- “Swarm” when the system is one orchestrator plus jobs.
- “All models” when only a declared subset is evaluated.
- “Production auto-routing” when only the contained demo canary was exercised.
- A forced winner when the evidence policy returned `ABSTAIN`.

## 14. Relationship to the startup

The hackathon build is not throwaway code. It establishes the durable core:

- Versioned model registry.
- Provider-native configuration schema.
- Immutable run ledger.
- Deterministic evaluation harness.
- Cost/outcome aggregation.
- Adaptive experiment design and sequential stopping.
- Versioned decision receipts and policy lifecycle.
- Public discovery and recommendation surface.
- Bounded orchestration and policy controls.

Post-hackathon work broadens provider coverage, task depth, private customer evaluation, routing integration, and enterprise governance only after the core pipeline is reliable.
