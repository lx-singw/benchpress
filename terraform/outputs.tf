# Terraform Outputs for Benchpress Platform

output "web_service_url" {
  description = "Public URL of Benchpress Next.js Web Platform"
  value       = google_cloud_run_v2_service.benchpress_web.uri
}

output "worker_service_url" {
  description = "Internal URL of Benchpress Sandbox Worker Service"
  value       = google_cloud_run_v2_service.benchpress_sandbox_worker.uri
}

output "bigquery_dataset_id" {
  description = "BigQuery Analytics Dataset ID"
  value       = google_bigquery_dataset.benchpress_analytics.dataset_id
}

output "redis_host" {
  description = "Memorystore Redis Host"
  value       = google_redis_instance.telemetry_buffer.host
}

output "redis_port" {
  description = "Memorystore Redis Port"
  value       = google_redis_instance.telemetry_buffer.port
}

output "cloud_tasks_queue_name" {
  description = "Cloud Tasks Trajectory Push Queue Name"
  value       = google_cloud_tasks_queue.trajectory_eval_queue.name
}
