/**
 * Main Entry Point for @benchpress/sdk (TypeScript SDK).
 */

export { BenchpressClient } from "./client";
export { TrajectoryStreamClient } from "./websocket";
export {
  BenchpressError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
} from "./errors";
export type {
  BenchpressClientOptions,
  TaskType,
  CodebaseLanguage,
  RoutingRecommendationRequest,
  RoutingRecommendationResponse,
  BenchmarkListRequest,
  BenchmarkListResponse,
  BenchmarkRow,
  DispatchTrajectoryRequest,
  DispatchTrajectoryResponse,
  TrajectoryStatusResponse,
} from "./types";
export type { TrajectoryStreamListener } from "./websocket";
