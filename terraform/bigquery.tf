# BigQuery Analytics Dataset & Partitioned Tables
# Document ID: BP-ARCH-004

resource "google_bigquery_dataset" "benchpress_analytics" {
  dataset_id                  = "benchpress_analytics"
  friendly_name               = "Benchpress AI Trajectory & Economic Analytics"
  description                 = "OLAP warehouse for continuous agent evaluation, CPR, TBR, and turn telemetry metrics"
  location                    = var.region
  default_table_expiration_ms = 31536000000 # 1 year retention
}

# 1. Trajectories Summary Table (Partitioned by Date, Clustered by Model & Suite)
resource "google_bigquery_table" "trajectories" {
  dataset_id = google_bigquery_dataset.benchpress_analytics.dataset_id
  table_id   = "trajectories"

  time_partitioning {
    type  = "DAY"
    field = "started_at"
  }

  clustering = ["model_id", "task_suite", "status"]

  schema = jsonencode([
    { name = "trajectory_id", type = "STRING", mode = "REQUIRED" },
    { name = "task_suite", type = "STRING", mode = "REQUIRED" },
    { name = "task_id", type = "STRING", mode = "REQUIRED" },
    { name = "model_id", type = "STRING", mode = "REQUIRED" },
    { name = "active_coder_model", type = "STRING", mode = "NULLABLE" },
    { name = "status", type = "STRING", mode = "REQUIRED" },
    { name = "pass_at_1", type = "BOOLEAN", mode = "REQUIRED" },
    { name = "resolved", type = "BOOLEAN", mode = "REQUIRED" },
    { name = "early_halted", type = "BOOLEAN", mode = "REQUIRED" },
    { name = "halt_reason", type = "STRING", mode = "NULLABLE" },
    { name = "total_turns", type = "INTEGER", mode = "REQUIRED" },
    { name = "total_cost_usd", type = "FLOAT", mode = "REQUIRED" },
    { name = "cpr_usd", type = "FLOAT", mode = "REQUIRED" },
    { name = "trajectory_bloat_ratio", type = "FLOAT", mode = "REQUIRED" },
    { name = "context_decay_score", type = "FLOAT", mode = "NULLABLE" },
    { name = "ast_heal_count", type = "INTEGER", mode = "REQUIRED" },
    { name = "git_snapshots_count", type = "INTEGER", mode = "REQUIRED" },
    { name = "started_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "completed_at", type = "TIMESTAMP", mode = "NULLABLE" }
  ])
}

# 2. Turn Telemetry Micro-Events Table (Partitioned by Ingestion Timestamp)
resource "google_bigquery_table" "turn_telemetry" {
  dataset_id = google_bigquery_dataset.benchpress_analytics.dataset_id
  table_id   = "turn_telemetry"

  time_partitioning {
    type = "DAY"
  }

  clustering = ["trajectory_id", "model_id", "fsm_state"]

  schema = jsonencode([
    { name = "trajectory_id", type = "STRING", mode = "REQUIRED" },
    { name = "turn_index", type = "INTEGER", mode = "REQUIRED" },
    { name = "fsm_state", type = "STRING", mode = "REQUIRED" },
    { name = "model_id", type = "STRING", mode = "REQUIRED" },
    { name = "prompt_tokens", type = "INTEGER", mode = "REQUIRED" },
    { name = "completion_tokens", type = "INTEGER", mode = "REQUIRED" },
    { name = "cached_tokens", type = "INTEGER", mode = "NULLABLE" },
    { name = "turn_cost_usd", type = "FLOAT", mode = "REQUIRED" },
    { name = "cumulative_cost_usd", type = "FLOAT", mode = "REQUIRED" },
    { name = "latency_ms", type = "FLOAT", mode = "REQUIRED" },
    { name = "tool_call_name", type = "STRING", mode = "NULLABLE" },
    { name = "tool_call_payload_json", type = "STRING", mode = "NULLABLE" },
    { name = "ast_healed", type = "BOOLEAN", mode = "REQUIRED" },
    { name = "ast_healing_trace", type = "STRING", mode = "NULLABLE" },
    { name = "sandbox_exit_code", type = "INTEGER", mode = "REQUIRED" },
    { name = "git_tree_hash", type = "STRING", mode = "NULLABLE" },
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])
}
