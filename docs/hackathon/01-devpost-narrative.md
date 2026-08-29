# Devpost submission narrative

> **Status:** Submission draft; replace bracketed evidence only with final demonstrated values
> **Track:** The Taskmaster

## Project title

**Benchpress**

## Tagline

**Autonomous model-change evaluation that publishes `STAY`, `TEST MORE`, or `SWITCH` before production quality or spend is at risk.**

## Inspiration

Engineering teams can choose among many AI models, service tiers, and reasoning settings, but provider catalogs do not answer the operational question that matters: which exact configuration is the best quality, cost, and latency tradeoff for this workload?

List prices and generic leaderboards are insufficient for agentic coding. A workflow may require multiple turns, tool calls, retries, test execution, and recovery from failures. The cheapest successful-looking request can become the most expensive verified resolution once failed attempts are included.

We built Benchpress to turn that guesswork into a bounded, repeatable background workflow.

## What it does

Benchpress detects or receives a relevant model, reasoning, capability, or pricing change. A Gemini-powered Evaluation Orchestrator fingerprints the target workload—including workflow phase—compares alternatives with the team’s exact current configuration, designs the smallest useful discriminating experiment, and submits its spend and stopping rules to deterministic policy.

Once approved, Benchpress dispatches parallel benchmark jobs through Google Cloud Tasks. Each worker invokes an exact model and native reasoning configuration, runs the same versioned coding task and tools, verifies the outcome with deterministic tests, and records actual usage, latency, failures, and cost.

Benchpress evaluates evidence as it arrives, stops invalid or clearly dominated branches, and preserves every incurred attempt in the economics. It can reject the cheapest option when it fails a quality or safety boundary, or abstain when the evidence cannot support a change.

An eligible candidate enters a versioned, contained canary. Deterministic quality, cost, latency, and failure guardrails promote it or automatically restore the previous version. Benchpress then publishes a replayable evidence receipt and one clear decision:

- `STAY` when the current baseline remains the safest eligible policy.
- `TEST MORE` when the evidence is insufficient, tied, stale, or incompatible.
- `SWITCH` when the candidate passes both evaluation and canary guardrails.

The published record shows the exact current and candidate configurations, task and workflow-phase match, sample count, harness version, evaluation date, provenance, decision boundary, limitations, “why,” and what would reverse the decision.

The catalog, aggregate explorer, methodology, and historical receipts remain free to browse. Decision cards and future IDE, SDK, or gateway integrations bring that same published evidence into the moment a team considers a switch. The long-term startup product adds private customer evaluations, continuous regression monitoring, routing APIs, team economics, and governed policy deployment.

## Autonomous workflow

Benchpress uses one autonomous Gemini Evaluation Orchestrator and many controlled workers:

1. Receive a catalog, price, or explicit evaluation event.
2. Use typed tools to inspect supported model configurations.
3. Fingerprint the workload and workflow phase; declare the exact current configuration as baseline.
4. Obtain deterministic budget, evidence-threshold, and stopping-rule approval.
5. Dispatch idempotent Cloud Tasks jobs.
6. Execute provider-backed evaluations, deterministic tests, and sequential stopping.
7. Persist usage, cost, latency, failures, stop reasons, and outcomes under one correlation ID.
8. Calculate versioned aggregates and return reject, abstain, or canary eligibility.
9. Verify the contained canary and promote or automatically roll back.
10. Publish an evidence receipt, decision replay, and `STAY`, `TEST MORE`, or `SWITCH` recommendation.

The workers are parallel execution jobs, not an uncontrolled agent swarm. Arithmetic, scoring, budgets, and promotion policy remain deterministic.

For this submission, candidates are exact single-model/reasoning configurations. Phase-aware planner/executor/reviewer policies are a direct extension of the same evidence loop, not a claim about the judged build.

## Google technology

- **Gemini 3.5 or newer:** bounded orchestration and structured tool selection; exact demonstrated model: `[MODEL_ID]`.
- **Google agent framework:** `[Google GenAI SDK or ADK]`.
- **Cloud Run:** hosts `[web/worker]` at revision `[REVISION]`.
- **Cloud Tasks:** dispatches configuration/task jobs with bounded concurrency and retries.
- **BigQuery or Firestore:** stores `[run ledger/aggregate state]`.
- **Correlation ID:** `[ID]` connects the event, agent, jobs, usage, tests, aggregate, and public result.

Optional bonus, include only when genuinely implemented and evidenced:

- **Gemma:** `[EXACT MODEL AND JUSTIFIED ROLE—TASK FINGERPRINT OR CHALLENGER]`; invocation, usage/cost, output, and workflow effect: `[EVIDENCE]`.

## What is measured

For the submitted cohort:

- Task category: `[CATEGORY]`
- Task count: `[COUNT]`
- Configurations: `[EXACT NATIVE CONFIGURATIONS]`
- Repetitions: `[COUNT]`
- Harness version: `[VERSION/HASH]`
- Evaluation timestamp: `[TIMESTAMP]`
- Result URL: `[URL]`

Insert final measured results here only after completing and retaining the corresponding run manifests.

## Challenges

The hardest parts were not drawing a leaderboard or calling a model. They were preserving comparability and trust:

- Normalizing provider metadata without pretending native reasoning controls are equivalent.
- Preventing duplicate jobs and double-counted cost under at-least-once delivery.
- Distinguishing infrastructure retries from model failures.
- Including failed attempts in cost per verified resolution.
- Separating official specifications, measured results, experiments, stale results, and UI fixtures.
- Keeping the model inside clear budget, tool, workspace, and publication boundaries.
- Designing early-stop rules that save future spend without hiding failures or biasing the denominator.
- Treating abstention and rollback as successful safety outcomes rather than forcing a recommendation.

## Accomplishments

Use only accomplishments visible in the final repository and video:

- `[REAL GEMINI ORCHESTRATION EVIDENCE]`
- `[REAL CLOUD TASKS EXECUTION EVIDENCE]`
- `[REAL PERSISTED RUN/AGGREGATE EVIDENCE]`
- `[REAL PUBLIC RESULT UPDATE]`
- `[REPRODUCIBILITY OR SECURITY EVIDENCE]`

## What we learned

The main lesson is that model selection is an empirical policy lifecycle, not a one-time leaderboard lookup. The right answer depends on task shape, native reasoning controls, tools, prompt and harness version, budget, latency tolerance, evidence sufficiency, and the definition of a verified outcome.

We also learned that autonomy is strongest when authority is explicit: Gemini decides which bounded experiment to run, while deterministic services enforce money, stopping, scoring, idempotency, promotion, and rollback.

## What is next

After the hackathon, Benchpress will:

1. Expand the official registry across Google, OpenAI, Anthropic, and additional providers.
2. Grow contamination-resistant coding cohorts and private customer evaluations.
3. Add confidence-aware continuous refresh when models, prices, or harnesses change.
4. Offer routing APIs and SDK integrations backed by measured customer outcomes.
5. Add governed policy rollout, monitoring, and rollback.
6. Build enterprise privacy, identity, data residency, and audit controls.

These are roadmap commitments, not claims about the submitted build.

## Disclosure and limitations

- Static model profiles and the legacy harvester contain demo fixtures unless explicitly marked Benchpress measured.
- `[LIST ANY REPLAYED OR SIMULATED EXTERNAL DEPENDENCIES]`.
- `[LIST PRE-EXISTING WORK INCORPORATED AND DEVELOPMENT-PERIOD DISCLOSURE]`.
- The submitted benchmark is intentionally small and demonstrates the pipeline rather than universal model superiority.
