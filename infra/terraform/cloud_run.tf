# ==============================================================================
# Benchpress: Environment-Aware Cloud Run v2 Services (Web & Sandbox Worker)
# ==============================================================================

# --- Service 1: Next.js 15 Web Platform ---

resource "google_cloud_run_v2_service" "web" {
  name     = "benchpress-web-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.web_min_instances
      max_instance_count = var.web_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/web:${var.environment}"

      resources {
        limits = {
          cpu    = var.environment == "prod" ? "2" : "1"
          memory = var.environment == "prod" ? "4Gi" : "2Gi"
        }
      }

      ports {
        container_port = 3000
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.environment == "prod" ? "benchpress_analytics" : "benchpress_dev_analytics"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "TASKS_QUEUE_NAME"
        value = "${var.environment}-trajectory-queue"
      }
    }
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_artifact_registry_repository.benchpress_repo
  ]
}

# --- Service 2: Python 3.12 gVisor Sandbox Worker ---

resource "google_cloud_run_v2_service" "sandbox_worker" {
  name     = "benchpress-worker-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    scaling {
      min_instance_count = var.worker_min_instances
      max_instance_count = var.worker_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/sandbox-worker:${var.environment}"

      resources {
        limits = {
          cpu    = var.environment == "prod" ? "4" : "2"
          memory = var.environment == "prod" ? "8Gi" : "4Gi"
        }
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.environment == "prod" ? "benchpress_analytics" : "benchpress_dev_analytics"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
    }
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_artifact_registry_repository.benchpress_repo
  ]
}

# --- Public IAM Access for Web ---

resource "google_cloud_run_v2_service_iam_member" "web_public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
