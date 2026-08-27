# Google Cloud VPC Service Controls (VPC-SC) Security Perimeter
# Encloses Cloud Run Gen2, BigQuery, Firestore, and Secret Manager inside an impenetrable network boundary.

resource "google_access_context_manager_service_perimeter" "enterprise_perimeter" {
  parent         = "accessPolicies/${var.access_policy_id}"
  name           = "accessPolicies/${var.access_policy_id}/servicePerimeters/${var.appliance_name}_perimeter"
  title          = "Benchpress Fortified Enterprise Security Perimeter"
  perimeter_type = "PERIMETER_TYPE_REGULAR"

  status {
    restricted_services = [
      "run.googleapis.com",
      "bigquery.googleapis.com",
      "firestore.googleapis.com",
      "secretmanager.googleapis.com",
      "aiplatform.googleapis.com",
      "redis.googleapis.com"
    ]

    resources = [
      "projects/${var.project_id}"
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = [
        "run.googleapis.com",
        "bigquery.googleapis.com",
        "firestore.googleapis.com",
        "aiplatform.googleapis.com"
      ]
    }
  }
}
