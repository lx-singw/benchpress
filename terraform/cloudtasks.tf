# Google Cloud Tasks: Trajectory Execution Push Queue
# Target Track: The Taskmaster (Grand Prize)

resource "google_cloud_tasks_queue" "trajectory_eval_queue" {
  name     = "trajectory-eval-queue"
  location = var.region

  rate_limits {
    max_dispatches_per_second = 50
    max_concurrent_dispatches = 100
  }

  retry_config {
    max_attempts       = 3
    min_backoff        = "2s"
    max_backoff        = "60s"
    max_doublings      = 4
    max_retry_duration = "300s"
  }
}
