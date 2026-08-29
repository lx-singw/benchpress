"""
State Machine Invariant and Transactional Integrity Tests.
Enforces fail-closed lifecycle transitions for Experiments and Logical Runs.
"""

import pytest
import sys
from pathlib import Path

# Add apps/sandbox-worker/src to pythonpath
worker_src = Path(__file__).resolve().parent.parent.parent / "apps" / "sandbox-worker" / "src"
if str(worker_src) not in sys.path:
    sys.path.insert(0, str(worker_src))

from contracts.states import (
    ExperimentState,
    LogicalRunState,
    VALID_EXPERIMENT_TRANSITIONS,
    VALID_RUN_TRANSITIONS,
    InvalidStateTransitionError,
    validate_experiment_transition,
    validate_run_transition,
)


def test_experiment_valid_transitions():
    """Verify that every explicitly defined valid transition passes validation."""
    for from_state, allowed_targets in VALID_EXPERIMENT_TRANSITIONS.items():
        for target in allowed_targets:
            validate_experiment_transition(from_state, target)


def test_experiment_invalid_transitions():
    """Verify that invalid leap transitions raise InvalidStateTransitionError."""
    invalid_pairs = [
        (ExperimentState.RECEIVED, ExperimentState.PUBLISHED),
        (ExperimentState.RECEIVED, ExperimentState.RECOMMENDED),
        (ExperimentState.PLANNING, ExperimentState.DISPATCHING),
        (ExperimentState.PLAN_APPROVED, ExperimentState.AGGREGATING),
        (ExperimentState.AGGREGATING, ExperimentState.PUBLISHED),
        (ExperimentState.PUBLISHED, ExperimentState.PLANNING),
        (ExperimentState.FAILED_TERMINAL, ExperimentState.RECEIVED),
    ]

    for from_state, invalid_target in invalid_pairs:
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            validate_experiment_transition(from_state, invalid_target)
        assert exc_info.value.from_state == from_state.value
        assert exc_info.value.to_state == invalid_target.value


def test_run_valid_transitions():
    """Verify that every explicitly defined valid run transition passes validation."""
    for from_state, allowed_targets in VALID_RUN_TRANSITIONS.items():
        for target in allowed_targets:
            validate_run_transition(from_state, target)


def test_run_invalid_transitions():
    """Verify that invalid run transitions raise InvalidStateTransitionError."""
    invalid_pairs = [
        (LogicalRunState.PENDING, LogicalRunState.SUCCEEDED),
        (LogicalRunState.CLAIMED, LogicalRunState.SUCCEEDED),
        (LogicalRunState.SUCCEEDED, LogicalRunState.PENDING),
        (LogicalRunState.FAILED_MODEL, LogicalRunState.VERIFYING),
        (LogicalRunState.CANCELLED_BEFORE_START, LogicalRunState.CLAIMED),
    ]

    for from_state, invalid_target in invalid_pairs:
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            validate_run_transition(from_state, invalid_target)
        assert exc_info.value.from_state == from_state.value
        assert exc_info.value.to_state == invalid_target.value


def test_terminal_states_immutable():
    """Assert that terminal states have 0 allowed outgoing transitions."""
    assert len(VALID_EXPERIMENT_TRANSITIONS[ExperimentState.PUBLISHED]) == 0
    assert len(VALID_EXPERIMENT_TRANSITIONS[ExperimentState.FAILED_TERMINAL]) == 0
    assert len(VALID_RUN_TRANSITIONS[LogicalRunState.SUCCEEDED]) == 0
    assert len(VALID_RUN_TRANSITIONS[LogicalRunState.FAILED_MODEL]) == 0
    assert len(VALID_RUN_TRANSITIONS[LogicalRunState.FAILED_ORACLE]) == 0
    assert len(VALID_RUN_TRANSITIONS[LogicalRunState.FAILED_INFRA]) == 0
