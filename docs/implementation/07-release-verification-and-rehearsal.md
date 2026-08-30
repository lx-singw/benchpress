# Release verification and rehearsal

> **Status:** Authoritative operator runbook
> **Applies to:** WP-13 through WP-15 of `BP-PLAN-007`
> **Safety:** Live preflight, provider execution, deployment, and rehearsal can create cloud resources and spend. Run them only in the authorized project.
> **Truth rule:** A command’s existence is not evidence. Retain its output against the exact release SHA.

## 1. Supported release environment

Use one Linux environment for the release path (native Linux or WSL Ubuntu) with repository dependencies installed in that same environment. Do not mix Windows-managed `node_modules` with WSL pnpm. Required tools are Python 3.12, Node/pnpm from the lockfile, Terraform, Docker, `gcloud`, `bq`, `curl`, `jq`, and Git.

Windows Terraform may be used for local `fmt`/`validate`, but the canonical deployment and evidence commands require Terraform on the Linux `PATH`.

Before any live action:

```bash
cd /home/lx_singw/projects/benchpress
git status --short
git rev-parse HEAD
gcloud auth list --filter=status:ACTIVE
gcloud config get-value project
```

Stop if the checkout is dirty, `HEAD` is not the intended full release SHA, the account/project is wrong, or the operator has not authorized spend.

## 2. Freeze inputs

Create a release record outside fixture directories containing:

- full 40-character Git SHA;
- target project, region, environment, Firestore database/prefix, queue, and Cloud Run service names;
- the exact account-available Gemini 3.5-or-newer planner model ID;
- immutable baseline and candidate `NativeConfiguration` records;
- active baseline policy version and pointer generation;
- frozen task, fingerprint, harness, oracle, prompt, tool-schema, price, aggregation-policy, and approval-boundary versions;
- matrix/per-run budgets, timeout, turn/tool/retry/concurrency ceilings, stopping thresholds, and deadline; and
- the authoritative provider source URL, source checksum, effective time, and retrieval time used by the `ChangeEvent`.

Do not copy IDs or metrics from `evidence/`, `docs/hackathon/demo-manifest.yaml`, or local web fixtures into a measured run.

## 3. Non-live release gates

From a clean checkout:

```bash
corepack enable
pnpm install --frozen-lockfile
python3.12 -m pip install -r apps/sandbox-worker/requirements.txt
python3.12 -m pip install ruff pytest
terraform -chdir=infra/terraform init -backend=false -input=false
bash scripts/verify_monorepo.sh | tee artifacts/tests/release-gate.log
```

Required result: every command exits zero, including the production dependency audit. Preserve `artifacts/tests/python-junit.xml`, the release-gate log, contract/web build logs produced by CI, and the CI run URL. The current development observation is 129 passed for Python with the Firestore emulator enabled and 8 passed for the web/API suite; rerun rather than copying those numbers into release evidence.

Run the Firestore emulator tests in the release environment instead of accepting the local skips:

```bash
gcloud emulators firestore start --host-port=127.0.0.1:8085 --quiet
FIRESTORE_EMULATOR_HOST=127.0.0.1:8085 \
  PYTHONPATH=apps/sandbox-worker/src:. \
  python3.12 -m pytest tests/ledger/test_firestore_restart_integration.py -q \
  --junitxml=artifacts/tests/firestore-emulator-junit.xml
```

Retain the emulator process output and test report.

## 4. Live release preflight

Set non-secret environment variables to the exact release values. Prefer workload identity/ADC; never paste keys into logs or the evidence bundle.

```bash
export RUNTIME_MODE=rehearsal
export USE_LOCAL_MOCK=false
export RELEASE_SHA="$(git rev-parse HEAD)"
export GOOGLE_CLOUD_PROJECT="<authorized-project>"
export GOOGLE_CLOUD_REGION="<region>"
export VERTEX_AI_LOCATION="<region>"
export GENAI_USE_VERTEXAI=true
export PLANNER_MODEL="<exact-account-verified-gemini-3.5+-model-id>"
export VERTEX_AI_LOCATION="global"
export REPOSITORY_BACKEND=firestore
export FIRESTORE_DATABASE_ID="(default)"
export FIRESTORE_COLLECTION_PREFIX="benchpress_rehearsal"
export GCP_TASKS_LOCATION="<region>"
export GCP_TASKS_QUEUE_NAME="dev-trajectory-queue"
export SANDBOX_WORKER_URL="<deployed-worker-url>"
export TASKS_OIDC_AUDIENCE="$SANDBOX_WORKER_URL"
export GCP_TASKS_INVOKER_SERVICE_ACCOUNT="<tasks-invoker-service-account>"
export BIGQUERY_DATASET="benchpress_dev_analytics"
```

