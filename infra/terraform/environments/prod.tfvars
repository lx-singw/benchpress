# ==============================================================================
# Production Environment Variables (`prod.tfvars`)
# Architecture Target: Pre-warmed High Availability, Sub-150ms Hydration, High Concurrency
# ==============================================================================

environment                = "prod"
runtime_mode               = "production"
web_min_instances          = 1
web_max_instances          = 20
worker_min_instances       = 2
worker_max_instances       = 100
redis_tier                 = "STANDARD_HA"
redis_memory_size_gb       = 5
cloud_tasks_dispatch_rate  = 500
cloud_tasks_max_concurrent = 50
