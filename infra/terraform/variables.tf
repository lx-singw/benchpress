# ==============================================================================
# Benchpress: Core Terraform Variables with Strict Environment Parameterization
# ==============================================================================

variable "environment" {
  type        = string
  description = "Deployment target environment ('dev' for scale-to-zero, 'prod' for pre-warmed HA)"
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "The environment variable must be either 'dev' or 'prod'."
  }
}

variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID"
  default     = "benchpress-platform"
}

variable "region" {
  type        = string
  description = "GCP Region for all regional resources (Cloud Run, Cloud Tasks, Redis, Artifact Registry)"
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = "GCP Primary Zone for zonal resources"
  default     = "us-central1-a"
}

# --- Cloud Run Web Platform Scaling & Sizing ---

variable "web_min_instances" {
  type        = number
  description = "Minimum instances for Cloud Run Web frontend (0 for dev, >=1 for prod)"
  default     = 0
}

variable "web_max_instances" {
  type        = number
  description = "Maximum instances for Cloud Run Web frontend"
  default     = 5
}

# --- Cloud Run Sandbox Worker Scaling & Sizing ---

variable "worker_min_instances" {
  type        = number
  description = "Minimum instances for Cloud Run Sandbox Worker (0 for dev, >=2 for prod)"
  default     = 0
}

variable "worker_max_instances" {
  type        = number
  description = "Maximum instances for Cloud Run Sandbox Worker"
  default     = 10
}

# --- Memorystore Redis Tiering ---

variable "redis_tier" {
  type        = string
  description = "Memorystore Redis tier (BASIC for single-node dev, STANDARD_HA for multi-zone prod)"
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be 'BASIC' or 'STANDARD_HA'."
  }
}

variable "redis_memory_size_gb" {
  type        = number
  description = "Redis memory capacity in GB (1 GB for dev, 5 GB for prod)"
  default     = 1
}

# --- Cloud Tasks Queue Rate Limits ---

variable "cloud_tasks_dispatch_rate" {
  type        = number
  description = "Max task dispatches per second (10/s for dev, 500/s for prod)"
  default     = 10
}

variable "cloud_tasks_max_concurrent" {
  type        = number
  description = "Max concurrent task dispatches across workers (5 for dev, 50 for prod)"
  default     = 5
}
