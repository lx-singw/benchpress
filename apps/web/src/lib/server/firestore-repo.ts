/**
 * Server-only Firestore Native Repository for Benchpress Read-Model.
 */

import { Firestore } from "@google-cloud/firestore";
import {
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

class FirestoreRepository {
  private client: Firestore | null = null;
  private useMock: boolean;

  // In-memory backing store for local mock mode & tests
  private experiments = new Map<string, ExperimentRecord>();
  private receipts = new Map<string, DecisionReceipt>();
  private decisions = new Map<string, DecisionReceipt>();
  private replays = new Map<string, ReplayEvent[]>();
  private policies = new Map<string, PolicyVersion>();
  private configurations = new Map<string, NativeConfiguration>();
  private aggregates = new Map<string, Aggregate>();

  constructor() {
    this.useMock = process.env.USE_LOCAL_MOCK !== "false";
    if (!this.useMock) {
      try {
        const projectId = process.env.GOOGLE_CLOUD_PROJECT || "benchpress-dev";
        this.client = new Firestore({ projectId });
      } catch (err) {
        console.warn("[FirestoreRepo] Failed to initialize Firestore client. Falling back to local mock store:", err);
        this.useMock = true;
      }
    }
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
      total_attempts: 4,
      resolved_count: 3,
      failed_count: 1,
      pass_rate: 0.75,
      total_cost_usd: "0.032400",
      cpr_usd: "0.010800",
      mean_latency_ms: 1850,
      p95_latency_ms: 2400,
      uncertainty_method: UncertaintyMethod.WILSON_SCORE,
      pass_rate_lower_bound: 0.3006,
      pass_rate_upper_bound: 0.9544,
      evidence_sufficient: true,
      quality_floor_breached: false,
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
      total_attempts: 4,
      resolved_count: 4,
      failed_count: 0,
      pass_rate: 1.0,
      total_cost_usd: "0.021600",
      cpr_usd: "0.005400",
      mean_latency_ms: 1620,
      p95_latency_ms: 2100,
      uncertainty_method: UncertaintyMethod.WILSON_SCORE,
      pass_rate_lower_bound: 0.5101,
      pass_rate_upper_bound: 1.0,
      evidence_sufficient: true,
      quality_floor_breached: false,
      created_at: "2026-08-29T10:05:05.000Z",
    };
    this.aggregates.set(candAgg.aggregate_id, candAgg);

    // Seed authoritative DecisionReceipt (SWITCH)
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
      truth_class: TruthClass.BENCHPRESS_MEASURED,
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
    if (this.useMock || !this.client) {
      return this.experiments.get(id) || null;
    }
    const doc = await this.client.collection("experiments").doc(id).get();
    return doc.exists ? (doc.data() as ExperimentRecord) : null;
  }

  async saveExperiment(experiment: ExperimentRecord): Promise<void> {
    if (this.useMock || !this.client) {
      this.experiments.set(experiment.experiment_id, experiment);
      return;
    }
    await this.client.collection("experiments").doc(experiment.experiment_id).set(experiment);
  }

  async getDecision(id: string): Promise<DecisionReceipt | null> {
    if (this.useMock || !this.client) {
      return this.decisions.get(id) || this.receipts.get(id) || null;
    }
    const doc = await this.client.collection("decisions").doc(id).get();
    return doc.exists ? (doc.data() as DecisionReceipt) : null;
  }

  async getReceipt(id: string): Promise<DecisionReceipt | null> {
    if (this.useMock || !this.client) {
      return this.receipts.get(id) || this.decisions.get(id) || null;
    }
    const doc = await this.client.collection("receipts").doc(id).get();
    return doc.exists ? (doc.data() as DecisionReceipt) : null;
  }

  async getReplayEvents(experimentId: string): Promise<ReplayEvent[]> {
    if (this.useMock || !this.client) {
      return this.replays.get(experimentId) || [];
    }
    const snap = await this.client
      .collection("experiments")
      .doc(experimentId)
      .collection("replays")
      .orderBy("sequence_id", "asc")
      .get();
    return snap.docs.map((d) => d.data() as ReplayEvent);
  }

  async getActivePolicy(segmentId: string): Promise<PolicyVersion | null> {
    if (this.useMock || !this.client) {
      return this.policies.get(segmentId) || null;
    }
    const snap = await this.client
      .collection("policies")
      .where("task_segment_id", "==", segmentId)
      .where("is_active", "==", true)
      .limit(1)
      .get();
    return snap.empty ? null : (snap.docs[0].data() as PolicyVersion);
  }

  async getConfiguration(configId: string): Promise<NativeConfiguration | null> {
    if (this.useMock || !this.client) {
      return this.configurations.get(configId) || null;
    }
    const doc = await this.client.collection("configurations").doc(configId).get();
    return doc.exists ? (doc.data() as NativeConfiguration) : null;
  }

  async getAggregate(aggregateId: string): Promise<Aggregate | null> {
    if (this.useMock || !this.client) {
      return this.aggregates.get(aggregateId) || null;
    }
    const doc = await this.client.collection("aggregates").doc(aggregateId).get();
    return doc.exists ? (doc.data() as Aggregate) : null;
  }
}

export const firestoreRepo = new FirestoreRepository();
