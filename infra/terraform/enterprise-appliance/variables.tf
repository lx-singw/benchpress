# Enterprise Single-Tenant Appliance Variables
# Target Track: The Fortified Enterprise Fleet (Google Cloud Hackathon 2026)

variable "project_id" {
  type        = string
  description = "Single-tenant GCP Project ID"
  default     = "benchpress-enterprise-prod"
}

variable "region" {
  type        = string
  description = "GCP Region for enterprise deployment"
  default     = "us-central1"
}

variable "access_policy_id" {
  type        = string
  description = "GCP Access Context Manager Policy ID for VPC-SC"
  default     = "123456789012"
}

variable "appliance_name" {
  type        = string
  description = "Identifier for enterprise single-tenant appliance deployment"
  default     = "benchpress-enterprise"
}

variable "vpc_network_name" {
  type        = string
  description = "Private VPC Network Name"
  default     = "benchpress-private-vpc"
}
