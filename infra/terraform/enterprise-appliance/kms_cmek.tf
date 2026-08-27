# Cloud KMS Keyrings & Customer-Managed Encryption Keys (CMEK)
# Automatic 90-Day Key Rotation for SOC2 Type II & HIPAA Compliance

resource "google_kms_key_ring" "enterprise_keyring" {
  name     = "${var.appliance_name}-keyring"
  location = var.region
  project  = var.project_id
}

resource "google_kms_crypto_key" "enterprise_cmek" {
  name            = "${var.appliance_name}-cmek"
  key_ring        = google_kms_key_ring.enterprise_keyring.id
  rotation_period = "7776000s" # 90 days automatic rotation

  lifecycle {
    prevent_destroy = true
  }
}
