"""
Benchpress Sandbox Worker Configuration & Environment Settings.
Hardened settings with production fail-closed validation and canonical queue paths.
"""

import os
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    # Google Cloud Platform
    google_cloud_project: str = Field(default="benchpress-dev", alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_region: str = Field(default="us-central1", alias="GOOGLE_CLOUD_REGION")
    google_application_credentials: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")

    # Vertex AI & Gemini Evaluation Orchestrator
    vertex_ai_location: str = Field(default="us-central1", alias="VERTEX_AI_LOCATION")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    planner_model: str = Field(default="gemini-2.5-pro", alias="PLANNER_MODEL")
    coder_model: str = Field(default="gemini-2.5-flash", alias="CODER_MODEL")
    supervisor_model: str = Field(default="gemini-2.5-pro", alias="SUPERVISOR_MODEL")

    # BigQuery Telemetry & Analytics
    bigquery_dataset: str = Field(default="benchpress_analytics", alias="BIGQUERY_DATASET")
    bigquery_table_trajectories: str = Field(default="trajectories", alias="BIGQUERY_TABLE_TRAJECTORIES")
    bigquery_table_turn_telemetry: str = Field(default="turn_telemetry", alias="BIGQUERY_TABLE_TURN_TELEMETRY")

    # Redis Memorystore
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # FinOps & Sandbox Execution Boundaries
    default_budget_limit_usd: float = Field(default=2.00, alias="DEFAULT_BUDGET_LIMIT_USD")
    max_turns: int = Field(default=20, alias="MAX_TURNS")
    early_halt_turn_threshold: int = Field(default=5, alias="EARLY_HALT_TURN_THRESHOLD")
    use_local_mock: bool = Field(default=True, alias="USE_LOCAL_MOCK")
    benchpress_hmac_secret: str = Field(default="benchpress-local-dev-hmac-secret-32b", alias="BENCHPRESS_HMAC_SECRET")

    # Server Configuration
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")

    # Canonical Task Queue Endpoint Paths
    endpoint_orchestrate: str = "/orchestrate"
    endpoint_execute_run: str = "/execute-run"
    endpoint_aggregate: str = "/aggregate"
    endpoint_canary: str = "/canary"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_production_invariants(self) -> "WorkerSettings":
        """Fail startup if USE_LOCAL_MOCK is false but required GCP credentials or models are missing."""
        if not self.use_local_mock:
            if not self.planner_model:
                raise ValueError("PLANNER_MODEL must be explicitly declared when USE_LOCAL_MOCK=false")
            has_creds = bool(self.gemini_api_key or self.google_application_credentials or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            if not has_creds:
                raise ValueError("GCP credentials (GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS) required in production mode (USE_LOCAL_MOCK=false)")
        return self


settings = WorkerSettings()
