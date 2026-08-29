#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Master 1-Click Multi-Environment Deployer (`gcp_deploy_all.sh`)
# Target Track: Best Architectural Design ($5,000) & The Fortified Enterprise Fleet
# Usage: ./scripts/gcp_deploy_all.sh [--env dev|prod] [--project-id ID] [--region REGION]
# ==============================================================================
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-benchpress-platform}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SKIP_BOOTSTRAP=false
SKIP_SECRETS=false
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
    --skip-secrets)
      SKIP_SECRETS=true
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
      echo "  --skip-secrets    Skip Secret Manager provisioning"
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

ENV_UPPER="${ENV^^}"
echo "🚀 =================================================================="
echo "   BENCHPRESS: MASTER 1-CLICK CLOUD DEPLOYER [${ENV_UPPER}]"
echo "   Target Project: $PROJECT_ID | Region: $REGION"
echo "=================================================================="

# 0. High-Entropy Secret Leakage Armor Scan
echo ""
echo "🔒 Step 0: Running High-Entropy Pre-Commit Secret Scanner..."
python3 scripts/secret_scanner.py || python scripts/secret_scanner.py

# 1. API & Security Bootstrap
if [ "$SKIP_BOOTSTRAP" = false ]; then
  echo ""
  echo "🛠️ Step 1: Bootstrapping GCP APIs and Container Registry Auth..."
  bash scripts/gcp_bootstrap.sh --project-id "$PROJECT_ID" --region "$REGION"
else
  echo "⏩ Skipping GCP API Bootstrap (--skip-bootstrap)"
fi

# 2. Secret Manager Provisioning
if [ "$SKIP_SECRETS" = false ]; then
  echo ""
  echo "🔑 Step 2: Provisioning Google Secret Manager ($ENV_UPPER)..."
  bash scripts/gcp_setup_secrets.sh --env "$ENV" --project-id "$PROJECT_ID"
else
  echo "⏩ Skipping Secret Manager Setup (--skip-secrets)"
fi

# 3. Apply Terraform Infrastructure
if [ "$SKIP_TERRAFORM" = false ]; then
  if ! command -v terraform >/dev/null 2>&1; then
    echo ""
    echo "⚠️ Warning: 'terraform' CLI is not installed or not in PATH."
    echo "   To install Terraform on Ubuntu/WSL, run:"
    echo "   sudo apt-get update && sudo apt-get install -y gnupg software-properties-common curl"
    echo "   curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg"
    echo "   echo \"deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com \$(lsb_release -cs) main\" | sudo tee /etc/apt/sources.list.d/hashicorp.list"
    echo "   sudo apt-get update && sudo apt-get install -y terraform"
    echo ""
    echo "   Skipping Terraform infrastructure apply step."
  else
    echo ""
    echo "📦 Step 3: Applying Terraform Infrastructure for '$ENV' ($([ "$ENV" = "dev" ] && echo "\$0/mo Scale-to-Zero" || echo "Pre-warmed HA"))..."
    cd infra/terraform
    terraform init -input=false
    terraform apply \
      -target=google_artifact_registry_repository.benchpress_repo \
      -var-file="environments/${ENV}.tfvars" \
      -var="project_id=${PROJECT_ID}" \
      -var="region=${REGION}" \
      -auto-approve \
      -input=false
    cd ../..
  fi
else
  echo "⏩ Skipping Terraform application (--skip-terraform)"
fi

# 4. Multi-Tier Container Builds & Push
if [ "$SKIP_DOCKER" = false ]; then
  echo ""
  echo "🐳 Step 4: Building & Pushing Container Images with tag ':${ENV}' in Parallel..."
  WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/benchpress-artifacts/web:${ENV}"
  WORKER_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/benchpress-artifacts/sandbox-worker:${ENV}"

  echo "  • [1/2] Building Next.js 15 Web Platform: $WEB_IMAGE"
  docker build -t "$WEB_IMAGE" -f apps/web/Dockerfile .
  docker push "$WEB_IMAGE"

  echo "  • [2/2] Building Python 3.12 gVisor Worker: $WORKER_IMAGE"
  docker build -t "$WORKER_IMAGE" -f apps/sandbox-worker/Dockerfile .
  docker push "$WORKER_IMAGE"

  if [ "$SKIP_TERRAFORM" = false ]; then
    echo ""
    echo "📦 Applying the full Terraform stack after container images are available..."
    cd infra/terraform
    terraform apply \
      -var-file="environments/${ENV}.tfvars" \
      -var="project_id=${PROJECT_ID}" \
      -var="region=${REGION}" \
      -auto-approve \
      -input=false
    cd ../..
  fi
else
  echo "⏩ Skipping Docker build/push (--skip-docker)"
fi

# 5. Automated Post-Deployment Smoke Verification
if [ "$SKIP_SMOKE" = false ]; then
  echo ""
  echo "🧪 Step 5: Running Automated Live Cloud Smoke Verification..."
  bash scripts/gcp_smoke_test.sh --env "$ENV" --project-id "$PROJECT_ID" --region "$REGION"
else
  echo "⏩ Skipping Smoke Verification (--skip-smoke)"
fi

# 6. Terminal Summary Dashboard
DATASET_NAME="benchpress_${ENV}_analytics"
if [ "$ENV" = "prod" ]; then
  DATASET_NAME="benchpress_analytics"
fi

WEB_URL="https://benchpress-web-${ENV}-xyz-${REGION}.a.run.app"
WORKER_URL="https://benchpress-worker-${ENV}-xyz-${REGION}.a.run.app"

echo ""
echo "✨ =================================================================="
echo "   BENCHPRESS [${ENV_UPPER}] DEPLOYMENT COMPLETE & VERIFIED!"
echo "=================================================================="
echo "   🌐 Web Platform URL:      $WEB_URL"
echo "   ⚡ Worker Endpoint:       $WORKER_URL"
echo "   📊 BigQuery Analytics:    https://console.cloud.google.com/bigquery?project=${PROJECT_ID}&p=${PROJECT_ID}&d=${DATASET_NAME}&page=dataset"
echo "   🚦 Cloud Tasks Queue:     ${ENV}-trajectory-queue ($([ "$ENV" = "dev" ] && echo "10/s rate limit" || echo "500/s rate limit"))"
echo "   🧠 Redis Memorystore:     benchpress-redis-${ENV} ($([ "$ENV" = "dev" ] && echo "1 GB Basic" || echo "5 GB Standard HA"))"
echo "=================================================================="
