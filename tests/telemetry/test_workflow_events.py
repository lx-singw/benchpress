import json

from config import RuntimeMode, settings
from telemetry.events import WorkflowEventEmitter


def test_workflow_event_ids_are_retry_safe_and_payloads_are_sanitized():
    emitter = WorkflowEventEmitter()
    kwargs = {
        "correlation_id": "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        "object_id": "run_0123456789abcdef",
        "event_type": "RUN_COMPLETED",
        "service": "sandbox-worker",
        "details": {"total_tokens": 42, "observed_cost_usd": "0.010000"},
    }
    first = emitter.emit(**kwargs)
    second = emitter.emit(**kwargs)
    assert first.event_id == second.event_id
    assert len(emitter.events) == 1


def test_sensitive_event_details_are_rejected():
    emitter = WorkflowEventEmitter()
    try:
        emitter.emit(
            correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
            object_id="run_0123456789abcdef",
            event_type="BAD",
            service="sandbox-worker",
            details={"prompt": "secret source"},
        )
    except ValueError as exc:
        assert "Sensitive telemetry" in str(exc)
    else:
        raise AssertionError("Sensitive telemetry was accepted")


def test_bigquery_json_details_are_serialized(monkeypatch):
    class RecordingBigQueryClient:
        def __init__(self):
            self.rows = []

        def insert_rows_json(self, table, rows, row_ids):
            self.rows.extend(rows)
            return []

    client = RecordingBigQueryClient()
    monkeypatch.setattr(settings, "runtime_mode", RuntimeMode.DEVELOPMENT)
    emitter = WorkflowEventEmitter(bigquery_client=client)

    emitted = emitter.emit(
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        object_id="run_0123456789abcdef",
        event_type="RUN_COMPLETED",
        service="sandbox-worker",
        details={"total_tokens": 42},
    )

    assert emitted.details == {"total_tokens": 42}
    assert json.loads(client.rows[0]["details"]) == {"total_tokens": 42}
