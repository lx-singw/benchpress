/**
 * Server-only Firestore Native Repository for Benchpress Read-Model.
 */

import { Firestore } from "@google-cloud/firestore";
import {
  DecisionReceiptSchema,
  generateReceiptId,
  UncertaintyMethod,
  PublicDecision,
  InternalOutcome,
  TruthClass,
  ExperimentState,
  type DecisionReceipt,
  type ExperimentPlan,
  type PolicyVersion,
  type ReplayEvent,
  type NativeConfiguration,
  type Aggregate,
  type ChangeEvent,
} from "@benchpress/contracts";

export interface ExperimentRecord {
  experiment_id: string;
  correlation_id: string;
  event_id: string;
  state: string;
  state_version: number;
  plan_id?: string;
  decision_id?: string;
  receipt_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface DecisionReadRepository {
  getExperiment(id: string): Promise<ExperimentRecord | null>;
  saveExperiment(experiment: ExperimentRecord): Promise<void>;
  saveChangeEvent(event: ChangeEvent): Promise<void>;
  getDecision(id: string): Promise<DecisionReceipt | null>;
  getReceipt(id: string): Promise<DecisionReceipt | null>;
  getReplayEvents(experimentId: string): Promise<ReplayEvent[]>;
  getActivePolicy(segmentId: string): Promise<PolicyVersion | null>;
  getConfiguration(configId: string): Promise<NativeConfiguration | null>;
  getAggregate(aggregateId: string): Promise<Aggregate | null>;
}

export class ReadModelUnavailableError extends Error {}

/** Explicit local-only fixture repository. Its records are never measured. */
export class FixtureDemoRepository implements DecisionReadRepository {
  private experiments = new Map<string, ExperimentRecord>();
  private receipts = new Map<string, DecisionReceipt>();
  private decisions = new Map<string, DecisionReceipt>();
  private replays = new Map<string, ReplayEvent[]>();
  private policies = new Map<string, PolicyVersion>();
  private configurations = new Map<string, NativeConfiguration>();
  private aggregates = new Map<string, Aggregate>();
  private changeEvents = new Map<string, ChangeEvent>();

  constructor() {
    this.seedDefaultFixtures();
  }

