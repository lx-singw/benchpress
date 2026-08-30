#!/usr/bin/env bash
# ==============================================================================
# Benchpress: immutable G0 deployment entry point (`gcp_deploy_all.sh`)
# Target Track: The Taskmaster
# Usage: ./scripts/gcp_deploy_all.sh [--env dev|prod] [--project-id ID] [--region REGION]
# ==============================================================================
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-benchpress-platform}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SKIP_BOOTSTRAP=false
SKIP_TERRAFORM=false
SKIP_DOCKER=false
SKIP_SMOKE=false

# --- Parse CLI Arguments ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENV="$2"
      shift 2
      ;;
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --skip-bootstrap)
      SKIP_BOOTSTRAP=true
      shift 1
      ;;
    --skip-terraform)
      SKIP_TERRAFORM=true
      shift 1
      ;;
    --skip-docker)
      SKIP_DOCKER=true
      shift 1
      ;;
    --skip-smoke)
      SKIP_SMOKE=true
      shift 1
      ;;
    -h|--help)
      echo "Usage: $0 [--env dev|prod] [--project-id <GCP_PROJECT>] [--region <GCP_REGION>]"
      echo ""
      echo "Options:"
      echo "  --env             Deployment target environment ('dev' or 'prod', default: dev)"
      echo "  --project-id      Target Google Cloud Project ID (default: $PROJECT_ID)"
      echo "  --region          Target Google Cloud Region (default: $REGION)"
      echo "  --skip-bootstrap  Skip GCP API enablement & project bootstrap"
      echo "  --skip-terraform  Skip Terraform infrastructure apply"
      echo "  --skip-docker     Skip Docker container build and push"
      echo "  --skip-smoke      Skip automated post-deployment smoke test"
      echo "  -h, --help        Show this help message"
      exit 0
      ;;
    *)
      echo "❌ Error: Unknown CLI option '$1'"
      exit 1
      ;;
  esac
done

if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
  echo "❌ Error: --env must be either 'dev' or 'prod' (received: '$ENV')."
  exit 1
fi

RELEASE_SHA="$(git rev-parse HEAD)"
if [[ ! "$RELEASE_SHA" =~ ^[a-f0-9]{40}$ ]]; then
  echo "Error: release commit must be a full 40-character Git SHA."
  exit 1
fi
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: immutable release images must be built from a clean working tree."
  exit 1
fi
PLANNER_MODEL="${PLANNER_MODEL:-}"
if [[ ! "$PLANNER_MODEL" =~ ^gemini-[3-9]\.[5-9] ]]; then
  echo "Error: PLANNER_MODEL must be the exact account-verified eligible Gemini 3.5+ model ID."
  exit 1
fi
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/benchpress-artifacts/web:${RELEASE_SHA}"
WORKER_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/benchpress-artifacts/sandbox-worker:${RELEASE_SHA}"

ENV_UPPER="${ENV^^}"
echo "🚀 =================================================================="
echo "   BENCHPRESS: IMMUTABLE G0 DEPLOYMENT [${ENV_UPPER}]"
echo "   Target Project: $PROJECT_ID | Region: $REGION"
echo "=================================================================="

# 0. Complete non-live release gate before any cloud mutation.
echo ""
echo "🔒 Step 0: Running complete non-live release gates..."
bash scripts/verify_monorepo.sh

# 1. API & Security Bootstrap
if [ "$SKIP_BOOTSTRAP" = false ]; then
  echo ""
  echo "🛠️ Step 1: Bootstrapping GCP APIs and Container Registry Auth..."
  bash scripts/gcp_bootstrap.sh --project-id "$PROJECT_ID" --region "$REGION"
else
  echo "⏩ Skipping GCP API Bootstrap (--skip-bootstrap)"
fi

# 2. Apply Terraform Infrastructure. The G0 path uses Vertex AI workload
# identity and Cloud Tasks OIDC; it does not provision API/HMAC secrets.
if [ "$SKIP_TERRAFORM" = false ]; then
  if ! command -v terraform >/dev/null 2>&1; then
    echo "Error: terraform is required unless --skip-terraform is explicitly supplied." >&2
    exit 1
  else
    echo ""
    echo "📦 Step 2: Applying Terraform Infrastructure for '$ENV'..."
    cd infra/terraform
    terraform init -input=false
    terraform apply \
      -target=google_artifact_registry_repository.benchpress_repo \
      -var-file="environments/${ENV}.tfvars" \
      -var="project_id=${PROJECT_ID}" \
      -var="region=${REGION}" \
      -var="release_sha=${RELEASE_SHA}" \
      -var="planner_model=${PLANNER_MODEL}" \
      -var="web_image=${WEB_IMAGE}" \
      -var="worker_image=${WORKER_IMAGE}" \
      -auto-approve \
      -input=false
    cd ../..
  fi
