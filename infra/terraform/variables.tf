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

variable "vertex_ai_location" {
  type        = string
  description = "Vertex AI publisher-model location; Gemini 3.7 Flash is accessed through global"
  default     = "global"
}

variable "runtime_mode" {
  type        = string
  description = "Explicit application runtime mode"
  validation {
    condition     = contains(["development", "rehearsal", "production"], var.runtime_mode)
    error_message = "runtime_mode must be development, rehearsal, or production."
  }
}

variable "release_sha" {
  type        = string
  description = "Exact clean Git release commit deployed to both services"
  validation {
    condition     = can(regex("^[a-f0-9]{40}$", var.release_sha))
    error_message = "release_sha must be a full lowercase 40-character Git SHA."
  }
}

variable "planner_model" {
  type        = string
  description = "Account-verified exact eligible Gemini 3.5+ planner model ID"
  validation {
    condition     = can(regex("^gemini-[3-9]\\.[5-9]", var.planner_model))
    error_message = "planner_model must be an exact account-verified Gemini 3.5+ model ID."
  }
}

variable "task_fingerprint_id" {
  type        = string
  description = "Frozen task fingerprint document used by the evaluation planner"
  default     = "fp_eeff17a2a24993a9"
  validation {
    condition     = can(regex("^fp_[a-f0-9]{16}$", var.task_fingerprint_id))
    error_message = "task_fingerprint_id must use the canonical fp_<sha256:16> form."
  }
}

variable "web_image" {
  type        = string
  description = "Immutable web image URL tagged with the full release SHA or pinned by digest"
  validation {
    condition     = can(regex("(@sha256:[a-f0-9]{64}|:[a-f0-9]{40})$", var.web_image))
    error_message = "web_image must end in a sha256 digest or the full 40-character release SHA tag."
  }
}

variable "worker_image" {
  type        = string
  description = "Immutable worker image URL tagged with the full release SHA or pinned by digest"
  validation {
    condition     = can(regex("(@sha256:[a-f0-9]{64}|:[a-f0-9]{40})$", var.worker_image))
    error_message = "worker_image must end in a sha256 digest or the full 40-character release SHA tag."
  }
}

variable "firestore_collection_prefix" {
  type        = string
  description = "Environment-isolated Firestore collection namespace"
  default     = "benchpress"
}

variable "routing_decision_experiment_id" {
  type        = string
  description = "Published measured experiment authorized for the routing read endpoint"
  default     = ""
}

variable "max_matrix_spend_usd" {
  type        = string
  description = "Frozen matrix spend ceiling"
  default     = "0.500000"
}

variable "per_run_spend_ceiling_usd" {
  type        = string
  description = "Frozen per-run spend ceiling"
  default     = "0.050000"
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
