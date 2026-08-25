# OpenAPI 3.0 REST API Specification & Payload Schemas

> **Document ID:** `BP-API-001`  
> **Status:** Approved / Production  
> **Target Track:** Developer Ecosystem & System Architecture • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. API Architecture & Global Conventions

The Benchpress REST API provides high-throughput programmatic access to real-time model routing rationales, dynamic Pareto frontier calculations, and asynchronous benchmark task execution.

- **Base URL:** `https://api.benchpress.ai/api/v1` (or local GCP endpoint `https://benchpress-api-gateway-uc.a.run.app/api/v1`)
- **Authentication:** Bearer API Token (`Authorization: Bearer bp_live_...`)
- **Rate Limits:** Standard: 1,000 req/min; Enterprise: 10,000 req/min
- **Response Format:** `application/json` with ISO-8601 UTC timestamps

---

## 2. Complete OpenAPI 3.0 Specification (YAML)

```yaml
openapi: 3.0.3
info:
  title: Benchpress Intelligence & Model Routing API
  version: 1.0.0
  description: >
    Production-grade economic and trajectory intelligence platform for autonomous AI agents.
    Powers dynamic model routing for Cursor, Windsurf, Not Diamond, and enterprise AI gateways.
servers:
  - url: https://api.benchpress.ai/api/v1
    description: Production Global Gateway (GCP us-central1)

paths:
  /routing-recommendation:
    post:
      summary: Fetch Real-Time Model Routing Recommendation & Rationale
      operationId: getRoutingRecommendation
      description: >
        Analyzes task complexity, target language, and budget constraints to return the mathematically
        optimal model choreography recipe with human-readable rationales and projected cost savings.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RoutingRequest'
      responses:
        '200':
          description: Optimal routing recipe computed successfully.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RoutingResponse'
        '400':
          $ref: '#/components/schemas/ErrorResponse'
        '429':
          $ref: '#/components/schemas/ErrorResponse'

  /benchmarks:
    get:
      summary: Query Aggregated Economic Leaderboard & Benchmark Scores
      operationId: listBenchmarks
      parameters:
        - name: suite
          in: query
          schema:
            type: string
            enum: [swe_bench_verified, financial_recon, multi_doc_ops]
            default: swe_bench_verified
        - name: sort_by
          in: query
          schema:
            type: string
            enum: [pareto_score, cpr_usd, pass_at_1, latency_ms]
            default: pareto_score
      responses:
        '200':
          description: List of aggregated model benchmark scores.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BenchmarkListResponse'

  /trajectory-run:
    post:
      summary: Dispatch Asynchronous Agent Benchmark Trajectory
      operationId: dispatchTrajectoryRun
      description: >
        Enqueues an asynchronous benchmark run on the Cloud Tasks fleet inside isolated gVisor sandboxes.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TrajectoryRunRequest'
      responses:
        '202':
          description: Benchmark task successfully enqueued.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrajectoryRunAcceptedResponse'

  /trajectories/{id}:
    get:
      summary: Retrieve Live Telemetry Trace & Step Breakdown
      operationId: getTrajectoryDetails
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Complete multi-turn trajectory trace.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrajectoryDetailResponse'

components:
  schemas:
    RoutingRequest:
      type: object
      required:
        - task_type
        - codebase_language
        - current_model
      properties:
        task_type:
          type: string
          enum: [code_bug_fix, architectural_refactor, financial_extraction, quick_edit]
        codebase_language:
          type: string
          example: python
        current_model:
          type: string
          example: claude-3-7-sonnet
        max_budget_per_task_usd:
          type: number
          format: float
          default: 0.50
        pareto_weights:
          type: object
          properties:
            accuracy: { type: number, default: 0.5 }
            cost: { type: number, default: 0.4 }
            latency: { type: number, default: 0.1 }

    RoutingResponse:
      type: object
      properties:
        recommended_strategy:
          type: string
          enum: [HYBRID_CHOREOGRAPHY, MONOLITHIC_FRONTIER, FAST_CODER]
          example: HYBRID_CHOREOGRAPHY
        planner_model:
          type: string
          example: gemini-2.5-pro
        coder_model:
          type: string
          example: gemini-3.5-flash
        rationale:
          type: string
          example: "Switching to Hybrid (Gemini 2.5 Pro + 3.5 Flash) provides 48.6% Pass@1 (+0.7% vs Claude 3.7 Sonnet) while reducing Cost Per Resolution by 87.0% ($0.24 vs $1.85)."
        projected_cpr_usd:
          type: number
          example: 0.24
        projected_savings_pct:
          type: number
          example: 87.0
        confidence_score:
          type: number
          example: 0.96

    BenchmarkListResponse:
      type: object
      properties:
        total_models:
          type: integer
        benchmarks:
          type: array
          items:
            type: object
            properties:
              model_id: { type: string }
              pass_at_1: { type: number }
              median_cpr_usd: { type: number }
              mean_turns: { type: number }
              bloat_ratio: { type: number }
              pareto_score: { type: number }

    TrajectoryRunRequest:
      type: object
      required:
        - task_suite
        - task_id
        - model_id
      properties:
        task_suite: { type: string, example: swe_bench_verified }
        task_id: { type: string, example: django__django-11099 }
        model_id: { type: string, example: gemini-hybrid-2.5-3.5 }
        max_turns: { type: integer, default: 20 }
        budget_cap_usd: { type: number, default: 2.00 }

    TrajectoryRunAcceptedResponse:
      type: object
      properties:
        trajectory_id: { type: string, example: tr_992140a }
        status: { type: string, example: ENQUEUED }
        estimated_start_ms: { type: integer, example: 400 }

    TrajectoryDetailResponse:
      type: object
      properties:
        trajectory_id: { type: string }
        status: { type: string, example: COMPLETE }
        pass_at_1: { type: boolean, example: true }
        total_turns: { type: integer, example: 4 }
        total_cost_usd: { type: number, example: 0.0245 }
        cpr_usd: { type: number, example: 0.0245 }
        turns:
          type: array
          items:
            type: object
            properties:
              turn_number: { type: integer }
              model_id: { type: string }
              fsm_state: { type: string }
              input_tokens: { type: integer }
              output_tokens: { type: integer }
              turn_cost_usd: { type: number }

    ErrorResponse:
      type: object
      properties:
        error_code: { type: string }
        message: { type: string }
        timestamp: { type: string }
```
