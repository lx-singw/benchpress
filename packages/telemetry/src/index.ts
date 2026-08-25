/**
 * @benchpress/telemetry
 * Shared OpenTelemetry GenAI semantics, BigQuery schemas, and event contracts.
 */

export enum FsmState {
  INIT_ENVIRONMENT = "INIT_ENVIRONMENT",
  FETCH_TASK = "FETCH_TASK",
  PROMPT_PLANNER = "PROMPT_PLANNER",
  VALIDATE_AST = "VALIDATE_AST",
  AST_HEALING = "AST_HEALING",
  EXECUTE_SANDBOX = "EXECUTE_SANDBOX",
  GIT_SNAPSHOT = "GIT_SNAPSHOT",
  FINOPS_SENTINEL = "FINOPS_SENTINEL",
  EVALUATE_REWARD = "EVALUATE_REWARD",
  ROLLBACK_COMPENSATION = "ROLLBACK_COMPENSATION",
  COMPACT_MEMORY = "COMPACT_MEMORY",
  FINALIZE_TELEMETRY = "FINALIZE_TELEMETRY",
  HALT_TERMINAL = "HALT_TERMINAL",
}

export enum TrajectoryStatus {
  QUEUED = "QUEUED",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  BUDGET_EXCEEDED = "BUDGET_EXCEEDED",
  TIMEOUT = "TIMEOUT",
}

export enum TaskSuite {
  SWE_BENCH_VERIFIED = "SWE_BENCH_VERIFIED",
  HUMANEVAL_XL = "HUMANEVAL_XL",
  CYBENCH = "CYBENCH",
  GAIA = "GAIA",
}

export const GenAiSpanAttributes = {
  SYSTEM: "gen_ai.system",
  REQUEST_MODEL: "gen_ai.request.model",
  RESPONSE_MODEL: "gen_ai.response.model",
  PROMPT_TOKENS: "gen_ai.usage.prompt_tokens",
  COMPLETION_TOKENS: "gen_ai.usage.completion_tokens",
  TOTAL_TOKENS: "gen_ai.usage.total_tokens",
  COST_USD: "gen_ai.cost.usd",
  TEMPERATURE: "gen_ai.request.temperature",
  TOP_P: "gen_ai.request.top_p",
  FINISH_REASON: "gen_ai.response.finish_reasons",
  TRAJECTORY_ID: "benchpress.trajectory.id",
  TURN_NUMBER: "benchpress.trajectory.turn",
  FSM_STATE: "benchpress.fsm.state",
  AST_HEALED: "benchpress.ast.healed",
} as const;

export interface TurnTelemetryRecord {
  trajectoryId: string;
  turnIndex: number;
  fsmState: FsmState;
  modelId: string;
  promptTokens: number;
  completionTokens: number;
  cachedTokens: number;
  turnCostUsd: number;
  cumulativeCostUsd: number;
  latencyMs: number;
  toolCallName?: string;
  toolCallArguments?: string;
  astHealingAttempted: boolean;
  astHealingSucceeded: boolean;
  sandboxExitCode?: number;
  sandboxStdout?: string;
  sandboxStderr?: string;
  gitCommitHash?: string;
  timestamp: string;
}

export interface TrajectoryRunRecord {
  trajectoryId: string;
  taskSuite: TaskSuite | string;
  taskId: string;
  modelId: string;
  status: TrajectoryStatus;
  totalTurns: number;
  totalCostUsd: number;
  cprUsd: number; // Cost per Resolved Task
  durationSeconds: number;
  resolved: boolean;
  earlyHalted: boolean;
  haltReason?: string;
  astHealingCount: number;
  memoryCompactionPct: number;
  gitSnapshotCount: number;
  startedAt: string;
  completedAt?: string;
}

export interface AstHealingEvent {
  trajectoryId: string;
  turnIndex: number;
  originalPayload: string;
  repairedPayload: string;
  errorType: "SCHEMA_MISMATCH" | "SYNTAX_ERROR" | "TYPE_COERCION" | "UNKNOWN_PARAM";
  astDiff: string;
  healerLatencyMs: number;
  success: boolean;
  timestamp: string;
}

export interface BudgetSentinelEvent {
  trajectoryId: string;
  turnIndex: number;
  projectedTurnsRemaining: number;
  projectedCostUsd: number;
  budgetLimitUsd: number;
  velocityTokensPerTurn: number;
  actionTaken: "CONTINUE" | "EARLY_HALT" | "THROTTLE";
  confidenceScore: number;
  timestamp: string;
}

export interface RoutingTelemetryEvent {
  requestId: string;
  taskType: string;
  inputTokensEstimated: number;
  budgetCapUsd: number;
  latencyTargetMs: number;
  recommendedModel: string;
  fallbackModel: string;
  projectedCprUsd: number;
  projectedSavingsPct: number;
  timestamp: string;
}
