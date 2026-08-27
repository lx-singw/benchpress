# Enterprise Single-Tenant Appliance Variables

variable "project_id" {
  type        = string
  description = "Single-tenant GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP Region for enterprise deployment"
  default     = "us-central1"
}

variable "appliance_name" {
  type        = string
  description = "Name identifier for enterprise appliance deployment"
  default     = "benchpress-enterprise"
}

variable "vpc_network_name" {
  type        = string
  description = "Private VPC Network Name"
  default     = "benchpress-private-vpc"
}
