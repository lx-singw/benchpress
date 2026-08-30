"""Immutable policy versions and transactional active-policy pointers."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Protocol

from config import settings
from contracts.hashing import utc_now_rfc3339
from contracts.models import PolicyVersion
from ledger.firestore import IntegrityConflict


class PolicyRepositoryProtocol(Protocol):
    def store_policy_version(self, policy: PolicyVersion) -> None: ...
    def get_policy(self, policy_version: str) -> Optional[PolicyVersion]: ...
    def get_active_policy(self, task_segment_id: str) -> Optional[PolicyVersion]: ...
    def get_active_pointer(self, task_segment_id: str) -> Optional[Dict[str, Any]]: ...
    def compare_and_swap_active_policy(self, task_segment_id: str, expected_active_version: str, new_candidate_version: str, decision_id: str, expected_generation: Optional[int] = None) -> bool: ...


class InMemoryPolicyRepository:
    """Thread-safe local/test repository with the same CAS semantics as Firestore."""

    def __init__(self, seed_default: bool = True):
        self._lock = threading.RLock()
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.active_pointers: Dict[str, Dict[str, Any]] = {}
        if seed_default:
            self._seed_default_policy()

    def _seed_default_policy(self) -> None:
        default = PolicyVersion(
            schema_version="1.0.0",
            policy_version="pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
            task_segment_id="swe_coding_python_interactive",
            configuration_id="cfg_948a3f81e3a1b029",
            is_active=True,
            state_version=1,
            created_at="2026-08-29T10:00:00.000Z",
        )
        self.store_policy_version(default)
        self.active_pointers[default.task_segment_id] = {
            "active_policy_version": default.policy_version,
            "generation": 1,
            "updated_at": default.created_at,
        }

    def store_policy_version(self, policy: PolicyVersion) -> None:
        payload = policy.model_dump(mode="json")
        with self._lock:
            existing = self.policies.get(policy.policy_version)
            if existing and existing != payload:
                raise IntegrityConflict(f"Conflicting policy content for {policy.policy_version}")
            self.policies.setdefault(policy.policy_version, payload)

    def get_policy(self, policy_version: str) -> Optional[PolicyVersion]:
        with self._lock:
            data = self.policies.get(policy_version)
            return PolicyVersion.model_validate(data) if data else None

    def get_active_policy(self, task_segment_id: str) -> Optional[PolicyVersion]:
        with self._lock:
            pointer = self.active_pointers.get(task_segment_id)
            if not pointer:
                return None
            data = self.policies.get(pointer["active_policy_version"])
            return PolicyVersion.model_validate(data) if data else None

    def get_active_pointer(self, task_segment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            pointer = self.active_pointers.get(task_segment_id)
            return dict(pointer) if pointer else None

    def compare_and_swap_active_policy(self, task_segment_id: str, expected_active_version: str, new_candidate_version: str, decision_id: str, expected_generation: Optional[int] = None) -> bool:
        with self._lock:
            pointer = self.active_pointers.get(task_segment_id)
            if not pointer or pointer["active_policy_version"] != expected_active_version:
                return False
            if expected_generation is not None and pointer["generation"] != expected_generation:
                return False
            candidate = self.policies.get(new_candidate_version)
            if not candidate or candidate["task_segment_id"] != task_segment_id:
                raise KeyError(f"Candidate policy not found for segment: {new_candidate_version}")
            current = self.policies.get(expected_active_version)
            if not current:
                raise IntegrityConflict(f"Active policy record missing: {expected_active_version}")

            now = utc_now_rfc3339()
            current.update({"is_active": False, "state_version": current["state_version"] + 1})
            candidate.update({
                "is_active": True,
                "promoted_by_decision_id": decision_id,
                "promoted_at": now,
                "state_version": candidate["state_version"] + 1,
            })
            self.active_pointers[task_segment_id] = {
                "active_policy_version": new_candidate_version,
                "generation": pointer["generation"] + 1,
                "updated_at": now,
                "decision_id": decision_id,
                "prior_policy_version": expected_active_version,
            }
            return True


class FirestorePolicyRepository:
    def __init__(self, client=None, collection_prefix: Optional[str] = None):
        from google.cloud import firestore

        self.firestore = firestore
        self.client = client or firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database_id,
        )
        self.prefix = collection_prefix or settings.firestore_collection_prefix

    def _collection(self, name: str):
        return self.client.collection(f"{self.prefix}_{name}")

    def store_policy_version(self, policy: PolicyVersion) -> None:
        reference = self._collection("policy_versions").document(policy.policy_version)
        payload = policy.model_dump(mode="json")
        transaction = self.client.transaction()

        @self.firestore.transactional
        def create(txn):
            snapshot = reference.get(transaction=txn)
            if snapshot.exists:
                if snapshot.to_dict() != payload:
                    raise IntegrityConflict(f"Conflicting policy content for {policy.policy_version}")
                return
            txn.create(reference, payload)

        create(transaction)

    def get_policy(self, policy_version: str) -> Optional[PolicyVersion]:
        snapshot = self._collection("policy_versions").document(policy_version).get()
        return PolicyVersion.model_validate(snapshot.to_dict()) if snapshot.exists else None

    def get_active_policy(self, task_segment_id: str) -> Optional[PolicyVersion]:
        pointer = self._collection("policy_pointers").document(task_segment_id).get()
        if not pointer.exists:
            return None
        return self.get_policy(pointer.get("active_policy_version"))

    def get_active_pointer(self, task_segment_id: str) -> Optional[Dict[str, Any]]:
        pointer = self._collection("policy_pointers").document(task_segment_id).get()
        return pointer.to_dict() if pointer.exists else None

    def initialize_active_policy(self, policy: PolicyVersion) -> None:
        """Create the first active pointer explicitly; production never seeds a fixture."""
        if not policy.is_active:
            raise ValueError("Initial policy must be active")
        policy_ref = self._collection("policy_versions").document(policy.policy_version)
        pointer_ref = self._collection("policy_pointers").document(policy.task_segment_id)
        transaction = self.client.transaction()

        @self.firestore.transactional
        def initialize(txn):
            pointer = pointer_ref.get(transaction=txn)
            if pointer.exists:
                if pointer.get("active_policy_version") != policy.policy_version:
                    raise IntegrityConflict("Active policy pointer already initialized differently")
                return
            policy_snapshot = policy_ref.get(transaction=txn)
            if policy_snapshot.exists and policy_snapshot.to_dict() != policy.model_dump(mode="json"):
                raise IntegrityConflict(f"Conflicting policy content for {policy.policy_version}")
            if not policy_snapshot.exists:
                txn.create(policy_ref, policy.model_dump(mode="json"))
            txn.create(pointer_ref, {
                "task_segment_id": policy.task_segment_id,
                "active_policy_version": policy.policy_version,
                "generation": 1,
                "updated_at": policy.created_at,
            })

        initialize(transaction)

    def compare_and_swap_active_policy(self, task_segment_id: str, expected_active_version: str, new_candidate_version: str, decision_id: str, expected_generation: Optional[int] = None) -> bool:
        pointer_ref = self._collection("policy_pointers").document(task_segment_id)
        current_ref = self._collection("policy_versions").document(expected_active_version)
        candidate_ref = self._collection("policy_versions").document(new_candidate_version)
        transaction = self.client.transaction()

        @self.firestore.transactional
        def promote(txn):
            pointer_snapshot = pointer_ref.get(transaction=txn)
            if not pointer_snapshot.exists or pointer_snapshot.get("active_policy_version") != expected_active_version:
                return False
            if expected_generation is not None and int(pointer_snapshot.get("generation")) != expected_generation:
                return False
            current_snapshot = current_ref.get(transaction=txn)
            candidate_snapshot = candidate_ref.get(transaction=txn)
            if not current_snapshot.exists:
                raise IntegrityConflict(f"Active policy record missing: {expected_active_version}")
            if not candidate_snapshot.exists or candidate_snapshot.get("task_segment_id") != task_segment_id:
                raise KeyError(f"Candidate policy not found for segment: {new_candidate_version}")
            now = utc_now_rfc3339()
            current = current_snapshot.to_dict()
            candidate = candidate_snapshot.to_dict()
            txn.update(current_ref, {"is_active": False, "state_version": current["state_version"] + 1})
            txn.update(candidate_ref, {
                "is_active": True,
                "promoted_by_decision_id": decision_id,
                "promoted_at": now,
                "state_version": candidate["state_version"] + 1,
            })
            txn.update(pointer_ref, {
                "active_policy_version": new_candidate_version,
                "generation": int(pointer_snapshot.get("generation")) + 1,
                "updated_at": now,
                "decision_id": decision_id,
                "prior_policy_version": expected_active_version,
            })
            return True

        return promote(transaction)


# Backward-compatible test name. Production selection occurs only in get_policy_repository().
PolicyRepository = InMemoryPolicyRepository

_policy_repo_instance: Optional[PolicyRepositoryProtocol] = None
_policy_backend: Optional[str] = None
_instance_lock = threading.Lock()


def get_policy_repository() -> PolicyRepositoryProtocol:
    global _policy_repo_instance, _policy_backend
    backend = settings.repository_backend
    with _instance_lock:
        if _policy_repo_instance is None or _policy_backend != backend:
            if backend == "memory" and settings.use_local_mock:
                _policy_repo_instance = InMemoryPolicyRepository()
            elif backend == "firestore" and not settings.use_local_mock:
                _policy_repo_instance = FirestorePolicyRepository()
            else:
                raise RuntimeError(
                    f"Policy backend '{backend}' is not allowed in runtime mode '{settings.runtime_mode.value}'"
                )
            _policy_backend = backend
        return _policy_repo_instance
