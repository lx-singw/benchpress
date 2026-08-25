/**
 * @benchpress/sdk
 * Production TypeScript SDK Client for Benchpress Model Routing & Trajectory Intelligence.
 */

import { FsmState, TrajectoryStatus, TaskSuite } from "@benchpress/telemetry";

export { FsmState, TrajectoryStatus, TaskSuite };

export interface RoutingRecommendation {
  recommendedStrategy: string;
  plannerModel: string;
  coderModel: string;
  rationale: string;
  projectedCprUsd: number;
  projectedSavingsPct: number;
  confidenceScore: number;
  evaluatedAt: string;
}

export interface RoutingRecommendationRequest {
  task_type: string;
  current_model: string;
  budget_limit_usd?: number;
  latency_target_ms?: number;
}

export interface TrajectorySubmissionRequest {
  task_suite: string;
  task_id: string;
  model_id: string;
  budget_limit_usd?: number;
  max_turns?: number;
  metadata?: Record<string, unknown>;
}

export interface TrajectorySubmissionResponse {
  trajectory_id: string;
  status: TrajectoryStatus | string;
  queue_name: string;
  enqueued_at: string;
  status_url: string;
}

export interface BenchmarkLeaderboardEntry {
  modelId: string;
  modelName: string;
  provider: string;
  taskSuite: string;
  passRatePct: number;
  cprUsd: number;
  meanTurns: number;
  meanLatencySeconds: number;
  astHealingCount: number;
  paretoFrontier: boolean;
}

export interface BenchpressClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeoutMs?: number;
}

export class BenchpressClient {
  private apiKey: string;
  private baseUrl: string;
  private timeoutMs: number;

  constructor(options: BenchpressClientOptions = {}) {
    this.apiKey = options.apiKey || process.env.BENCHPRESS_API_KEY || "";
    this.baseUrl = (options.baseUrl || process.env.BENCHPRESS_BASE_URL || "http://localhost:3000/api/v1").replace(/\/$/, "");
    this.timeoutMs = options.timeoutMs || 30000;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "User-Agent": "benchpress-sdk-ts/1.0.0",
      ...(options.headers as Record<string, string>),
    };

    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        throw new Error(`Benchpress API error (${response.status} ${response.statusText}): ${errorText}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  /**
   * Request an optimal model routing recommendation based on live Pareto frontier data.
   */
  async getRoutingRecommendation(params: RoutingRecommendationRequest): Promise<RoutingRecommendation> {
    return this.request<RoutingRecommendation>("/routing-recommendation", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Submit an autonomous agent trajectory task to the execution queue.
   */
  async submitTrajectory(params: TrajectorySubmissionRequest): Promise<TrajectorySubmissionResponse> {
    return this.request<TrajectorySubmissionResponse>("/trajectory-run", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Fetch latest benchmark leaderboard across model providers.
   */
  async getBenchmarks(suite?: string): Promise<{ benchmarks: BenchmarkLeaderboardEntry[]; generatedAt: string }> {
    const query = suite ? `?suite=${encodeURIComponent(suite)}` : "";
    return this.request<{ benchmarks: BenchmarkLeaderboardEntry[]; generatedAt: string }>(`/benchmarks${query}`, {
      method: "GET",
    });
  }
}
