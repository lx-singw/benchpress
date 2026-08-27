/**
 * Comprehensive TypeScript Type Definitions for Benchpress Frontend Platform.
 */

export enum FsmState {
  IDLE = "IDLE",
  INITIALIZING = "INITIALIZING",
  PERCEPTION = "PERCEPTION",
  PREDICTIVE_SENTINEL_EVAL = "PREDICTIVE_SENTINEL_EVAL",
  REASONING_PLANNER = "REASONING_PLANNER",
  TOOL_DISPATCH_CODER = "TOOL_DISPATCH_CODER",
  SAGA_SNAPSHOT_CAPTURE = "SAGA_SNAPSHOT_CAPTURE",
  AST_VALIDATION = "AST_VALIDATION",
  SUPERVISOR_AST_HEAL = "SUPERVISOR_AST_HEAL",
  SAGA_COMPENSATING_ROLLBACK = "SAGA_COMPENSATING_ROLLBACK",
  SANDBOX_EXECUTION = "SANDBOX_EXECUTION",
  EVAL_ASSERTION = "EVAL_ASSERTION",
  TELEMETRY_FLUSH = "TELEMETRY_FLUSH",
  COMPLETE = "COMPLETE",
  FATAL_HALT = "FATAL_HALT",

  // Legacy mappings for backward compatibility
  INIT_ENVIRONMENT = "INITIALIZING",
  PROMPT_PLANNER = "REASONING_PLANNER",
  VALIDATE_AST = "AST_VALIDATION",
  EXECUTE_SANDBOX = "SANDBOX_EXECUTION",
  FINOPS_SENTINEL = "PREDICTIVE_SENTINEL_EVAL",
  HALT_TERMINAL = "COMPLETE",
}

export enum TrajectoryStatus {
  QUEUED = "QUEUED",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  BUDGET_EXCEEDED = "BUDGET_EXCEEDED",
  EARLY_HALTED = "EARLY_HALTED",
  TIMEOUT = "TIMEOUT",
}

export interface ModelLeaderboardEntry {
  model_id: string;
  name: string;
  provider: "Google" | "Anthropic" | "OpenAI" | "Meta" | "Benchpress Hybrid" | "DeepSeek";
  task_suite: "SWE_BENCH_VERIFIED" | "HUMANEVAL_XL" | "CYBENCH";
  cpr_usd: number; // Cost per resolution ($)
  pass_at_1: number; // 0.0 to 1.0
  trajectory_bloat_ratio: number; // Actual turns / optimal turns
  mean_latency_sec: number;
  ast_healing_success_rate: number; // 0.0 to 1.0
  is_pareto_frontier: boolean;
  context_window_tokens: number;
  price_per_1m_input: number;
  price_per_1m_output: number;
}

export interface BenchmarkLeaderboardRow {
  modelId: string;
  modelName: string;
  provider: string;
  taskSuite: string;
  passRatePct: number;
  cprUsd: number;
  meanTurns: number;
  meanLatencySeconds: number;
  astHealingCount: number;
  tokenVelocityKps?: number;
  paretoFrontier: boolean;
}

export interface TrajectoryTurnEvent {
  turn_index: number;
  state: FsmState | string;
  model_id: string;
  prompt_tokens: number;
  completion_tokens: number;
  reasoning_tokens?: number;
  turn_cost_usd: number;
  cumulative_cost_usd: number;
  latency_ms: number;
  tool_call_name?: string;
  tool_call_payload?: Record<string, any>;
  ast_healed: boolean;
  ast_healing_trace?: string;
  sandbox_exit_code: number;
  sandbox_stdout?: string;
  sandbox_stderr?: string;
  git_tree_hash?: string;
  timestamp: string;
}

export interface TrajectoryStreamMessage {
  type: "STATE_CHANGE" | "TURN_COMPLETED" | "AST_HEAL_TRIGGERED" | "GIT_ROLLBACK_EXECUTED" | "TRAJECTORY_FINISHED";
  trajectory_id: string;
  state?: FsmState | string;
  turn?: TrajectoryTurnEvent;
  status?: string;
  pass_at_1?: boolean;
  total_cost_usd?: number;
  message?: string;
}

export interface ParetoPoint {
  model_id: string;
  name: string;
  provider: string;
  cpr_usd: number;
  pass_at_1: number;
  latency_sec: number;
  efficiency_score: number;
  is_pareto_frontier: boolean;
  is_recommended: boolean;
}

export interface ParetoDataPoint {
  model_id?: string;
  modelId?: string;
  name?: string;
  modelName?: string;
  provider: string;
  cpr_usd?: number;
  cprUsd?: number;
  pass_at_1?: number;
  passRatePct?: number;
  latency_sec?: number;
  meanLatencySeconds?: number;
  efficiency_score?: number;
  is_pareto_frontier?: boolean;
  isOnFrontier?: boolean;
  is_recommended?: boolean;
}

export interface VoiceDomSyncEvent {
  action: "HIGHLIGHT_TURN" | "UPDATE_PARETO_WEIGHTS" | "OPEN_DIFF_VIEWER" | "TRIGGER_AST_HEAL";
  targetTurn?: number;
  costWeight?: number;
  message: string;
}
