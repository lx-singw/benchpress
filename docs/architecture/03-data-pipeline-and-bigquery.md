# Data Pipeline, Telemetry Ingestion & BigQuery Analytics

> **Document ID:** `BP-ARCH-003`  
> **Status:** Historical target-state design — not deployed or verified
> **Target Track:** Best Architectural Design ($5,000) • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. Data Pipeline Architecture & Ingestion Flow

Benchpress processes millions of multi-turn telemetry metrics across thousands of concurrent asynchronous agent executions. To satisfy both **sub-millisecond live UI updates** and **petabyte-scale OLAP analytics**, Benchpress implements a dual-tier streaming pipeline:

```mermaid
flowchart TD
    subgraph AgentWorkerFleet["Cloud Run Gen2 Trajectory Sandbox Fleet"]
        Worker1["Worker Instance #1"]
        Worker2["Worker Instance #2"]
        WorkerN["Worker Instance #N"]
    end

    subgraph FastPath["Hot State & Live Stream Path"]
        Firestore["Firestore Native Mode<br/>(Live Step State & Leaderboard Cache)"]
        WebSocketRelay["Cloud Run WebSocket Relay<br/>(Push to Active UI Sessions)"]
    end

    subgraph BufferLayer["High-Throughput Ingestion Buffer"]
        RedisBuffer["Memorystore Redis 7.2<br/>(Micro-batch buffer: lists & stream hashes)"]
        FlushDaemon["Telemetry Flush Daemon<br/>(Cloud Run Sidecar / Batcher)"]
    end

    subgraph AnalyticsWarehouse["Analytical Data Warehouse (GCP)"]
        BigQueryWriteAPI["BigQuery Storage Write API<br/>(Default / Committed Stream)"]
        
        subgraph BigQueryTables["benchpress_analytics (Partitioned & Clustered)"]
            TableTrajectories["trajectories"]
            TableTurns["turn_telemetry"]
            TableTools["tool_call_metrics"]
            TableAggregates["aggregated_model_indices"]
        end
    end

    subgraph MaterializationLoop["Continuous Materialization Engine"]
        ScheduledQueries["BigQuery Scheduled Query<br/>(Hourly CPR & Pareto Rollups)"]
    end

    %% Worker Dispatches
    Worker1 -->|Live Step Update (gRPC)| Firestore
    Worker1 -->|RPUSH telemetry_queue| RedisBuffer
    Worker2 -->|RPUSH telemetry_queue| RedisBuffer
    WorkerN -->|RPUSH telemetry_queue| RedisBuffer

    Firestore -->|onSnapshot / Change Stream| WebSocketRelay

    %% Ingestion Buffer Flush
    RedisBuffer --> FlushDaemon
    FlushDaemon -->|Micro-batch Flush (Protobuf)| BigQueryWriteAPI
    BigQueryWriteAPI --> TableTrajectories
    BigQueryWriteAPI --> TableTurns
    BigQueryWriteAPI --> TableTools

    %% Analytics & Materialization
    TableTrajectories & TableTurns & TableTools --> ScheduledQueries
    ScheduledQueries --> TableAggregates
    TableAggregates -->|Cache Refresh Sync| Firestore
```

---

## 2. Production BigQuery DDL Schemas

All tables in the `benchpress_analytics` dataset are strictly typed, partitioned by timestamp dates, and clustered on multi-column query keys to ensure deterministic sub-second analytical execution.

### 2.1 Table: `trajectories`
Stores the top-level execution metadata, economic cost, and resolution outcome for each benchmark run.

