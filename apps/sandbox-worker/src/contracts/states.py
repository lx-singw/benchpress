"""
Benchpress Sovereign State Enums and Transition Matrices.
Enforces transactional integrity and fail-closed state machines across Python worker and orchestrator.
"""

from enum import Enum
from typing import Set, Dict


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state machine transition is attempted."""
    def __init__(self, from_state: str, to_state: str, allowed: Set[str]):
        super().__init__(
            f"Invalid state transition from '{from_state}' to '{to_state}'. "
            f"Allowed target states: {sorted(list(allowed))}"
        )
        self.from_state = from_state
        self.to_state = to_state
        self.allowed = allowed


class ExperimentState(str, Enum):
    RECEIVED = "RECEIVED"
    PLANNING = "PLANNING"
    PLAN_REJECTED = "PLAN_REJECTED"
    PLAN_APPROVED = "PLAN_APPROVED"
    DISPATCHING = "DISPATCHING"
    RUNNING = "RUNNING"
    AGGREGATING = "AGGREGATING"
    REJECTED = "REJECTED"
    ABSTAINED = "ABSTAINED"
    CANARY_PENDING = "CANARY_PENDING"
    CANARY_RUNNING = "CANARY_RUNNING"
    ROLLED_BACK = "ROLLED_BACK"
    RECOMMENDED = "RECOMMENDED"
    PUBLISHED = "PUBLISHED"
    FAILED_TERMINAL = "FAILED_TERMINAL"


class LogicalRunState(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    PROVIDER_RUNNING = "PROVIDER_RUNNING"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_MODEL = "FAILED_MODEL"
    FAILED_ORACLE = "FAILED_ORACLE"
    FAILED_INFRA = "FAILED_INFRA"
    TIMED_OUT = "TIMED_OUT"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    CANCELLED_BEFORE_START = "CANCELLED_BEFORE_START"


class PublicDecision(str, Enum):
    STAY = "STAY"
    TEST_MORE = "TEST MORE"
    SWITCH = "SWITCH"


class InternalOutcome(str, Enum):
    SWITCH_RECOMMENDED = "SWITCH_RECOMMENDED"
    STAY_CHEAPEST_FAILED = "STAY_CHEAPEST_FAILED"
    STAY_BASELINE_SUPERIOR = "STAY_BASELINE_SUPERIOR"
    ABSTAIN_INSUFFICIENT_EVIDENCE = "ABSTAIN_INSUFFICIENT_EVIDENCE"
    REJECTED_QUALITY_FLOOR = "REJECTED_QUALITY_FLOOR"
    REJECTED_BUDGET_EXCEEDED = "REJECTED_BUDGET_EXCEEDED"
    CANARY_ROLLED_BACK = "CANARY_ROLLED_BACK"


class TruthClass(str, Enum):
    BENCHPRESS_MEASURED = "BENCHPRESS_MEASURED"
    OFFICIAL_SPECIFICATION = "OFFICIAL_SPECIFICATION"
    PROJECTED = "PROJECTED"
    ILLUSTRATIVE = "ILLUSTRATIVE"
    DEMO_FIXTURE = "DEMO_FIXTURE"


class WorkflowPhase(str, Enum):
    RESEARCH_PLANNING = "RESEARCH_PLANNING"
    SPECIFICATION = "SPECIFICATION"
    EXECUTION = "EXECUTION"
    REVIEW = "REVIEW"
    REFINEMENT = "REFINEMENT"
    WHOLE_WORKFLOW = "WHOLE_WORKFLOW"


class RiskClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LatencySensitivity(str, Enum):
    INTERACTIVE = "INTERACTIVE"
    NEAR_REALTIME = "NEAR_REALTIME"
    BATCH = "BATCH"
    BACKGROUND = "BACKGROUND"


class FailureReason(str, Enum):
    NONE = "NONE"
    TIMEOUT = "TIMEOUT"
    MAX_TURNS_EXCEEDED = "MAX_TURNS_EXCEEDED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    ORACLE_ASSERTION_FAILED = "ORACLE_ASSERTION_FAILED"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RUNTIME_EXCEPTION = "RUNTIME_EXCEPTION"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    CANCELLED = "CANCELLED"


class EventType(str, Enum):
    MODEL_RELEASE = "MODEL_RELEASE"
    PRICE_CHANGE = "PRICE_CHANGE"
    REASONING_UPGRADE = "REASONING_UPGRADE"
    DEPRECATION_NOTICE = "DEPRECATION_NOTICE"
    MANUAL_TRIGGER = "MANUAL_TRIGGER"
    SCHEDULED_SWEEP = "SCHEDULED_SWEEP"


class SourceKind(str, Enum):
    PROVIDER_CATALOG = "PROVIDER_CATALOG"
    PRICE_INDEX = "PRICE_INDEX"
    ADMIN_CONSOLE = "ADMIN_CONSOLE"
    WEBHOOK = "WEBHOOK"
    SYNTHETIC_REPLAY = "SYNTHETIC_REPLAY"


class UncertaintyMethod(str, Enum):
    WILSON_SCORE = "WILSON_SCORE"
    BOOTSTRAP_PERCENTILE = "BOOTSTRAP_PERCENTILE"
    NOT_COMPUTED_SMALL_SAMPLE = "NOT_COMPUTED_SMALL_SAMPLE"


class StalenessReason(str, Enum):
    MODEL_SNAPSHOT_UPGRADED = "MODEL_SNAPSHOT_UPGRADED"
    PRICE_INDEX_CHANGED = "PRICE_INDEX_CHANGED"
    TOOL_SCHEMA_MUTATED = "TOOL_SCHEMA_MUTATED"
    BENCHMARK_TASK_REVISED = "BENCHMARK_TASK_REVISED"
    QUALITY_REGRESSION_DETECTED = "QUALITY_REGRESSION_DETECTED"
    MANUAL_INVALIDATION = "MANUAL_INVALIDATION"


VALID_EXPERIMENT_TRANSITIONS: Dict[ExperimentState, Set[ExperimentState]] = {
    ExperimentState.RECEIVED: {ExperimentState.PLANNING, ExperimentState.FAILED_TERMINAL},
    ExperimentState.PLANNING: {ExperimentState.PLAN_APPROVED, ExperimentState.PLAN_REJECTED, ExperimentState.FAILED_TERMINAL},
    ExperimentState.PLAN_APPROVED: {ExperimentState.DISPATCHING, ExperimentState.FAILED_TERMINAL},
    ExperimentState.PLAN_REJECTED: {ExperimentState.FAILED_TERMINAL},
    ExperimentState.DISPATCHING: {ExperimentState.RUNNING, ExperimentState.FAILED_TERMINAL},
    ExperimentState.RUNNING: {ExperimentState.AGGREGATING, ExperimentState.FAILED_TERMINAL},
    ExperimentState.AGGREGATING: {
        ExperimentState.REJECTED,
        ExperimentState.ABSTAINED,
        ExperimentState.CANARY_PENDING,
        ExperimentState.FAILED_TERMINAL,
    },
    ExperimentState.CANARY_PENDING: {ExperimentState.CANARY_RUNNING, ExperimentState.FAILED_TERMINAL},
    ExperimentState.CANARY_RUNNING: {
        ExperimentState.ROLLED_BACK,
        ExperimentState.RECOMMENDED,
        ExperimentState.FAILED_TERMINAL,
    },
    ExperimentState.REJECTED: {ExperimentState.PUBLISHED, ExperimentState.FAILED_TERMINAL},
    ExperimentState.ABSTAINED: {ExperimentState.PUBLISHED, ExperimentState.FAILED_TERMINAL},
    ExperimentState.ROLLED_BACK: {ExperimentState.PUBLISHED, ExperimentState.FAILED_TERMINAL},
    ExperimentState.RECOMMENDED: {ExperimentState.PUBLISHED, ExperimentState.FAILED_TERMINAL},
    ExperimentState.PUBLISHED: set(),
    ExperimentState.FAILED_TERMINAL: set(),
}

VALID_RUN_TRANSITIONS: Dict[LogicalRunState, Set[LogicalRunState]] = {
    LogicalRunState.PENDING: {LogicalRunState.CLAIMED, LogicalRunState.CANCELLED_BEFORE_START},
    LogicalRunState.CLAIMED: {LogicalRunState.PROVIDER_RUNNING, LogicalRunState.FAILED_INFRA},
    LogicalRunState.PROVIDER_RUNNING: {
        LogicalRunState.VERIFYING,
        LogicalRunState.FAILED_MODEL,
        LogicalRunState.TIMED_OUT,
        LogicalRunState.BUDGET_EXCEEDED,
        LogicalRunState.FAILED_INFRA,
    },
    LogicalRunState.VERIFYING: {
        LogicalRunState.SUCCEEDED,
        LogicalRunState.FAILED_ORACLE,
        LogicalRunState.TIMED_OUT,
        LogicalRunState.FAILED_INFRA,
    },
    LogicalRunState.SUCCEEDED: set(),
    LogicalRunState.FAILED_MODEL: set(),
    LogicalRunState.FAILED_ORACLE: set(),
    LogicalRunState.FAILED_INFRA: set(),
    LogicalRunState.TIMED_OUT: set(),
    LogicalRunState.BUDGET_EXCEEDED: set(),
    LogicalRunState.CANCELLED_BEFORE_START: set(),
}


def validate_experiment_transition(current_state: ExperimentState, target_state: ExperimentState) -> None:
    """Validate that transition from current_state to target_state is legal."""
    allowed = VALID_EXPERIMENT_TRANSITIONS.get(current_state, set())
    if target_state not in allowed:
        raise InvalidStateTransitionError(
            from_state=current_state.value,
            to_state=target_state.value,
            allowed={s.value for s in allowed},
        )


def validate_run_transition(current_state: LogicalRunState, target_state: LogicalRunState) -> None:
    """Validate that transition from current_state to target_state is legal."""
    allowed = VALID_RUN_TRANSITIONS.get(current_state, set())
    if target_state not in allowed:
        raise InvalidStateTransitionError(
            from_state=current_state.value,
            to_state=target_state.value,
            allowed={s.value for s in allowed},
        )
