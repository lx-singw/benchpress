"""
Pytest Test Suite for 13-State Deterministic FSM Engine & Components.
"""

import pytest
import asyncio
from fsm.states import FsmState, TrajectoryContext
from fsm.engine import AsyncFsmEngine
from supervisor.ast_healer import AstHealer
from sentinel.velocity_sentinel import VelocitySentinel
from memory.memory_bus import MemoryBus
from sandbox.runner import SandboxRunner
from telemetry.bq_streamer import BigQueryStreamer


@pytest.mark.asyncio
async def test_ast_healer_validation_and_repair():
    healer = AstHealer()

    # Valid payload
    valid_payload = {"tool": "edit_file", "path": "test.py", "replacement": "x = 1\n"}
    valid, err = healer.validate_tool_call(valid_payload)
    assert valid is True
    assert err is None

    # Invalid syntax in replacement
    invalid_payload = {"tool": "edit_file", "path": "test.py", "replacement": "def invalid syntax :("}
    valid, err = healer.validate_tool_call(invalid_payload)
    assert valid is False
    assert "SyntaxError" in err

    # Repair schema mismatch (e.g. "file_path" -> "path")
    broken_schema = {"name": "edit_file", "file_path": "test.py", "replacement": "x = 2"}
    repaired, healed = await healer.repair_payload(broken_schema, "Schema mismatch")
    assert healed is True
    assert repaired["tool"] == "edit_file"
    assert repaired["path"] == "test.py"


@pytest.mark.asyncio
async def test_velocity_sentinel_hard_cap_and_markov():
    sentinel = VelocitySentinel(budget_limit_usd=1.00, early_halt_turn_threshold=5)

    # Turn 1: within budget
    d1 = sentinel.evaluate_turn(1, 0.05, 1000)
    assert d1.action == "CONTINUE"

    # Turn 5 with high cost rate (> budget limit)
    d5 = sentinel.evaluate_turn(5, 0.85, 3000)
    assert d5.action == "EARLY_HALT"

    # Hard cap exceeded
    d_cap = sentinel.evaluate_turn(2, 1.20, 1000)
    assert d_cap.action == "EARLY_HALT"


@pytest.mark.asyncio
async def test_memory_bus_compaction():
    bus = MemoryBus()
    await bus.set_working_context("small_key", "hello")
    await bus.set_working_context("large_output", "A" * 500)

    ratio = await bus.compact_working_memory()
    assert ratio > 0.0
    assert len(bus.l2_compacted_history) == 1


@pytest.mark.asyncio
async def test_fsm_engine_trajectory_lifecycle():
    ctx = TrajectoryContext(
        trajectory_id="test-traj-001",
        task_suite="SWE_BENCH_VERIFIED",
        task_id="django-test-01",
        model_id="gemini-2.5-pro",
        budget_limit_usd=2.00,
        max_turns=3,
    )
    engine = AsyncFsmEngine(context=ctx)
    result = await engine.run_trajectory()

    assert result.current_state in (FsmState.HALT_TERMINAL, FsmState.FINALIZE_TELEMETRY)
    assert len(result.turns) > 0
    assert result.current_turn >= 1