```sql
-- DDL: benchpress_analytics.trajectories
CREATE TABLE IF NOT EXISTS `benchpress_analytics.trajectories` (
    trajectory_id STRING NOT NULL OPTIONS(description="Globally unique UUID for the benchmark trajectory run"),
    run_session_id STRING NOT NULL OPTIONS(description="Session grouping ID for multi-model comparisons"),
    model_id STRING NOT NULL OPTIONS(description="Fully qualified model identifier, e.g., gemini-2.5-pro, gemini-3.5-flash"),
    model_family STRING NOT NULL OPTIONS(description="Model family grouping: gemini, claude, gpt, deepseek, open-weights"),
    task_suite STRING NOT NULL OPTIONS(description="Benchmark suite: swe_bench_verified, financial_recon, multi_doc_ops"),
    task_id STRING NOT NULL OPTIONS(description="Specific test case ID, e.g., django__django-11099"),
    task_complexity_score FLOAT64 NOT NULL OPTIONS(description="Normalized task complexity score [0.0 - 1.0]"),
    
    -- Execution Status & Outcomes
    status STRING NOT NULL OPTIONS(description="Terminal status: COMPLETE, FAILED_ASSERTION, TIMEOUT, CIRCUIT_BREAKER"),
    pass_at_1 BOOLEAN NOT NULL OPTIONS(description="True if all ground-truth verification unit tests passed"),
    total_turns INT64 NOT NULL OPTIONS(description="Total agentic turns executed before resolution or halt"),
    duration_ms INT64 NOT NULL OPTIONS(description="Total wall-clock execution duration in milliseconds"),
    
    -- Economic & Token Telemetry
    total_input_tokens INT64 NOT NULL OPTIONS(description="Sum of all input tokens consumed across all turns"),
    total_output_tokens INT64 NOT NULL OPTIONS(description="Sum of all generated output tokens"),
    total_reasoning_tokens INT64 NOT NULL OPTIONS(description="Sum of all internal chain-of-thought tokens"),
    total_cost_usd NUMERIC NOT NULL OPTIONS(description="Total dollar cost incurred based on official provider pricing"),
    cpr_usd NUMERIC OPTIONS(description="Cost Per Resolution: total_cost_usd / (1.0 if pass_at_1 else 0.0)"),
    
    -- Efficiency Metrics
    trajectory_bloat_ratio FLOAT64 NOT NULL OPTIONS(description="Ratio of wasted/failed tool tokens to total tokens [0.0 - 1.0]"),
    context_degradation_score FLOAT64 NOT NULL OPTIONS(description="Decay metric measuring accuracy loss over token accumulation"),
    
    -- Audit & Storage
    patch_diff_gcs_uri STRING OPTIONS(description="Cloud Storage URI to raw git diff patch generated by agent"),
    stdout_log_gcs_uri STRING OPTIONS(description="Cloud Storage URI to complete sandboxed execution log"),
    client_ip_hash STRING OPTIONS(description="SHA-256 hashed client IP for rate limiting and fraud analysis"),
    timestamp TIMESTAMP NOT NULL OPTIONS(description="UTC timestamp of trajectory initiation")
)
PARTITION BY DATE(timestamp)
CLUSTER BY model_family, task_suite, task_complexity_score
OPTIONS(
    description="Primary analytical store for agent benchmark trajectory outcomes and economic metrics",
    require_partition_filter=TRUE
);
```

---

### 2.2 Table: `turn_telemetry`
Captures granular, turn-by-turn state transitions, context memory footprints, and reasoning latencies.

```sql
-- DDL: benchpress_analytics.turn_telemetry
CREATE TABLE IF NOT EXISTS `benchpress_analytics.turn_telemetry` (
    turn_id STRING NOT NULL OPTIONS(description="Unique turn identifier: {trajectory_id}_turn_{turn_number}"),
    trajectory_id STRING NOT NULL OPTIONS(description="Foreign key referencing trajectories.trajectory_id"),
    turn_number INT64 NOT NULL OPTIONS(description="Sequential turn index (1-indexed)"),
    model_id STRING NOT NULL OPTIONS(description="Model invoked for this specific turn (supports hybrid routing)"),
    fsm_state STRING NOT NULL OPTIONS(description="FSM state active during turn, e.g., PERCEPTION, REASONING, TOOL_INVOCATION"),
    
    -- Token Breakdown
    turn_input_tokens INT64 NOT NULL OPTIONS(description="Input tokens for this turn"),
    turn_output_tokens INT64 NOT NULL OPTIONS(description="Output tokens generated in this turn"),
    turn_reasoning_tokens INT64 NOT NULL OPTIONS(description="Reasoning/CoT tokens generated in this turn"),
    turn_cost_usd NUMERIC NOT NULL OPTIONS(description="Dollar cost incurred during this turn"),
    latency_ms INT64 NOT NULL OPTIONS(description="Model inference response latency in milliseconds"),
    
    -- Context Dynamics
    cumulative_context_tokens INT64 NOT NULL OPTIONS(description="Total token payload in context window at this turn"),
    was_context_compacted BOOLEAN NOT NULL OPTIONS(description="True if context pruning/compaction was executed prior to turn"),
    
    -- Self-Healing & Errors
    self_healing_retries_count INT64 NOT NULL OPTIONS(description="Number of self-healing retries consumed in this turn"),
    error_code STRING OPTIONS(description="Error classification code if self-healing was triggered"),
    
    timestamp TIMESTAMP NOT NULL OPTIONS(description="UTC timestamp of turn execution")
)
PARTITION BY DATE(timestamp)
CLUSTER BY trajectory_id, model_id
OPTIONS(
    description="Granular turn-by-turn state, token, and latency metrics",
    require_partition_filter=TRUE
);
```

