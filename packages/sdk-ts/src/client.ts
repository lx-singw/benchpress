/**
 * Universal Benchpress API Client (@benchpress/sdk).
 * Isomorphic HTTP client for Node.js, Bun, Deno, and modern browsers.
 */

import {
  BenchpressClientOptions,
  RoutingRecommendationRequest,
  RoutingRecommendationResponse,
  BenchmarkListRequest,
  BenchmarkListResponse,
  DispatchTrajectoryRequest,
  DispatchTrajectoryResponse,
  TrajectoryStatusResponse,
} from "./types";
import { BenchpressError, AuthenticationError, RateLimitError, ValidationError } from "./errors";

export class BenchpressClient {
  private readonly apiKey?: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;

  constructor(options: BenchpressClientOptions = {}) {
    this.apiKey = options.apiKey || (typeof process !== "undefined" ? process.env?.BENCHPRESS_API_KEY : undefined);
    this.baseUrl = options.baseUrl || "http://localhost:3000";
    this.timeoutMs = options.timeoutMs || 10000;
    this.maxRetries = options.maxRetries || 2;
  }

  private async fetchWithRetry<T>(path: string, init: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      "User-Agent": "benchpress-sdk-ts/1.0.0",
      ...(init.headers as Record<string, string>),
    };

    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

        const response = await fetch(url, {
          ...init,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          if (response.status === 401) {
            throw new AuthenticationError(body.message || "Unauthorized API request");
          } else if (response.status === 429) {
            throw new RateLimitError(body.message || "Too many requests to Benchpress API");
          } else if (response.status === 400) {
            throw new ValidationError(body.message || "Invalid request payload", body.errors);
          } else {
            throw new BenchpressError(
              body.message || `HTTP ${response.status} from Benchpress API`,
              response.status,
              body.code
            );
          }
        }

        return (await response.json()) as T;
      } catch (err: any) {
        lastError = err;
        if (err instanceof BenchpressError && (err.status === 400 || err.status === 401)) {
          throw err; // Do not retry validation or auth errors
        }
        if (attempt < this.maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 200));
        }
      }
    }

    throw lastError || new BenchpressError("Request failed after retries");
  }

  /**
   * Compute dynamic Pareto model routing recommendation.
   */
  public async getRoutingRecommendation(
    request: RoutingRecommendationRequest
  ): Promise<RoutingRecommendationResponse> {
    return this.fetchWithRetry<RoutingRecommendationResponse>("/api/v1/routing-recommendation", {
      method: "POST",
      body: JSON.stringify({
        task_type: request.taskType,
        codebase_language: request.codebaseLanguage,
        current_model: request.currentModel || "claude-3-7-sonnet",
        max_budget_per_task_usd: request.maxBudgetPerTaskUsd,
        estimated_prompt_tokens: request.estimatedPromptTokens,
        estimated_completion_tokens: request.estimatedCompletionTokens,
        pareto_weights: request.paretoWeights,
      }),
    });
  }

  /**
   * Query filtered economic leaderboard and multi-benchmark catalog.
   */
  public async listBenchmarks(request: BenchmarkListRequest = {}): Promise<BenchmarkListResponse> {
    const params = new URLSearchParams();
    if (request.suite) params.append("suite", request.suite);
    if (request.provider) params.append("provider", request.provider);
    if (request.paretoOnly) params.append("paretoOnly", "true");
    if (request.maxCpr !== undefined) params.append("maxCpr", String(request.maxCpr));

    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.fetchWithRetry<BenchmarkListResponse>(`/api/v1/benchmarks${qs}`, {
      method: "GET",
    });
  }

  /**
   * Dispatch an asynchronous trajectory evaluation run.
   */
  public async dispatchTrajectory(
    request: DispatchTrajectoryRequest
  ): Promise<DispatchTrajectoryResponse> {
    return this.fetchWithRetry<DispatchTrajectoryResponse>("/api/v1/trajectory-run", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Retrieve live execution telemetry and turn traces for a trajectory ID.
   */
  public async getTrajectoryStatus(trajectoryId: string): Promise<TrajectoryStatusResponse> {
    return this.fetchWithRetry<TrajectoryStatusResponse>(`/api/v1/trajectories/${trajectoryId}`, {
      method: "GET",
    });
  }
}
