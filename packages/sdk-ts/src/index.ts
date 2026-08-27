/**
 * @benchpress/sdk
 * Production TypeScript SDK Client for Benchpress Model Routing, Trajectory Intelligence & IDE Integrations.
 */

import { FsmState, TrajectoryStatus, TaskSuite } from "@benchpress/telemetry";

export { FsmState, TrajectoryStatus, TaskSuite };

export interface RoutingRecommendation {
  recommended_strategy: "HYBRID_CHOREOGRAPHY" | "FLASH_ONLY" | "PRO_ONLY";
  planner_model: string;
  coder_model: string;
  estimated_cpr_usd: number;
  baseline_frontier_cost_usd: number;
  projected_savings_percent: number;
  expected_pass_at_1: number;
  expected_latency_sec: number;
  rationale: string;
  breakdown: {
    planner_turns_est: number;
    coder_turns_est: number;
    planner_cost_est: number;
    coder_cost_est: number;
  };
}

export interface RoutingRecommendationRequest {
  task_type: "code_bug_fix" | "feature_generation" | "refactor" | "test_assertion" | "general_agent" | string;
  language?: string;
  repo_size_lines?: number;
  cyclomatic_complexity?: number;
  cost_weight?: number; // 0.0 to 1.0
  max_latency_sec?: number;
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
  wsUrl?: string;
  timeoutMs?: number;
}

export class BenchpressClient {
  private apiKey: string;
  private baseUrl: string;
  private wsUrl: string;
  private timeoutMs: number;

  constructor(options: BenchpressClientOptions = {}) {
    this.apiKey = options.apiKey || (typeof process !== "undefined" ? process.env?.BENCHPRESS_API_KEY : "") || "";
    this.baseUrl = (
      options.baseUrl ||
      (typeof process !== "undefined" ? process.env?.BENCHPRESS_BASE_URL : "") ||
      "http://localhost:3000/api/v1"
    ).replace(/\/$/, "");
    this.wsUrl = (
      options.wsUrl ||
      (typeof process !== "undefined" ? process.env?.BENCHPRESS_WS_URL : "") ||
      "ws://localhost:8080"
    ).replace(/\/$/, "");
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

      const json = await response.json();
      return (json.data ?? json) as T;
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

  /**
   * Real-time WebSocket subscription to trajectory events (state transitions, AST repairs, tool outputs).
   */
  subscribeTrajectory(trajectoryId: string, onEvent: (event: any) => void): () => void {
    if (typeof WebSocket === "undefined") {
      // In Node.js environment without native WebSocket, gracefully return no-op unsubscriber
      return () => {};
    }

    const ws = new WebSocket(`${this.wsUrl}/ws/trajectories/${trajectoryId}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(data);
      } catch (err) {
        onEvent({ raw: event.data });
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }
}
