import { z } from "zod";
import {
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
} from "./types.js";

// Common Patterns
export const ULID_PATTERN = /^[0-9A-HJKMNP-TV-Z]{26}$/;
export const SHA256_16_PATTERN = /^[a-f0-9]{16}$/;
export const SHA256_40_PATTERN = /^[a-f0-9]{40}$/;
export const SHA256_64_PATTERN = /^[a-f0-9]{64}$/;
export const RFC3339_MILLIS_PATTERN = /^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$/;
export const DECIMAL_USD_PATTERN = /^[0-9]+\.[0-9]{6}$/;

export const EventIdSchema = z.string().regex(/^evt_[0-9A-HJKMNP-TV-Z]{26}$/);
export const CorrelationIdSchema = z.string().regex(/^corr_[0-9A-HJKMNP-TV-Z]{26}$/);
export const ExperimentIdSchema = z.string().regex(/^exp_[0-9A-HJKMNP-TV-Z]{26}$/);
export const ConfigurationIdSchema = z.string().regex(/^cfg_[a-f0-9]{16}$/);
export const FingerprintIdSchema = z.string().regex(/^fp_[a-f0-9]{16}$/);
export const PlanIdSchema = z.string().regex(/^plan_[a-f0-9]{16}$/);
export const LogicalRunKeySchema = z.string().regex(/^run_[a-f0-9]{16}$/);
export const AttemptIdSchema = z.string().regex(/^att_[0-9A-HJKMNP-TV-Z]{26}$/);
export const AggregateIdSchema = z.string().regex(/^agg_[a-f0-9]{16}$/);
export const PolicyVersionSchema = z.string().regex(/^pol_[0-9A-HJKMNP-TV-Z]{26}$/);
export const DecisionIdSchema = z.string().regex(/^dec_[0-9A-HJKMNP-TV-Z]{26}$/);
export const ReceiptIdSchema = z.string().regex(/^rcpt_[a-f0-9]{16}$/);
export const CanaryIdSchema = z.string().regex(/^cnry_[0-9A-HJKMNP-TV-Z]{26}$/);

export const TimestampSchema = z.string().regex(RFC3339_MILLIS_PATTERN);
export const DecimalUsdSchema = z.string().regex(DECIMAL_USD_PATTERN);
export const Sha256HashSchema = z.string().regex(SHA256_64_PATTERN);

// 1. ChangeEvent Schema
export const ChangeEventSchema = z.object({
  schema_version: z.literal("1.0.0"),
  event_id: EventIdSchema,
  correlation_id: CorrelationIdSchema,
  event_type: z.nativeEnum(EventType),
  source_kind: z.nativeEnum(SourceKind),
  source_reference: z.string().min(1),
  target_provider: z.string().min(1),
  target_model_family: z.string().min(1),
  changed_fields: z.array(z.string()),
  source_checksum: Sha256HashSchema,
  effective_at: TimestampSchema,
  retrieved_at: TimestampSchema,
  baseline_policy_version: PolicyVersionSchema,
  baseline_configuration_id: ConfigurationIdSchema,
  max_spend_usd: DecimalUsdSchema,
  deadline_at: TimestampSchema,
  initiator: z.string().min(1),
  replay: z.boolean(),
  replay_label: z.string().optional(),
  created_at: TimestampSchema,
}).strict();
export type ChangeEvent = z.infer<typeof ChangeEventSchema>;

// 2. TaskFingerprint Schema
export const TaskFingerprintSchema = z.object({
  schema_version: z.literal("1.0.0"),
  fingerprint_id: FingerprintIdSchema,
  task_family: z.string().min(1),
  workflow_phase: z.nativeEnum(WorkflowPhase),
  language: z.string().min(1),
  framework: z.string().min(1),
  ast_depth: z.number().int().min(0),
  cyclomatic_complexity: z.number().int().min(0),
  context_token_weight: z.number().int().min(0),
  required_tools: z.array(z.string()),
  risk_class: z.nativeEnum(RiskClass),
  latency_sensitivity: z.nativeEnum(LatencySensitivity),
  feature_vector_hash: Sha256HashSchema,
  created_at: TimestampSchema,
}).strict();
export type TaskFingerprint = z.infer<typeof TaskFingerprintSchema>;

