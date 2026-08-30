"""Validated worker configuration with a fail-closed non-local boundary."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeMode(str, Enum):
    LOCAL_MOCK = "local_mock"
    DEVELOPMENT = "development"
    REHEARSAL = "rehearsal"
    PRODUCTION = "production"


ELIGIBLE_PLANNER_VERSION = (3, 5)
_MODEL_VERSION = re.compile(r"(?:^|/)gemini-(\d+)(?:\.(\d+))?(?:-|$)", re.IGNORECASE)
_FULL_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SERVICE_ACCOUNT = re.compile(
    r"^[a-z0-9][a-z0-9-]{4,28}[a-z0-9]@"
    r"[a-z0-9][a-z0-9-]{4,28}[a-z0-9]\.iam\.gserviceaccount\.com$"
)


def planner_model_version(model_id: str) -> tuple[int, int] | None:
    """Return the numeric Gemini family version encoded in a model ID."""
    match = _MODEL_VERSION.search(model_id.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2) or 0)


def is_eligible_planner_model(model_id: str) -> bool:
    version = planner_model_version(model_id)
    return version is not None and version >= ELIGIBLE_PLANNER_VERSION


class WorkerSettings(BaseSettings):
    runtime_mode: RuntimeMode = Field(default=RuntimeMode.LOCAL_MOCK, alias="RUNTIME_MODE")
    legacy_use_local_mock: Optional[bool] = Field(default=None, alias="USE_LOCAL_MOCK", exclude=True)
    release_sha: str = Field(default="local-development", alias="RELEASE_SHA")

    google_cloud_project: str = Field(default="benchpress-dev", alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_region: str = Field(default="us-central1", alias="GOOGLE_CLOUD_REGION")
    google_application_credentials: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    firestore_database_id: str = Field(default="(default)", alias="FIRESTORE_DATABASE_ID")
    firestore_collection_prefix: str = Field(default="local", alias="FIRESTORE_COLLECTION_PREFIX")
    repository_backend: str = Field(default="memory", alias="REPOSITORY_BACKEND")

    tasks_queue_name: str = Field(default="local-trajectory-queue", alias="GCP_TASKS_QUEUE_NAME")
    tasks_location: str = Field(default="us-central1", alias="GCP_TASKS_LOCATION")
    worker_base_url: str = Field(default="http://localhost:8000", alias="SANDBOX_WORKER_URL")
    tasks_oidc_audience: str = Field(default="http://localhost:8000", alias="TASKS_OIDC_AUDIENCE")
    tasks_invoker_service_account: str = Field(
        default="local-tasks-invoker@benchpress-dev.iam.gserviceaccount.com",
        alias="GCP_TASKS_INVOKER_SERVICE_ACCOUNT",
    )

    vertex_ai_location: str = Field(default="us-central1", alias="VERTEX_AI_LOCATION")
    genai_use_vertexai: bool = Field(default=False, alias="GENAI_USE_VERTEXAI")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    planner_model: str = Field(default="gemini-3.5-local-fixture", alias="PLANNER_MODEL")
    coder_model: str = Field(default="gemini-2.5-flash", alias="CODER_MODEL")
    supervisor_model: str = Field(default="gemini-2.5-pro", alias="SUPERVISOR_MODEL")

    bigquery_dataset: str = Field(default="benchpress_dev_analytics", alias="BIGQUERY_DATASET")
    bigquery_table_trajectories: str = Field(default="trajectories", alias="BIGQUERY_TABLE_TRAJECTORIES")
    bigquery_table_turn_telemetry: str = Field(default="turn_telemetry", alias="BIGQUERY_TABLE_TURN_TELEMETRY")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    max_matrix_spend_usd: float = Field(default=0.50, gt=0, le=10, alias="MAX_MATRIX_SPEND_USD")
    per_run_spend_ceiling_usd: float = Field(default=0.05, gt=0, le=1, alias="PER_RUN_SPEND_CEILING_USD")
    default_budget_limit_usd: float = Field(default=0.05, gt=0, le=1, alias="DEFAULT_BUDGET_LIMIT_USD")
    max_turns: int = Field(default=15, ge=1, le=50, alias="MAX_TURNS")
    max_tool_calls: int = Field(default=20, ge=1, le=100, alias="MAX_TOOL_CALLS")
    per_run_timeout_seconds: int = Field(default=60, ge=1, le=900, alias="PER_RUN_TIMEOUT_SECONDS")
    max_provider_retries: int = Field(default=2, ge=0, le=5, alias="MAX_PROVIDER_RETRIES")
    concurrency_limit: int = Field(default=4, ge=1, le=50, alias="CONCURRENCY_LIMIT")
    early_halt_turn_threshold: int = Field(default=5, ge=1, le=50, alias="EARLY_HALT_TURN_THRESHOLD")
    benchpress_hmac_secret: str = Field(default="local-development-only", alias="BENCHPRESS_HMAC_SECRET")

    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")

    endpoint_orchestrate: str = "/orchestrate"
    endpoint_execute_run: str = "/execute-run"
    endpoint_aggregate: str = "/aggregate"
    endpoint_canary: str = "/canary"
    endpoint_publish: str = "/publish"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def use_local_mock(self) -> bool:
        return self.runtime_mode is RuntimeMode.LOCAL_MOCK

    @model_validator(mode="after")
    def validate_runtime_invariants(self) -> "WorkerSettings":
        if self.legacy_use_local_mock is not None and self.legacy_use_local_mock != self.use_local_mock:
            raise ValueError("USE_LOCAL_MOCK conflicts with RUNTIME_MODE; remove it and use RUNTIME_MODE only")

        if self.per_run_spend_ceiling_usd > self.max_matrix_spend_usd:
            raise ValueError("PER_RUN_SPEND_CEILING_USD cannot exceed MAX_MATRIX_SPEND_USD")
        if self.default_budget_limit_usd > self.per_run_spend_ceiling_usd:
            raise ValueError("DEFAULT_BUDGET_LIMIT_USD cannot exceed PER_RUN_SPEND_CEILING_USD")

        if self.use_local_mock:
            return self

        required = {
            "GOOGLE_CLOUD_PROJECT": self.google_cloud_project,
            "GOOGLE_CLOUD_REGION": self.google_cloud_region,
            "PLANNER_MODEL": self.planner_model,
            "GCP_TASKS_QUEUE_NAME": self.tasks_queue_name,
            "GCP_TASKS_LOCATION": self.tasks_location,
            "SANDBOX_WORKER_URL": self.worker_base_url,
            "TASKS_OIDC_AUDIENCE": self.tasks_oidc_audience,
            "GCP_TASKS_INVOKER_SERVICE_ACCOUNT": self.tasks_invoker_service_account,
            "FIRESTORE_DATABASE_ID": self.firestore_database_id,
            "FIRESTORE_COLLECTION_PREFIX": self.firestore_collection_prefix,
            "RELEASE_SHA": self.release_sha,
        }
        missing = sorted(name for name, value in required.items() if not str(value).strip())
        if missing:
            raise ValueError(f"Missing required non-local settings: {', '.join(missing)}")

        if not is_eligible_planner_model(self.planner_model):
            raise ValueError("PLANNER_MODEL must identify Gemini 3.5 or newer in non-local modes")
        if not _FULL_GIT_SHA.fullmatch(self.release_sha):
            raise ValueError("RELEASE_SHA must be the full 40-character lowercase Git commit SHA")
        if self.repository_backend != "firestore":
            raise ValueError("REPOSITORY_BACKEND must be 'firestore' outside local_mock mode")
        if not (self.gemini_api_key or self.genai_use_vertexai):
            raise ValueError("Configure GEMINI_API_KEY or set GENAI_USE_VERTEXAI=true")
        if not _SERVICE_ACCOUNT.fullmatch(self.tasks_invoker_service_account):
            raise ValueError("GCP_TASKS_INVOKER_SERVICE_ACCOUNT is not a valid service-account email")

        for name, value in {
            "SANDBOX_WORKER_URL": self.worker_base_url,
            "TASKS_OIDC_AUDIENCE": self.tasks_oidc_audience,
        }.items():
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"{name} must be an absolute HTTPS URL outside local_mock mode")
            if parsed.hostname in {"localhost", "0.0.0.0", "127.0.0.1", "::1"}:
                raise ValueError(f"{name} cannot target a local address outside local_mock mode")

        return self

    def readiness_summary(self) -> dict[str, object]:
        return {
            "configuration_status": "validated",
            "runtime_mode": self.runtime_mode.value,
            "release_sha": self.release_sha,
            "planner_model": self.planner_model,
            "repository_backend": self.repository_backend,
            "google_cloud_project": self.google_cloud_project,
            "google_cloud_region": self.google_cloud_region,
            "tasks_queue_name": self.tasks_queue_name,
            "tasks_location": self.tasks_location,
            "worker_base_url": self.worker_base_url,
        }


settings = WorkerSettings()
