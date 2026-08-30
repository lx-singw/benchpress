data "google_project" "current" { project_id = var.project_id }

resource "google_service_account" "web_runtime" {
  project      = var.project_id
  account_id   = "benchpress-web-${var.environment}"
  display_name = "Benchpress ${var.environment} web runtime"
}

resource "google_service_account" "worker_runtime" {
  project      = var.project_id
  account_id   = "benchpress-worker-${var.environment}"
  display_name = "Benchpress ${var.environment} worker runtime"
}

resource "google_service_account" "cloud_tasks_invoker" {
  project      = var.project_id
  account_id   = "benchpress-tasks-${var.environment}"
  display_name = "Benchpress ${var.environment} Cloud Tasks worker invoker"
}

resource "google_cloud_run_v2_service_iam_member" "worker_cloud_tasks_invoker" {
  project  = var.project_id
  location = google_cloud_run_v2_service.sandbox_worker.location
  name     = google_cloud_run_v2_service.sandbox_worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_tasks_invoker.email}"
}

resource "google_service_account_iam_member" "cloud_tasks_token_creator" {
  service_account_id = google_service_account.cloud_tasks_invoker.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudtasks.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "web_can_use_tasks_invoker" {
  service_account_id = google_service_account.cloud_tasks_invoker.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.web_runtime.email}"
}

resource "google_service_account_iam_member" "worker_can_use_tasks_invoker" {
  service_account_id = google_service_account.cloud_tasks_invoker.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.worker_runtime.email}"
}

locals {
  web_project_roles = toset(["roles/cloudtasks.enqueuer", "roles/datastore.user", "roles/logging.logWriter"])
  worker_project_roles = toset([
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/cloudtasks.enqueuer",
    "roles/datastore.user",
    "roles/logging.logWriter",
  ])
}

resource "google_project_iam_member" "web_runtime_roles" {
  for_each = local.web_project_roles
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.web_runtime.email}"
}

resource "google_project_iam_member" "worker_runtime_roles" {
  for_each = local.worker_project_roles
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.worker_runtime.email}"
}
