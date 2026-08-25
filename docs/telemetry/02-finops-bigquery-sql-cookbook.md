# FinOps BigQuery SQL Cookbook: 10 Production Analytical Queries

> **Document ID:** `BP-TEL-002`  
> **Status:** Approved / Production Standard  
> **Target Track:** Observability & FinOps • Google Cloud Hackathon (2026)

---

## 1. Analytics Schema & FinOps Query Philosophy

Benchpress multi-turn telemetry is streamed in real time via the **BigQuery Storage Write API** into partitioned and clustered dataset tables (`benchpress_analytics.trajectories`, `benchpress_analytics.turns`, `benchpress_analytics.events`).

This cookbook provides **10 production-grade SQL recipes** utilizing Common Table Expressions (CTEs), analytical window functions, array aggregations, and mathematical statistics to power real-time dashboards, FinOps token accounting, and dynamic model routing.

---

## 2. Query 1: Cost Per Resolution (CPR) Leaderboard across Complexity Tiers

```sql
-- Query 1: Computes median CPR and Pass@1 across all benchmark complexity tiers
WITH TaskMetrics AS (
  SELECT
    model_id,
    task_suite,
    complexity_tier,
    COUNT(trajectory_id) AS total_runs,
    COUNTIF(pass_at_1) AS successful_resolutions,
    SUM(total_cost_usd) AS total_spend_usd,
    -- Pass@1 Accuracy Percentage
    ROUND(COUNTIF(pass_at_1) / COUNT(trajectory_id) * 100, 2) AS pass_at_1_pct,
    -- Cost Per Resolution (CPR) = Total Spend / Successful Resolutions
    ROUND(SUM(total_cost_usd) / NULLIF(COUNTIF(pass_at_1), 0), 4) AS cpr_usd
  FROM `benchpress_analytics.trajectories`
  WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY model_id, task_suite, complexity_tier
)
SELECT
  model_id,
  task_suite,
  complexity_tier,
  total_runs,
  pass_at_1_pct,
  cpr_usd,
  DENSE_RANK() OVER (PARTITION BY complexity_tier ORDER BY cpr_usd ASC) AS economic_rank
FROM TaskMetrics
ORDER BY complexity_tier ASC, cpr_usd ASC;
```

---

## 3. Query 2: Trajectory Bloat Ratio (TBR) & Token Waste Breakdown

```sql
-- Query 2: Identifies token waste and calculates Trajectory Bloat Ratio (TBR)
WITH TrajectoryAggs AS (
  SELECT
    t.model_id,
    t.trajectory_id,
    t.pass_at_1,
    t.total_turns,
    SUM(tn.input_tokens + tn.output_tokens) AS total_tokens_used,
    -- Optimal baseline tokens (first 3 turns)
    SUM(CASE WHEN tn.turn_number <= 3 THEN tn.input_tokens + tn.output_tokens ELSE 0 END) AS baseline_tokens
  FROM `benchpress_analytics.trajectories` t
  JOIN `benchpress_analytics.turns` tn ON t.trajectory_id = tn.trajectory_id
  WHERE t.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  GROUP BY t.model_id, t.trajectory_id, t.pass_at_1, t.total_turns
)
SELECT
  model_id,
  COUNT(trajectory_id) AS evaluated_trajectories,
  ROUND(AVG(total_turns), 1) AS avg_turns_per_task,
  ROUND(AVG(total_tokens_used), 0) AS avg_tokens_consumed,
  -- TBR = Total Tokens / Baseline Tokens
  ROUND(AVG(total_tokens_used / NULLIF(baseline_tokens, 0)), 2) AS avg_trajectory_bloat_ratio,
  ROUND(SUM(CASE WHEN NOT pass_at_1 THEN total_tokens_used ELSE 0 END) / SUM(total_tokens_used) * 100, 2) AS wasted_token_pct
FROM TrajectoryAggs
GROUP BY model_id
ORDER BY avg_trajectory_bloat_ratio ASC;
```

---

## 4. Query 3: Context Rot & Cognitive Decay Turn-by-Turn Analysis

