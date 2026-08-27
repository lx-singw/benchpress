# ==============================================================================
# Benchpress: Memorystore Redis (Cache, FSM MemoryBus & Token Bucket Rate Limiting)
# ==============================================================================

resource "google_redis_instance" "cache" {
  name           = "benchpress-redis-${var.environment}"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  location_id    = var.zone

  alternative_location_id = var.redis_tier == "STANDARD_HA" ? "us-central1-f" : null

  redis_version = "REDIS_7_0"
  display_name  = "Benchpress Redis Cache (${upper(var.environment)})"

  labels = {
    env       = var.environment
    framework = "benchpress"
  }

  depends_on = [google_project_service.enabled_apis]
}
