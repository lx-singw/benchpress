# ==============================================================================
# Cloud Tasks Queue Configuration for Deterministic Rate-Limited Dispatches
# Safeguard: Protects Vertex AI quotas and prevents multi-judge concurrency spikes
# ==============================================================================

resource "google_cloud_tasks_queue" "benchpress_trajectory_dispatch" {
  name     = "benchpress-trajectory-dispatch"
  location = var.region
  project  = var.project_id

  rate_limits {
    # Constrain dispatches to max 10 per second to protect Vertex AI TPM/RPM quotas
    max_dispatches_per_second = 10

    # Max 5 concurrent tasks dispatched simultaneously across worker instances
    max_concurrent_dispatches = 5

    # Max burst size to accommodate brief initial bursts
    max_burst_size            = 10
  }

  retry_config {
    # Retry up to 5 times on 429 ResourceExhausted / 503 errors
    max_attempts       = 5
    min_backoff        = "2s"
    max_backoff        = "60s"
    max_doublings      = 4
    max_retry_duration = "600s"
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0
  }
}
