# ==============================================================================
# Benchpress: Cloud Tasks Queue Configuration for Rate-Limited Dispatches
# ==============================================================================

resource "google_cloud_tasks_queue" "trajectory_dispatch" {
  name     = "${var.environment}-trajectory-queue"
  location = var.region
  project  = var.project_id

  rate_limits {
    # Rate limits: 10/s in dev to protect quota, up to 500/s in prod for load surges
    max_dispatches_per_second = var.cloud_tasks_dispatch_rate
    max_concurrent_dispatches = var.cloud_tasks_max_concurrent
    max_burst_size            = var.cloud_tasks_dispatch_rate
  }

  retry_config {
    max_attempts       = 5
    min_backoff        = "2s"
    max_backoff        = "60s"
    max_doublings      = 4
    max_retry_duration = "600s"
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0
  }

  depends_on = [google_project_service.enabled_apis]
}
