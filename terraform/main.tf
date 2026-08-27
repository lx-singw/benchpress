# Benchpress Google Cloud Infrastructure as Code (Terraform)
# Document ID: BP-ARCH-004
# Target Track: Best Architectural Design ($5,000) & The Taskmaster (Grand Prize)

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.20.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ==============================================================================
# 1. ARTIFACT REGISTRY
# ==============================================================================
resource "google_artifact_registry_repository" "benchpress_artifacts" {
  location      = var.region
  repository_id = "benchpress-artifacts"
  description   = "Docker repository for Benchpress 2-Service Monorepo"
  format        = "DOCKER"
}

# ==============================================================================
# 2. MEMORYSTORE REDIS (TELEMETRY BUFFER)
# ==============================================================================
resource "google_redis_instance" "telemetry_buffer" {
  name           = "benchpress-telemetry-buffer"
  tier           = "BASIC"
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  redis_version  = "REDIS_7_2"

  display_name = "Benchpress High-Throughput Turn Telemetry Ingestion Cache"
}

# ==============================================================================
# 3. SERVICE 1: BENCHPRESS WEB (NEXT.JS 15 APP ROUTER)
# ==============================================================================
resource "google_cloud_run_v2_service" "benchpress_web" {
  name     = "benchpress-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.web_min_instances
      max_instance_count = var.web_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/web:latest"
      ports {
        container_port = 3000
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "NEXT_PUBLIC_APP_ENV"
        value = var.environment
      }
    }
  }
}

# Allow public unauthenticated access to Next.js Web platform
resource "google_cloud_run_service_iam_member" "web_public_access" {
  location = google_cloud_run_v2_service.benchpress_web.location
  service  = google_cloud_run_v2_service.benchpress_web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ==============================================================================
# 4. SERVICE 2: BENCHPRESS SANDBOX WORKER (PYTHON 3.12 FSM & GVISOR)
# ==============================================================================
resource "google_cloud_run_v2_service" "benchpress_sandbox_worker" {
  name     = "benchpress-sandbox-worker"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    scaling {
      min_instance_count = var.worker_min_instances
      max_instance_count = var.worker_max_instances
    }

    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/sandbox-worker:latest"
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.telemetry_buffer.host}:${google_redis_instance.telemetry_buffer.port}"
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = "benchpress_analytics"
      }
    }
  }
}
