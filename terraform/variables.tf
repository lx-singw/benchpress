# Google Cloud Infrastructure Variables for Benchpress

variable "project_id" {
  type        = string
  description = "GCP Project ID for Benchpress Platform"
  default     = "benchpress-prod"
}

variable "region" {
  type        = string
  description = "Primary GCP Region for Cloud Run and Cloud Tasks"
  default     = "us-central1"
}

variable "environment" {
  type        = string
  description = "Deployment Environment (production, staging, dev)"
  default     = "production"
}

variable "web_min_instances" {
  type        = number
  description = "Minimum instances for Next.js Web service"
  default     = 1
}

variable "web_max_instances" {
  type        = number
  description = "Maximum instances for Next.js Web service"
  default     = 20
}

variable "worker_min_instances" {
  type        = number
  description = "Minimum instances for Sandbox Worker service"
  default     = 2
}

variable "worker_max_instances" {
  type        = number
  description = "Maximum instances for Sandbox Worker service"
  default     = 50
}

variable "redis_memory_size_gb" {
  type        = number
  description = "Memorystore Redis cache capacity (GB)"
  default     = 5
}
