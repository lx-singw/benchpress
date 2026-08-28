# Final hackathon submission checklist

> **Status:** Release gate
> **Track:** The Taskmaster
> **Deadline:** 2026-08-31 17:00 PDT / 2026-09-01 02:00 SAST

## 1. Eligibility and account

- [ ] The project is registered on Devpost.
- [ ] All team members are added and have accepted invitations.
- [ ] One representative is designated.
- [ ] The submission selects exactly one core track: **The Taskmaster**.
- [ ] Any pre-existing incorporated work is disclosed accurately.
- [ ] Startup Excellence is selected only if submitting for an incorporated organization with a corporate email.
- [ ] Repository and submission assets will remain unchanged during the judging window unless the rules permit an update.

## 2. Mandatory technology

- [ ] A genuine Gemini 3.5-or-newer request is part of the judged workflow.
- [ ] The exact Gemini model ID is captured.
- [ ] Google GenAI SDK, ADK, Antigravity SDK, or Genkit is genuinely used.
- [ ] At least one Google Cloud service is genuinely used.
- [ ] Cloud Run deployment is visible in the video.
- [ ] Cloud Tasks or the selected asynchronous infrastructure is visible in the video.
- [ ] Model usage and cloud logs can be correlated to the same run.

## 3. Core workflow

- [ ] A real or clearly labelled replay event triggers the workflow.
- [ ] The Gemini orchestrator uses typed tools to create a bounded plan.
- [ ] The exact current model/configuration or active policy version is the declared baseline.
- [ ] A versioned task fingerprint—including workflow phase—drives experiment selection.
- [ ] The selected experiment is smaller or more discriminating than an unconditional full matrix, with rationale.
- [ ] Native model/reasoning configurations are shown exactly.
- [ ] Deterministic policy approves or rejects the plan, budget, thresholds, and stopping rules.
- [ ] Every job has a logical run key and correlation ID.
- [ ] Duplicate delivery is handled idempotently.
- [ ] At least two or three configurations run.
- [ ] Deterministic tests produce outcome evidence.
- [ ] Failed attempts remain in the result and cost accounting.
- [ ] A cheapest-but-failing candidate is visibly rejected by a frozen quality or safety boundary.
- [ ] Sequential stopping cancels only future work and preserves all incurred evidence and cost.
- [ ] Actual provider usage and latency are stored.
- [ ] Aggregation is versioned.
- [ ] Insufficient, tied, stale, or overly failure-prone evidence returns `ABSTAIN` with a reason.
- [ ] The candidate and baseline are immutable policy versions.
- [ ] A contained canary is promoted on pass or automatically rolled back on failure.
- [ ] Every terminal outcome publishes exactly one decision: `STAY`, `TEST MORE`, or `SWITCH`.
- [ ] The public recommendation, Switch Decision Card, evidence receipt, and decision replay update from stored records.
- [ ] Incomplete cohorts cannot overwrite a valid recommendation.

## 4. Safety and reliability

- [ ] Worker authentication is required outside local mock mode.
- [ ] Invalid or missing authentication has a tested failure path.
- [ ] Per-run and matrix spend limits are enforced by code.
- [ ] Turn, timeout, retry, and concurrency ceilings are enforced.
- [ ] Unsupported provider parameters are rejected, not silently substituted.
- [ ] Worker tools and workspace paths are allowlisted.
- [ ] No destructive Git command is executed automatically.
- [ ] External writes and package installation are outside scope or separately authorized.
- [ ] Provider 429/5xx handling is bounded.
- [ ] Model failure is not misclassified as an infrastructure retry.
- [ ] Stop, rejection, and abstention thresholds are versioned before execution.
- [ ] Canary authority is limited to a contained demo route and cannot alter customer production traffic.
- [ ] Automatic rollback restores the exact prior policy version and is tested.
- [ ] Secrets are absent from repository, logs, video, and public records.

## 5. Data integrity and provenance

- [ ] Official provider facts include source URLs and retrieval/effective dates.
- [ ] Every measured run stores exact native configuration.
- [ ] Task, repository, prompt, tool-schema, and harness versions are retained.
- [ ] Test commands and exit codes are retained.
- [ ] Usage, tool costs, and in-scope compute costs are accounted for.
- [ ] Sample count, exclusions, and limitations appear publicly.
- [ ] Demo fixtures cannot enter measured aggregates.
- [ ] Fixture pages display a persistent `DEMO FIXTURE` badge.
- [ ] Stale or experimental results cannot be presented as current defaults.
- [ ] Alias, price, tool-schema, task-suite, harness, oracle, and delayed-regression changes can mark evidence stale.
- [ ] The receipt contains trigger, fingerprint, baseline, candidate, selected cohort, eligible runs, failures, verified successes, total cost, CPR, uncertainty, decision, approval boundary, and canary outcome.
- [ ] The “Why not cheapest?” card links the rejection to actual test/risk evidence.
- [ ] Counterfactual costs use only actual compatible runs.
- [ ] Every financial value is visibly labelled `OBSERVED`, `PROJECTED`, or `ILLUSTRATIVE` where appropriate.
- [ ] Projections show volume, time horizon, price version, evaluation cost, switching assumptions, and uncertainty.
- [ ] The Switch Decision Card shows “why this decision?” and “what would reverse it?”