```sql
-- Query 3: Measures failure probability and tool hallucination rate as turn depth increases
SELECT
  turn_number,
  COUNT(turn_id) AS total_turn_invocations,
  COUNTIF(has_schema_error) AS schema_error_count,
  ROUND(COUNTIF(has_schema_error) / COUNT(turn_id) * 100, 2) AS schema_error_rate_pct,
  ROUND(AVG(turn_latency_ms), 0) AS avg_turn_latency_ms,
  ROUND(AVG(input_tokens), 0) AS avg_context_window_size
FROM `benchpress_analytics.turns`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
GROUP BY turn_number
HAVING total_turn_invocations >= 20
ORDER BY turn_number ASC;
```

---

## 5. Query 4: Real-Time Pareto Frontier Derivation (Accuracy vs. Cost)

```sql
-- Query 4: Derives non-dominated Pareto optimal models across all suites
WITH ModelAggregates AS (
  SELECT
    model_id,
    ROUND(COUNTIF(pass_at_1) / COUNT(trajectory_id) * 100, 2) AS accuracy_pct,
    ROUND(AVG(total_cost_usd), 4) AS avg_cost_usd
  FROM `benchpress_analytics.trajectories`
  WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  GROUP BY model_id
)
SELECT
  a.model_id,
  a.accuracy_pct,
  a.avg_cost_usd,
  -- A model is Pareto optimal if no other model has higher accuracy AND lower cost
  NOT EXISTS (
    SELECT 1 FROM ModelAggregates b
    WHERE b.accuracy_pct >= a.accuracy_pct 
      AND b.avg_cost_usd <= a.avg_cost_usd
      AND (b.accuracy_pct > a.accuracy_pct OR b.avg_cost_usd < a.avg_cost_usd)
  ) AS is_pareto_optimal
FROM ModelAggregates a
ORDER BY a.accuracy_pct DESC, a.avg_cost_usd ASC;
```

---

## 6. Query 5: Autonomous AST Tool-Healer Recovery Effectiveness

```sql
-- Query 5: Evaluates the recovery rate and financial savings from Supervisor AST tool-healing
SELECT
  model_id,
  COUNTIF(supervisor_healing_triggered) AS total_healed_attempts,
  COUNTIF(supervisor_healing_triggered AND pass_at_1) AS recovered_resolutions,
  ROUND(COUNTIF(supervisor_healing_triggered AND pass_at_1) / NULLIF(COUNTIF(supervisor_healing_triggered), 0) * 100, 2) AS healing_recovery_rate_pct,
  ROUND(SUM(CASE WHEN supervisor_healing_triggered AND pass_at_1 THEN estimated_saved_spend_usd ELSE 0 END), 2) AS total_saved_spend_usd
FROM `benchpress_analytics.trajectories`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY model_id
ORDER BY total_saved_spend_usd DESC;
```

---

## 7. Query 6: Predictive Budget Sentinel (Turn 5) Model Downgrade ROI

```sql
-- Query 6: Measures cost savings and accuracy impact when models are down-tiered from Pro to Flash at Turn 5
SELECT
  sentinel_action,
  COUNT(trajectory_id) AS total_trajectories,
  ROUND(COUNTIF(pass_at_1) / COUNT(trajectory_id) * 100, 2) AS resolution_rate_pct,
  ROUND(AVG(total_cost_usd), 4) AS avg_cost_per_task_usd,
  ROUND(SUM(saved_budget_usd), 2) AS aggregate_saved_usd
FROM `benchpress_analytics.trajectories`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY sentinel_action
ORDER BY total_trajectories DESC;
```

---

## 8. Query 7: Multi-Turn Tool Invocation Frequency & Latency Percentiles

```sql
-- Query 7: Calculates tool usage distributions and p50, p95, p99 execution latencies
SELECT
  tool_name,
  COUNT(event_id) AS total_invocations,
  ROUND(COUNTIF(exit_code = 0) / COUNT(event_id) * 100, 2) AS tool_success_rate_pct,
  APPROX_QUANTILES(execution_duration_ms, 100)[OFFSET(50)] AS p50_duration_ms,
  APPROX_QUANTILES(execution_duration_ms, 100)[OFFSET(95)] AS p95_duration_ms,
  APPROX_QUANTILES(execution_duration_ms, 100)[OFFSET(99)] AS p99_duration_ms
FROM `benchpress_analytics.events`
WHERE event_type = 'TOOL_EXECUTION'
  AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY tool_name
ORDER BY total_invocations DESC;
```

---

## 9. Query 8: Closed-Loop Canary Drift Detection & Regression Alerting