  private seedDefaultFixtures() {
    // Seed verified baseline configuration
    const baselineCfg: NativeConfiguration = {
      schema_version: "1.0.0",
      configuration_id: "cfg_948a3f81e3a1b029",
      provider: "google",
      request_model: "gemini-2.5-pro",
      thinking_budget_tokens: 0,
      temperature: 0.0,
      top_p: 1.0,
      max_output_tokens: 8192,
      system_instruction_hash: "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
      tool_schema_hash: "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
      price_input_per_million_usd: "1.250000",
      price_output_per_million_usd: "5.000000",
      price_source_version: "2026-08-29",
      created_at: "2026-08-29T10:00:00.000Z",
    };
    this.configurations.set(baselineCfg.configuration_id, baselineCfg);

    // Seed candidate configuration (thinking 2048)
    const candidateCfg: NativeConfiguration = {
      schema_version: "1.0.0",
      configuration_id: "cfg_4f1b82d3e9a0c784",
      provider: "google",
      request_model: "gemini-2.5-pro",
      thinking_budget_tokens: 2048,
      temperature: 0.0,
      top_p: 1.0,
      max_output_tokens: 8192,
      system_instruction_hash: "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
      tool_schema_hash: "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
      price_input_per_million_usd: "1.250000",
      price_output_per_million_usd: "5.000000",
      price_source_version: "2026-08-29",
      created_at: "2026-08-29T10:00:15.000Z",
    };
    this.configurations.set(candidateCfg.configuration_id, candidateCfg);

    // Seed failing cheap candidate configuration (flash)
    const flashCfg: NativeConfiguration = {
      schema_version: "1.0.0",
      configuration_id: "cfg_7c2a93e4f1b80d19",
      provider: "google",
      request_model: "gemini-2.5-flash",
      thinking_budget_tokens: 0,
      temperature: 0.0,
      top_p: 1.0,
      max_output_tokens: 8192,
      system_instruction_hash: "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
      tool_schema_hash: "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
      price_input_per_million_usd: "0.075000",
      price_output_per_million_usd: "0.300000",
      price_source_version: "2026-08-29",
      created_at: "2026-08-29T10:00:00.000Z",
    };
    this.configurations.set(flashCfg.configuration_id, flashCfg);

    // Seed active policy
    const activePolicy: PolicyVersion = {
      schema_version: "1.0.0",
      policy_version: "pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
      task_segment_id: "swe_coding_python_interactive",
      configuration_id: "cfg_948a3f81e3a1b029",
      is_active: true,
      state_version: 1,
      parent_policy_version: null,
      promoted_by_decision_id: null,
      promoted_at: null,
      created_at: "2026-08-29T10:00:00.000Z",
    };
    this.policies.set(activePolicy.task_segment_id, activePolicy);

    // Seed baseline aggregate
    const baseAgg: Aggregate = {
      schema_version: "1.0.0",
      aggregate_id: "agg_0123456789abcdef",
      experiment_id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
      correlation_id: "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
      configuration_id: "cfg_948a3f81e3a1b029",
      aggregation_policy_version: "agg_pol_v1_taskmaster",
      eligible_run_keys: ["run_01a2b3c4d5e6f780", "run_01a2b3c4d5e6f781", "run_01a2b3c4d5e6f782", "run_01a2b3c4d5e6f783"],
      ineligible_run_keys: [],
      ineligible_run_reasons: {},
      total_attempts: 4,
      resolved_count: 3,
      failed_count: 1,
      pass_rate: 0.75,
      total_cost_usd: "0.032400",
      prompt_tokens: 2400,
      completion_tokens: 800,
      cached_tokens: 0,
      reasoning_tokens: 0,
      total_tokens: 3200,
      failure_counts: { ORACLE_ASSERTION_FAILED: 1 },
      cpr_usd: "0.010800",
      cpr_defined: true,
      cpr_undefined_reason: null,
      mean_latency_ms: 1850,
      p95_latency_ms: 2400,
      uncertainty_method: UncertaintyMethod.WILSON_SCORE,
      pass_rate_lower_bound: 0.3006,
      pass_rate_upper_bound: 0.9544,
      evidence_sufficient: true,
      quality_floor_breached: false,
      formula_version: "cpr_failure_inclusive_v1",
      quality_floor_pass_rate: 0.75,
      minimum_attempts: 2,
      source_result_digest: "1".repeat(64),
      created_at: "2026-08-29T10:05:00.000Z",
    };
    this.aggregates.set(baseAgg.aggregate_id, baseAgg);

    // Seed candidate aggregate (thinking 2048)
    const candAgg: Aggregate = {
      schema_version: "1.0.0",
      aggregate_id: "agg_fedcba9876543210",
      experiment_id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
      correlation_id: "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
      configuration_id: "cfg_4f1b82d3e9a0c784",
      aggregation_policy_version: "agg_pol_v1_taskmaster",
      eligible_run_keys: ["run_01a2b3c4d5e6f784", "run_01a2b3c4d5e6f785", "run_01a2b3c4d5e6f786", "run_01a2b3c4d5e6f787"],
      ineligible_run_keys: [],
      ineligible_run_reasons: {},
      total_attempts: 4,
      resolved_count: 4,
      failed_count: 0,
      pass_rate: 1.0,
      total_cost_usd: "0.021600",
      prompt_tokens: 2400,
      completion_tokens: 800,
      cached_tokens: 0,
      reasoning_tokens: 512,
      total_tokens: 3712,
      failure_counts: {},
      cpr_usd: "0.005400",
      cpr_defined: true,
      cpr_undefined_reason: null,
      mean_latency_ms: 1620,
      p95_latency_ms: 2100,
      uncertainty_method: UncertaintyMethod.WILSON_SCORE,
      pass_rate_lower_bound: 0.5101,
      pass_rate_upper_bound: 1.0,
      evidence_sufficient: true,
      quality_floor_breached: false,
      formula_version: "cpr_failure_inclusive_v1",
      quality_floor_pass_rate: 0.75,
      minimum_attempts: 2,
      source_result_digest: "2".repeat(64),
      created_at: "2026-08-29T10:05:05.000Z",
    };
    this.aggregates.set(candAgg.aggregate_id, candAgg);

    // Seed a synthetic DecisionReceipt for explicit local demo mode only.
    const defaultReceipt: DecisionReceipt = {
      schema_version: "1.0.0",
      receipt_id: "rcpt_0123456789abcdef",
      decision_id: "dec_01J6G7R8Q9ABCDEFGHJKMNPQ50",
      experiment_id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
      correlation_id: "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
      public_decision: PublicDecision.SWITCH,
      internal_outcome: InternalOutcome.SWITCH_RECOMMENDED,
      baseline_configuration_id: "cfg_948a3f81e3a1b029",
      candidate_configuration_id: "cfg_4f1b82d3e9a0c784",
      task_segment_id: "swe_coding_python_interactive",
      baseline_aggregate_id: "agg_0123456789abcdef",
      candidate_aggregate_id: "agg_fedcba9876543210",
      canary_id: "cnry_01J6G7R8Q9ABCDEFGHJKMNPQ40",
      why_decision: "Candidate policy (gemini-2.5-pro with 2048 thinking budget) achieved 100% Pass@1 (4/4) with 50% lower CPR ($0.005400 vs $0.010800) and verified contained canary.",
      why_not_cheapest: "gemini-2.5-flash is cheaper per raw token ($0.075/1M vs $1.25/1M), but failed 2 of 4 task assertions (TASK-003 and TASK-004), causing infinite effective CPR on failures.",
      what_would_reverse_it: "Candidate experiencing quality regression on canary suite or provider pricing increase > 35%.",
      known_limitations: ["Evaluated against judged 4-task SWE cohort; Wilson Score confidence interval 0.5101 - 1.0000."],
      trigger_event_id: "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
      fingerprint_id: null,
      plan_id: null,
      baseline_policy_version: "pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
      candidate_policy_version: null,
      selected_task_ids: ["TASK-001", "TASK-002", "TASK-003", "TASK-004"],
      eligible_run_keys: [...baseAgg.eligible_run_keys, ...candAgg.eligible_run_keys].sort(),
      excluded_run_reasons: {},
      baseline_evidence: baseAgg,
      candidate_evidence: candAgg,
      approval_boundary_version: "decision_policy_v1",
      rollback_performed: false,
      publication_status: "PUBLISHED",
      truth_class: TruthClass.DEMO_FIXTURE,
      evidence_hash: "7d11f64f43477e60058b8f2d52528b3ee1dc2287c7e52bca7e868a2bf6cb862a",
      code_commit_sha: "7dfb9a4000000000000000000000000000000000",
      created_at: "2026-08-29T10:05:30.000Z",
    };
    this.receipts.set(defaultReceipt.receipt_id, defaultReceipt);
    this.decisions.set(defaultReceipt.decision_id, defaultReceipt);
    this.decisions.set(defaultReceipt.experiment_id, defaultReceipt);

    // Seed experiment record
    const expRecord: ExperimentRecord = {
      experiment_id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
      correlation_id: "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
      event_id: "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
      state: ExperimentState.PUBLISHED,
      state_version: 7,
      decision_id: defaultReceipt.decision_id,
      receipt_id: defaultReceipt.receipt_id,
      created_at: "2026-08-29T10:00:00.000Z",
      updated_at: "2026-08-29T10:05:30.000Z",
    };
    this.experiments.set(expRecord.experiment_id, expRecord);

    // Seed replay timeline events
    const replayEvents: ReplayEvent[] = [
      {
        schema_version: "1.0.0",
        sequence_id: 1,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.RECEIVED,
        to_state: ExperimentState.PLANNING,
        actor: "orchestrator_service",
        payload_hash: "b28014529ec97b76435cfa320cf9e32ea2a1a89c89a071853d535b9ba1bf5e95",
        transition_reason: "ChangeEvent validated; invoking Gemini 3.5+ Evaluation Planner",
        timestamp: "2026-08-29T10:00:05.000Z",
      },
      {
        schema_version: "1.0.0",
        sequence_id: 2,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.PLANNING,
        to_state: ExperimentState.PLAN_APPROVED,
        actor: "plan_policy_gate",
        payload_hash: "7d11f64f43477e60058b8f2d52528b3ee1dc2287c7e52bca7e868a2bf6cb862a",
        transition_reason: "Plan approved: baseline included, budget verified within $0.50 reservation",
        timestamp: "2026-08-29T10:00:10.000Z",
      },
      {
        schema_version: "1.0.0",
        sequence_id: 3,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.PLAN_APPROVED,
        to_state: ExperimentState.DISPATCHING,
        actor: "cloud_tasks_dispatcher",
        payload_hash: "81ee6c30f40d65b79873d6b05be5cf11ba6bbcb795bc99ecfdfd4e0e24177d6e",
        transition_reason: "Fan-out 8 immutable run manifests to Cloud Tasks with deterministic keys",
        timestamp: "2026-08-29T10:00:15.000Z",
      },
      {
        schema_version: "1.0.0",
        sequence_id: 4,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.DISPATCHING,
        to_state: ExperimentState.RUNNING,
        actor: "sandbox_worker_pool",
        payload_hash: "0b14ce9e3b9709230559194ec8942a78f237db875e5332f143714b1b38f8cf62",
        transition_reason: "Ephemeral workspaces provisioned; Pytest deterministic oracles executing",
        timestamp: "2026-08-29T10:01:00.000Z",
      },
      {
        schema_version: "1.0.0",
        sequence_id: 5,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.RUNNING,
        to_state: ExperimentState.AGGREGATING,
        actor: "failure_inclusive_aggregator",
        payload_hash: "0447fa43fa2dd4d8d17208e92f2560ceea1952f2054ff83ffca522f254f676bc",
        transition_reason: "Aggregated CPR computed: Candidate $0.005400 vs Baseline $0.010800",
        timestamp: "2026-08-29T10:04:30.000Z",
      },
      {
        schema_version: "1.0.0",
        sequence_id: 6,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.AGGREGATING,
        to_state: ExperimentState.CANARY_RUNNING,
        actor: "canary_governor",
        payload_hash: "02be69a8427f7fe0ae95ff372551a37c15438848cfcfcbf5c4d51cb3e479d20c",
        transition_reason: "Sufficiency reached; dispatched contained canary verification on TASK-001",
        timestamp: "2026-08-29T10:05:00.000Z",
      },
      {
        schema_version: "1.0.0",
        sequence_id: 7,
        experiment_id: expRecord.experiment_id,
        correlation_id: expRecord.correlation_id,
        from_state: ExperimentState.CANARY_RUNNING,
        to_state: ExperimentState.PUBLISHED,
        actor: "policy_promotion_service",
        payload_hash: "a69eb6809ec0dcbe8b553fa65239a5f782f9dd1204ca658f895c8ba0ec51fe22",
        transition_reason: "Canary passed all guardrails; CAS promoted active policy pointer to candidate",
        timestamp: "2026-08-29T10:05:30.000Z",
      },
    ];
    this.replays.set(expRecord.experiment_id, replayEvents);
  }

