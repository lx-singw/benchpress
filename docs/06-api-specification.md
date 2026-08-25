# 06. Developer API Specification

## 🌐 Overview & Authentication

The **Benchpress Developer API** is a high-throughput, low-latency REST interface engineered for AI model routers (e.g., Not Diamond, Cursor, Windsurf), enterprise AI gateways, and developer dashboards.

* **Base URL:** `https://benchpress.ai/api/v1` (or `http://localhost:3000/api/v1` locally)
* **Format:** JSON (`application/json`)
* **Authentication:** `Bearer <API_KEY>` (in `Authorization` header)

---

## 📡 Endpoints Summary

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/benchmarks` | Retrieve complete ranked leaderboard with CPR, Pareto, and reliability scores. |
| `GET` | `/api/v1/models/{id}` | Get in-depth metrics and context degradation curves for a single model. |
| `POST` | `/api/v1/routing-recommendation` | Query the dynamic rationale engine for the optimal model routing recipe. |
| `POST` | `/api/v1/trajectory-run` | Trigger an asynchronous background agent evaluation trajectory. |
| `GET` | `/api/v1/trajectories/{id}` | Query the live status, token telemetry, and execution trace of a trajectory. |

---

## 📋 Endpoint Details

### 1. `GET /api/v1/benchmarks`
Retrieves all ranked models filtered by task suite, category, or provider.

#### Query Parameters
* `task_suite` *(optional, string)*: Filter by `all`, `swe_bench_verified`, `financial_recon`, or `multi_doc_ops`.
* `provider` *(optional, string)*: Filter by `google`, `anthropic`, `openai`, `deepseek`, `meta`.
* `sort_by` *(optional, string)*: `cpr_asc`, `score_desc`, `pass_rate_desc`, `savings_desc`.

#### Example Response (`200 OK`)
```json
{
  "status": "success",
  "data": {
    "total_models": 12,
    "task_suite": "swe_bench_verified",
    "updated_at": "2026-08-25T18:30:00Z",
    "models": [
      {
        "id": "gemini-3-5-flash",
        "name": "Gemini 3.5 Flash",
        "provider": "Google",
        "category": "High-Efficiency Workhorse",
        "benchpress_overall_rating": 91.4,
        "pass_at_1": 84.2,
        "cost_per_resolution": 0.084,
        "tool_reliability_score": 96.8,
        "trajectory_bloat_ratio": 0.062,
        "context_degradation_50": 0.91,
        "recommended_routing_partner": "gemini-2-5-pro",
        "hybrid_cost_savings_pct": 71.4
      },
      {
        "id": "gemini-2-5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "Google",
        "category": "Frontier Reasoner",
        "benchpress_overall_rating": 94.8,
        "pass_at_1": 92.6,
        "cost_per_resolution": 0.420,
        "tool_reliability_score": 98.4,
        "trajectory_bloat_ratio": 0.038,
        "context_degradation_50": 0.96,
        "recommended_routing_partner": "gemini-3-5-flash",
        "hybrid_cost_savings_pct": 68.2
      }
    ]
  }
}
```

---

### 2. `POST /api/v1/routing-recommendation`
Computes the optimal model pair and generates a verifiable, human-readable rationale based on task complexity and budget targets.

#### Request Body
```json
{
  "task_type": "code_refactor_and_test",
  "task_description": "Refactor database query optimization logic and verify all integration tests pass.",
  "complexity_score": 3,
  "budget_sensitivity": "balanced"
}
```

#### Example Response (`200 OK`)
```json
{
  "status": "success",
  "recommendation": {
    "routing_mode": "hybrid_split",
    "planner_model": {
      "id": "gemini-2-5-pro",
      "name": "Gemini 2.5 Pro",
      "phase": "Architecture, Specification & PR Review",
      "thinking_effort": "medium"
    },
    "executor_model": {
      "id": "gemini-3-5-flash",
      "name": "Gemini 3.5 Flash",
      "phase": "High-Volume Code Generation & Unit Testing",
      "thinking_effort": "low"
    },
    "estimated_cost": 0.118,
    "baseline_frontier_cost": 0.412,
    "estimated_savings_pct": 71.4,
    "confidence_score": 0.95,
    "rationale": "For Level 3 refactoring tasks, routing architectural planning to Gemini 2.5 Pro and code implementation to Gemini 3.5 Flash achieves a 94% verified pass rate while reducing token expenditures by 71.4% compared to a single-model frontier baseline."
  }
}
```

---

### 3. `POST /api/v1/trajectory-run`
Dispatches an asynchronous benchmark evaluation into the Google Cloud sandbox queue.

#### Request Body
```json
{
  "model_id": "gemini-3-5-flash",
  "task_suite": "swe_bench_verified",
  "task_id": "swe_042_django_orm_leak",
  "thinking_effort": "low"
}
```

#### Example Response (`202 Accepted`)
```json
{
  "status": "accepted",
  "trajectory_id": "trj_99a81f3b7c2",
  "queued_at": "2026-08-25T18:45:00Z",
  "status_endpoint": "/api/v1/trajectories/trj_99a81f3b7c2"
}
```
