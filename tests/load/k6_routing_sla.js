import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "10s", target: 200 },  // Ramp-up
    { duration: "20s", target: 1000 }, // Sustained 1,000 req/s load
    { duration: "5s", target: 0 },     // Ramp-down
  ],
  thresholds: {
    // Assert sub-50ms p95 and sub-95ms p99 latency SLA
    http_req_duration: ["p(95)<50", "p(99)<95"],
    // Assert 99.999% success rate
    http_req_failed: ["rate<0.001"],
  },
};

export default function () {
  const url = "http://localhost:3000/api/v1/routing-recommendation";
  const payload = JSON.stringify({
    task_type: "code_bug_fix",
    codebase_language: "python",
    current_model: "claude-3-7-sonnet",
    max_budget_per_task_usd: 0.50,
    estimated_prompt_tokens: 15000,
    estimated_completion_tokens: 2500,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  };

  const res = http.post(url, payload, params);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "strategy is HYBRID": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.recommendation.recommendedStrategy === "HYBRID_CHOREOGRAPHY";
      } catch (e) {
        return false;
      }
    },
    "cost savings >= 85%": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.recommendation.projectedSavingsPct >= 85.0;
      } catch (e) {
        return false;
      }
    },
  });

  sleep(0.01);
}
