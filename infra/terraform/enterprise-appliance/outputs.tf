# Enterprise Appliance Provisioning Outputs

output "perimeter_name" {
  description = "VPC Service Controls Perimeter Name"
  value       = google_access_context_manager_service_perimeter.enterprise_perimeter.name
}

output "cmek_key_id" {
  description = "Cloud KMS Customer-Managed Encryption Key ID"
  value       = google_kms_crypto_key.enterprise_cmek.id
}

output "private_worker_uri" {
  description = "Private Cloud Run Gen2 Worker Service URI"
  value       = google_cloud_run_v2_service.enterprise_private_worker.uri
}

output "enterprise_vault_dataset" {
  description = "Encrypted BigQuery Dataset Vault ID"
  value       = google_bigquery_dataset.enterprise_vault.dataset_id
}
