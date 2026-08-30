locals {
  security_alert_patterns = {
    auth_failure       = "(textPayload:\"Cloud Tasks OIDC validation failed\" OR textPayload:\"Rejecting request without a Bearer identity token\")"
    immutable_conflict = "(textPayload:\"Conflicting immutable\" OR textPayload:\"IntegrityConflict\")"
    rollback_failure   = "(textPayload:\"Rollback CAS conflict\" OR textPayload:\"baseline restoration could not be proven\")"
    receipt_failure    = "(textPayload:\"Receipt digest/ID mismatch\" OR textPayload:\"publication mismatch\")"
    budget_breach      = "(textPayload:\"BUDGET_EXCEEDED\" OR textPayload:\"budget breach\")"
  }
}

resource "google_logging_metric" "security_events" {
  for_each = local.security_alert_patterns
  project  = var.project_id
  name     = "benchpress_${var.environment}_${each.key}"
  filter   = "resource.type=\"cloud_run_revision\" AND ${each.value}"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_monitoring_alert_policy" "security_events" {
  for_each     = google_logging_metric.security_events
  project      = var.project_id
  display_name = "Benchpress ${var.environment}: ${each.key}"
  combiner     = "OR"
  conditions {
    display_name = "${each.key} observed"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${each.value.name}\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }
  alert_strategy { auto_close = "1800s" }
}
