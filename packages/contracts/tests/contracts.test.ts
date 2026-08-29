import assert from "node:assert";
import { test } from "node:test";
import {
  computeCanonicalHash,
  canonicalJsonStringify,
  generateConfigurationId,
  generateLogicalRunKey,
  generateAggregateId,
  generateReceiptId,
} from "../src/hashing.js";
import {
  ExperimentState,
  LogicalRunState,
  PublicDecision,
  InternalOutcome,
  TruthClass,
  WorkflowPhase,
  VALID_EXPERIMENT_TRANSITIONS,
  VALID_RUN_TRANSITIONS,
} from "../src/types.js";
import {
  ChangeEventSchema,
  TaskFingerprintSchema,
  NativeConfigurationSchema,
  ExperimentPlanSchema,
  RunManifestSchema,
  RunResultSchema,
  AggregateSchema,
  PolicyVersionSchemaObj,
  CanaryResultSchema,
  DecisionReceiptSchema,
  ReplayEventSchema,
  StalenessEventSchema,
} from "../src/zod.js";

test("Canonical JSON RFC 8785 key sorting", () => {
  const obj1 = { z: 1, a: 2, m: { b: 3, a: 4 } };
  const obj2 = { a: 2, m: { a: 4, b: 3 }, z: 1 };
  
  const json1 = canonicalJsonStringify(obj1);
  const json2 = canonicalJsonStringify(obj2);
  
  assert.strictEqual(json1, json2);
  assert.strictEqual(json1, '{"a":2,"m":{"a":4,"b":3},"z":1}');
  
  const hash1 = computeCanonicalHash(obj1);
  const hash2 = computeCanonicalHash(obj2);
  assert.strictEqual(hash1, hash2);
});

test("Canonical ID generation formatting", () => {
  const cfgId = generateConfigurationId({
    provider: "google",
    request_model: "gemini-2.5-pro",
    thinking_budget_tokens: 2048,
    temperature: 0.0,
    top_p: 1.0,
    max_output_tokens: 8192,
    system_instruction_hash: "a".repeat(64),
    tool_schema_hash: "b".repeat(64),
    price_input_per_million_usd: "1.250000",
    price_output_per_million_usd: "5.000000",
    price_source_version: "2026-08-29",
  });
  assert.match(cfgId, /^cfg_[a-f0-9]{16}$/);

  const runKey = generateLogicalRunKey({
    experiment_id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQRS",
    task_id: "TASK-001",
    task_version_hash: "c".repeat(64),
    configuration_id: cfgId,
    repetition_index: 0,
    harness_version: "pytest-8.3.0",
    oracle_version: "v1.0.0",
  });
  assert.match(runKey, /^run_[a-f0-9]{16}$/);

  const aggId = generateAggregateId({
    experiment_id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQRS",
    configuration_id: cfgId,
    aggregation_policy_version: "agg_pol_v1",
    eligible_run_keys: [runKey],
  });
  assert.match(aggId, /^agg_[a-f0-9]{16}$/);
});

test("State Transition invariants", () => {
  assert.ok(VALID_EXPERIMENT_TRANSITIONS[ExperimentState.RECEIVED].has(ExperimentState.PLANNING));
  assert.ok(!VALID_EXPERIMENT_TRANSITIONS[ExperimentState.RECEIVED].has(ExperimentState.PUBLISHED));
  assert.ok(VALID_RUN_TRANSITIONS[LogicalRunState.PENDING].has(LogicalRunState.CLAIMED));
  assert.ok(!VALID_RUN_TRANSITIONS[LogicalRunState.PENDING].has(LogicalRunState.SUCCEEDED));
});
