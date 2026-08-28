# Four-minute hackathon demo script

> **Status:** Recording plan; adapt timestamps to the final deployed build
> **Maximum duration:** 4:00
> **Target duration:** 3:45–3:55
> **Rule:** Every claim must be visible or linked to retained evidence.

## Recording principles

- Prefer one continuous recording of the core workflow.
- Keep the correlation ID visible whenever practical.
- Show real model metadata, Cloud Tasks activity, persisted state, and tests.
- Clearly label any replayed source event as `REPLAY EVENT`.
- Clearly label fixture-backed pages as `DEMO FIXTURE`.
- Do not spend time on roadmap UI until the real result is proven.
- Show the Cloud Console, Cloud Run revision/URL, or logs required to prove deployment.
- Make one controlled failure visible; rejection, abstention, or rollback is evidence of safe autonomy.
- Show an additional Google AI model only if it is genuinely integrated and the core story still fits.

## Storyboard

### 0:00–0:20 — The decision problem

**Visual**

- Open the Benchpress model/configuration explorer.
- Show that the same model can have multiple reasoning configurations.
- Highlight source, freshness, and measured/fixture badges.

**Narration**

> The cheapest model setting is not cheapest if it fails the task, and the most expensive setting is wasteful if extra reasoning adds no value. Benchpress tests a proposed change against the team’s current configuration and publishes whether to stay, test more, or switch before production quality or spend is at risk.

### 0:20–0:48 — Change, fingerprint, and adaptive plan

**Visual**

- Trigger a real or clearly labelled replayed model/configuration change.
- Show the generated correlation ID.
- Show the exact current model/reasoning configuration as the baseline.
- Show the Gemini Evaluation Orchestrator inspecting the change and invoking typed tools.
- Show the task fingerprint—including workflow phase—and the supported domain versus the smaller selected experiment.

**Narration**

> A model, capability, or price change triggers one bounded Gemini orchestrator. It fingerprints this workload and phase, keeps the current configuration as the decision baseline, and chooses the alternatives and tasks most likely to distinguish the tradeoff instead of blindly running every combination.

### 0:48–1:08 — Deterministic approval

**Visual**

- Show the exact configurations, tasks, maximum spend, evidence thresholds, stopping rules, turn/time ceilings, and idempotency key.
- Show an approved decision from deterministic policy.

**Narration**

> Gemini designs the experiment; deterministic policy controls the money, evidence threshold, and stopping boundaries. Unsupported parameters, duplicates, or an over-budget plan fail closed.

### 1:08–1:55 — Unedited parallel execution

**Visual**

- Open Cloud Tasks and Cloud Run logs.
- Show multiple configuration/task jobs executing.
- Show the same correlation ID.
- Show exact provider model/configuration metadata and actual usage.

**Narration**

> Cloud Tasks fans the approved matrix into parallel, idempotent worker jobs. These are controlled executions, not an agent swarm. Each worker runs one immutable manifest, records actual provider usage and latency, and cannot alter the global recommendation.

### 1:55–2:25 — “Why not cheapest?” and early stopping

**Visual**

- Show test commands and pass/fail evidence.
- Show failed attempts retained rather than hidden.
- Show persisted run records.
- Show the low-cost candidate fail a declared security/correctness boundary and receive `REJECT`.
- Show a dominated/invalid branch stop, or show the fixed-budget completion decision.

**Narration**

> Every result is checked by deterministic tests. This low-thinking candidate is cheapest per request, but it failed the frozen boundary, so Benchpress rejects it. The failure and its cost stay in the ledger. A predeclared stopping rule cancels only future waste; it never erases evidence.

### 2:25–2:55 — Decide, canary, and protect the baseline

**Visual**

- Show aggregation return `REJECT`, `ABSTAIN`, or `CANARY` internally and its public `STAY`, `TEST MORE`, or `SWITCH` meaning.
- Show the immutable baseline and candidate policy versions.
- Route one contained demo task through the candidate.
- Show promotion on pass; separately retain a test/log/replay proving automatic rollback on guardrail failure.

**Narration**

> Benchpress publishes `TEST MORE` when the evidence is not strong enough and `STAY` when the candidate loses or rolls back. Here, the eligible candidate enters a contained canary. Passing guardrails produces `SWITCH`; failure atomically restores the previous version. This demo never changes customer production traffic.

### 2:55–3:22 — Receipt, replay, and public result

**Visual**

- Refresh/open the public recommendation page.
- Highlight the Switch Decision Card: current baseline, candidate, `STAY`/`TEST MORE`/`SWITCH`, workflow-phase match, “why,” “what would reverse it,” and limitations.
- Highlight the “Why not cheapest?” evidence and observed counterfactual costs. Any volume forecast must carry a `PROJECTED` label and its assumptions.
- Open the evidence receipt and scrub the decision replay from change through policy outcome.

**Narration**

> The public result is not just a score or a hidden routing action. Benchpress publishes the decision for free with the baseline, evidence, failures, total experiment cost, uncertainty, approval boundary, policy version, and canary outcome. The same record can later appear in an IDE or gateway exactly when a switch is considered.

### 3:22–3:43 — Architecture and Google Cloud proof

**Visual**

- Show the architecture diagram.
- Briefly show Cloud Run revision, Cloud Tasks queue, data store, Gemini/SDK evidence, and the same correlation ID.

**Narration**

> The architecture is deliberately disciplined: one Gemini orchestrator, typed tools, Cloud Tasks workers, deterministic tests and policy, and an immutable evidence ledger. One correlation ID connects the event, cloud execution, decision, and public receipt.

### 3:43–3:55 — Startup path and optional bonus

**Visual**

- End on the public Benchpress explorer.
- If genuinely integrated, show a small Gemma badge/evidence link without leaving the core path.

**Narration**

> The same evidence loop expands after the hackathon into multi-provider public intelligence, private evaluations, and governed routing. Benchpress helps teams measure first, reject unsafe savings, and spend with evidence.

## Required captured evidence

- `[PUBLIC APP URL]`
- `[CLOUD RUN REVISION/URL]`
- `[CLOUD TASKS QUEUE AND JOB IDS]`
- `[GEMINI MODEL ID AND USAGE]`
- `[CORRELATION ID]`
- `[PERSISTED RUN/AGGREGATE RECORD]`
- `[TEST OUTPUT]`
- `[PUBLIC RECOMMENDATION URL]`
- `[SWITCH DECISION: STAY / TEST MORE / SWITCH]`
- `[POLICY VERSION, CANARY RESULT, AND ROLLBACK TEST/REPLAY]`
- `[EVIDENCE RECEIPT AND DECISION REPLAY URL]`
- `[OPTIONAL GEMMA MODEL/USAGE/WORKFLOW EFFECT, IF CLAIMED]`
- `[SUBMISSION COMMIT]`

## Remove from the old video story

Unless independently implemented and demonstrated, do not show or narrate:

- Sub-200ms voice claims.
- Automatic AST wrapper injection.
- Markov prediction percentages.
- Automatic crash-to-PR.
- gVisor or confidential-computing claims.
- Exact hybrid savings percentages.
- Enterprise compliance certification.
- A swarm of autonomous agents.
