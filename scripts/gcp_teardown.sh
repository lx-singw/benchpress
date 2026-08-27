#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Cloud Teardown CLI (`gcp_teardown.sh`)
# Usage: ./scripts/gcp_teardown.sh --env [dev|prod] [--project-id ID] [--region REGION]
# ==============================================================================
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-benchpress-hackathon-2026}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"

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
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
  echo "❌ Error: --env must be either 'dev' or 'prod'."
  exit 1
fi

echo "⚠️ =================================================================="
echo "   BENCHPRESS TEARDOWN: [Environment: ${ENV^^}]"
echo "   Target Project: $PROJECT_ID | Region: $REGION"
echo "=================================================================="

if [ "$ENV" = "prod" ]; then
  read -p "⚠️ WARNING: You are about to DESTROY the PRODUCTION environment! Type 'DESTROY' to confirm: " CONFIRM
  if [ "$CONFIRM" != "DESTROY" ]; then
    echo "Aborted."
    exit 1
  fi
fi

echo "📦 Destroying Terraform resources for '$ENV' environment..."
cd infra/terraform
terraform destroy \
  -var-file="environments/${ENV}.tfvars" \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -auto-approve
cd ../..

echo "✅ [$ENV] Environment teardown complete."
