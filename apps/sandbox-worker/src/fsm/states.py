"""
13 Formal Enum States and Trajectory Context Models for Benchpress FSM.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class FsmState(str, Enum):
    INIT_ENVIRONMENT = "INIT_ENVIRONMENT"
    FETCH_TASK = "FETCH_TASK"
    PROMPT_PLANNER = "PROMPT_PLANNER"
    VALIDATE_AST = "VALIDATE_AST"
    AST_HEALING = "AST_HEALING"
    EXECUTE_SANDBOX = "EXECUTE_SANDBOX"
    GIT_SNAPSHOT = "GIT_SNAPSHOT"
    FINOPS_SENTINEL = "FINOPS_SENTINEL"
    EVALUATE_REWARD = "EVALUATE_REWARD"
    ROLLBACK_COMPENSATION = "ROLLBACK_COMPENSATION"
    COMPACT_MEMORY = "COMPACT_MEMORY"
    FINALIZE_TELEMETRY = "FINALIZE_TELEMETRY"
    HALT_TERMINAL = "HALT_TERMINAL"


@dataclass
class TurnResult:
    turn_index: int
    state: FsmState
    model_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    turn_cost_usd: float = 0.0
    latency_ms: float = 0.0
    tool_call_name: Optional[str] = None
    tool_call_payload: Optional[Dict[str, Any]] = None
    ast_healed: bool = False
    sandbox_exit_code: int = 0
    sandbox_output: str = ""
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
    current_state: FsmState = FsmState.INIT_ENVIRONMENT
    resolved: bool = False
    early_halted: bool = False
    halt_reason: Optional[str] = None
    turns: List[TurnResult] = field(default_factory=list)
    git_snapshots: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    workspace_path: Optional[str] = None