// 3. NativeConfiguration Schema
export const NativeConfigurationSchema = z.object({
  schema_version: z.literal("1.0.0"),
  configuration_id: ConfigurationIdSchema,
  provider: z.string().min(1),
  request_model: z.string().min(1),
  resolved_model_snapshot: z.string().optional(),
  thinking_budget_tokens: z.number().int().min(0),
  temperature: z.number().min(0.0).max(2.0),
  top_p: z.number().min(0.0).max(1.0),
  max_output_tokens: z.number().int().min(1),
  system_instruction_hash: Sha256HashSchema,
  tool_schema_hash: Sha256HashSchema,
  price_input_per_million_usd: DecimalUsdSchema,
  price_output_per_million_usd: DecimalUsdSchema,
  price_source_version: z.string().min(1),
  created_at: TimestampSchema,
}).strict();
export type NativeConfiguration = z.infer<typeof NativeConfigurationSchema>;

// 4. ExperimentPlan Schema
export const ExperimentPlanSchema = z.object({
  schema_version: z.literal("1.0.0"),
  plan_id: PlanIdSchema,
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  event_id: EventIdSchema,
  fingerprint_id: FingerprintIdSchema,
  baseline_configuration_id: ConfigurationIdSchema,
  candidate_configuration_ids: z.array(ConfigurationIdSchema).min(1),
  task_cohort_version: z.string().min(1),
  selected_task_ids: z.array(z.string().min(1)).min(1),
  repetitions_per_task: z.number().int().min(1),
  max_matrix_spend_usd: DecimalUsdSchema,
  reserved_budget_usd: DecimalUsdSchema,
  per_run_timeout_seconds: z.number().int().min(1),
  max_turns_per_run: z.number().int().min(1),
  quality_floor_pass_rate: z.number().min(0.0).max(1.0),
  early_stop_consecutive_failures: z.number().int().min(1),
  planner_model: z.string().min(1),
  plan_policy_version: z.string().min(1),
  planning_rationale: z.string().min(1),
  created_at: TimestampSchema,
}).strict();
export type ExperimentPlan = z.infer<typeof ExperimentPlanSchema>;

// 5. RunManifest Schema
export const RunManifestSchema = z.object({
  schema_version: z.literal("1.0.0"),
  logical_run_key: LogicalRunKeySchema,
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  configuration_id: ConfigurationIdSchema,
  task_id: z.string().min(1),
  task_version_hash: Sha256HashSchema,
  repetition_index: z.number().int().min(0),
  harness_version: z.string().min(1),
  oracle_version: z.string().min(1),
  tool_allowlist: z.array(z.string()).min(1),
  path_allowlist: z.array(z.string()),
  max_turns: z.number().int().min(1),
  timeout_seconds: z.number().int().min(1),
  max_spend_usd: DecimalUsdSchema,
  created_at: TimestampSchema,
}).strict();
export type RunManifest = z.infer<typeof RunManifestSchema>;

// 6. RunResult Schema
export const RunResultSchema = z.object({
  schema_version: z.literal("1.0.0"),
  logical_run_key: LogicalRunKeySchema,
  attempt_id: AttemptIdSchema,
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  configuration_id: ConfigurationIdSchema,
  task_id: z.string().min(1),
  repetition_index: z.number().int().min(0),
  run_state: z.nativeEnum(LogicalRunState),
  resolved: z.boolean(),
  failure_reason: z.nativeEnum(FailureReason),
  failure_details: z.string().optional(),
  turns_executed: z.number().int().min(0),
  prompt_tokens: z.number().int().min(0),
  completion_tokens: z.number().int().min(0),
  cached_tokens: z.number().int().min(0),
  total_tokens: z.number().int().min(0),
  observed_cost_usd: DecimalUsdSchema,
  price_version: z.string().min(1),
  latency_ms: z.number().int().min(0),
  exit_code: z.number().int(),
  assertions_passed: z.number().int().min(0),
  assertions_failed: z.number().int().min(0),
  eligible_for_aggregation: z.boolean(),
  ineligibility_reason: z.string().optional(),
  lease_owner: z.string().min(1),
  started_at: TimestampSchema,
  finished_at: TimestampSchema,
  created_at: TimestampSchema,
}).strict();
export type RunResult = z.infer<typeof RunResultSchema>;

// 7. Aggregate Schema
export const AggregateSchema = z.object({
  schema_version: z.literal("1.0.0"),
  aggregate_id: AggregateIdSchema,
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  configuration_id: ConfigurationIdSchema,
  aggregation_policy_version: z.string().min(1),
  eligible_run_keys: z.array(LogicalRunKeySchema).min(1),
  ineligible_run_keys: z.array(LogicalRunKeySchema),
  total_attempts: z.number().int().min(1),
  resolved_count: z.number().int().min(0),
  failed_count: z.number().int().min(0),
  pass_rate: z.number().min(0.0).max(1.0),
  total_cost_usd: DecimalUsdSchema,
  cpr_usd: DecimalUsdSchema,
  mean_latency_ms: z.number().int().min(0),
  p95_latency_ms: z.number().int().min(0),
  uncertainty_method: z.nativeEnum(UncertaintyMethod),
  pass_rate_lower_bound: z.number().min(0.0).max(1.0),
  pass_rate_upper_bound: z.number().min(0.0).max(1.0),
  evidence_sufficient: z.boolean(),
  quality_floor_breached: z.boolean(),
  created_at: TimestampSchema,
}).strict();
export type Aggregate = z.infer<typeof AggregateSchema>;