## 6. Repository readiness

- [ ] Root README describes the demonstrated product truthfully.
- [ ] Local setup steps work or known limitations are explicit.
- [ ] Architecture diagram matches the deployed path.
- [ ] Demonstrated services are solid; roadmap services are dashed/grey.
- [ ] Primary Terraform source is identified.
- [ ] Build succeeds from a clean install.
- [ ] Relevant Python and TypeScript tests pass.
- [ ] No unsupported exact performance claims remain in submission-facing documents.
- [ ] A submission commit/tag is created and recorded.

## 7. Video

- [ ] Duration is under four minutes.
- [ ] The problem and value proposition are clear within 25 seconds.
- [ ] The agent takes visible action beyond returning text.
- [ ] The core workflow is shown unedited.
- [ ] Gemini model/framework evidence is visible.
- [ ] Google Cloud deployment evidence is visible.
- [ ] Correlation ID connects the workflow.
- [ ] Test results and persisted data are visible.
- [ ] The public recommendation update is visible.
- [ ] The current-versus-candidate Switch Decision Card is visible.
- [ ] One controlled failure is visible: rejection, abstention, or rollback.
- [ ] The evidence receipt and decision replay are readable.
- [ ] Replay and fixture states are labelled.
- [ ] Captions are readable at standard playback size.
- [ ] No credentials, tenant data, or private prompts are exposed.
- [ ] Video is public on YouTube or Vimeo as required.

## 8. Devpost fields

- [ ] Project title: `Benchpress`.
- [ ] Tagline matches the final narrative.
- [ ] Track: `The Taskmaster`.
- [ ] Problem, workflow, Google technology, challenges, accomplishments, learning, and next steps are complete.
- [ ] Repository URL is public and correct.
- [ ] Video URL is public and correct.
- [ ] Architecture image is attached or linked.
- [ ] Setup instructions are linked.
- [ ] Pre-existing work and limitations are disclosed.
- [ ] Optional content/social contributions meet the exact rules before being claimed.

## 9. Optional bonus gate

Do not begin a bonus integration until every P0 core-workflow and mandatory-technology item is complete.

### Additional Google AI model

- [ ] The chosen additional model has a justified product role; preferred: Gemma for task fingerprinting or as a measured challenger.
- [ ] The exact model ID, invocation, output, usage/cost, and effect on the core workflow are retained.
- [ ] The model is genuinely integrated into the judged path, not shown as an unused dependency or decorative API call.
- [ ] It remains a model/tool role under the one-orchestrator architecture, not an unnecessary second agent.
- [ ] Veo, Lyria, or multimodal UX is omitted unless it materially improves the core decision workflow.

### Public content and social

- [ ] Any bonus build article, podcast, or video is public and includes the hackathon-purpose disclosure required by the official overview.
- [ ] Any qualifying social post is public, highlights Benchpress, and includes `#AllThingsAgenticHackathon` where required.
- [ ] URLs and screenshots are retained before submission.

## 10. Evidence record

Complete before submission:

```text
Submission commit:
Public repository URL:
Public app URL:
Cloud Run service/revision:
Cloud Tasks queue:
Data store and aggregate record:
Gemini model ID:
Google agent framework:
Correlation ID:
Measured cohort ID:
Public recommendation URL:
Published decision (STAY / TEST MORE / SWITCH):
Evidence receipt/replay URL:
Baseline/candidate/active policy versions:
Canary result and rollback evidence:
Optional additional Google model ID/evidence:
Optional public content/social URLs:
Video URL:
Architecture image:
Known limitations:
Pre-existing work disclosure:
```

## 11. Final claim audit

- [ ] Every number in the Devpost text can be traced to a source or retained run.
- [ ] Every cloud/security capability named in the submission is visible in code and evidence.
- [ ] No roadmap component is described in the present tense.
- [ ] “Measured,” “official,” “community,” “experimental,” “stale,” and “fixture” are used consistently.
- [ ] The submission never claims universal model superiority from a small cohort.
- [ ] A contained demo canary is never described as automatic customer production routing.
- [ ] An abstention is never rewritten as a recommendation.
- [ ] Bonus points are claimed only for completed, public, evidenced bonus work.
