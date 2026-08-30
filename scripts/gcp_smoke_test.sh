#!/usr/bin/env bash
# Fail-closed smoke test for one deployed Benchpress release.
#
# This test performs no provider run and creates no measured evidence. It proves
# that the immutable services, private worker identity boundary, Cloud Tasks
# queue, and required BigQuery tables are reachable. Pass --experiment-id only
# after a measured decision has been published.
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
WEB_URL=""
EXPERIMENT_ID=""
EXPECTED_RELEASE_SHA="${EXPECTED_RELEASE_SHA:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) ENV="$2"; shift 2 ;;
    --project-id) PROJECT_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --web-url) WEB_URL="$2"; shift 2 ;;
    --experiment-id) EXPERIMENT_ID="$2"; shift 2 ;;
    --release-sha) EXPECTED_RELEASE_SHA="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --env dev|prod --project-id ID [--region REGION] [--web-url URL] [--release-sha SHA] [--experiment-id ID]"
      exit 0
      ;;
    *) echo "Error: unknown option '$1'" >&2; exit 2 ;;
  esac
done

if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
  echo "Error: --env must be dev or prod." >&2
  exit 2
fi
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: --project-id or GOOGLE_CLOUD_PROJECT is required." >&2
  exit 2
fi
for command_name in gcloud bq curl jq git; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Error: required command is unavailable: $command_name" >&2
    exit 2
  }
done
if [[ -z "$EXPECTED_RELEASE_SHA" ]]; then
  EXPECTED_RELEASE_SHA="$(git rev-parse HEAD)"
fi
if [[ ! "$EXPECTED_RELEASE_SHA" =~ ^[a-f0-9]{40}$ ]]; then
  echo "Error: expected release SHA must be a full lowercase Git SHA." >&2
  exit 2
fi

WEB_SERVICE="benchpress-web-${ENV}"
WORKER_SERVICE="benchpress-worker-${ENV}"
QUEUE_NAME="${ENV}-trajectory-queue"
DATASET_NAME="benchpress_dev_analytics"
if [[ "$ENV" == "prod" ]]; then
  DATASET_NAME="benchpress_analytics"
fi

if [[ -z "$WEB_URL" ]]; then
  WEB_URL="$(gcloud run services describe "$WEB_SERVICE" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')"
fi
WORKER_URL="$(gcloud run services describe "$WORKER_SERVICE" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')"
[[ "$WEB_URL" == https://* ]] || { echo "Error: invalid deployed web URL." >&2; exit 1; }
[[ "$WORKER_URL" == https://* ]] || { echo "Error: invalid deployed worker URL." >&2; exit 1; }

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_DIR"' EXIT

require_status() {
  local expected="$1"
  local output_file="$2"
  local url="$3"
  shift 3
  local observed
  observed="$(curl --silent --show-error --output "$output_file" --write-out '%{http_code}' "$@" "$url")"
  if [[ "$observed" != "$expected" ]]; then
    echo "Error: $url returned HTTP $observed; expected $expected." >&2
    return 1
  fi
}

require_status 200 "$TEMP_DIR/web-health.json" "${WEB_URL}/api/healthz"
jq -e --arg sha "$EXPECTED_RELEASE_SHA" \
  '.status == "healthy" and .release_sha == $sha and (.runtime_mode == "development" or .runtime_mode == "production")' \
  "$TEMP_DIR/web-health.json" >/dev/null

WORKER_TOKEN="$(gcloud auth print-identity-token --audiences="$WORKER_URL")"
require_status 200 "$TEMP_DIR/worker-ready.json" "${WORKER_URL}/readyz" \
  --header "Authorization: Bearer ${WORKER_TOKEN}"
jq -e --arg sha "$EXPECTED_RELEASE_SHA" \
  '.status == "ready" and .release_sha == $sha' "$TEMP_DIR/worker-ready.json" >/dev/null

gcloud tasks queues describe "$QUEUE_NAME" \
  --project="$PROJECT_ID" --location="$REGION" --format=json >"$TEMP_DIR/queue.json"
jq -e '.state == "RUNNING"' "$TEMP_DIR/queue.json" >/dev/null

for table_name in trajectories fsm_turns workflow_events; do
  bq --project_id="$PROJECT_ID" show "${PROJECT_ID}:${DATASET_NAME}.${table_name}" >/dev/null
done

if [[ -n "$EXPERIMENT_ID" ]]; then
  require_status 200 "$TEMP_DIR/decision.json" "${WEB_URL}/api/v1/decisions/${EXPERIMENT_ID}"
  jq -e --arg id "$EXPERIMENT_ID" \
    '.experiment_id == $id and .truth_class == "BENCHPRESS_MEASURED" and .publication_status == "PUBLISHED"' \
    "$TEMP_DIR/decision.json" >/dev/null
fi

echo "PASS: deployed services match release ${EXPECTED_RELEASE_SHA}; worker auth, queue, and BigQuery checks succeeded."
if [[ -n "$EXPERIMENT_ID" ]]; then
  echo "PASS: published measured decision ${EXPERIMENT_ID} is readable from the public API."
fi
