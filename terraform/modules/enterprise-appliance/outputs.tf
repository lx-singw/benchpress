# Enterprise Appliance Outputs

output "cmek_crypto_key_id" {
  description = "Cloud KMS Customer-Managed Encryption Key Resource ID"
  value       = google_kms_crypto_key.enterprise_cmek.id
}

output "vpc_connector_id" {
  description = "VPC Access Connector ID"
  value       = google_vpc_access_connector.enterprise_connector.id
}

output "enterprise_dataset_id" {
  description = "Encrypted BigQuery Dataset ID"
  value       = google_bigquery_dataset.enterprise_analytics.dataset_id
}
