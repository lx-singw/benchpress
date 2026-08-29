# ==============================================================================
# Benchpress: Main Terraform Manifest & Core GCP Infrastructure
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.30"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# --- Core GCP APIs ---

locals {
  required_services = [
    "run.googleapis.com",
    "cloudtasks.googleapis.com",
    "firestore.googleapis.com",
    "bigquery.googleapis.com",
    "redis.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com",
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each           = toset(local.required_services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# --- Artifact Registry Repository ---

resource "google_artifact_registry_repository" "benchpress_repo" {
  provider      = google-beta
  location      = var.region
  repository_id = "benchpress-artifacts"
  description   = "Docker repository for Benchpress Web and Worker container images"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis]
}

# --- Cloud Storage Artifact & Fixture Bucket ---

resource "google_storage_bucket" "artifacts" {
  name                        = "benchpress-${var.environment}-artifacts-${var.project_id}"
  location                    = var.region
  force_destroy               = var.environment == "dev" ? true : false
  uniform_bucket_level_access = true

  versioning {
    enabled = var.environment == "prod" ? true : false
  }

  lifecycle_rule {
    condition {
      age = var.environment == "dev" ? 14 : 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.enabled_apis]
}
