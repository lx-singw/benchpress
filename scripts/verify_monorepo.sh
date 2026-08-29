#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Master Monorepo Release Gate (IMP-10 / Taskmaster)
# ==============================================================================
set -euo pipefail

echo "🛡️ =================================================================="
echo "   BENCHPRESS: MASTER MONOREPO VERIFICATION & RELEASE GATE"
echo "=================================================================="

# 0. Zero-Secret Leakage Pre-Commit Armor Scan
echo ""
echo "🔒 Step 0: Running High-Entropy Secret Leak Scanner..."
if command -v python3 >/dev/null 2>&1; then
    python3 scripts/secret_scanner.py
else
    python scripts/secret_scanner.py
fi

# 1. TypeScript Sovereign Contracts Test Suite
echo ""
echo "📦 Step 1: Running TypeScript Sovereign Contracts test suite..."
pnpm --filter @benchpress/contracts test

# 2. Web API & Read-Model Contract Tests
echo ""
echo "🌐 Step 2: Running Next.js Web API contract tests..."
pnpm --filter web test

# 3. Next.js 15 Production Build Gate
echo ""
echo "🏗️ Step 3: Compiling Next.js 15 production build (0 type/lint errors)..."
pnpm --filter web build

# 4. Manifest Checksum & Task Cohort Verification
echo ""
echo "📑 Step 4: Validating Judged Task Cohort & Demo Manifests..."
if [ -f "apps/sandbox-worker/.venv/bin/activate" ]; then
    source apps/sandbox-worker/.venv/bin/activate
fi
python scripts/validate_demo_manifest.py

# 5. Full Python Test Suites
echo ""
echo "🐍 Step 5: Running Complete Python Pytest Suites..."
export PYTHONPATH="apps/sandbox-worker/src:.:${PYTHONPATH:-}"
pytest tests/execution/ tests/aggregation/ tests/policy/ tests/orchestrator/ tests/security/ tests/ledger/ tests/contracts/ apps/sandbox-worker/tests/ -v

echo ""
echo "🎉 =================================================================="
echo "   ALL MONOREPO QUALITY GATES PASSED! 100% GREEN BUILD."
echo "=================================================================="
