# Google Cloud Infrastructure as Code (Terraform) & Zero-Touch Deployment

> **Document ID:** `BP-ARCH-004`  
> **Status:** Approved / Production Standard  
> **Target Track:** Best Architectural Design ($5,000) • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. Cloud Architecture Topology & IaC Philosophy

Benchpress is provisioned using **Terraform (HCL)** across Google Cloud Platform (`us-central1`). The infrastructure codifies the **2-Service High-Performance Monorepo Architecture**:
1. **`benchpress-web` (`apps/web`):** Public Cloud Run service running Next.js 15 App Router on port 3000, handling UI rendering, WebRTC handshakes, and Edge REST API route handlers.
2. **`benchpress-sandbox-worker` (`apps/sandbox-worker`):** Private Confidential Cloud Run Gen2 service running on port 8080 with AMD SEV-SNP hardware memory encryption, executing the 13-State Deterministic FSM inside gVisor `runsc` sandboxes.
3. **Core Asynchronous Plumbing:** Google Cloud Tasks push queues, Memorystore Redis 7.2 telemetry buffers, BigQuery Storage Write API datasets, and Firestore Native database.

---

## 2. Complete Production Terraform Configuration

```hcl
# File: terraform/main.tf
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
  backend "gcs" {
    bucket = "benchpress-tf-state-prod"
    prefix = "terraform/state"
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

variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "benchpress-prod"
}

variable "region" {
  type        = string
  description = "Primary GCP Region"
  default     = "us-central1"
}

# ==============================================================================
# 1. GOOGLE ARTIFACT REGISTRY
# ==============================================================================
resource "google_artifact_registry_repository" "benchpress_artifacts" {
  location      = var.region
  repository_id = "benchpress-artifacts"
  description   = "Docker repository for Benchpress 2-Service Monorepo"
  format        = "DOCKER"
}

# ==============================================================================
# 2. GOOGLE CLOUD TASKS (THE TASKMASTER QUEUE)
# ==============================================================================
resource "google_cloud_tasks_queue" "trajectory_eval_queue" {
  name     = "trajectory-eval-queue"
  location = var.region

  rate_limits {
    max_dispatches_per_second = 50
    max_concurrent_dispatches = 100
  }

  retry_config {
    max_attempts       = 5
    min_backoff        = "2s"
    max_backoff        = "60s"
    max_doublings      = 4
    max_retry_duration = "3600s"
  }
}

# ==============================================================================
# 3. SERVICE 1: BENCHPRESS WEB & EDGE API (Next.js 15)
# ==============================================================================
resource "google_cloud_run_v2_service" "benchpress_web" {
  name     = "benchpress-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 50
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/web:latest"

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2048Mi"
        }
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "WORKER_SERVICE_URL"
        value = google_cloud_run_v2_service.benchpress_sandbox_worker.uri
      }
    }
  }
}

# Allow public access to Web Hub & Edge API
resource "google_cloud_run_service_iam_member" "web_public_access" {
  service  = google_cloud_run_v2_service.benchpress_web.name
  location = google_cloud_run_v2_service.benchpress_web.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ==============================================================================
# 4. SERVICE 2: CONFIDENTIAL SANDBOX WORKER (Python 3.12 + gVisor)
# ==============================================================================
resource "google_cloud_run_v2_service" "benchpress_sandbox_worker" {
  name     = "benchpress-sandbox-worker"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    
    # Enforce AMD SEV-SNP Hardware Memory Encryption
    confidential_compute = true

    scaling {
      min_instance_count = 0
      max_instance_count = 100
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/sandbox-worker:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "4000m"
          memory = "8192Mi"
        }
      }

      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
    }
  }
}

# Allow Cloud Tasks service account to invoke Private Sandbox Worker
resource "google_cloud_run_service_iam_member" "worker_tasks_invoker" {
  service  = google_cloud_run_v2_service.benchpress_sandbox_worker.name
  location = google_cloud_run_v2_service.benchpress_sandbox_worker.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:cloud-tasks-invoker@${var.project_id}.iam.gserviceaccount.com"
}

# ==============================================================================
# 5. GOOGLE MEMORYSTORE REDIS (TELEMETRY MICRO-BATCH BUFFER)
# ==============================================================================
resource "google_redis_instance" "telemetry_buffer" {
  name           = "benchpress-redis-buffer"
  tier           = "BASIC"
  memory_size_gb = 5
  region         = var.region
  redis_version  = "REDIS_7_2"
}

# ==============================================================================
# 6. BIGQUERY ANALYTICS WAREHOUSE (STORAGE WRITE API)
# ==============================================================================
resource "google_bigquery_dataset" "benchpress_analytics" {
  dataset_id                  = "benchpress_analytics"
  friendly_name               = "Benchpress Trajectory Telemetry"
  description                 = "High-throughput warehouse storing multi-turn agent telemetry and CPR indices"
  location                    = var.region
  default_table_expiration_ms = null
}

resource "google_bigquery_table" "trajectories" {
  dataset_id = google_bigquery_dataset.benchpress_analytics.dataset_id
  table_id   = "trajectories"

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["model_id", "task_suite", "pass_at_1"]

  schema = <<EOF
[
  {"name": "trajectory_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "model_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "task_suite", "type": "STRING", "mode": "REQUIRED"},
  {"name": "task_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "total_turns", "type": "INT64", "mode": "REQUIRED"},
  {"name": "total_cost_usd", "type": "FLOAT64", "mode": "REQUIRED"},
  {"name": "pass_at_1", "type": "BOOLEAN", "mode": "REQUIRED"},
  {"name": "cpr_score_usd", "type": "FLOAT64", "mode": "REQUIRED"},
  {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
]
EOF
}

# ==============================================================================
# 7. GOOGLE CLOUD ARMOR SECURITY POLICY (WAF & RATE LIMITING)
# ==============================================================================
resource "google_compute_security_policy" "cloud_armor_policy" {
  name        = "benchpress-cloud-armor"
  description = "WAF rules and DDoS rate-limiting for Benchpress Public API"

  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 120
        interval_sec = 60
      }
      ban_threshold {
        count        = 300
        interval_sec = 60
      }
      ban_duration_sec = 600
    }
    description = "Throttle clients exceeding 120 req/minute"
  }

  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }
}
```
