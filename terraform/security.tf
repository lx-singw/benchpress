# Enterprise Security, IAM Least-Privilege & Secret Management
# Document ID: BP-GOV-001

# 1. Dedicated Service Account for Sandbox Worker
resource "google_service_account" "worker_sa" {
  account_id   = "benchpress-worker-sa"
  display_name = "Benchpress Sandbox Worker Execution Service Account"
}

# Grant BigQuery Storage Write API permissions
resource "google_project_iam_member" "worker_bq_writer" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# Grant Vertex AI Invoker permissions
resource "google_project_iam_member" "worker_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 2. Firestore Native Database
resource "google_firestore_database" "benchpress_db" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# 3. Secret Manager for HMAC Signature Secret
resource "google_secret_manager_secret" "benchpress_hmac_secret" {
  secret_id = "benchpress-hmac-secret"

  replication {
    auto {}
  }
}
