from __future__ import annotations

import pytest
from pydantic import ValidationError

from config import RuntimeMode, WorkerSettings, is_eligible_planner_model


def production_settings(**overrides):
    values = {
        "runtime_mode": RuntimeMode.PRODUCTION,
        "legacy_use_local_mock": False,
        "release_sha": "a" * 40,
        "google_cloud_project": "benchpress-project",
        "google_cloud_region": "us-central1",
        "firestore_database_id": "(default)",
        "firestore_collection_prefix": "prod",
        "repository_backend": "firestore",
        "tasks_queue_name": "prod-trajectory-queue",
        "tasks_location": "us-central1",
        "worker_base_url": "https://worker.example.run.app",
        "tasks_oidc_audience": "https://worker.example.run.app",
        "tasks_invoker_service_account": "benchpress-tasks-invoker@benchpress-project.iam.gserviceaccount.com",
        "genai_use_vertexai": True,
        "planner_model": "gemini-3.5-pro-preview-20260801",
    }
    values.update(overrides)
    return WorkerSettings(_env_file=None, **values)


@pytest.mark.parametrize(
    ("model_id", "eligible"),
    [
        ("gemini-2.5-pro", False),
        ("gemini-3.0-pro", False),
        ("gemini-3.5-pro-preview-20260801", True),
        ("publishers/google/models/gemini-4-pro", True),
        ("not-a-gemini-model", False),
    ],
)
def test_eligible_planner_model_boundary(model_id, eligible):
    assert is_eligible_planner_model(model_id) is eligible


def test_local_mock_defaults_are_explicit_and_safe():
    settings = WorkerSettings(_env_file=None)
    assert settings.runtime_mode is RuntimeMode.LOCAL_MOCK
    assert settings.use_local_mock is True
    assert settings.repository_backend == "memory"


def test_valid_production_settings_pass():
    settings = production_settings()
    assert settings.use_local_mock is False
    assert settings.readiness_summary()["release_sha"] == "a" * 40


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("planner_model", "gemini-2.5-pro", "Gemini 3.5 or newer"),
        ("release_sha", "abc123", "40-character"),
        ("repository_backend", "memory", "must be 'firestore'"),
        ("worker_base_url", "http://0.0.0.0:8000", "absolute HTTPS"),
        ("tasks_oidc_audience", "https://localhost:8000", "local address"),
        ("tasks_invoker_service_account", "not-an-email", "service-account email"),
    ],
)
def test_production_rejects_unsafe_settings(field, value, message):
    with pytest.raises(ValidationError, match=message):
        production_settings(**{field: value})


def test_legacy_mock_flag_must_agree_with_runtime_mode():
    with pytest.raises(ValidationError, match="conflicts with RUNTIME_MODE"):
        production_settings(legacy_use_local_mock=True)


def test_budget_hierarchy_is_validated():
    with pytest.raises(ValidationError, match="cannot exceed MAX_MATRIX_SPEND_USD"):
        production_settings(max_matrix_spend_usd=0.01, per_run_spend_ceiling_usd=0.02)
