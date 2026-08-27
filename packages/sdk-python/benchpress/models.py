"""
Pydantic v2 Request and Response Data Models for benchpress-python.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


TaskType = Literal["code_bug_fix", "architectural_refactor", "financial_extraction", "quick_edit", "bug_fix"]
CodebaseLanguage = Literal["python", "typescript", "rust", "go", "java"]


class RoutingRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    task_type: str = "code_bug_fix"
    codebase_language: str = "python"
    current_model: str = "claude-3-7-sonnet"
    max_budget_per_task_usd: Optional[float] = 0.50
    budget_limit_usd: Optional[float] = None
    estimated_prompt_tokens: Optional[int] = 15000
    estimated_completion_tokens: Optional[int] = 2500
    pareto_weights: Optional[Dict[str, float]] = None


class ProxyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    baseUrl: Optional[str] = "http://localhost:3000/api/v1/proxy"
    modelHeader: Optional[str] = "x-benchpress-route"


class RoutingRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: Optional[str] = "success"
    recommendedStrategy: Optional[str] = Field(default="HYBRID_CHOREOGRAPHY", alias="recommended_strategy")
    plannerModel: Optional[str] = Field(default="gemini-2.5-pro", alias="planner_model")
    coderModel: Optional[str] = Field(default="gemini-2.5-flash", alias="coder_model")
    projectedCprUsd: Optional[float] = Field(default=0.185, alias="projected_cpr_usd")
    currentModelCprUsd: Optional[float] = Field(default=1.48, alias="current_model_cpr_usd")
    projectedSavingsPct: Optional[float] = Field(default=87.5, alias="projected_savings_pct")
    passAt1EstimatePct: Optional[float] = Field(default=71.2, alias="pass_at_1_estimate_pct")
    confidenceScore: Optional[float] = Field(default=0.94, alias="confidence_score")
    estimatedTurns: Optional[int] = Field(default=9, alias="estimated_turns")
    rationale: Optional[str] = "Optimal hybrid route"
    evaluatedAt: Optional[str] = Field(default=None, alias="evaluated_at")
    proxyConfig: Optional[ProxyConfig] = None

    @property
    def recommended_strategy(self) -> str:
        return self.recommendedStrategy or "HYBRID_CHOREOGRAPHY"

    @property
    def planner_model(self) -> str:
        return self.plannerModel or "gemini-2.5-pro"

    @property
    def coder_model(self) -> str:
        return self.coderModel or "gemini-2.5-flash"

    @property
    def projected_cpr_usd(self) -> float:
        return self.projectedCprUsd or 0.185

    @property
    def projected_savings_pct(self) -> float:
        return self.projectedSavingsPct or 87.5

    @property
    def confidence_score(self) -> float:
        return self.confidenceScore or 0.94


class RoutingRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: str = "success"
    latency_ms: Optional[float] = 5.0
    timestamp: Optional[str] = None
    recommendation: RoutingRecommendation


class BenchmarkRow(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    modelId: Optional[str] = Field(default="gemini-2.5-pro", alias="model_id")
    modelName: Optional[str] = Field(default="Gemini 2.5 Pro", alias="model_name")
    provider: Optional[str] = "Google"
    taskSuite: Optional[str] = Field(default="SWE-bench Verified", alias="task_suite")
    passRatePct: Optional[float] = Field(default=70.0, alias="pass_rate_pct")
    cprUsd: Optional[float] = Field(default=0.42, alias="cpr_usd")
    meanTurns: Optional[float] = Field(default=10.0, alias="mean_turns")
    meanLatencySeconds: Optional[float] = Field(default=15.0, alias="mean_latency_seconds")
    astHealingCount: Optional[int] = Field(default=10, alias="ast_healing_count")
    tokenVelocityKps: Optional[float] = Field(default=4.0, alias="token_velocity_kps")
    paretoFrontier: Optional[bool] = Field(default=True, alias="pareto_frontier")

    @property
    def model_id(self) -> str:
        return self.modelId or ""

    @property
    def model_name(self) -> str:
        return self.modelName or ""

    @property
    def task_suite(self) -> str:
        return self.taskSuite or ""

    @property
    def pass_rate_pct(self) -> float:
        return self.passRatePct or 0.0

    @property
    def cpr_usd(self) -> float:
        return self.cprUsd or 0.0

    @property
    def mean_turns(self) -> float:
        return self.meanTurns or 0.0

    @property
    def mean_latency_seconds(self) -> float:
        return self.meanLatencySeconds or 0.0

    @property
    def pareto_frontier(self) -> bool:
        return bool(self.paretoFrontier)


class BenchmarkListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: str = "success"
    count: Optional[int] = 0
    timestamp: Optional[str] = None
    queriedAt: Optional[str] = None
    data: List[BenchmarkRow] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def unify_data_field(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "benchmarks" in values and "data" not in values:
                values["data"] = values["benchmarks"]
            if "data" in values and not values.get("count"):
                values["count"] = len(values["data"])
        return values


class DispatchTrajectoryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    taskSuite: Optional[str] = Field(default="SWE_BENCH_VERIFIED", alias="task_suite")
    taskId: Optional[str] = Field(default="", alias="task_id")
    modelId: Optional[str] = Field(default="gemini-2.5-pro", alias="model_id")
    budgetLimitUsd: Optional[float] = Field(default=2.00, alias="budget_limit_usd")
    maxTurns: Optional[int] = Field(default=20, alias="max_turns")


class DispatchTrajectoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: str = "queued"
    trajectoryId: Optional[str] = Field(default="traj-001", alias="trajectory_id")
    state: Optional[str] = "QUEUED"
    queueName: Optional[str] = Field(default="trajectory-execution-queue", alias="queue_name")
    taskSuite: Optional[str] = Field(default="SWE_BENCH_VERIFIED", alias="task_suite")
    taskId: Optional[str] = Field(default="", alias="task_id")
    modelId: Optional[str] = Field(default="gemini-2.5-pro", alias="model_id")
    budgetLimitUsd: Optional[float] = Field(default=2.00, alias="budget_limit_usd")
    maxTurns: Optional[int] = Field(default=20, alias="max_turns")
    traceUrl: Optional[str] = Field(default=None, alias="trace_url")
    estimatedDispatchLatencyMs: Optional[float] = 12.0

    @property
    def status_url(self) -> str:
        return f"/api/v1/trajectories/{self.trajectory_id}"

    @property
    def queue_name(self) -> str:
        return self.queueName or "trajectory-execution-queue"

    @property
    def trajectory_id(self) -> str:
        return self.trajectoryId or ""

    @property
    def task_suite(self) -> str:
        return self.taskSuite or ""

    @property
    def task_id(self) -> str:
        return self.taskId or ""

    @property
    def model_id(self) -> str:
        return self.modelId or ""

    @property
    def budget_limit_usd(self) -> float:
        return self.budgetLimitUsd or 2.00

    @property
    def max_turns(self) -> int:
        return self.maxTurns or 20

    @property
    def trace_url(self) -> Optional[str]:
        return self.traceUrl


class TurnTrace(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    turn_index: int
    state: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    turn_cost_usd: float
    cumulative_cost_usd: float
    latency_ms: float
    tool_call_name: Optional[str] = None
    ast_healed: bool = False
    sandbox_exit_code: int = 0


class TrajectoryDetails(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    trajectory_id: str
    task_suite: str
    task_id: str
    model_id: str
    status: str
    current_state: str
    pass_at_1: bool
    resolved: bool
    total_cost_usd: float
    cpr_usd: float
    trajectory_bloat_ratio: float
    ast_heal_count: int
    git_snapshots_count: int
    turns_count: int
    started_at: str
    completed_at: Optional[str] = None
    turns: List[TurnTrace] = Field(default_factory=list)


class TrajectoryStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: str
    data: TrajectoryDetails
