data "google_project" "current" {
  project_id = var.project_id
}

resource "google_service_account" "cloud_tasks_invoker" {
  project      = var.project_id
  account_id   = "benchpress-tasks-invoker"
  display_name = "Benchpress Cloud Tasks worker invoker"
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

resource "google_project_iam_member" "web_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "web_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}