// 8. PolicyVersion Schema
export const PolicyVersionSchemaObj = z.object({
  schema_version: z.literal("1.0.0"),
  policy_version: PolicyVersionSchema,
  task_segment_id: z.string().min(1),
  configuration_id: ConfigurationIdSchema,
  is_active: z.boolean(),
  state_version: z.number().int().min(1),
  parent_policy_version: PolicyVersionSchema.nullable(),
  promoted_by_decision_id: DecisionIdSchema.nullable(),
  promoted_at: TimestampSchema.nullable(),
  created_at: TimestampSchema,
}).strict();
export type PolicyVersion = z.infer<typeof PolicyVersionSchemaObj>;

// 9. CanaryResult Schema
export const CanaryResultSchema = z.object({
  schema_version: z.literal("1.0.0"),
  canary_id: CanaryIdSchema,
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  baseline_policy_version: PolicyVersionSchema,
  candidate_policy_version: PolicyVersionSchema,
  canary_task_ids: z.array(z.string()).min(1),
  baseline_run_keys: z.array(LogicalRunKeySchema).min(1),
  candidate_run_keys: z.array(LogicalRunKeySchema).min(1),
  candidate_passed: z.boolean(),
  guardrails_evaluated: z.array(z.string()),
  guardrails_breached: z.array(z.string()),
  promotion_approved: z.boolean(),
  rollback_triggered: z.boolean(),
  rollback_reason: z.string().optional(),
  evaluated_at: TimestampSchema,
  created_at: TimestampSchema,
}).strict();
export type CanaryResult = z.infer<typeof CanaryResultSchema>;

// 10. DecisionReceipt Schema
export const DecisionReceiptSchema = z.object({
  schema_version: z.literal("1.0.0"),
  receipt_id: ReceiptIdSchema,
  decision_id: DecisionIdSchema,
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  public_decision: z.nativeEnum(PublicDecision),
  internal_outcome: z.nativeEnum(InternalOutcome),
  baseline_configuration_id: ConfigurationIdSchema,
  candidate_configuration_id: ConfigurationIdSchema.nullable(),
  task_segment_id: z.string().min(1),
  baseline_aggregate_id: AggregateIdSchema,
  candidate_aggregate_id: AggregateIdSchema.nullable(),
  canary_id: CanaryIdSchema.nullable(),
  why_decision: z.string().min(1),
  why_not_cheapest: z.string().min(1),
  what_would_reverse_it: z.string().min(1),
  known_limitations: z.array(z.string()).min(1),
  truth_class: z.nativeEnum(TruthClass),
  evidence_hash: Sha256HashSchema,
  code_commit_sha: z.string().regex(/^[a-f0-9]{40}$/),
  created_at: TimestampSchema,
}).strict();
export type DecisionReceipt = z.infer<typeof DecisionReceiptSchema>;

// 11. ReplayEvent Schema
export const ReplayEventSchema = z.object({
  schema_version: z.literal("1.0.0"),
  sequence_id: z.number().int().min(0),
  experiment_id: ExperimentIdSchema,
  correlation_id: CorrelationIdSchema,
  from_state: z.nativeEnum(ExperimentState),
  to_state: z.nativeEnum(ExperimentState),
  actor: z.string().min(1),
  payload_hash: Sha256HashSchema,
  transition_reason: z.string().min(1),
  timestamp: TimestampSchema,
}).strict();
export type ReplayEvent = z.infer<typeof ReplayEventSchema>;

// 12. StalenessEvent Schema
export const StalenessEventSchema = z.object({
  schema_version: z.literal("1.0.0"),
  event_id: EventIdSchema,
  correlation_id: CorrelationIdSchema,
  invalidated_policy_version: PolicyVersionSchema,
  invalidated_receipt_id: ReceiptIdSchema,
  task_segment_id: z.string().min(1),
  staleness_reason: z.nativeEnum(StalenessReason),
  drift_details: z.string().min(1),
  trigger_event_id: EventIdSchema,
  detected_at: TimestampSchema,
}).strict();
export type StalenessEvent = z.infer<typeof StalenessEventSchema>;
