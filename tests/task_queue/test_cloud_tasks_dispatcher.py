from __future__ import annotations

from types import SimpleNamespace

from config import settings
from contracts.models import RunManifest
from task_queue.cloud_tasks import CloudTasksDispatcher, deterministic_task_id


def manifest() -> RunManifest:
    return RunManifest(
        logical_run_key="run_01a2b3c4d5e6f789",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id="cfg_4f1b82d3e9a0c784",
        task_id="TASK-001",
        task_version_hash="6" * 64,
        repetition_index=0,
        harness_version="pytest-8.3.0",
        oracle_version="oracle-v1",
        tool_allowlist=["read_file"],
        path_allowlist=[],
        max_turns=3,
        timeout_seconds=30,
        max_spend_usd="0.010000",
        created_at="2026-08-29T10:00:00.000Z",
    )


def test_local_dispatch_is_deterministic_and_does_not_call_network():
    dispatcher = CloudTasksDispatcher()
    first = dispatcher.dispatch_run_tasks([manifest()])[0]
    second = dispatcher.dispatch_run_tasks([manifest()])[0]
    assert first == second
    assert first.endswith("/tasks/" + deterministic_task_id("run", manifest().logical_run_key))
    assert dispatcher.dispatched_tasks[0]["target_url"].endswith("/execute-run")


def test_every_nonlocal_task_has_exact_oidc_identity(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.requests = []

        def create_task(self, request):
            self.requests.append(request)
            return SimpleNamespace(name=request["task"]["name"])

    class FakeEmitter:
        def __init__(self):
            self.events = []

        def emit(self, **event):
            self.events.append(event)

    monkeypatch.setattr(type(settings), "use_local_mock", property(lambda self: False))
    monkeypatch.setattr(settings, "worker_base_url", "https://worker.example.run.app")
    monkeypatch.setattr(settings, "tasks_oidc_audience", "https://worker.example.run.app")
    monkeypatch.setattr(
        settings,
        "tasks_invoker_service_account",
        "benchpress-tasks-invoker@benchpress-project.iam.gserviceaccount.com",
    )
    fake = FakeClient()
    emitter = FakeEmitter()
    dispatcher = CloudTasksDispatcher(
        project_id="benchpress-project",
        location="us-central1",
        queue_name="dev-trajectory-queue",
        client=fake,
        event_emitter=emitter,
    )

    dispatcher.dispatch_orchestrate_task(
        "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
        "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
    )
    dispatcher.dispatch_run_tasks([manifest()])
    dispatcher.dispatch_aggregate_task(
        manifest().experiment_id,
        manifest().correlation_id,
        {"experiment_id": manifest().experiment_id},
    )
    dispatcher.dispatch_canary_task(
        "cnry_01J6G7R8Q9ABCDEFGHJKMNPQ40",
        manifest().correlation_id,
        {"canary_id": "cnry_01J6G7R8Q9ABCDEFGHJKMNPQ40"},
    )
    dispatcher.dispatch_publish_task(
        "dec_01J6G7R8Q9ABCDEFGHJKMNPQ50",
        manifest().correlation_id,
        {"decision_id": "dec_01J6G7R8Q9ABCDEFGHJKMNPQ50"},
    )

    assert len(fake.requests) == 5
    assert len(emitter.events) == 5
    assert all(event["event_type"] == "CLOUD_TASK_DISPATCHED" for event in emitter.events)
    assert all(len(event["details"]["payload_sha256"]) == 64 for event in emitter.events)
    for request in fake.requests:
        http_request = request["task"]["http_request"]
        assert http_request["url"].startswith("https://worker.example.run.app/")
        assert http_request["oidc_token"] == {
            "service_account_email": "benchpress-tasks-invoker@benchpress-project.iam.gserviceaccount.com",
            "audience": "https://worker.example.run.app",
        }
