"""
End-to-End 13-State Deterministic FSM Transition Verification.
"""

import pytest
from fsm.states import FsmState, TrajectoryContext, TrajectoryStatus
from fsm.engine import AsyncFSMRunner
from fsm.transitions import validate_transition, TransitionGuardViolation


@pytest.mark.asyncio
async def test_full_13_state_progression_lifecycle(sample_trajectory_context):
    """Assert that the trajectory executes and transitions through FSM states to completion."""
    runner = AsyncFSMRunner(context=sample_trajectory_context)
    result = await runner.run()

    # Verify final terminal state
    assert result.current_state in (FsmState.COMPLETE, FsmState.FATAL_HALT)
    assert result.pass_at_1 is True
    assert result.status == TrajectoryStatus.COMPLETED

    # Verify that turns were recorded and processed
    assert len(result.turns) >= 2
    assert result.current_turn >= 2
    assert result.accumulated_cost_usd > 0.0
    assert len(result.git_snapshots) >= 1

    # Verify turn states
    turn_states = [t.state for t in result.turns]
    assert FsmState.SANDBOX_EXECUTION in turn_states or FsmState.EVAL_ASSERTION in turn_states


@pytest.mark.asyncio
async def test_transition_guard_violation():
    """Assert that illegal state transitions are blocked by guard clauses."""
    ctx = TrajectoryContext(
        trajectory_id="guard-test",
        task_suite="SWE_BENCH_VERIFIED",
        task_id="test",
        model_id="gemini-2.5-pro",
    )

    # Illegal transition: IDLE -> SANDBOX_EXECUTION (must go to INITIALIZING first)
    with pytest.raises(TransitionGuardViolation):
        validate_transition(FsmState.IDLE, FsmState.SANDBOX_EXECUTION, ctx)

    # Valid transition: IDLE -> INITIALIZING
    assert validate_transition(FsmState.IDLE, FsmState.INITIALIZING, ctx) is True
