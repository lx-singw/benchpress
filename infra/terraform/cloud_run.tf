# Benchpress Cloud Run services. Release images are immutable full-SHA tags or digests.

locals {
  worker_service_uri = "https://benchpress-worker-${var.environment}-${data.google_project.current.number}.${var.region}.run.app"
}

resource "google_cloud_run_v2_service" "web" {
  name     = "benchpress-web-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.web_runtime.email
    scaling {
      min_instance_count = var.web_min_instances
      max_instance_count = var.web_max_instances
    }
    containers {
      image = var.web_image
      resources {
        limits = {
          cpu    = var.environment == "prod" ? "2" : "1"
          memory = var.environment == "prod" ? "4Gi" : "2Gi"
        }
      }
      ports { container_port = 3000 }
      dynamic "env" {
        for_each = {
          NODE_ENV                          = "production"
          ENVIRONMENT                       = var.environment
          RUNTIME_MODE                      = var.runtime_mode
          USE_LOCAL_MOCK                    = "false"
          RELEASE_SHA                       = var.release_sha
          GOOGLE_CLOUD_PROJECT              = var.project_id
          GOOGLE_CLOUD_REGION               = var.region
          GCP_TASKS_LOCATION                = var.region
          GCP_TASKS_QUEUE_NAME              = google_cloud_tasks_queue.trajectory_dispatch.name
          SANDBOX_WORKER_URL                = local.worker_service_uri
          TASKS_OIDC_AUDIENCE               = local.worker_service_uri
          GCP_TASKS_INVOKER_SERVICE_ACCOUNT = google_service_account.cloud_tasks_invoker.email
          FIRESTORE_DATABASE_ID             = "(default)"
          FIRESTORE_COLLECTION_PREFIX       = "${var.firestore_collection_prefix}_${var.environment}"
          ROUTING_DECISION_EXPERIMENT_ID    = var.routing_decision_experiment_id
        }
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
  depends_on = [google_project_service.enabled_apis, google_artifact_registry_repository.benchpress_repo]
}

resource "google_cloud_run_v2_service" "sandbox_worker" {
  name     = "benchpress-worker-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    service_account       = google_service_account.worker_runtime.email
    scaling {
      min_instance_count = var.worker_min_instances
      max_instance_count = var.worker_max_instances
    }
    containers {
      image = var.worker_image
      resources {
        limits = {
          cpu    = var.environment == "prod" ? "4" : "2"
          memory = var.environment == "prod" ? "8Gi" : "4Gi"
        }
      }
      ports { container_port = 8080 }
      dynamic "env" {
        for_each = {
          ENVIRONMENT                       = var.environment
          RUNTIME_MODE                      = var.runtime_mode
          USE_LOCAL_MOCK                    = "false"
          RELEASE_SHA                       = var.release_sha
          GOOGLE_CLOUD_PROJECT              = var.project_id
          GOOGLE_CLOUD_REGION               = var.region
          VERTEX_AI_LOCATION                = var.vertex_ai_location
          GENAI_USE_VERTEXAI                = "true"
          PLANNER_MODEL                     = var.planner_model
          REPOSITORY_BACKEND                = "firestore"
          FIRESTORE_DATABASE_ID             = "(default)"
          FIRESTORE_COLLECTION_PREFIX       = "${var.firestore_collection_prefix}_${var.environment}"
          BIGQUERY_DATASET                  = google_bigquery_dataset.analytics.dataset_id
          GCP_TASKS_LOCATION                = var.region
          GCP_TASKS_QUEUE_NAME              = google_cloud_tasks_queue.trajectory_dispatch.name
          SANDBOX_WORKER_URL                = local.worker_service_uri
          TASKS_OIDC_AUDIENCE               = local.worker_service_uri
          GCP_TASKS_INVOKER_SERVICE_ACCOUNT = google_service_account.cloud_tasks_invoker.email
          MAX_MATRIX_SPEND_USD              = var.max_matrix_spend_usd
          PER_RUN_SPEND_CEILING_USD         = var.per_run_spend_ceiling_usd
        }
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
  depends_on = [google_project_service.enabled_apis, google_artifact_registry_repository.benchpress_repo]
}

resource "google_cloud_run_v2_service_iam_member" "web_public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
