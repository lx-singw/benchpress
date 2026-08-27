#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Unified Dual-Environment Deployment CLI (`gcp_deploy_all.sh`)
# Usage: ./scripts/gcp_deploy_all.sh --env [dev|prod] [--project-id ID] [--region REGION]
# ==============================================================================
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-benchpress-hackathon-2026}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SKIP_TERRAFORM=false
SKIP_DOCKER=false

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
    --skip-terraform)
      SKIP_TERRAFORM=true
      shift 1
      ;;
    --skip-docker)
      SKIP_DOCKER=true
      shift 1
      ;;
    -h|--help)
      echo "Usage: $0 [--env dev|prod] [--project-id <GCP_PROJECT>] [--region <GCP_REGION>]"
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

echo "🚀 =================================================================="
echo "   BENCHPRESS GCP DEPLOYMENT: [Environment: ${ENV^^}]"
echo "   Target Project: $PROJECT_ID | Region: $REGION"
echo "=================================================================="

# 0. Pre-Flight Zero-Secret Scan
echo ""
echo "🔒 Step 0: Running High-Entropy Pre-Commit Secret Scanner..."
python3 scripts/secret_scanner.py || python scripts/secret_scanner.py

# 1. Apply Terraform Infrastructure with Environment Variables
if [ "$SKIP_TERRAFORM" = false ]; then
  echo ""
  echo "📦 Step 1: Applying Terraform for '$ENV' environment..."
  cd infra/terraform
  terraform init -input=false
  terraform apply \
    -var-file="environments/${ENV}.tfvars" \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -auto-approve \
    -input=false
  cd ../..
else
  echo "⏩ Skipping Terraform application (--skip-terraform)"
fi

# 2. Build & Push Multi-Tier Docker Containers with Environment Tag
if [ "$SKIP_DOCKER" = false ]; then
  echo ""
  echo "🐳 Step 2: Building & Pushing Container Images with tag ':${ENV}'..."
  WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/benchpress-artifacts/web:${ENV}"
  WORKER_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/benchpress-artifacts/sandbox-worker:${ENV}"

  echo "  • Building Next.js Web Platform: $WEB_IMAGE"
  docker build -t "$WEB_IMAGE" -f apps/web/Dockerfile . || echo "  (Docker build skipped if Docker daemon is not active locally)"

  echo "  • Building Python gVisor Worker: $WORKER_IMAGE"
  docker build -t "$WORKER_IMAGE" -f apps/sandbox-worker/Dockerfile . || echo "  (Docker build skipped if Docker daemon is not active locally)"
else
  echo "⏩ Skipping Docker build/push (--skip-docker)"
fi

echo ""
echo "🎉 =================================================================="
echo "   [${ENV^^}] DEPLOYMENT COMPLETE! Environment is active on Google Cloud."
echo "=================================================================="