---

### 2.3 Table: `tool_call_metrics`
Tracks tool signature correctness, execution sandboxing latencies, and AST validation failures.

```sql
-- DDL: benchpress_analytics.tool_call_metrics
CREATE TABLE IF NOT EXISTS `benchpress_analytics.tool_call_metrics` (
    tool_call_id STRING NOT NULL OPTIONS(description="Unique tool call execution UUID"),
    trajectory_id STRING NOT NULL OPTIONS(description="Foreign key referencing trajectories.trajectory_id"),
    turn_id STRING NOT NULL OPTIONS(description="Foreign key referencing turn_telemetry.turn_id"),
    tool_name STRING NOT NULL OPTIONS(description="Name of invoked tool: edit_file, view_file, grep_search, run_command"),
    
    -- Validation & Security Interception
    is_hallucinated BOOLEAN NOT NULL OPTIONS(description="True if model invoked non-existent tool name"),
    is_schema_valid BOOLEAN NOT NULL OPTIONS(description="True if arguments matched Pydantic/JSON schema"),
    is_security_blocked BOOLEAN NOT NULL OPTIONS(description="True if command attempted unauthorized network/file access"),
    
    -- Sandbox Execution
    execution_duration_ms INT64 NOT NULL OPTIONS(description="Execution time inside gVisor sandbox in milliseconds"),
    exit_code INT64 NOT NULL OPTIONS(description="Process exit code (0 for success, non-zero for error)"),
    output_byte_size INT64 NOT NULL OPTIONS(description="Byte size of stdout/stderr returned by tool"),
    output_truncated BOOLEAN NOT NULL OPTIONS(description="True if output was pruned by context orchestrator"),
    
    timestamp TIMESTAMP NOT NULL OPTIONS(description="UTC timestamp of tool invocation")
)
PARTITION BY DATE(timestamp)
CLUSTER BY tool_name, is_schema_valid
OPTIONS(
    description="Telemetry for tool invocation accuracy, schema conformance, and sandbox execution performance",
    require_partition_filter=TRUE
);
```

---

### 2.4 Table: `aggregated_model_indices`
Continuous rollup table powering real-time Pareto routing, Cost Per Resolution rankings, and API query responses.

```sql
-- DDL: benchpress_analytics.aggregated_model_indices
CREATE TABLE IF NOT EXISTS `benchpress_analytics.aggregated_model_indices` (
    model_id STRING NOT NULL,
    task_suite STRING NOT NULL,
    window_period STRING NOT NULL OPTIONS(description="Aggregation window: 24H, 7D, 30D, ALL_TIME"),
    
    -- Core Economic & Quality Indices
    sample_size INT64 NOT NULL OPTIONS(description="Number of benchmark trajectory runs evaluated"),
    pass_at_1_rate FLOAT64 NOT NULL OPTIONS(description="Empirical Pass@1 success rate [0.0 - 1.0]"),
    median_cpr_usd NUMERIC NOT NULL OPTIONS(description="Median Cost Per Resolution in USD"),
    p90_cpr_usd NUMERIC NOT NULL OPTIONS(description="90th percentile Cost Per Resolution in USD"),
    mean_turns_to_resolve FLOAT64 NOT NULL OPTIONS(description="Average turns required to achieve resolution"),
    mean_trajectory_bloat FLOAT64 NOT NULL OPTIONS(description="Average Trajectory Bloat Ratio"),
    
    -- Pareto Routing Scores
    pareto_efficiency_score FLOAT64 NOT NULL OPTIONS(description="Normalized composite efficiency score [0.0 - 100.0]"),
    recommended_tier STRING NOT NULL OPTIONS(description="Routing tier: FRONTIER_REASONER, HIGH_SPEED_CODER, HYBRID_CHOREOGRAPHY"),
    
    last_updated TIMESTAMP NOT NULL OPTIONS(description="Timestamp of last rollup computation")
)
PARTITION BY DATE(last_updated)
CLUSTER BY model_id, task_suite
OPTIONS(
    description="Materialized model benchmark metrics for sub-millisecond API responses and UI leaderboards"
);
```