For initial infrastructure validation before the worker exists:

```bash
python3.12 scripts/preflight_release.py --skip-worker \
  --output artifacts/release/preflight-infrastructure.json
```

After deployment, rerun without `--skip-worker`:

```bash
python3.12 scripts/preflight_release.py \
  --output artifacts/release/preflight-complete.json
```

The complete report must say `PASS` and retain the requested and provider-returned eligible model IDs, response ID, usage metadata, response-text digest, Firestore transaction, queue, required BigQuery tables, worker URL, and matching release SHA. This is intentionally spend-producing and is never part of ordinary unit tests.

## 5. Immutable deployment

The deployment script refuses a dirty checkout, non-full SHA, missing Terraform, and an ineligible planner-model name. Review the Terraform plan before applying in the authorized project.

```bash
export GOOGLE_CLOUD_PROJECT="<authorized-project>"
export GOOGLE_CLOUD_REGION="<region>"
export PLANNER_MODEL="<exact-account-verified-gemini-3.5+-model-id>"
bash scripts/gcp_deploy_all.sh \
  --env dev \
  --project-id "$GOOGLE_CLOUD_PROJECT" \
  --region "$GOOGLE_CLOUD_REGION"
```

Retain:

```bash
terraform -chdir=infra/terraform output -json > artifacts/release/terraform-outputs.json
gcloud run services describe benchpress-web-dev --project "$GOOGLE_CLOUD_PROJECT" --region "$GOOGLE_CLOUD_REGION" --format=json > artifacts/release/web-service.json
gcloud run services describe benchpress-worker-dev --project "$GOOGLE_CLOUD_PROJECT" --region "$GOOGLE_CLOUD_REGION" --format=json > artifacts/release/worker-service.json
```

Both images must be identified by the release SHA or digest, both revisions must expose the same `RELEASE_SHA`, neither runtime may use the default Compute Engine service account, the web service must be the only public service, and only the dedicated tasks invoker may invoke the worker.

Run the fail-closed smoke test:

```bash
bash scripts/gcp_smoke_test.sh \
  --env dev \
  --project-id "$GOOGLE_CLOUD_PROJECT" \
  --region "$GOOGLE_CLOUD_REGION" \
  --release-sha "$RELEASE_SHA" | tee artifacts/release/cloud-smoke.log
```

It must verify the web release health response, authenticated private worker readiness, running Cloud Tasks queue, and all required BigQuery tables. It has no mock-success path.

## 6. Primary measured rehearsal

1. Confirm the active baseline policy and immutable configuration documents exist in the release-prefixed Firestore collections.
2. Prepare a new schema-valid `ChangeEvent`. Use new event/correlation IDs, an authoritative source checksum, the frozen baseline version/configuration, the authorized budget/deadline, and `replay=false` for a real detected change or `source_kind=SYNTHETIC_REPLAY`, `replay=true`, and an explicit label for a replay. A replay may exercise the workflow but must never misrepresent the trigger as an observed provider event.
3. Validate it locally against `packages/contracts/schemas/change-event.v1.json`.
4. Submit once and retain the complete `202` response:

```bash
WEB_URL="$(terraform -chdir=infra/terraform output -raw web_service_uri)"
curl --fail-with-body --silent --show-error \
  --request POST "${WEB_URL}/api/v1/experiments" \
  --header 'Content-Type: application/json' \
  --data-binary @artifacts/release/change-event.json \
  | tee artifacts/release/experiment-accepted.json
```

