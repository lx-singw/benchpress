#!/usr/bin/env bash
# Compatibility entry point. infra/terraform is the sole infrastructure root.
set -euo pipefail

if [[ -z "${PLANNER_MODEL:-}" ]]; then
  echo "PLANNER_MODEL must be set to the exact account-verified eligible Gemini 3.5+ model ID."
  exit 1
fi

exec bash scripts/gcp_deploy_all.sh --env prod "$@"