---

## 3. High-Throughput Micro-Batch Ingestion Pipeline

### Micro-Batching with BigQuery Storage Write API
Benchpress does not use legacy streaming inserts (`tabledata.insertAll`), which incur higher per-row costs and lack transactional atomicity. Instead, the system uses the **BigQuery Storage Write API** in `DEFAULT` stream mode:

1. **Worker Buffer (`Memorystore Redis`):** During active execution, workers push JSON-serialized turn telemetry to Redis lists using `RPUSH telemetry:queue:{batch_id}`.
2. **Batch Flusher Daemon:** A high-concurrency Python/AsyncIO daemon consumes Redis batches every $2,000\,\text{ms}$ or when queue depth exceeds 500 records.
3. **Protobuf Serialization:** Records are serialized into native Protocol Buffers matching the BigQuery table schemas and streamed via gRPC directly into BigQuery.
4. **Zero Duplicate Guarantee:** The Storage Write API uses deduplication stream offsets, guaranteeing exactly-once semantics even under network retries.

```python
# File: benchpress/telemetry/bq_streamer.py
from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types, writer
import json
import logging

class BigQueryTelemetryStreamer:
    """
    High-performance telemetry streamer using BigQuery Storage Write API.
    """
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.client = bigquery_storage_v1.BigQueryWriteClient()
        self.parent = self.client.table_path(project_id, dataset_id, table_id)
        self.stream_name = f"{self.parent}/streams/_default"

    def stream_micro_batch(self, proto_rows: list[bytes]) -> None:
        request = types.AppendRowsRequest(
            write_stream=self.stream_name,
            proto_rows=types.AppendRowsRequest.ProtoData(
                rows=types.ProtoRows(serialized_rows=proto_rows)
            )
        )
        # Execute streaming gRPC call
        response = self.client.append_rows(iter([request]))
        for r in response:
            if r.error.code != 0:
                logging.error(f"BigQuery Write Error: {r.error.message}")
```

---

## 4. Sub-Second Analytical Query Strategy

By enforcing mandatory partition filters (`require_partition_filter=TRUE`) and multi-column clustering on `(model_family, task_suite, task_complexity_score)`, typical analytical queries scan $< 15\,\text{MB}$ of data and execute in $< 350\,\text{ms}$.

### Example: Real-Time Dynamic Pareto Computation Query
```sql
-- Query: Dynamic Pareto Frontier Calculation for Python Coding Suite
SELECT 
    model_id,
    model_family,
    COUNT(1) as total_runs,
    ROUND(AVG(IF(pass_at_1, 1.0, 0.0)) * 100, 2) as pass_rate_pct,
    ROUND(APPROX_QUANTILES(cpr_usd, 100)[OFFSET(50)], 4) as median_cpr_usd,
    ROUND(AVG(duration_ms) / 1000.0, 2) as avg_latency_seconds,
    ROUND(AVG(trajectory_bloat_ratio) * 100, 2) as avg_bloat_pct
FROM 
    `benchpress_analytics.trajectories`
WHERE 
    timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    AND task_suite = 'swe_bench_verified'
    AND status = 'COMPLETE'
GROUP BY 
    model_id, 
    model_family
ORDER BY 
    pass_rate_pct DESC, 
    median_cpr_usd ASC;
```
