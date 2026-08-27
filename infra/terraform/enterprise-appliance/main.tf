# Benchpress Fortified Enterprise Single-Tenant Appliance Module
# Target Track: The Fortified Enterprise Fleet & Grand Prize ($5,000)

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

# Single-tenant BigQuery Vault Dataset encrypted with CMEK
resource "google_bigquery_dataset" "enterprise_vault" {
  dataset_id  = "benchpress_enterprise_vault"
  project     = var.project_id
  location    = var.region
  description = "Single-tenant isolated trajectory vault with customer-managed encryption"

  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.enterprise_cmek.id
  }
}