  async getExperiment(id: string): Promise<ExperimentRecord | null> {
    return this.experiments.get(id) || null;
  }

  async saveExperiment(experiment: ExperimentRecord): Promise<void> {
    this.experiments.set(experiment.experiment_id, experiment);
  }

  async saveChangeEvent(event: ChangeEvent): Promise<void> {
    const existing = this.changeEvents.get(event.event_id);
    if (existing && JSON.stringify(existing) !== JSON.stringify(event)) {
      throw new Error(`Conflicting fixture ChangeEvent ${event.event_id}`);
    }
    this.changeEvents.set(event.event_id, event);
  }

  async getDecision(id: string): Promise<DecisionReceipt | null> {
    return this.decisions.get(id) || this.receipts.get(id) || null;
  }

  async getReceipt(id: string): Promise<DecisionReceipt | null> {
    return this.receipts.get(id) || this.decisions.get(id) || null;
  }

  async getReplayEvents(experimentId: string): Promise<ReplayEvent[]> {
    return this.replays.get(experimentId) || [];
  }

  async getActivePolicy(segmentId: string): Promise<PolicyVersion | null> {
    return this.policies.get(segmentId) || null;
  }

  async getConfiguration(configId: string): Promise<NativeConfiguration | null> {
    return this.configurations.get(configId) || null;
  }

