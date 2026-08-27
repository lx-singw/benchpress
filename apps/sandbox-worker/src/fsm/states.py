"""
13 Formal FSM Enum States and Turn State Models for Benchpress Trajectory Engine.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class FsmState(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    PERCEPTION = "PERCEPTION"
    PREDICTIVE_SENTINEL_EVAL = "PREDICTIVE_SENTINEL_EVAL"
    REASONING_PLANNER = "REASONING_PLANNER"
    TOOL_DISPATCH_CODER = "TOOL_DISPATCH_CODER"
    SAGA_SNAPSHOT_CAPTURE = "SAGA_SNAPSHOT_CAPTURE"
    AST_VALIDATION = "AST_VALIDATION"
    SUPERVISOR_AST_HEAL = "SUPERVISOR_AST_HEAL"
    SAGA_COMPENSATING_ROLLBACK = "SAGA_COMPENSATING_ROLLBACK"
    SANDBOX_EXECUTION = "SANDBOX_EXECUTION"
    EVAL_ASSERTION = "EVAL_ASSERTION"
    TELEMETRY_FLUSH = "TELEMETRY_FLUSH"

    # Terminal outcomes
    COMPLETE = "COMPLETE"
    FATAL_HALT = "FATAL_HALT"


class TrajectoryStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    EARLY_HALTED = "EARLY_HALTED"
    TIMEOUT = "TIMEOUT"


@dataclass
class TurnRecord:
    turn_index: int
    state: FsmState
    model_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    turn_cost_usd: float = 0.0
    cumulative_cost_usd: float = 0.0
    latency_ms: float = 0.0
    tool_call_name: Optional[str] = None
    tool_call_payload: Optional[Dict[str, Any]] = None
    ast_healed: bool = False
    ast_healing_trace: Optional[str] = None
    sandbox_exit_code: int = 0
    sandbox_stdout: str = ""
    sandbox_stderr: str = ""
    git_tree_hash: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TrajectoryContext:
    trajectory_id: str
    task_suite: str
    task_id: str
    model_id: str
    budget_limit_usd: float = 2.00
    max_turns: int = 20
    current_turn: int = 0
    accumulated_cost_usd: float = 0.0
    current_state: FsmState = FsmState.IDLE
    status: TrajectoryStatus = TrajectoryStatus.RUNNING
    pass_at_1: bool = False
    resolved: bool = False
    early_halted: bool = False
    halt_reason: Optional[str] = None
    current_plan: Optional[str] = None
    active_coder_model: str = "gemini-2.5-flash"
    consecutive_tool_failures: int = 0
    turns: List[TurnRecord] = field(default_factory=list)
    git_snapshots: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    workspace_path: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
