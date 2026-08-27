#!/usr/bin/env bash
# ==============================================================================
# Benchpress: Automated Live Chaos Mesh & Fault Injection Runner
# ==============================================================================
set -euo pipefail

echo "🧪 Running Benchpress Chaos Resilience Mesh..."

source apps/sandbox-worker/.venv/bin/activate || true

pytest -v tests/chaos/test_chaos_mesh_live.py

echo "✅ Chaos mesh test completed: All fault injections survived with zero data loss."
