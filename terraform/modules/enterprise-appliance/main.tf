# Benchpress Single-Tenant Enterprise Private Appliance Module
# Target: Fortune 500 On-Prem / VPC-SC Deployments with CMEK Encryption

# 1. Cloud KMS Key Ring & CMEK Key for Customer Data Encryption
resource "google_kms_key_ring" "enterprise_keyring" {
  name     = "${var.appliance_name}-keyring"
  location = var.region
  project  = var.project_id
}

resource "google_kms_crypto_key" "enterprise_cmek" {
  name            = "${var.appliance_name}-cmek"
  key_ring        = google_kms_key_ring.enterprise_keyring.id
  rotation_period = "7776000s" # 90 days rotation
}

# 2. Serverless VPC Access Connector for Private Subnet Routing
resource "google_vpc_access_connector" "enterprise_connector" {
  name          = "bp-vpc-conn"
  region        = var.region
  project       = var.project_id
  ip_cidr_range = "10.8.0.0/28"
  network       = var.vpc_network_name
}

# 3. Private BigQuery Dataset with CMEK Encryption
resource "google_bigquery_dataset" "enterprise_analytics" {
  dataset_id  = "benchpress_enterprise_vault"
  project     = var.project_id
  location    = var.region
  description = "Single-tenant isolated trajectory vault with customer-managed encryption"

  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.enterprise_cmek.id
  }
}
