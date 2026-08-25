import { FsmState, TrajectoryStatus, TaskSuite } from "@benchpress/telemetry";

export { FsmState, TrajectoryStatus, TaskSuite };

export interface BenchmarkLeaderboardRow {
  modelId: string;
  modelName: string;
  provider: "Google" | "Anthropic" | "OpenAI" | "Meta" | "Mistral" | string;
  taskSuite: string;
  passRatePct: number;
  cprUsd: number;
  meanTurns: number;
  meanLatencySeconds: number;
  astHealingCount: number;
  tokenVelocityKps: number;
  paretoFrontier: boolean;
}

export interface ParetoDataPoint {
  modelId: string;
  modelName: string;
  provider: string;
  cprUsd: number; // X-axis (Cost per Resolved Task)
  passRatePct: number; // Y-axis (Pass Rate %)
  meanLatencySeconds: number;
  isOnFrontier: boolean;
}

export interface TrajectoryTimelineStep {
  turnIndex: number;
  fsmState: FsmState;
  modelId: string;
  promptTokens: number;
  completionTokens: number;
  costUsd: number;
  latencyMs: number;
  actionSummary: string;
  astHealed: boolean;
  timestamp: string;
}

export interface LiveTrajectorySession {
  trajectoryId: string;
  modelId: string;
  taskSuite: string;
  taskId: string;
  status: TrajectoryStatus;
  currentTurn: number;
  maxTurns: number;
  accumulatedCostUsd: number;
  budgetCapUsd: number;
  steps: TrajectoryTimelineStep[];
  startedAt: string;
}
