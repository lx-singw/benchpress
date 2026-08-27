/**
 * Strict TypeScript Request & Response Schemas for @benchpress/sdk.
 */

export interface BenchpressClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeoutMs?: number;
  maxRetries?: number;
}

export type TaskType =
  | "code_bug_fix"
  | "architectural_refactor"
  | "financial_extraction"
  | "quick_edit";

export type CodebaseLanguage =
  | "python"
  | "typescript"
  | "rust"
  | "go"
  | "java";

export interface RoutingRecommendationRequest {
  taskType: TaskType;
  codebaseLanguage: CodebaseLanguage;
  currentModel?: string;
  maxBudgetPerTaskUsd?: number;
  estimatedPromptTokens?: number;
  estimatedCompletionTokens?: number;
  paretoWeights?: {
    accuracy?: number;
    cost?: number;
    latency?: number;
  };
}

export interface RoutingRecommendationResponse {
  status: "success" | "error";
  latency_ms: number;
  timestamp: string;
  recommendation: {
    recommendedStrategy: "FAST_CODER" | "HYBRID_CHOREOGRAPHY" | "HIGH_REASONING_PLANNER";
    plannerModel: string;
    coderModel: string;
    projectedCprUsd: number;
    currentModelCprUsd: number;
    projectedSavingsPct: number;
    passAt1EstimatePct: number;
    estimatedTurns: number;
    rationale: string;
    proxyConfig: {
      baseUrl: string;
      modelHeader: string;
    };
    query: {
      task_type: string;
      codebase_language: string;
      current_model: string;
    };
  };
}

export interface BenchmarkListRequest {
  suite?: string;
  provider?: string;
  paretoOnly?: boolean;
  maxCpr?: number;
}

export interface BenchmarkRow {
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

export interface BenchmarkListResponse {
  status: "success" | "error";
  count: number;
  timestamp: string;
  data: BenchmarkRow[];
}

export interface DispatchTrajectoryRequest {
  taskSuite: string;
  taskId: string;
  modelId: string;
  budgetLimitUsd?: number;
  maxTurns?: number;
}

export interface DispatchTrajectoryResponse {
  status: "queued" | "error";
  trajectoryId: string;
  taskSuite: string;
  taskId: string;
  modelId: string;
  budgetLimitUsd: number;
  maxTurns: number;
  estimatedDispatchLatencyMs: number;
}

export interface TrajectoryStatusResponse {
  status: "success" | "error";
  data: {
    trajectory_id: string;
    task_suite: string;
    task_id: string;
    model_id: string;
    status: string;
    current_state: string;
    pass_at_1: boolean;
    resolved: boolean;
    total_cost_usd: number;
    cpr_usd: number;
    trajectory_bloat_ratio: number;
    ast_heal_count: number;
    git_snapshots_count: number;
    turns_count: number;
    started_at: string;
    completed_at?: string;
    turns: Array<{
      turn_index: number;
      state: string;
      model_id: string;
      prompt_tokens: number;
      completion_tokens: number;
      turn_cost_usd: number;
      cumulative_cost_usd: number;
      latency_ms: number;
      tool_call_name?: string;
      ast_healed: boolean;
      sandbox_exit_code: number;
    }>;
  };
}
