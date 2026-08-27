"""
Fault Injection Chaos & Git-Tree Compensation Rollback Test Suite.
"""

import os
import pytest
import asyncio
from typing import List, Dict, Any

from fsm.states import FsmState, TrajectoryContext
from fsm.engine import AsyncFsmEngine
from sandbox.runner import SandboxRunner
from supervisor.ast_healer import AstHealer
from sentinel.velocity_sentinel import VelocitySentinel
from memory.memory_bus import MemoryBus
from telemetry.bq_streamer import BigQueryStreamer


@pytest.mark.asyncio
async def test_git_tree_atomic_rollback_on_test_regression():
    """Fault injection: Mutate code, inject regression, verify atomic git write-tree rollback."""
    runner = SandboxRunner()
    workspace = await runner.prepare_workspace(task_id="chaos_test_01")

    app_py_path = os.path.join(workspace, "app.py")
    
    # 1. Baseline state
    with open(app_py_path, "w") as f:
        f.write("def baseline_fn():\n    return 'PRISTINE_STATE'\n")

    # Record git tree SHA
    snapshot_sha = await runner.git_write_tree(cwd=workspace)
    assert snapshot_sha is not None
    assert len(snapshot_sha) > 0

    # 2. Chaos Injection: Break the code (regression)
    with open(app_py_path, "w") as f:
        f.write("def baseline_fn():\n    return 'REGRESSIVE_BROKEN_STATE'\n")

    with open(app_py_path, "r") as f:
        assert "REGRESSIVE_BROKEN_STATE" in f.read()

    # 3. Compensating Saga: Rollback to snapshot
    rollback_success = await runner.rollback_to_snapshot(snapshot_sha, cwd=workspace)
    assert rollback_success is True

    # 4. Verify pristine workspace restoration
    with open(app_py_path, "r") as f:
        restored_content = f.read()
        assert "PRISTINE_STATE" in restored_content
        assert "REGRESSIVE_BROKEN_STATE" not in restored_content


@pytest.mark.asyncio
async def test_fsm_engine_compensation_saga_transition():
    """Verify 13-state FSM enters ROLLBACK_COMPENSATION upon exit code 2."""
    class RegressionMockRunner(SandboxRunner):
        async def execute_command(self, command: str, cwd: str = None, timeout_seconds: float = 30.0):
            # Simulate non-recoverable test regression
            return {"exit_code": 2, "output": "AssertionError: regression detected in test suite"}

    ctx = TrajectoryContext(
        trajectory_id="traj-chaos-002",
        task_suite="SWE_BENCH_VERIFIED",
        task_id="chaos-task-02",
        model_id="gemini-2.5-pro",
        budget_limit_usd=2.00,
        max_turns=3,
    )

    recorded_states: List[FsmState] = []

    async def record_event(event: Dict[str, Any]):
        if event.get("type") == "STATE_CHANGE":
            recorded_states.append(event.get("state"))

    mock_runner = RegressionMockRunner()
    engine = AsyncFsmEngine(context=ctx, sandbox_runner=mock_runner, on_event=record_event)
    result = await engine.run_trajectory()

    # Assert that ROLLBACK_COMPENSATION state was triggered
    assert FsmState.ROLLBACK_COMPENSATION.value in recorded_states
    assert FsmState.HALT_TERMINAL.value in recorded_states
    assert len(result.turns) > 0


@pytest.mark.asyncio
async def test_fsm_websocket_turn_event_broadcasting():
    """Verify FSM emits real-time STATE_CHANGE, TURN_COMPLETED, and TRAJECTORY_FINISHED events."""
    ctx = TrajectoryContext(
        trajectory_id="traj-ws-broadcast-003",
        task_suite="SWE_BENCH_VERIFIED",
        task_id="ws-task-03",
        model_id="gemini-2.5-flash",
        budget_limit_usd=1.00,
        max_turns=2,
    )

    events_received: List[Dict[str, Any]] = []

    async def capture_event(event: Dict[str, Any]):
        events_received.append(event)

    engine = AsyncFsmEngine(context=ctx, on_event=capture_event)
    await engine.run_trajectory()

    event_types = [e.get("type") for e in events_received]
    assert "STATE_CHANGE" in event_types
    assert "TURN_COMPLETED" in event_types
    assert "TRAJECTORY_FINISHED" in event_types

    turn_events = [e for e in events_received if e.get("type") == "TURN_COMPLETED"]
    assert len(turn_events) >= 1
    assert turn_events[0]["trajectory_id"] == "traj-ws-broadcast-003"
    assert "turn" in turn_events[0]
    assert turn_events[0]["turn"]["model_id"] == "gemini-2.5-flash"
