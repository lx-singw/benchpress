# ==============================================================================
# Development Environment Variables (`dev.tfvars`)
# Architecture Target: $0/month Idle Compute, Scale-to-Zero, Low Quota Limits
# ==============================================================================

environment                = "dev"
runtime_mode               = "development"
web_min_instances          = 0
web_max_instances          = 5
worker_min_instances       = 0
worker_max_instances       = 10
redis_tier                 = "BASIC"
redis_memory_size_gb       = 1
cloud_tasks_dispatch_rate  = 10
cloud_tasks_max_concurrent = 5
