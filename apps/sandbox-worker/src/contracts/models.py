"""
Pydantic V2 Strict Projections of the Sovereign Benchpress JSON Schemas.
Fail-closed validation with extra="forbid" and cross-language deterministic regexes.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from .states import (
    ExperimentState,
    LogicalRunState,
    PublicDecision,
    InternalOutcome,
    TruthClass,
    WorkflowPhase,
    RiskClass,
    LatencySensitivity,
    FailureReason,
    EventType,
    SourceKind,
    UncertaintyMethod,
    StalenessReason,
)

# Common Regex Patterns
ULID_REGEX = r"^[0-9A-HJKMNP-TV-Z]{26}$"
SHA256_16_REGEX = r"^[a-f0-9]{16}$"
SHA256_40_REGEX = r"^[a-f0-9]{40}$"
SHA256_64_REGEX = r"^[a-f0-9]{64}$"
RFC3339_MILLIS_REGEX = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$"
DECIMAL_USD_REGEX = r"^[0-9]+\.[0-9]{6}$"

EVENT_ID_REGEX = r"^evt_[0-9A-HJKMNP-TV-Z]{26}$"
CORRELATION_ID_REGEX = r"^corr_[0-9A-HJKMNP-TV-Z]{26}$"
EXPERIMENT_ID_REGEX = r"^exp_[0-9A-HJKMNP-TV-Z]{26}$"
CONFIGURATION_ID_REGEX = r"^cfg_[a-f0-9]{16}$"
FINGERPRINT_ID_REGEX = r"^fp_[a-f0-9]{16}$"
PLAN_ID_REGEX = r"^plan_[a-f0-9]{16}$"
LOGICAL_RUN_KEY_REGEX = r"^run_[a-f0-9]{16}$"
ATTEMPT_ID_REGEX = r"^att_[0-9A-HJKMNP-TV-Z]{26}$"
AGGREGATE_ID_REGEX = r"^agg_[a-f0-9]{16}$"
POLICY_VERSION_REGEX = r"^pol_[0-9A-HJKMNP-TV-Z]{26}$"
DECISION_ID_REGEX = r"^dec_[0-9A-HJKMNP-TV-Z]{26}$"
RECEIPT_ID_REGEX = r"^rcpt_[a-f0-9]{16}$"
CANARY_ID_REGEX = r"^cnry_[0-9A-HJKMNP-TV-Z]{26}$"


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# 1. ChangeEvent
class ChangeEvent(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    event_id: str = Field(..., pattern=EVENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    event_type: EventType
    source_kind: SourceKind
    source_reference: str = Field(..., min_length=1)
    target_provider: str = Field(..., min_length=1)
    target_model_family: str = Field(..., min_length=1)
    changed_fields: List[str]
    source_checksum: str = Field(..., pattern=SHA256_64_REGEX)
    effective_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
    retrieved_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
    baseline_policy_version: str = Field(..., pattern=POLICY_VERSION_REGEX)
    baseline_configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    max_spend_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    deadline_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
    initiator: str = Field(..., min_length=1)
    replay: bool
    replay_label: Optional[str] = None
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 2. TaskFingerprint
class TaskFingerprint(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    fingerprint_id: str = Field(..., pattern=FINGERPRINT_ID_REGEX)
    task_family: str = Field(..., min_length=1)
    workflow_phase: WorkflowPhase
    language: str = Field(..., min_length=1)
    framework: str = Field(..., min_length=1)
    ast_depth: int = Field(..., ge=0)
    cyclomatic_complexity: int = Field(..., ge=0)
    context_token_weight: int = Field(..., ge=0)
    required_tools: List[str]
    risk_class: RiskClass
    latency_sensitivity: LatencySensitivity
    feature_vector_hash: str = Field(..., pattern=SHA256_64_REGEX)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 3. NativeConfiguration
class NativeConfiguration(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    provider: str = Field(..., min_length=1)
    request_model: str = Field(..., min_length=1)
    resolved_model_snapshot: Optional[str] = None
    thinking_budget_tokens: int = Field(..., ge=0)
    temperature: float = Field(..., ge=0.0, le=2.0)
    top_p: float = Field(..., ge=0.0, le=1.0)
    max_output_tokens: int = Field(..., ge=1)
    system_instruction_hash: str = Field(..., pattern=SHA256_64_REGEX)
    tool_schema_hash: str = Field(..., pattern=SHA256_64_REGEX)
    price_input_per_million_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    price_output_per_million_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    price_source_version: str = Field(..., min_length=1)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 4. ExperimentPlan
class ExperimentPlan(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    plan_id: str = Field(..., pattern=PLAN_ID_REGEX)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    event_id: str = Field(..., pattern=EVENT_ID_REGEX)
    fingerprint_id: str = Field(..., pattern=FINGERPRINT_ID_REGEX)
    baseline_configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    candidate_configuration_ids: List[str] = Field(..., min_length=1)
    task_cohort_version: str = Field(..., min_length=1)
    selected_task_ids: List[str] = Field(..., min_length=1)
    repetitions_per_task: int = Field(..., ge=1)
    max_matrix_spend_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    reserved_budget_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    per_run_timeout_seconds: int = Field(..., ge=1)
    max_turns_per_run: int = Field(..., ge=1)
    quality_floor_pass_rate: float = Field(..., ge=0.0, le=1.0)
    early_stop_consecutive_failures: int = Field(..., ge=1)
    planner_model: str = Field(..., min_length=1)
    plan_policy_version: str = Field(..., min_length=1)
    planning_rationale: str = Field(..., min_length=1)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 5. RunManifest
class RunManifest(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    logical_run_key: str = Field(..., pattern=LOGICAL_RUN_KEY_REGEX)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    task_id: str = Field(..., min_length=1)
    task_version_hash: str = Field(..., pattern=SHA256_64_REGEX)
    repetition_index: int = Field(..., ge=0)
    harness_version: str = Field(..., min_length=1)
    oracle_version: str = Field(..., min_length=1)
    tool_allowlist: List[str] = Field(..., min_length=1)
    path_allowlist: List[str]
    max_turns: int = Field(..., ge=1)
    timeout_seconds: int = Field(..., ge=1)
    max_spend_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 6. RunResult
class RunResult(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    logical_run_key: str = Field(..., pattern=LOGICAL_RUN_KEY_REGEX)
    attempt_id: str = Field(..., pattern=ATTEMPT_ID_REGEX)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    task_id: str = Field(..., min_length=1)
    repetition_index: int = Field(..., ge=0)
    run_state: LogicalRunState
    resolved: bool
    failure_reason: FailureReason
    failure_details: Optional[str] = None
    turns_executed: int = Field(..., ge=0)
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    cached_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    observed_cost_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    price_version: str = Field(..., min_length=1)
    latency_ms: int = Field(..., ge=0)
    exit_code: int
    assertions_passed: int = Field(..., ge=0)
    assertions_failed: int = Field(..., ge=0)
    eligible_for_aggregation: bool
    ineligibility_reason: Optional[str] = None
    lease_owner: str = Field(..., min_length=1)
    started_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
    finished_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 7. Aggregate
class Aggregate(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    aggregate_id: str = Field(..., pattern=AGGREGATE_ID_REGEX)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    aggregation_policy_version: str = Field(..., min_length=1)
    eligible_run_keys: List[str] = Field(..., min_length=1)
    ineligible_run_keys: List[str]
    total_attempts: int = Field(..., ge=1)
    resolved_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    pass_rate: float = Field(..., ge=0.0, le=1.0)
    total_cost_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    cpr_usd: str = Field(..., pattern=DECIMAL_USD_REGEX)
    mean_latency_ms: int = Field(..., ge=0)
    p95_latency_ms: int = Field(..., ge=0)
    uncertainty_method: UncertaintyMethod
    pass_rate_lower_bound: float = Field(..., ge=0.0, le=1.0)
    pass_rate_upper_bound: float = Field(..., ge=0.0, le=1.0)
    evidence_sufficient: bool
    quality_floor_breached: bool
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 8. PolicyVersion
class PolicyVersion(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    policy_version: str = Field(..., pattern=POLICY_VERSION_REGEX)
    task_segment_id: str = Field(..., min_length=1)
    configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    is_active: bool
    state_version: int = Field(..., ge=1)
    parent_policy_version: Optional[str] = Field(None, pattern=POLICY_VERSION_REGEX)
    promoted_by_decision_id: Optional[str] = Field(None, pattern=DECISION_ID_REGEX)
    promoted_at: Optional[str] = Field(None, pattern=RFC3339_MILLIS_REGEX)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 9. CanaryResult
class CanaryResult(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    canary_id: str = Field(..., pattern=CANARY_ID_REGEX)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    baseline_policy_version: str = Field(..., pattern=POLICY_VERSION_REGEX)
    candidate_policy_version: str = Field(..., pattern=POLICY_VERSION_REGEX)
    canary_task_ids: List[str] = Field(..., min_length=1)
    baseline_run_keys: List[str] = Field(..., min_length=1)
    candidate_run_keys: List[str] = Field(..., min_length=1)
    candidate_passed: bool
    guardrails_evaluated: List[str]
    guardrails_breached: List[str]
    promotion_approved: bool
    rollback_triggered: bool
    rollback_reason: Optional[str] = None
    evaluated_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 10. DecisionReceipt
class DecisionReceipt(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    receipt_id: str = Field(..., pattern=RECEIPT_ID_REGEX)
    decision_id: str = Field(..., pattern=DECISION_ID_REGEX)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    public_decision: PublicDecision
    internal_outcome: InternalOutcome
    baseline_configuration_id: str = Field(..., pattern=CONFIGURATION_ID_REGEX)
    candidate_configuration_id: Optional[str] = Field(None, pattern=CONFIGURATION_ID_REGEX)
    task_segment_id: str = Field(..., min_length=1)
    baseline_aggregate_id: str = Field(..., pattern=AGGREGATE_ID_REGEX)
    candidate_aggregate_id: Optional[str] = Field(None, pattern=AGGREGATE_ID_REGEX)
    canary_id: Optional[str] = Field(None, pattern=CANARY_ID_REGEX)
    why_decision: str = Field(..., min_length=1)
    why_not_cheapest: str = Field(..., min_length=1)
    what_would_reverse_it: str = Field(..., min_length=1)
    known_limitations: List[str] = Field(..., min_length=1)
    truth_class: TruthClass
    evidence_hash: str = Field(..., pattern=SHA256_64_REGEX)
    code_commit_sha: str = Field(..., pattern=SHA256_40_REGEX)
    created_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 11. ReplayEvent
class ReplayEvent(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    sequence_id: int = Field(..., ge=0)
    experiment_id: str = Field(..., pattern=EXPERIMENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    from_state: ExperimentState
    to_state: ExperimentState
    actor: str = Field(..., min_length=1)
    payload_hash: str = Field(..., pattern=SHA256_64_REGEX)
    transition_reason: str = Field(..., min_length=1)
    timestamp: str = Field(..., pattern=RFC3339_MILLIS_REGEX)


# 12. StalenessEvent
class StalenessEvent(StrictBaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    event_id: str = Field(..., pattern=EVENT_ID_REGEX)
    correlation_id: str = Field(..., pattern=CORRELATION_ID_REGEX)
    invalidated_policy_version: str = Field(..., pattern=POLICY_VERSION_REGEX)
    invalidated_receipt_id: str = Field(..., pattern=RECEIPT_ID_REGEX)
    task_segment_id: str = Field(..., min_length=1)
    staleness_reason: StalenessReason
    drift_details: str = Field(..., min_length=1)
    trigger_event_id: str = Field(..., pattern=EVENT_ID_REGEX)
    detected_at: str = Field(..., pattern=RFC3339_MILLIS_REGEX)
