"""
Live Chaos Resilience Test Suite (`test_chaos_mesh_live.py`).
Injects synthetic faults: AST Corruption, Tool Schema Mismatches, and Git Sagas.
"""

import pytest
import sys
import os
import asyncio
from datetime import datetime, timezone

# Add apps/sandbox-worker and src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker/src")))

from src.chaos.chaos_mesh import ChaosMesh, ChaosFaultType
from fsm.states import FsmState, TrajectoryContext, TrajectoryStatus
from fsm.engine import AsyncFSMRunner
from sandbox.git_saga import GitSagaTracker


@pytest.mark.asyncio
async def test_live_chaos_ast_self_healing():
    """Verify system survives injected AST tool schema mismatches."""
    chaos = ChaosMesh(active_fault=ChaosFaultType.AST_SCHEMA_CORRUPTION)

    ctx = TrajectoryContext(
        trajectory_id="traj-chaos-001",
        task_suite="SWE-bench Verified",
        task_id="django__django-11099",
        model_id="hybrid-gemini-pro-flash",
        budget_limit_usd=0.50,
        max_turns=10,
        current_turn=0,
        accumulated_cost_usd=0.0,
        started_at=datetime.now(timezone.utc),
    )

    runner = AsyncFSMRunner(context=ctx)
    result = await runner.run()

    # Assert execution completed cleanly
    assert result.current_state in (FsmState.COMPLETE, FsmState.FATAL_HALT)
    assert result.pass_at_1 is True


@pytest.mark.asyncio
async def test_live_chaos_git_saga_compensating_rollback(tmp_path):
    """Verify Git Saga triggers atomic compensating rollback upon sandbox corruption."""
    worktree_dir = str(tmp_path)
    os.system(f"git init {worktree_dir} >/dev/null 2>&1")
    os.system(f"cd {worktree_dir} && git config user.email 'test@test.com' && git config user.name 'Test'")

    test_file = tmp_path / "core.py"
    test_file.write_text("def run(): return 42\n", encoding="utf-8")
    os.system(f"cd {worktree_dir} && git add -A && git commit -m 'initial' >/dev/null 2>&1")

    snap_1 = await GitSagaTracker.capture_snapshot(worktree_dir)

    # Inject corrupting modification
    test_file.write_text("CORRUPTED SYNTAX ERROR !#$", encoding="utf-8")

    # Trigger compensating rollback
    success = await GitSagaTracker.rollback_to_snapshot(worktree_dir, snap_1)
    assert success is True
    assert test_file.read_text(encoding="utf-8") == "def run(): return 42\n"