  async getAggregate(aggregateId: string): Promise<Aggregate | null> {
    return this.aggregates.get(aggregateId) || null;
  }
}

/** Production/rehearsal read model. It has no fixture fallback. */
export class FirestoreMeasuredRepository implements DecisionReadRepository {
  private client: Firestore;
  private prefix: string;

  constructor(client?: Firestore) {
    const projectId = process.env.GOOGLE_CLOUD_PROJECT?.trim();
    if (!client && !projectId) {
      throw new ReadModelUnavailableError("GOOGLE_CLOUD_PROJECT is required for the measured read model");
    }
    this.client = client || new Firestore({
      projectId,
      databaseId: process.env.FIRESTORE_DATABASE_ID || "(default)",
    });
    this.prefix = process.env.FIRESTORE_COLLECTION_PREFIX?.trim() || "benchpress";
  }

  private collection(name: string) {
    return this.client.collection(`${this.prefix}_${name}`);
  }

  private async requirePublishedReceipt(raw: unknown): Promise<DecisionReceipt | null> {
    const parsed = DecisionReceiptSchema.safeParse(raw);
    if (!parsed.success || parsed.data.truth_class !== TruthClass.BENCHPRESS_MEASURED) return null;
    const receipt = parsed.data;
    if (generateReceiptId(receipt as unknown as Record<string, unknown>) !== receipt.receipt_id) return null;
    const publication = await this.collection("published_decisions").doc(receipt.experiment_id).get();
    if (
      !publication.exists ||
      publication.get("publication_status") !== "PUBLISHED" ||
      publication.get("receipt_id") !== receipt.receipt_id
    ) return null;
    return receipt;
  }

