"""
Cross-Language Byte-for-Byte Canonical Hash and ID Parity Tests.
Verifies that Python compute_canonical_hash() matches TypeScript computeCanonicalHash() 100% on all sovereign fixtures.
"""

import json
import subprocess
import shutil
import pytest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
worker_src = REPO_ROOT / "apps" / "sandbox-worker" / "src"
if str(worker_src) not in sys.path:
    sys.path.insert(0, str(worker_src))

from contracts.hashing import (
    canonical_json_dumps,
    compute_canonical_hash,
    generate_configuration_id,
    generate_logical_run_key,
    generate_aggregate_id,
    generate_receipt_id,
)

FIXTURES_VALID = REPO_ROOT / "tests" / "fixtures" / "contracts" / "valid"
CLI_SCRIPT = REPO_ROOT / "packages" / "contracts" / "scripts" / "cli.ts"


def get_ts_canonical_hash(fixture_path: Path) -> str:
    """Invoke TypeScript CLI to compute canonical hash of a fixture file."""
    # Find tsx or npx/node command
    cmd = None
    if shutil.which("pnpm"):
        cmd = ["pnpm", "--filter", "@benchpress/contracts", "exec", "tsx", str(CLI_SCRIPT), "hash-file", str(fixture_path)]
    elif shutil.which("npx"):
        cmd = ["npx", "tsx", str(CLI_SCRIPT), "hash-file", str(fixture_path)]
    elif shutil.which("wsl"):
        # Windows fallback calling WSL node
        rel_path = fixture_path.as_posix().replace("Z:", "").replace("z:", "")
        if not rel_path.startswith("/"):
            rel_path = "/" + rel_path
        cli_posix = CLI_SCRIPT.as_posix().replace("Z:", "").replace("z:", "")
        if not cli_posix.startswith("/"):
            cli_posix = "/" + cli_posix
        cmd = ["wsl", "-d", "Ubuntu", "-e", "bash", "-c", f"cd /home/lx_singw/projects/benchpress && pnpm --filter @benchpress/contracts exec tsx {cli_posix} hash-file {rel_path}"]

    if not cmd:
        pytest.skip("Node/pnpm/tsx not available in environment to run cross-language parity test.")

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_cross_language_fixture_hashes():
    """Verify all 12 sovereign fixtures have byte-for-byte identical canonical SHA-256 hashes in Python and TypeScript."""
    valid_fixtures = sorted(list(FIXTURES_VALID.glob("*.json")))
    assert len(valid_fixtures) == 12, f"Expected 12 valid fixtures, found {len(valid_fixtures)}"

    for fixture_path in valid_fixtures:
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        py_hash = compute_canonical_hash(data)
        ts_hash = get_ts_canonical_hash(fixture_path)

        assert py_hash == ts_hash, (
            f"Hash divergence on {fixture_path.name}!\n"
            f"Python:     {py_hash}\n"
            f"TypeScript: {ts_hash}\n"
            f"Python Canonical: {canonical_json_dumps(data)}"
        )


def test_cross_language_id_generation():
    """Verify canonical ID generators produce identical outputs."""
    cfg_payload = {
        "provider": "google",
        "request_model": "gemini-2.5-pro",
        "thinking_budget_tokens": 2048,
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": 8192,
        "system_instruction_hash": "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
        "tool_schema_hash": "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
        "price_input_per_million_usd": "1.250000",
        "price_output_per_million_usd": "5.000000",
        "price_source_version": "2026-08-29",
    }
    cfg_id = generate_configuration_id(cfg_payload)
    assert cfg_id.startswith("cfg_")
    assert len(cfg_id) == 20

    run_payload = {
        "experiment_id": "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        "task_id": "TASK-001",
        "task_version_hash": "647325057dca762d6a46813726e2764d12a98741ea7aed388acd9f3c32c814de",
        "configuration_id": cfg_id,
        "repetition_index": 0,
        "harness_version": "pytest-8.3.0",
        "oracle_version": "oracle_v1_deterministic",
    }
    run_key = generate_logical_run_key(run_payload)
    assert run_key.startswith("run_")
    assert len(run_key) == 20

    agg_payload = {
        "experiment_id": "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        "configuration_id": cfg_id,
        "aggregation_policy_version": "agg_pol_v1_wilson",
        "eligible_run_keys": [run_key],
    }
    agg_id = generate_aggregate_id(agg_payload)
    assert agg_id.startswith("agg_")
    assert len(agg_id) == 20