else
  echo "⏩ Skipping Terraform application (--skip-terraform)"
fi

# 3. Container Builds & Push
if [ "$SKIP_DOCKER" = false ]; then
  echo ""
  echo "🐳 Step 3: Building & Pushing immutable release images tagged '${RELEASE_SHA}'..."

  echo "  • [1/2] Building Next.js 15 Web Platform: $WEB_IMAGE"
  docker build -t "$WEB_IMAGE" -f apps/web/Dockerfile .
  docker push "$WEB_IMAGE"

  echo "  • [2/2] Building bounded Python 3.12 Worker: $WORKER_IMAGE"
  docker build -t "$WORKER_IMAGE" -f apps/sandbox-worker/Dockerfile .
  docker push "$WORKER_IMAGE"

else
  echo "⏩ Skipping Docker build/push; verifying immutable release images already exist..."
  gcloud artifacts docker images describe "$WEB_IMAGE" --project "$PROJECT_ID" >/dev/null
  gcloud artifacts docker images describe "$WORKER_IMAGE" --project "$PROJECT_ID" >/dev/null
fi

if [ "$SKIP_TERRAFORM" = false ]; then
  echo ""
  echo "📦 Applying the full Terraform stack after immutable images are available..."
  cd infra/terraform
  terraform apply \
    -var-file="environments/${ENV}.tfvars" \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="release_sha=${RELEASE_SHA}" \
    -var="planner_model=${PLANNER_MODEL}" \
    -var="web_image=${WEB_IMAGE}" \
    -var="worker_image=${WORKER_IMAGE}" \
    -auto-approve \
    -input=false
  cd ../..
fi

# 4. Automated Post-Deployment Smoke Verification
if [ "$SKIP_SMOKE" = false ]; then
  echo ""
  echo "🧪 Step 4: Running Automated Live Cloud Smoke Verification..."
  bash scripts/gcp_smoke_test.sh --env "$ENV" --project-id "$PROJECT_ID" --region "$REGION"
else
  echo "⏩ Skipping Smoke Verification (--skip-smoke)"
fi

# 5. Terminal Summary
DATASET_NAME="benchpress_${ENV}_analytics"
if [ "$ENV" = "prod" ]; then
  DATASET_NAME="benchpress_analytics"
fi

if [ "$SKIP_TERRAFORM" = false ] && command -v terraform >/dev/null 2>&1; then
  WEB_URL="$(terraform -chdir=infra/terraform output -raw web_service_uri)"
  WORKER_URL="$(terraform -chdir=infra/terraform output -raw worker_service_uri)"
else
  WEB_URL="not-applied"
  WORKER_URL="not-applied"
fi

echo ""
echo "✨ =================================================================="
echo "   BENCHPRESS [${ENV_UPPER}] DEPLOYMENT APPLIED; VERIFY EVIDENCE BEFORE RELEASE"
echo "=================================================================="
echo "   🌐 Web Platform URL:      $WEB_URL"
echo "   ⚡ Worker Endpoint:       $WORKER_URL"
echo "   🔒 Release SHA:           $RELEASE_SHA"
echo "   📦 Web image:             $WEB_IMAGE"
echo "   📦 Worker image:          $WORKER_IMAGE"
echo "   📊 BigQuery Analytics:    https://console.cloud.google.com/bigquery?project=${PROJECT_ID}&p=${PROJECT_ID}&d=${DATASET_NAME}&page=dataset"
echo "   🚦 Cloud Tasks Queue:     ${ENV}-trajectory-queue ($([ "$ENV" = "dev" ] && echo "10/s rate limit" || echo "500/s rate limit"))"
echo "   🧠 Redis Memorystore:     benchpress-redis-${ENV} ($([ "$ENV" = "dev" ] && echo "1 GB Basic" || echo "5 GB Standard HA"))"
echo "=================================================================="
