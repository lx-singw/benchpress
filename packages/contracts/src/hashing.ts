import { createHash } from "crypto";

/**
 * RFC 8785 / Canonical JSON Serialization
 * Recursively sorts object keys in lexicographical Unicode order and outputs compact JSON without superfluous whitespace.
 */
export function canonicalJsonStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    const items = value.map((item) => canonicalJsonStringify(item));
    return `[${items.join(",")}]`;
  }

  // Object key sorting
  const obj = value as Record<string, unknown>;
  const sortedKeys = Object.keys(obj).sort();
  const pairs = sortedKeys.map((key) => {
    const valStr = canonicalJsonStringify(obj[key]);
    return `${JSON.stringify(key)}:${valStr}`;
  });

  return `{${pairs.join(",")}}`;
}

/**
 * Compute hex SHA-256 digest of canonical JSON serialization
 */
export function computeCanonicalHash(value: unknown): string {
  const canonicalJson = canonicalJsonStringify(value);
  return createHash("sha256").update(canonicalJson, "utf8").digest("hex");
}

/**
 * Canonical ID Generators
 */

export function generateConfigurationId(payload: {
  provider: string;
  request_model: string;
  thinking_budget_tokens: number;
  temperature: number;
  top_p: number;
  max_output_tokens: number;
  system_instruction_hash: string;
  tool_schema_hash: string;
  price_input_per_million_usd: string;
  price_output_per_million_usd: string;
  price_source_version: string;
}): string {
  const hash = computeCanonicalHash(payload);
  return `cfg_${hash.slice(0, 16)}`;
}

export function generateFingerprintId(payload: {
  task_family: string;
  workflow_phase: string;
  language: string;
  framework: string;
  ast_depth: number;
  cyclomatic_complexity: number;
  context_token_weight: number;
  required_tools: string[];
  risk_class: string;
  latency_sensitivity: string;
  feature_vector_hash: string;
}): string {
  const hash = computeCanonicalHash(payload);
  return `fp_${hash.slice(0, 16)}`;
}

export function generatePlanId(payload: {
  experiment_id: string;
  correlation_id: string;
  event_id: string;
  fingerprint_id: string;
  baseline_configuration_id: string;
  candidate_configuration_ids: string[];
  task_cohort_version: string;
  selected_task_ids: string[];
  repetitions_per_task: number;
  max_matrix_spend_usd: string;
  reserved_budget_usd: string;
  per_run_timeout_seconds: number;
  max_turns_per_run: number;
  quality_floor_pass_rate: number;
  early_stop_consecutive_failures: number;
  planner_model: string;
  plan_policy_version: string;
}): string {
  const hash = computeCanonicalHash(payload);
  return `plan_${hash.slice(0, 16)}`;
}

export function generateLogicalRunKey(payload: {
  experiment_id: string;
  task_id: string;
  task_version_hash: string;
  configuration_id: string;
  repetition_index: number;
  harness_version: string;
  oracle_version: string;
}): string {
  const hash = computeCanonicalHash(payload);
  return `run_${hash.slice(0, 16)}`;
}

export function generateAggregateId(payload: {
  experiment_id: string;
  configuration_id: string;
  aggregation_policy_version: string;
  eligible_run_keys: string[];
}): string {
  const sortedRunKeys = [...payload.eligible_run_keys].sort();
  const hash = computeCanonicalHash({
    experiment_id: payload.experiment_id,
    configuration_id: payload.configuration_id,
    aggregation_policy_version: payload.aggregation_policy_version,
    eligible_run_keys: sortedRunKeys,
  });
  return `agg_${hash.slice(0, 16)}`;
}

export function generateReceiptId(payloadWithoutReceiptId: Record<string, unknown>): string {
  // Ensure receipt_id is omitted from hash input
  const { receipt_id: _, ...cleanPayload } = payloadWithoutReceiptId;
  const hash = computeCanonicalHash(cleanPayload);
  return `rcpt_${hash.slice(0, 16)}`;
}
