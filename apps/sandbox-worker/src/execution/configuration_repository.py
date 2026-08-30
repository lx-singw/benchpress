"""Immutable native provider configuration repositories."""

from __future__ import annotations

import threading
from typing import Dict, Iterable, Optional, Protocol

from config import settings
from contracts.models import NativeConfiguration
from contracts.hashing import generate_configuration_id
from ledger.firestore import IntegrityConflict


class ConfigurationRepository(Protocol):
    def get_configuration(self, configuration_id: str) -> Optional[NativeConfiguration]: ...
    def store_configuration(self, configuration: NativeConfiguration) -> None: ...


def derive_configuration_id(configuration: NativeConfiguration | dict) -> str:
    payload = (
        configuration.model_dump(mode="json", exclude_none=True)
        if isinstance(configuration, NativeConfiguration)
        else {key: value for key, value in dict(configuration).items() if value is not None}
    )
    payload.pop("configuration_id", None)
    payload.pop("created_at", None)
    return generate_configuration_id(payload)


def local_fixture_configurations() -> Iterable[NativeConfiguration]:
    common = {
        "schema_version": "1.0.0",
        "provider": "google",
        "request_model": "gemini-2.5-pro",
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": 8192,
        "system_instruction_hash": "c2" * 32,
        "tool_schema_hash": "d3" * 32,
        "price_input_per_million_usd": "1.250000",
        "price_output_per_million_usd": "5.000000",
        "price_source_version": "DEMO_FIXTURE_2026-08-29",
        "created_at": "2026-08-29T10:00:00.000Z",
    }
    yield NativeConfiguration(configuration_id="cfg_948a3f81e3a1b029", thinking_budget_tokens=0, **common)
    yield NativeConfiguration(configuration_id="cfg_4f1b82d3e9a0c784", thinking_budget_tokens=2048, **common)
    yield NativeConfiguration(
        configuration_id="cfg_7c2a93e4f1b80d19",
        thinking_budget_tokens=0,
        **{
            **common,
            "request_model": "gemini-2.5-flash",
            "price_input_per_million_usd": "0.075000",
            "price_output_per_million_usd": "0.300000",
        },
    )


class InMemoryConfigurationRepository:
    def __init__(self, seed_fixtures: bool = True):
        self._lock = threading.RLock()
        self.configurations: Dict[str, dict] = {}
        if seed_fixtures:
            for configuration in local_fixture_configurations():
                self.store_configuration(configuration)

    def get_configuration(self, configuration_id: str) -> Optional[NativeConfiguration]:
        with self._lock:
            value = self.configurations.get(configuration_id)
            return NativeConfiguration.model_validate(value) if value else None

    def store_configuration(self, configuration: NativeConfiguration) -> None:
        payload = configuration.model_dump(mode="json", exclude_none=True)
        with self._lock:
            existing = self.configurations.get(configuration.configuration_id)
            if existing and existing != payload:
                raise IntegrityConflict(f"Conflicting configuration content for {configuration.configuration_id}")
            self.configurations.setdefault(configuration.configuration_id, payload)


class FirestoreConfigurationRepository:
    def __init__(self, client=None, collection_prefix: Optional[str] = None):
        from google.cloud import firestore

        self.firestore = firestore
        self.client = client or firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database_id,
        )
        self.prefix = collection_prefix or settings.firestore_collection_prefix

    @property
    def collection(self):
        return self.client.collection(f"{self.prefix}_configurations")

    def get_configuration(self, configuration_id: str) -> Optional[NativeConfiguration]:
        snapshot = self.collection.document(configuration_id).get()
        return NativeConfiguration.model_validate(snapshot.to_dict()) if snapshot.exists else None

    def store_configuration(self, configuration: NativeConfiguration) -> None:
        expected_id = derive_configuration_id(configuration)
        if configuration.configuration_id != expected_id:
            raise ValueError(
                f"Configuration ID does not match canonical native settings: expected {expected_id}"
            )
        reference = self.collection.document(configuration.configuration_id)
        transaction = self.client.transaction()
        payload = configuration.model_dump(mode="json", exclude_none=True)

        @self.firestore.transactional
        def create(txn):
            snapshot = reference.get(transaction=txn)
            if snapshot.exists:
                if snapshot.to_dict() != payload:
                    raise IntegrityConflict(f"Conflicting configuration content for {configuration.configuration_id}")
                return
            txn.create(reference, payload)

        create(transaction)


_instance: Optional[ConfigurationRepository] = None
_backend: Optional[str] = None
_lock = threading.Lock()


def get_configuration_repository() -> ConfigurationRepository:
    global _instance, _backend
    backend = settings.repository_backend
    with _lock:
        if _instance is None or _backend != backend:
            if backend == "memory" and settings.use_local_mock:
                _instance = InMemoryConfigurationRepository()
            elif backend == "firestore" and not settings.use_local_mock:
                _instance = FirestoreConfigurationRepository()
            else:
                raise RuntimeError(f"Configuration backend '{backend}' is not allowed")
            _backend = backend
        return _instance
