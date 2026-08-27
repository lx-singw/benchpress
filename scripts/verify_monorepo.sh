#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Full Monorepo Quality Gate (Test + Build + Typecheck)
# ==============================================================================
set -euo pipefail

echo "🛡️ =================================================================="
echo "   BENCHPRESS: FULL MONOREPO QUALITY & VERIFICATION GATE"
echo "=================================================================="

# 0. Zero-Secret Leakage Pre-Commit Armor Scan
echo ""
echo "🔒 Step 0: Running High-Entropy Secret Leak Scanner..."
python3 scripts/secret_scanner.py || python scripts/secret_scanner.py

# 1. Run Turborepo Monorepo Build
echo ""
echo "📦 Step 1: Building all TypeScript packages and Next.js 15 apps..."
pnpm turbo run build

# 2. Run Python Test Suites
echo ""
echo "🐍 Step 2: Running all Python Pytest suites..."
if [ -f "apps/sandbox-worker/.venv/bin/activate" ]; then
    source apps/sandbox-worker/.venv/bin/activate
fi

echo "  • Sandbox Worker Tests:"
(cd apps/sandbox-worker && (pytest -v || python -m pytest -v))

echo "  • Python SDK Tests:"
(cd packages/sdk-python && (pytest -v || python -m pytest -v))

echo "  • Enterprise, Safeguards, Autonomous, Live E2E & Chaos Resilience Tests:"
pytest -v tests/enterprise/ tests/safeguards/ tests/autonomous/ tests/e2e/ tests/chaos/ || \
python -m pytest -v tests/enterprise/ tests/safeguards/ tests/autonomous/ tests/e2e/ tests/chaos/

echo ""
echo "🎉 =================================================================="
echo "   ALL MONOREPO QUALITY GATES PASSED! 100% GREEN BUILD."
echo "=================================================================="
