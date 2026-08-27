"""
Deterministic State Transition Matrix & Guard Clauses for Benchpress FSM.
"""

from typing import Set, Dict, Optional
from .states import FsmState, TrajectoryContext


# Formal 13-State Transition Graph
STATE_TRANSITION_GRAPH: Dict[FsmState, Set[FsmState]] = {
    FsmState.IDLE: {FsmState.INITIALIZING, FsmState.FATAL_HALT},
    FsmState.INITIALIZING: {FsmState.PERCEPTION, FsmState.FATAL_HALT},
    FsmState.PERCEPTION: {
        FsmState.PREDICTIVE_SENTINEL_EVAL,
        FsmState.REASONING_PLANNER,
        FsmState.FATAL_HALT,
    },
    FsmState.PREDICTIVE_SENTINEL_EVAL: {
        FsmState.REASONING_PLANNER,
        FsmState.TELEMETRY_FLUSH,
        FsmState.FATAL_HALT,
    },
    FsmState.REASONING_PLANNER: {
        FsmState.TOOL_DISPATCH_CODER,
        FsmState.TELEMETRY_FLUSH,
        FsmState.FATAL_HALT,
    },
    FsmState.TOOL_DISPATCH_CODER: {
        FsmState.SAGA_SNAPSHOT_CAPTURE,
        FsmState.AST_VALIDATION,
        FsmState.FATAL_HALT,
    },
    FsmState.SAGA_SNAPSHOT_CAPTURE: {
        FsmState.AST_VALIDATION,
        FsmState.SANDBOX_EXECUTION,
        FsmState.FATAL_HALT,
    },
    FsmState.AST_VALIDATION: {
        FsmState.SANDBOX_EXECUTION,
        FsmState.SUPERVISOR_AST_HEAL,
        FsmState.SAGA_COMPENSATING_ROLLBACK,
        FsmState.FATAL_HALT,
    },
    FsmState.SUPERVISOR_AST_HEAL: {
        FsmState.AST_VALIDATION,
        FsmState.SANDBOX_EXECUTION,
        FsmState.SAGA_COMPENSATING_ROLLBACK,
        FsmState.FATAL_HALT,
    },
    FsmState.SAGA_COMPENSATING_ROLLBACK: {
        FsmState.REASONING_PLANNER,
        FsmState.TOOL_DISPATCH_CODER,
        FsmState.TELEMETRY_FLUSH,
        FsmState.FATAL_HALT,
    },
    FsmState.SANDBOX_EXECUTION: {
        FsmState.EVAL_ASSERTION,
        FsmState.SAGA_COMPENSATING_ROLLBACK,
        FsmState.PERCEPTION,
        FsmState.PREDICTIVE_SENTINEL_EVAL,
        FsmState.REASONING_PLANNER,
        FsmState.FATAL_HALT,
    },
    FsmState.EVAL_ASSERTION: {
        FsmState.TELEMETRY_FLUSH,
        FsmState.PERCEPTION,
        FsmState.PREDICTIVE_SENTINEL_EVAL,
        FsmState.REASONING_PLANNER,
        FsmState.FATAL_HALT,
    },
    FsmState.TELEMETRY_FLUSH: {
        FsmState.COMPLETE,
        FsmState.FATAL_HALT,
    },
    FsmState.COMPLETE: set(),
    FsmState.FATAL_HALT: set(),
}


class TransitionGuardViolation(Exception):
    """Raised when an illegal FSM transition is attempted."""
    pass


def validate_transition(from_state: FsmState, to_state: FsmState, ctx: Optional[TrajectoryContext] = None) -> bool:
    """Ensure that the state transition obeys the deterministic state graph and guard clauses."""
    allowed = STATE_TRANSITION_GRAPH.get(from_state, set())
    if to_state not in allowed:
        raise TransitionGuardViolation(
            f"Illegal FSM transition from {from_state.value} to {to_state.value}. Allowed targets: {[s.value for s in allowed]}"
        )

    # Invariant Guard Clauses
    if ctx:
        if to_state != FsmState.TELEMETRY_FLUSH and to_state != FsmState.FATAL_HALT:
            if ctx.accumulated_cost_usd >= ctx.budget_limit_usd:
                raise TransitionGuardViolation(
                    f"Budget cap violation: accumulated cost ${ctx.accumulated_cost_usd:.4f} >= limit ${ctx.budget_limit_usd:.2f}"
                )
            if ctx.current_turn > ctx.max_turns:
                raise TransitionGuardViolation(
                    f"Turn limit violation: turn {ctx.current_turn} > max turns {ctx.max_turns}"
                )

    return True
