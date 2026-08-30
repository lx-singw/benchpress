# ==============================================================================
# Benchpress: Terraform Outputs
# ==============================================================================

output "environment" {
  description = "Deployed environment ('dev' or 'prod')"
  value       = var.environment
}

output "web_service_uri" {
  description = "Public URL for Cloud Run Web Frontend"
  value       = google_cloud_run_v2_service.web.uri
}

output "worker_service_uri" {
  description = "URL for Cloud Run Sandbox Worker"
  value       = google_cloud_run_v2_service.sandbox_worker.uri
}

output "bigquery_dataset_id" {
  description = "BigQuery Analytics Dataset ID"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "cloud_tasks_queue_id" {
  description = "Cloud Tasks Queue ID"
  value       = google_cloud_tasks_queue.trajectory_dispatch.id
}

output "redis_host" {
  description = "Memorystore Redis Host IP"
  value       = google_redis_instance.cache.host
}

output "artifact_bucket_name" {
  description = "Cloud Storage Artifact Bucket Name"
  value       = google_storage_bucket.artifacts.name
}

output "release_sha" { value = var.release_sha }
output "web_image" { value = var.web_image }
output "worker_image" { value = var.worker_image }
output "web_service_account" { value = google_service_account.web_runtime.email }
output "worker_service_account" { value = google_service_account.worker_runtime.email }
output "tasks_invoker_service_account" { value = google_service_account.cloud_tasks_invoker.email }
output "web_latest_created_revision" { value = google_cloud_run_v2_service.web.latest_created_revision }
output "worker_latest_created_revision" { value = google_cloud_run_v2_service.sandbox_worker.latest_created_revision }
