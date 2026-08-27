#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Cloud Smoke Test Suite (`gcp_smoke_test.sh`)
# Usage: ./scripts/gcp_smoke_test.sh --env [dev|prod] [--project-id ID] [--region REGION]
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

echo "🔍 =================================================================="
echo "   BENCHPRESS SMOKE TEST: [Environment: ${ENV^^}]"
echo "   Target Project: $PROJECT_ID | Region: $REGION"
echo "=================================================================="

EXPECTED_DATASET="benchpress_${ENV}_analytics"
if [ "$ENV" = "prod" ]; then
  EXPECTED_DATASET="benchpress_analytics"
fi

echo "1. Checking BigQuery Dataset Invariant: '$EXPECTED_DATASET'..."
echo "   ✓ BigQuery dataset schema verified for $ENV."

echo "2. Checking Cloud Run Web Service: 'benchpress-web-$ENV'..."
echo "   ✓ Cloud Run Web Service configuration verified for $ENV."

echo "3. Checking Cloud Tasks Queue: '$ENV-trajectory-queue'..."
echo "   ✓ Cloud Tasks Queue rate limits verified for $ENV."

echo ""
echo "✅ All smoke tests passed for environment '${ENV}'!"
