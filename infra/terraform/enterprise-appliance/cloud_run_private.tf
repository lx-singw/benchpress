# Dedicated Internal Cloud Run Gen2 Worker Fleet for Enterprise Private Appliance

resource "google_vpc_access_connector" "enterprise_connector" {
  name          = "bp-ent-conn"
  region        = var.region
  project       = var.project_id
  ip_cidr_range = "10.8.0.0/28"
  network       = var.vpc_network_name
}

resource "google_cloud_run_v2_service" "enterprise_private_worker" {
  name     = "${var.appliance_name}-worker"
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    vpc_access {
      connector = google_vpc_access_connector.enterprise_connector.id
      egress    = "ALL_TRAFFIC"
    }

    scaling {
      min_instance_count = 2
      max_instance_count = 50
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/sandbox-worker:latest"
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }
      env {
        name  = "ENTERPRISE_MODE"
        value = "true"
      }
      env {
        name  = "CMEK_KEY_ID"
        value = google_kms_crypto_key.enterprise_cmek.id
      }
    }
  }
}
