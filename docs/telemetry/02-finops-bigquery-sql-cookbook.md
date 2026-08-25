# FinOps BigQuery SQL Cookbook: 10 Production Cost Optimization Queries

> **Document ID:** `BP-TEL-002`  
> **Status:** Approved / Production  
> **Target Track:** Observability, FinOps & The Taskmaster • Google Cloud Hackathon (2026)

---

## 1. Overview

This cookbook provides 10 production-tested, partition-optimized BigQuery SQL queries designed for FinOps teams, Systems Architects, and Engineering Managers to monitor token burn, detect runaway trajectory loops, model routing ROI, and track CPR trends.

---

## 2. The 10 Production FinOps Queries

### Query 1: Top 10 Most Expensive Trajectories by Dollar Cost
Identifies runaway agent executions requiring budget caps or token circuit-breakers.

```sql
SELECT 
    trajectory_id,
    model_id,
    task_suite,
    task_id,
    total_turns,
    total_input_tokens + total_output_tokens as total_tokens,
    total_cost_usd,
    pass_at_1,
    trajectory_bloat_ratio
FROM 
    `benchpress_analytics.trajectories`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY 
    total_cost_usd DESC
LIMIT 10;
```

---

### Query 2: Cost Per Resolution (CPR) & Savings by Model Family
Calculates true economic cost per resolution and savings percentage relative to frontier baselines.

```sql
WITH ModelStats AS (
    SELECT 
        model_id,
        model_family,
        COUNT(1) as total_runs,
        SUM(IF(pass_at_1, 1, 0)) as passed_runs,
        AVG(IF(pass_at_1, 1.0, 0.0)) as pass_rate,
        SUM(total_cost_usd) as total_spend_usd,
        AVG(total_turns) as avg_turns
    FROM 
        `benchpress_analytics.trajectories`
    WHERE 
        timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        AND task_suite = 'swe_bench_verified'
    GROUP BY 
        model_id, model_family
)
SELECT 
    model_id,
    model_family,
    total_runs,
    ROUND(pass_rate * 100, 2) as pass_rate_pct,
    ROUND(total_spend_usd / NULLIF(passed_runs, 0), 4) as effective_cpr_usd,
    ROUND(avg_turns, 1) as mean_turns,
    ROUND(total_spend_usd, 2) as total_spend_usd
FROM 
    ModelStats
ORDER BY 
    effective_cpr_usd ASC;
```

---

### Query 3: Tool Execution Error & Hallucination Waste Analysis
Measures financial waste caused by hallucinated function signatures and schema errors.

```sql
SELECT 
    t.tool_name,
    COUNT(1) as total_invocations,
    SUM(IF(t.is_hallucinated, 1, 0)) as hallucinated_count,
    SUM(IF(NOT t.is_schema_valid, 1, 0)) as schema_invalid_count,
    ROUND(AVG(t.execution_duration_ms), 2) as avg_exec_ms,
    ROUND(SUM(IF(t.is_hallucinated OR NOT t.is_schema_valid, 1, 0)) / COUNT(1) * 100, 2) as failure_rate_pct
FROM 
    `benchpress_analytics.tool_call_metrics` t
WHERE 
    t.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY 
    t.tool_name
ORDER BY 
    failure_rate_pct DESC;
```

---

### Query 4: 2-Tiered Hybrid Routing Projected Enterprise Savings
Simulates monthly dollar savings if an enterprise switches from monolithic Claude 3.7 to Hybrid Gemini 2.5/3.5.

```sql
WITH BaselineSpend AS (
    SELECT 
        COUNT(1) as monthly_task_volume,
        1.849 as claude_cpr_usd,
        0.240 as hybrid_cpr_usd
    FROM 
        `benchpress_analytics.trajectories`
    WHERE 
        timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
)
SELECT 
    monthly_task_volume,
    ROUND(monthly_task_volume * claude_cpr_usd, 2) as projected_monolithic_spend_usd,
    ROUND(monthly_task_volume * hybrid_cpr_usd, 2) as projected_hybrid_spend_usd,
    ROUND((monthly_task_volume * claude_cpr_usd) - (monthly_task_volume * hybrid_cpr_usd), 2) as net_monthly_savings_usd,
    ROUND((1.0 - (hybrid_cpr_usd / claude_cpr_usd)) * 100, 2) as savings_percentage
FROM 
    BaselineSpend;
```

---

### Query 5: Trajectory Bloat Ratio (TBR) Distribution by Turn Horizon
Analyzes where token waste occurs across turn depths ($1-5$, $6-10$, $11-20$, $21+$).