5. Record `experiment_id`, `correlation_id`, `event_id`, and deterministic orchestration task ID without editing the stored event.
6. Follow status until `PUBLISHED`. Inspect Firestore and correlated logs; do not mutate workflow records manually.
7. Confirm the approved plan includes the baseline, frozen task IDs, immutable configurations, budget and stopping policy. Confirm all manifests resolve exactly.
8. Confirm every provider call produces provider-returned usage, latency, terminal result, oracle evidence, eligibility, and cost. Failed attempts remain present.
9. Confirm aggregates recompute from exactly their eligible result keys and that zero-success CPR is undefined rather than zero.
10. Accept the genuine `STAY`, `TEST MORE`, or `SWITCH`. Never change thresholds after seeing results to force an outcome.
11. If a candidate reaches canary, prove the contained policy CAS and exact rollback behavior. The canary must not control customer production traffic.
12. Confirm one immutable publication pointer exists and that decision, receipt, replay, and routing reads reject anything unpublished or invalid-digest.
13. After publication, set Terraform `routing_decision_experiment_id` to this exact published experiment and reapply the same immutable image/SHA variables. Verify the new web revision still exposes the frozen release SHA, then call the routing endpoint and retain its `BENCHPRESS_MEASURED` response. Never point it at an unpublished experiment.

## 7. Required reliability and negative proofs

Use separate, clearly labelled rehearsal correlation IDs where a proof would contaminate the primary cohort:

- redeliver one orchestration/run task and prove one manifest, provider invocation, result, and charge for the logical key;
- restart the worker between durable transitions and prove the workflow resumes;
- call a worker task endpoint without a token, with the wrong audience, and with the wrong identity; retain `401`/`403` and sanitized logs;
- trigger a frozen budget/per-run ceiling and prove no unreserved provider call occurs;
- trigger an unsupported native control and prove rejection without substitution;
- exercise zero verified successes and verify undefined CPR plus the reason;
- attempt a stale CAS and prove the active pointer is unchanged;
- force a contained canary failure and prove exact baseline restoration; and
- tamper with a copied receipt/bundle and prove the public read model or offline verifier rejects it.

Do not alter the primary measured records to manufacture these cases.

## 8. Evidence export and offline verification

Export only from a clean checkout whose `HEAD` matches the deployed release. The exporter requires a new/empty destination, one published measured receipt, its plan and fingerprint, Cloud Tasks metadata, logs, service metadata, Terraform outputs, public API responses, and at least one test report.

```bash
CORRELATION_ID="<primary-correlation-id>"
EXPERIMENT_ID="exp_${CORRELATION_ID#corr_}"

bash scripts/gcp_smoke_test.sh \
  --env dev \
  --project-id "$GOOGLE_CLOUD_PROJECT" \
  --region "$GOOGLE_CLOUD_REGION" \
  --release-sha "$RELEASE_SHA" \
  --experiment-id "$EXPERIMENT_ID" \
  | tee artifacts/release/published-smoke.log

python3.12 scripts/export_evidence_package.py "$CORRELATION_ID" \
  --environment rehearsal \
  --output "evidence/runs/${CORRELATION_ID}" \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --region "$GOOGLE_CLOUD_REGION" \
  --queue dev-trajectory-queue \
  --bigquery-dataset benchpress_dev_analytics \
  --database "(default)" \
  --collection-prefix benchpress_rehearsal \
  --web-service benchpress-web-dev \
  --worker-service benchpress-worker-dev \
  --public-url "$WEB_URL" \
  --test-report artifacts/tests/python-junit.xml \
  --test-report artifacts/tests/firestore-emulator-junit.xml

python3.12 scripts/verify_evidence_package.py "evidence/runs/${CORRELATION_ID}"
```

Required result: `PASS` and a `verification-report.json` whose correlation ID, receipt ID, and release SHA match the deployment. Copy the repository and bundle to a clean, credential-free clone and rerun the verifier there. Preserve that output.

## 9. Submission freeze

Only after the live bundle passes:

1. Replace placeholders in the Devpost narrative and demo script with evidence-linked values.
2. Update `docs/00-implementation-status.md` from the exported records.
3. Complete every technical item in the final checklist with an adjacent artifact/URL; leave account, team, video-hosting, and Devpost actions to their authorized owner.
4. Record the public app, decision, receipt, replay, repository, video, Cloud Run revision, queue, model, correlation, policy, canary, and evidence URLs.
5. Record the demo from the exact frozen revisions; expose no token, credential, private prompt, or tenant data.
6. Rerun the full local gate, live preflight, published smoke test, and offline verifier after recording.
7. Create the annotated release tag only after all evidence-linked content is committed and clean.
8. Freeze code and deployment changes for the judging window, with an availability/rollback contact note that does not rewrite evidence.

G0 is complete only when an independent reviewer can start with the public decision, verify its receipt and bundle offline, trace the same correlation through the deployed services, and find no unchecked technical item.
