#!/usr/bin/env bash
# Canonical non-live release gate. Live cloud/preflight gates remain explicit opt-ins.
set -euo pipefail

if [[ ! -f pnpm-lock.yaml || ! -d apps/sandbox-worker/src ]]; then
  echo "Run this command from the Benchpress repository root." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "Python 3.12 is required; set PYTHON_BIN to the Python 3.12 executable." >&2
  exit 2
}
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' || {
  echo "PYTHON_BIN must resolve to Python 3.12 exactly." >&2
  exit 2
}
TERRAFORM_BIN="${TERRAFORM_BIN:-terraform}"
command -v "$TERRAFORM_BIN" >/dev/null 2>&1 || {
  echo "Terraform is required; set TERRAFORM_BIN to the Terraform executable." >&2
  exit 2
}

echo "[1/9] Secret and truth/provenance scans"
"$PYTHON_BIN" scripts/secret_scanner.py
"$PYTHON_BIN" scripts/verify_truth_boundaries.py

echo "[2/9] Contract schema/parity tests and build"
pnpm --filter @benchpress/contracts test
pnpm --filter @benchpress/contracts build

echo "[3/9] Complete Python suite with production import layout"
export PYTHONPATH="apps/sandbox-worker/src:.:${PYTHONPATH:-}"
mkdir -p artifacts/tests
"$PYTHON_BIN" -m pytest tests apps/sandbox-worker/tests -q --junitxml=artifacts/tests/python-junit.xml

echo "[4/9] Worker syntax and critical static checks"
"$PYTHON_BIN" -m compileall -q apps/sandbox-worker/src scripts
"$PYTHON_BIN" -m ruff check apps/sandbox-worker/src scripts tests --select E9,F63,F7,F82

echo "[5/9] Web unit/API tests, typecheck, and production build"
pnpm --filter web test
pnpm --filter web exec tsc --noEmit
pnpm --filter web build
pnpm audit --prod --audit-level moderate

echo "[6/9] SDK and telemetry package builds"
pnpm --filter @benchpress/telemetry build
pnpm --filter @benchpress/sdk build

echo "[7/9] Manifest fixture validation"
"$PYTHON_BIN" scripts/validate_demo_manifest.py

echo "[8/9] Terraform format and validation"
"$TERRAFORM_BIN" -chdir=infra/terraform init -backend=false -input=false
"$TERRAFORM_BIN" -chdir=infra/terraform fmt -check -recursive
"$TERRAFORM_BIN" -chdir=infra/terraform validate

echo "[9/9] Evidence verifier negative-path tests"
"$PYTHON_BIN" -m pytest tests/evidence -q

echo "All non-live release gates passed. Live preflight, rehearsal, and URL checks are still required."
