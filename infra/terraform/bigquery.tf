# ==============================================================================
# Benchpress: BigQuery Analytics Dataset & Partitioned/Clustered Tables
# ==============================================================================

locals {
  dataset_id = var.environment == "prod" ? "benchpress_analytics" : "benchpress_dev_analytics"
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                 = local.dataset_id
  friendly_name              = "Benchpress AI Agent Telemetry (${upper(var.environment)})"
  description                = "Analytics dataset for multi-model SWE-bench trajectories and FinOps CPR economics"
  location                   = "US"
  delete_contents_on_destroy = var.environment == "dev" ? true : false

  labels = {
    env       = var.environment
    framework = "benchpress"
  }

  depends_on = [google_project_service.enabled_apis]
}

# --- Table 1: Trajectories (Runs) ---

resource "google_bigquery_table" "trajectories" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "trajectories"
  deletion_protection = var.environment == "prod" ? true : false

  time_partitioning {
    type  = "DAY"
    field = "started_at"
  }

  clustering = ["model_id", "task_suite", "status"]

  schema = jsonencode([
    { name = "trajectory_id", type = "STRING", mode = "REQUIRED", description = "Unique run UUID" },
    { name = "task_suite", type = "STRING", mode = "REQUIRED", description = "SWE_BENCH_VERIFIED, CYBENCH, GAIA" },
    { name = "task_id", type = "STRING", mode = "REQUIRED", description = "Task identifier (e.g., django__django-11099)" },
    { name = "model_id", type = "STRING", mode = "REQUIRED", description = "Model identifier" },
    { name = "status", type = "STRING", mode = "REQUIRED", description = "COMPLETED, FAILED, EARLY_HALTED" },
    { name = "pass_at_1", type = "BOOLEAN", mode = "REQUIRED", description = "Ground-truth pytest resolution" },
    { name = "total_cost_usd", type = "FLOAT", mode = "REQUIRED", description = "Gross token spend in USD" },
    { name = "cpr_usd", type = "FLOAT", mode = "REQUIRED", description = "Cost Per Resolution in USD" },
    { name = "turns_count", type = "INTEGER", mode = "REQUIRED", description = "Total executed FSM turns" },
    { name = "trajectory_bloat_ratio", type = "FLOAT", mode = "NULLABLE", description = "Token bloat multiplier vs golden path" },
    { name = "context_decay_score", type = "FLOAT", mode = "NULLABLE", description = "Attention entropy rate" },
    { name = "ast_heal_count", type = "INTEGER", mode = "NULLABLE", description = "Number of tool calls repaired by AST Healer" },
    { name = "started_at", type = "TIMESTAMP", mode = "REQUIRED", description = "Run start timestamp" },
    { name = "completed_at", type = "TIMESTAMP", mode = "NULLABLE", description = "Run completion timestamp" }
  ])
}

# --- Table 2: FSM Turns ---

resource "google_bigquery_table" "fsm_turns" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "fsm_turns"
  deletion_protection = var.environment == "prod" ? true : false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["trajectory_id", "state", "model_id"]

  schema = jsonencode([
    { name = "turn_id", type = "STRING", mode = "REQUIRED", description = "Unique turn UUID" },
    { name = "trajectory_id", type = "STRING", mode = "REQUIRED", description = "Parent trajectory ID" },
    { name = "turn_index", type = "INTEGER", mode = "REQUIRED", description = "1-indexed turn position" },
    { name = "state", type = "STRING", mode = "REQUIRED", description = "13-state FSM Enum value" },
    { name = "model_id", type = "STRING", mode = "REQUIRED", description = "Active planner or coder model" },
    { name = "prompt_tokens", type = "INTEGER", mode = "REQUIRED", description = "Input prompt token count" },
    { name = "completion_tokens", type = "INTEGER", mode = "REQUIRED", description = "Generated completion token count" },
    { name = "turn_cost_usd", type = "FLOAT", mode = "REQUIRED", description = "Spend on this turn in USD" },
    { name = "cumulative_cost_usd", type = "FLOAT", mode = "REQUIRED", description = "Running trajectory cost" },
    { name = "latency_ms", type = "FLOAT", mode = "REQUIRED", description = "Turn round-trip latency in ms" },
    { name = "tool_call_name", type = "STRING", mode = "NULLABLE", description = "Invoked tool name" },
    { name = "ast_healed", type = "BOOLEAN", mode = "REQUIRED", description = "Whether AST Healer normalized payload" },
    { name = "sandbox_exit_code", type = "INTEGER", mode = "NULLABLE", description = "Process exit code from gVisor sandbox" },
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED", description = "Turn timestamp" }
  ])
}