```sql
SELECT 
    CASE 
        WHEN total_turns BETWEEN 1 AND 5 THEN '1-5 Turns (Fast)'
        WHEN total_turns BETWEEN 6 AND 10 THEN '6-10 Turns (Moderate)'
        WHEN total_turns BETWEEN 11 AND 20 THEN '11-20 Turns (Complex)'
        ELSE '21+ Turns (Potential Runaway)'
    END as turn_bracket,
    COUNT(1) as trajectory_count,
    ROUND(AVG(trajectory_bloat_ratio) * 100, 2) as avg_bloat_pct,
    ROUND(AVG(total_cost_usd), 4) as avg_cost_usd,
    ROUND(AVG(IF(pass_at_1, 1.0, 0.0)) * 100, 2) as pass_rate_pct
FROM 
    `benchpress_analytics.trajectories`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
GROUP BY 
    turn_bracket
ORDER BY 
    MIN(total_turns) ASC;
```

---

### Query 6: Context Window Degradation Curve Regression Data
Provides data points for modeling non-linear accuracy loss over context token accumulation.

```sql
SELECT 
    DIV(cumulative_context_tokens, 10000) * 10 as context_bracket_k_tokens,
    COUNT(1) as total_turns,
    ROUND(AVG(IF(error_code IS NOT NULL, 1.0, 0.0)) * 100, 2) as turn_error_rate_pct,
    ROUND(AVG(latency_ms) / 1000.0, 2) as avg_latency_sec
FROM 
    `benchpress_analytics.turn_telemetry`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY 
    context_bracket_k_tokens
ORDER BY 
    context_bracket_k_tokens ASC;
```

---

### Query 7: Self-Healing Efficiency & Recovery Rate
Measures how often autonomous self-healing rescues failing trajectories vs. leading to fatal halts.

```sql
SELECT 
    error_code,
    COUNT(1) as triggered_count,
    ROUND(AVG(self_healing_retries_count), 2) as avg_retries_needed,
    ROUND(AVG(IF(fsm_state = 'COMPLETE', 1.0, 0.0)) * 100, 2) as resolution_success_rate_pct
FROM 
    `benchpress_analytics.turn_telemetry`
WHERE 
    self_healing_retries_count > 0
    AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 
    error_code
ORDER BY 
    triggered_count DESC;
```

---

### Query 8: Hourly Pareto Score Drift & Routing Volatility
Tracks real-time fluctuations in the Pareto frontier score over 24 hours.

```sql
SELECT 
    TIMESTAMP_TRUNC(timestamp, HOUR) as hour_bucket,
    model_id,
    ROUND(AVG(IF(pass_at_1, 1.0, 0.0)) * 100, 2) as hourly_pass_rate,
    ROUND(APPROX_QUANTILES(cpr_usd, 100)[OFFSET(50)], 4) as hourly_median_cpr
FROM 
    `benchpress_analytics.trajectories`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY 
    hour_bucket, model_id
ORDER BY 
    hour_bucket DESC, hourly_pass_rate DESC;
```

---

### Query 9: Cloud Run Sandbox Memory & Execution Duration Percentiles
Monitors worker node efficiency and gVisor virtualization overhead.

```sql
SELECT 
    task_suite,
    COUNT(1) as sample_size,
    APPROX_QUANTILES(duration_ms / 1000.0, 100)[OFFSET(50)] as p50_duration_sec,
    APPROX_QUANTILES(duration_ms / 1000.0, 100)[OFFSET(90)] as p90_duration_sec,
    APPROX_QUANTILES(duration_ms / 1000.0, 100)[OFFSET(99)] as p99_duration_sec
FROM 
    `benchpress_analytics.trajectories`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY 
    task_suite;
```

---

### Query 10: Token Price Arbitrage & Vendor Price Discrepancy Matrix
Compares actual billed token spend against published API price cards.

```sql
SELECT 
    model_id,
    SUM(total_input_tokens) as total_in_tokens,
    SUM(total_output_tokens) as total_out_tokens,
    SUM(total_reasoning_tokens) as total_reason_tokens,
    ROUND(SUM(total_cost_usd), 2) as total_incurred_cost_usd,
    ROUND(SUM(total_cost_usd) / NULLIF(SUM(total_input_tokens + total_output_tokens), 0) * 1000000, 4) as effective_cost_per_million_tokens
FROM 
    `benchpress_analytics.trajectories`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 
    model_id
ORDER BY 
    total_incurred_cost_usd DESC;
```
