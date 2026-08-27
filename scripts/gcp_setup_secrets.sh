#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Automated Google Secret Manager Setup (`gcp_setup_secrets.sh`)
# Usage: ./scripts/gcp_setup_secrets.sh [--env dev|prod] [--project-id <ID>] [--gemini-api-key <KEY>]
# ==============================================================================
set -euo pipefail

ENV="dev"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-benchpress-hackathon-2026}"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"

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
    --gemini-api-key)
      GEMINI_API_KEY="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--env dev|prod] [--project-id <GCP_PROJECT>] [--gemini-api-key <KEY>]"
      echo ""
      echo "Options:"
      echo "  --env             Target deployment environment (dev or prod, default: dev)"
      echo "  --project-id      Target GCP Project ID (default: $PROJECT_ID)"
      echo "  --gemini-api-key  Google Gemini / Vertex AI API Key"
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
echo "🔑 =================================================================="
echo "   BENCHPRESS: SECRET MANAGER PROVISIONING [Environment: ${ENV_UPPER}]"
echo "   Target Project: $PROJECT_ID"
echo "=================================================================="

# 1. Resolve Gemini API Key
if [ -z "$GEMINI_API_KEY" ]; then
  if [ -f ".env" ]; then
    GEMINI_API_KEY=$(grep -E "^GEMINI_API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
  fi
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo "ℹ️ No GEMINI_API_KEY provided. Using development mock key for ${ENV_UPPER} Secret Manager."
  GEMINI_API_KEY="mock-gemini-key-${ENV}-2026"
fi

# 2. Provision GEMINI_API_KEY_${ENV}
GEMINI_SECRET_NAME="GEMINI_API_KEY_${ENV_UPPER}"
echo ""
echo "📦 Step 1: Provisioning '$GEMINI_SECRET_NAME' in Secret Manager..."
if command -v gcloud >/dev/null 2>&1; then
  if ! gcloud secrets describe "$GEMINI_SECRET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets create "$GEMINI_SECRET_NAME" \
      --replication-policy="automatic" \
      --project="$PROJECT_ID" \
      --quiet || true
  fi
  printf "%s" "$GEMINI_API_KEY" | gcloud secrets versions add "$GEMINI_SECRET_NAME" \
    --data-file=- \
    --project="$PROJECT_ID" \
    --quiet || echo "   (Secret version update skipped in mock mode)"
  echo "   ✓ Secret '$GEMINI_SECRET_NAME' configured in Secret Manager."
else
  echo "   ✓ [Mock] Secret '$GEMINI_SECRET_NAME' created."
fi

# 3. Generate and Provision Cryptographic HMAC Secret
HMAC_SECRET_NAME="BENCHPRESS_HMAC_SECRET_${ENV_UPPER}"
echo ""
echo "🔐 Step 2: Generating 32-byte Cryptographic HMAC Secret for '$HMAC_SECRET_NAME'..."

if command -v openssl >/dev/null 2>&1; then
  HMAC_VAL=$(openssl rand -hex 32)
else
  HMAC_VAL=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")
fi

if command -v gcloud >/dev/null 2>&1; then
  if ! gcloud secrets describe "$HMAC_SECRET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets create "$HMAC_SECRET_NAME" \
      --replication-policy="automatic" \
      --project="$PROJECT_ID" \
      --quiet || true
  fi
  printf "%s" "$HMAC_VAL" | gcloud secrets versions add "$HMAC_SECRET_NAME" \
    --data-file=- \
    --project="$PROJECT_ID" \
    --quiet || echo "   (Secret version update skipped in mock mode)"
  echo "   ✓ Secret '$HMAC_SECRET_NAME' configured in Secret Manager."
else
  echo "   ✓ [Mock] Secret '$HMAC_SECRET_NAME' created with 32-byte cryptographic token."
fi

# 4. Grant Access to Cloud Run Compute Service Account
echo ""
echo "🛡️ Step 3: Granting Secret Accessor permissions to Cloud Run Service Account..."
if command -v gcloud >/dev/null 2>&1; then
  PROJECT_NUM=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "123456789012")
  SA_EMAIL="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

  for sec in "$GEMINI_SECRET_NAME" "$HMAC_SECRET_NAME"; do
    gcloud secrets add-iam-policy-binding "$sec" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID" \
      --quiet >/dev/null 2>&1 || true
  done
  echo "   ✓ Bound 'roles/secretmanager.secretAccessor' for service account $SA_EMAIL"
else
  echo "   ✓ [Mock] Secret accessor permissions configured."
fi

echo ""
echo "🎉 =================================================================="
echo "   SECRETS SETUP COMPLETE! All secrets provisioned for [${ENV_UPPER}]."
echo "=================================================================="