  async getExperiment(id: string): Promise<ExperimentRecord | null> {
    const doc = await this.collection("experiments").doc(id).get();
    return doc.exists ? (doc.data() as ExperimentRecord) : null;
  }

  async saveExperiment(experiment: ExperimentRecord): Promise<void> {
    const ref = this.collection("experiments").doc(experiment.experiment_id);
    await this.client.runTransaction(async (transaction) => {
      const existing = await transaction.get(ref);
      if (existing.exists) {
        const data = existing.data() as ExperimentRecord;
        if (data.event_id !== experiment.event_id || data.correlation_id !== experiment.correlation_id) {
          throw new Error(`Conflicting experiment ${experiment.experiment_id}`);
        }
        return;
      }
      transaction.create(ref, experiment);
    });
  }

  async saveChangeEvent(event: ChangeEvent): Promise<void> {
    const ref = this.collection("change_events").doc(event.event_id);
    await this.client.runTransaction(async (transaction) => {
      const existing = await transaction.get(ref);
      if (existing.exists) {
        if (JSON.stringify(existing.data()) !== JSON.stringify(event)) {
          throw new Error(`Conflicting ChangeEvent ${event.event_id}`);
        }
        return;
      }
      transaction.create(ref, event);
    });
  }

  async getDecision(id: string): Promise<DecisionReceipt | null> {
    let raw: unknown = null;
    if (id.startsWith("exp_")) {
      const publication = await this.collection("published_decisions").doc(id).get();
      if (!publication.exists || publication.get("publication_status") !== "PUBLISHED") return null;
      const receipt = await this.collection("decision_receipts").doc(publication.get("receipt_id")).get();
      raw = receipt.exists ? receipt.data() : null;
    } else if (id.startsWith("rcpt_")) {
      const receipt = await this.collection("decision_receipts").doc(id).get();
      raw = receipt.exists ? receipt.data() : null;
    } else if (id.startsWith("dec_")) {
      const matches = await this.collection("decision_receipts").where("decision_id", "==", id).limit(2).get();
      if (matches.size !== 1) return null;
      raw = matches.docs[0].data();
    }
    return raw ? this.requirePublishedReceipt(raw) : null;
  }

  async getReceipt(id: string): Promise<DecisionReceipt | null> {
    return this.getDecision(id);
  }

  async getReplayEvents(experimentId: string): Promise<ReplayEvent[]> {
    const published = await this.getDecision(experimentId);
    if (!published) return [];
    const snap = await this.collection("replay_events").where("experiment_id", "==", experimentId).get();
    return snap.docs
      .map((doc) => doc.data() as ReplayEvent)
      .sort((left, right) => left.sequence_id - right.sequence_id);
  }

  async getActivePolicy(segmentId: string): Promise<PolicyVersion | null> {
    const pointer = await this.collection("policy_pointers").doc(segmentId).get();
    if (!pointer.exists) return null;
    const policy = await this.collection("policy_versions").doc(pointer.get("active_policy_version")).get();
    return policy.exists ? (policy.data() as PolicyVersion) : null;
  }

  async getConfiguration(configId: string): Promise<NativeConfiguration | null> {
    const doc = await this.collection("configurations").doc(configId).get();
    return doc.exists ? (doc.data() as NativeConfiguration) : null;
  }

  async getAggregate(aggregateId: string): Promise<Aggregate | null> {
    const doc = await this.collection("aggregates").doc(aggregateId).get();
    return doc.exists ? (doc.data() as Aggregate) : null;
  }
}

const runtimeMode = process.env.RUNTIME_MODE || "local_mock";
if (runtimeMode === "local_mock" && process.env.USE_LOCAL_MOCK === "false") {
  throw new Error("USE_LOCAL_MOCK conflicts with RUNTIME_MODE=local_mock");
}
export const firestoreRepo: DecisionReadRepository = runtimeMode === "local_mock"
  ? new FixtureDemoRepository()
  : new FirestoreMeasuredRepository();