```sql
-- Query 8: Detects foundation model CPR regressions > 10% between consecutive 6-hour canary sweeps
WITH CanarySweeps AS (
  SELECT
    model_id,
    sweep_id,
    sweep_timestamp,
    ROUND(SUM(total_cost_usd) / NULLIF(COUNTIF(pass_at_1), 0), 4) AS sweep_cpr_usd,
    LAG(ROUND(SUM(total_cost_usd) / NULLIF(COUNTIF(pass_at_1), 0), 4), 1) OVER (
      PARTITION BY model_id ORDER BY sweep_timestamp ASC
    ) AS prior_sweep_cpr_usd
  FROM `benchpress_analytics.canary_runs`
  WHERE sweep_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  GROUP BY model_id, sweep_id, sweep_timestamp
)
SELECT
  model_id,
  sweep_id,
  sweep_timestamp,
  sweep_cpr_usd,
  prior_sweep_cpr_usd,
  -- Calculate Delta CPR Percentage
  ROUND(((sweep_cpr_usd - prior_sweep_cpr_usd) / prior_sweep_cpr_usd) * 100, 2) AS delta_cpr_pct,
  CASE 
    WHEN ((sweep_cpr_usd - prior_sweep_cpr_usd) / prior_sweep_cpr_usd) > 0.10 THEN 'ALERT: REGRESSION DETECTED'
    WHEN ((sweep_cpr_usd - prior_sweep_cpr_usd) / prior_sweep_cpr_usd) < -0.10 THEN 'NOTICE: EFFICIENCY GAIN'
    ELSE 'STABLE'
  END AS drift_status
FROM CanarySweeps
WHERE prior_sweep_cpr_usd IS NOT NULL
ORDER BY sweep_timestamp DESC;
```

---

## 10. Query 9: CI/CD Auto-Remediation CPR Savings vs. Human Engineer Cost

```sql
-- Query 9: Computes total dollar ROI from automated GitHub Actions crash-to-PR remediation
SELECT
  COUNT(remediation_id) AS total_ci_crashes_remediated,
  ROUND(AVG(remediation_duration_seconds) / 60, 1) AS avg_resolution_time_minutes,
  ROUND(SUM(total_tokens_spend_usd), 2) AS total_ai_inference_spend_usd,
  -- Assuming human software engineer average cost of $120.00 / hour ($2.00 / minute)
  ROUND(SUM(human_engineer_baseline_minutes * 2.00), 2) AS human_labor_equivalent_usd,
  -- Net Savings = Human Cost - AI Spend
  ROUND(SUM(human_engineer_baseline_minutes * 2.00) - SUM(total_tokens_spend_usd), 2) AS net_enterprise_savings_usd,
  ROUND((1 - (SUM(total_tokens_spend_usd) / SUM(human_engineer_baseline_minutes * 2.00))) * 100, 2) AS cost_reduction_pct
FROM `benchpress_analytics.ci_remediations`
WHERE status = 'PR_MERGED'
  AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY);
```

---

## 11. Query 10: Real-Time Provider Price Arbitrage Opportunity Identification

```sql
-- Query 10: Calculates the economic spread between monolithic frontier models and hybrid routes
WITH LatestEconomics AS (
  SELECT
    model_id,
    AVG(cpr_score_usd) AS current_cpr_usd,
    AVG(pass_at_1_pct) AS current_accuracy_pct
  FROM `benchpress_analytics.pareto_indices`
  WHERE calculated_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  GROUP BY model_id
)
SELECT
  frontier.model_id AS frontier_monolithic_model,
  frontier.current_cpr_usd AS frontier_cpr_usd,
  hybrid.model_id AS recommended_hybrid_route,
  hybrid.current_cpr_usd AS hybrid_cpr_usd,
  -- Arbitrage Spread = Frontier CPR - Hybrid CPR
  ROUND(frontier.current_cpr_usd - hybrid.current_cpr_usd, 4) AS arbitrage_spread_usd,
  ROUND(((frontier.current_cpr_usd - hybrid.current_cpr_usd) / frontier.current_cpr_usd) * 100, 2) AS savings_potential_pct
FROM LatestEconomics frontier
CROSS JOIN LatestEconomics hybrid
WHERE frontier.model_id = 'claude-3-7-sonnet'
  AND hybrid.model_id = 'hybrid-gemini-pro-flash';
```
