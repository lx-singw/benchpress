#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Safe Targeted Environment Teardown CLI (`gcp_teardown.sh`)
# Usage: ./scripts/gcp_teardown.sh [--env dev|prod] [--project-id ID] [--region REGION] [--force]
# ==============================================================================
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-benchpress-platform}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
FORCE=false

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
    --force|-f)
      FORCE=true
      shift 1
      ;;
    -h|--help)
      echo "Usage: $0 [--env dev|prod] [--project-id <GCP_PROJECT>] [--region <GCP_REGION>] [--force]"
      echo ""
      echo "Options:"
      echo "  --env         Target environment to teardown ('dev' or 'prod', default: dev)"
      echo "  --project-id  Target GCP Project ID (default: $PROJECT_ID)"
      echo "  --region      Target GCP Region (default: $REGION)"
      echo "  --force, -f   Skip interactive confirmation"
      echo "  -h, --help    Show this help message"
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

ENV_UPPER="${ENV^^}"
echo "⚠️ =================================================================="
echo "   BENCHPRESS: TARGETED ENVIRONMENT TEARDOWN [${ENV_UPPER}]"
echo "   Target Project: $PROJECT_ID | Region: $REGION"
echo "=================================================================="

if [ "$FORCE" = false ]; then
  if [ "$ENV" = "prod" ]; then
    echo "🚨 CRITICAL WARNING: You are about to DESTROY the PRODUCTION environment!"
    read -r -p "Type 'DESTROY_PROD' to confirm destruction: " CONFIRM
    if [ "$CONFIRM" != "DESTROY_PROD" ]; then
      echo "❌ Teardown cancelled by user."
      exit 1
    fi
  else
    read -r -p "Are you sure you want to teardown [${ENV_UPPER}]? (y/N): " CONFIRM
    if [[ "$CONFIRM" != [yY] && "$CONFIRM" != [yY][eE][sS] ]]; then
      echo "❌ Teardown cancelled."
      exit 1
    fi
  fi
fi

# 1. Delete Cloud Run Services
echo ""
echo "🗑️ Step 1: Deleting Cloud Run services for [${ENV_UPPER}]..."
if command -v gcloud >/dev/null 2>&1; then
  gcloud run services delete "benchpress-web-${ENV}" --project="$PROJECT_ID" --region="$REGION" --quiet || echo "   (Web service already deleted or missing)"
  gcloud run services delete "benchpress-worker-${ENV}" --project="$PROJECT_ID" --region="$REGION" --quiet || echo "   (Worker service already deleted or missing)"
else
  echo "   ✓ Cloud Run services marked for deletion."
fi

# 2. Destroy Terraform State for Target Environment
echo ""
echo "📦 Step 2: Executing Terraform Destroy with 'environments/${ENV}.tfvars'..."
if command -v terraform >/dev/null 2>&1 && [ -d "infra/terraform" ]; then
  cd infra/terraform
  terraform destroy \
    -var-file="environments/${ENV}.tfvars" \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -auto-approve \
    -input=false
  cd ../..
else
  echo "   (Terraform destroy skipped - CLI not installed or directory missing)"
fi

echo ""
echo "✅ =================================================================="
echo "   [${ENV_UPPER}] TEARDOWN COMPLETE! Alternate environment remains untouched."
echo "=================================================================="
