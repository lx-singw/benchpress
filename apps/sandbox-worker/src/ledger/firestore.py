"""Transactional run ledger implementations for local tests and Firestore."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from config import settings
from contracts.models import Aggregate, CanaryResult, DecisionReceipt, ExperimentPlan, RunManifest, RunResult
from contracts.states import ExperimentState, LogicalRunState, validate_experiment_transition


TERMINAL_RUN_STATES = {
    LogicalRunState.SUCCEEDED.value,
    LogicalRunState.FAILED_MODEL.value,
    LogicalRunState.FAILED_ORACLE.value,
    LogicalRunState.FAILED_INFRA.value,
    LogicalRunState.TIMED_OUT.value,
    LogicalRunState.BUDGET_EXCEEDED.value,
    LogicalRunState.CANCELLED_BEFORE_START.value,
}


class ClaimStatus(str, Enum):
    CLAIM_GRANTED = "CLAIM_GRANTED"
    ACTIVE_LEASE_HELD = "ACTIVE_LEASE_HELD"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    NOT_FOUND = "NOT_FOUND"


@dataclass
class ClaimResult:
    status: ClaimStatus
    manifest: Optional[Dict[str, Any]] = None
    terminal_result: Optional[Dict[str, Any]] = None
    lease_owner: Optional[str] = None
    lease_expires_at: Optional[float] = None
    state_version: int = 1
    invocation_fence: int = 0


class TransactionalLedger(Protocol):
    def store_experiment(self, experiment_id: str, initial_data: Dict[str, Any]) -> None: ...
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]: ...
    def update_experiment_state(self, experiment_id: str, target_state: ExperimentState, reason: str, actor: str = "orchestrator") -> Dict[str, Any]: ...
    def store_plan(self, plan: ExperimentPlan) -> None: ...
    def store_run_manifests(self, manifests: List[RunManifest]) -> None: ...
    def list_run_manifests(self, experiment_id: str) -> List[Dict[str, Any]]: ...
    def claim_logical_run(self, run_key: str, worker_id: str, lease_seconds: int = 120) -> ClaimResult: ...
    def commit_terminal_result(self, run_key: str, result: RunResult) -> None: ...
    def cancel_pending_run(self, run_key: str, result: RunResult) -> bool: ...
    def list_run_results(self, experiment_id: str) -> List[Dict[str, Any]]: ...
    def store_planner_invocation(self, experiment_id: str, record: Dict[str, Any]) -> None: ...
    def store_aggregate(self, aggregate: Aggregate) -> None: ...
    def get_aggregate(self, aggregate_id: str) -> Optional[Dict[str, Any]]: ...
    def store_canary_result(self, result: CanaryResult) -> None: ...
    def get_canary_result(self, canary_id: str) -> Optional[Dict[str, Any]]: ...
    def store_decision_receipt(self, receipt: DecisionReceipt) -> None: ...
    def publish_decision_receipt(self, receipt: DecisionReceipt, reason: str, actor: str = "publisher") -> None: ...
    def get_decision_receipt_for_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]: ...
    def list_replay_events(self, experiment_id: str) -> List[Dict[str, Any]]: ...
    def get_plan_for_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]: ...


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _canonical(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _payload_hash(value: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


class IntegrityConflict(RuntimeError):
    """Raised when an immutable ID is reused with different content."""


class InMemoryTransactionalLedger:
    """Thread-safe repository used only through explicit local/test injection."""

    def __init__(self):
        self._lock = threading.RLock()
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.plans: Dict[str, Dict[str, Any]] = {}
        self.manifests: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.replays: Dict[str, List[Dict[str, Any]]] = {}
        self.leases: Dict[str, Dict[str, Any]] = {}
        self.planner_invocations: Dict[str, Dict[str, Any]] = {}
        self.aggregates: Dict[str, Dict[str, Any]] = {}
        self.canary_results: Dict[str, Dict[str, Any]] = {}
        self.decision_receipts: Dict[str, Dict[str, Any]] = {}
        self.published_decisions: Dict[str, str] = {}

    def store_experiment(self, experiment_id: str, initial_data: Dict[str, Any]) -> None:
        with self._lock:
            proposed = {
                "experiment_id": experiment_id,
                "state": initial_data.get("state", ExperimentState.RECEIVED.value),
                "state_version": 1,
                "created_at": _utc_now(),
                **initial_data,
            }
            existing = self.experiments.get(experiment_id)
            if existing:
                material_keys = set(initial_data) | {"experiment_id"}
                if any(existing.get(key) != proposed.get(key) for key in material_keys):
                    raise IntegrityConflict(f"Conflicting experiment content for {experiment_id}")
                return
            self.experiments[experiment_id] = proposed

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            value = self.experiments.get(experiment_id)
            return dict(value) if value else None

    def update_experiment_state(self, experiment_id: str, target_state: ExperimentState, reason: str, actor: str = "orchestrator") -> Dict[str, Any]:
        with self._lock:
            exp = self.experiments.get(experiment_id)
            if not exp:
                raise KeyError(f"Experiment not found: {experiment_id}")
            current_state = ExperimentState(exp["state"])
            if current_state == target_state:
                return dict(exp)
            validate_experiment_transition(current_state, target_state)
            exp["state"] = target_state.value
            exp["state_version"] += 1
            exp["updated_at"] = _utc_now()
            events = self.replays.setdefault(experiment_id, [])
            event = {
                "sequence_id": len(events) + 1,
                "experiment_id": experiment_id,
                "correlation_id": exp.get("correlation_id"),
                "from_state": current_state.value,
                "to_state": target_state.value,
                "actor": actor,
                "transition_reason": reason,
                "timestamp": exp["updated_at"],
            }
            event["payload_hash"] = _payload_hash(event)
            events.append(event)
            return dict(exp)

    def store_plan(self, plan: ExperimentPlan) -> None:
        payload = plan.model_dump(mode="json")
        with self._lock:
            existing = self.plans.get(plan.plan_id)
            if existing and existing != payload:
                raise IntegrityConflict(f"Conflicting plan content for {plan.plan_id}")
            self.plans.setdefault(plan.plan_id, payload)

    def get_plan_for_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return next((dict(plan) for plan in self.plans.values() if plan.get("experiment_id") == experiment_id), None)

    def store_run_manifests(self, manifests: List[RunManifest]) -> None:
        with self._lock:
            for manifest in manifests:
                payload = {
                    **manifest.model_dump(mode="json"),
                    "run_state": LogicalRunState.PENDING.value,
                    "state_version": 1,
                    "invocation_fence": 0,
                }
                existing = self.manifests.get(manifest.logical_run_key)
                if existing:
                    material = manifest.model_dump(mode="json")
                    if any(existing.get(key) != value for key, value in material.items()):
                        raise IntegrityConflict(f"Conflicting run manifest for {manifest.logical_run_key}")
                    continue
                self.manifests[manifest.logical_run_key] = payload

    def list_run_manifests(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(value) for value in self.manifests.values() if value.get("experiment_id") == experiment_id]

    def claim_logical_run(self, run_key: str, worker_id: str, lease_seconds: int = 120) -> ClaimResult:
        with self._lock:
            manifest = self.manifests.get(run_key)
            if not manifest:
                return ClaimResult(status=ClaimStatus.NOT_FOUND)
            if manifest.get("run_state") in TERMINAL_RUN_STATES:
                return ClaimResult(
                    status=ClaimStatus.ALREADY_COMPLETED,
                    manifest=dict(manifest),
                    terminal_result=self.results.get(run_key),
                    state_version=manifest["state_version"],
                    invocation_fence=manifest.get("invocation_fence", 0),
                )
            now = time.time()
            lease = self.leases.get(run_key)
            if lease and lease["expires_at"] > now and lease["owner"] != worker_id:
                return ClaimResult(
                    status=ClaimStatus.ACTIVE_LEASE_HELD,
                    manifest=dict(manifest),
                    lease_owner=lease["owner"],
                    lease_expires_at=lease["expires_at"],
                    state_version=manifest["state_version"],
                    invocation_fence=manifest.get("invocation_fence", 0),
                )
            manifest["run_state"] = LogicalRunState.CLAIMED.value
            manifest["state_version"] += 1
            manifest["invocation_fence"] = manifest.get("invocation_fence", 0) + 1
            expires_at = now + lease_seconds
            manifest["lease_owner"] = worker_id
            manifest["lease_expires_at"] = expires_at
            self.leases[run_key] = {"owner": worker_id, "expires_at": expires_at}
            return ClaimResult(
                status=ClaimStatus.CLAIM_GRANTED,
                manifest=dict(manifest),
                lease_owner=worker_id,
                lease_expires_at=expires_at,
                state_version=manifest["state_version"],
                invocation_fence=manifest["invocation_fence"],
            )

    def commit_terminal_result(self, run_key: str, result: RunResult) -> None:
        payload = result.model_dump(mode="json")
        with self._lock:
            manifest = self.manifests.get(run_key)
            if not manifest:
                raise KeyError(f"Run manifest not found: {run_key}")
            existing = self.results.get(run_key)
            if existing:
                if existing != payload:
                    raise IntegrityConflict(f"Conflicting terminal result for {run_key}")
                return
            self.results[run_key] = payload
            manifest["run_state"] = result.run_state.value
            manifest["state_version"] += 1
            manifest["terminal_result_key"] = run_key
            manifest.pop("lease_owner", None)
            manifest.pop("lease_expires_at", None)
            self.leases.pop(run_key, None)

    def cancel_pending_run(self, run_key: str, result: RunResult) -> bool:
        if result.run_state != LogicalRunState.CANCELLED_BEFORE_START:
            raise ValueError("Cancellation result must use CANCELLED_BEFORE_START")
        with self._lock:
            manifest = self.manifests.get(run_key)
            if not manifest or manifest.get("run_state") != LogicalRunState.PENDING.value:
                return False
            self.results[run_key] = result.model_dump(mode="json")
            manifest["run_state"] = LogicalRunState.CANCELLED_BEFORE_START.value
            manifest["state_version"] += 1
            manifest["terminal_result_key"] = run_key
            return True

    def list_run_results(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(value) for value in self.results.values() if value.get("experiment_id") == experiment_id]

    def store_planner_invocation(self, experiment_id: str, record: Dict[str, Any]) -> None:
        with self._lock:
            existing = self.planner_invocations.get(experiment_id)
            if existing and existing != record:
                raise IntegrityConflict(f"Conflicting planner invocation for {experiment_id}")
            self.planner_invocations.setdefault(experiment_id, dict(record))

    def _store_model(self, target: Dict[str, Dict[str, Any]], key: str, model: Any) -> None:
        payload = model.model_dump(mode="json")
        with self._lock:
            existing = target.get(key)
            if existing and existing != payload:
                raise IntegrityConflict(f"Conflicting immutable record for {key}")
            target.setdefault(key, payload)

    def store_aggregate(self, aggregate: Aggregate) -> None:
        self._store_model(self.aggregates, aggregate.aggregate_id, aggregate)

    def get_aggregate(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            value = self.aggregates.get(aggregate_id)
            return dict(value) if value else None

    def store_canary_result(self, result: CanaryResult) -> None:
        self._store_model(self.canary_results, result.canary_id, result)

    def get_canary_result(self, canary_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            value = self.canary_results.get(canary_id)
            return dict(value) if value else None

    def store_decision_receipt(self, receipt: DecisionReceipt) -> None:
        self._store_model(self.decision_receipts, receipt.receipt_id, receipt)

    def publish_decision_receipt(self, receipt: DecisionReceipt, reason: str, actor: str = "publisher") -> None:
        payload = receipt.model_dump(mode="json")
        with self._lock:
            experiment = self.experiments.get(receipt.experiment_id)
            if not experiment:
                raise KeyError(f"Experiment not found: {receipt.experiment_id}")
            published_id = self.published_decisions.get(receipt.experiment_id)
            if published_id:
                if published_id != receipt.receipt_id:
                    raise IntegrityConflict(f"Experiment already published receipt {published_id}")
                return
            current_state = ExperimentState(experiment["state"])
            validate_experiment_transition(current_state, ExperimentState.PUBLISHED)
            existing = self.decision_receipts.get(receipt.receipt_id)
            if existing and existing != payload:
                raise IntegrityConflict(f"Conflicting immutable record for {receipt.receipt_id}")
            self.decision_receipts.setdefault(receipt.receipt_id, payload)
            self.published_decisions[receipt.experiment_id] = receipt.receipt_id
            updated_at = _utc_now()
            experiment.update({
                "state": ExperimentState.PUBLISHED.value,
                "state_version": experiment["state_version"] + 1,
                "decision_id": receipt.decision_id,
                "receipt_id": receipt.receipt_id,
                "publication_status": "PUBLISHED",
                "updated_at": updated_at,
            })
            events = self.replays.setdefault(receipt.experiment_id, [])
            event = {
                "sequence_id": len(events) + 1,
                "experiment_id": receipt.experiment_id,
                "correlation_id": receipt.correlation_id,
                "from_state": current_state.value,
                "to_state": ExperimentState.PUBLISHED.value,
                "actor": actor,
                "transition_reason": reason,
                "timestamp": updated_at,
            }
            event["payload_hash"] = _payload_hash(event)
            events.append(event)

    def get_decision_receipt_for_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            receipt_id = self.published_decisions.get(experiment_id)
            value = self.decision_receipts.get(receipt_id) if receipt_id else None
            return dict(value) if value else None

    def list_replay_events(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(event) for event in self.replays.get(experiment_id, [])]


class FirestoreTransactionalLedger:
    """Synchronous Firestore repository with transactional CAS and create-only evidence."""

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

    def store_experiment(self, experiment_id: str, initial_data: Dict[str, Any]) -> None:
        reference = self._collection("experiments").document(experiment_id)
        transaction = self.client.transaction()
        proposed = {
            "experiment_id": experiment_id,
            "state": initial_data.get("state", ExperimentState.RECEIVED.value),
            "state_version": 1,
            "created_at": _utc_now(),
            **initial_data,
        }

        @self.firestore.transactional
        def create(txn):
            snapshot = reference.get(transaction=txn)
            if snapshot.exists:
                existing = snapshot.to_dict()
                material_keys = set(initial_data) | {"experiment_id"}
                if any(existing.get(key) != proposed.get(key) for key in material_keys):
                    raise IntegrityConflict(f"Conflicting experiment content for {experiment_id}")
                return
            txn.create(reference, proposed)

        create(transaction)

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        snapshot = self._collection("experiments").document(experiment_id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def update_experiment_state(self, experiment_id: str, target_state: ExperimentState, reason: str, actor: str = "orchestrator") -> Dict[str, Any]:
        reference = self._collection("experiments").document(experiment_id)
        transaction = self.client.transaction()

        @self.firestore.transactional
        def transition(txn):
            snapshot = reference.get(transaction=txn)
            if not snapshot.exists:
                raise KeyError(f"Experiment not found: {experiment_id}")
            current = snapshot.to_dict()
            current_state = ExperimentState(current["state"])
            if current_state == target_state:
                return current
            validate_experiment_transition(current_state, target_state)
            sequence = int(current.get("state_version", 1))
            timestamp = _utc_now()
            event = {
                "sequence_id": sequence,
                "experiment_id": experiment_id,
                "correlation_id": current.get("correlation_id"),
                "from_state": current_state.value,
                "to_state": target_state.value,
                "actor": actor,
                "transition_reason": reason,
                "timestamp": timestamp,
            }
            event["payload_hash"] = _payload_hash(event)
            replay_ref = self._collection("replay_events").document(f"{experiment_id}:{sequence:06d}")
            updated = {
                **current,
                "state": target_state.value,
                "state_version": sequence + 1,
                "updated_at": timestamp,
            }
            txn.update(reference, {"state": target_state.value, "state_version": sequence + 1, "updated_at": timestamp})
            txn.create(replay_ref, event)
            return updated

        return transition(transaction)

    def _create_immutable(self, collection: str, key: str, payload: Dict[str, Any]) -> None:
        reference = self._collection(collection).document(key)
        transaction = self.client.transaction()

        @self.firestore.transactional
        def create(txn):
            snapshot = reference.get(transaction=txn)
            if snapshot.exists:
                existing = snapshot.to_dict()
                if any(existing.get(name) != value for name, value in payload.items()):
                    raise IntegrityConflict(f"Conflicting immutable {collection} content for {key}")
                return
            txn.create(reference, payload)

        create(transaction)

    def store_plan(self, plan: ExperimentPlan) -> None:
        self._create_immutable("plans", plan.plan_id, plan.model_dump(mode="json"))

    def get_plan_for_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        snapshots = list(self._collection("plans").where("experiment_id", "==", experiment_id).limit(2).stream())
        if len(snapshots) > 1:
            raise IntegrityConflict(f"Multiple approved plans found for {experiment_id}")
        return snapshots[0].to_dict() if snapshots else None

    def store_run_manifests(self, manifests: List[RunManifest]) -> None:
        for manifest in manifests:
            self._create_immutable(
                "run_manifests",
                manifest.logical_run_key,
                {
                    **manifest.model_dump(mode="json"),
                    "run_state": LogicalRunState.PENDING.value,
                    "state_version": 1,
                    "invocation_fence": 0,
                },
            )

    def list_run_manifests(self, experiment_id: str) -> List[Dict[str, Any]]:
        query = self._collection("run_manifests").where("experiment_id", "==", experiment_id)
        return [snapshot.to_dict() for snapshot in query.stream()]

    def claim_logical_run(self, run_key: str, worker_id: str, lease_seconds: int = 120) -> ClaimResult:
        reference = self._collection("run_manifests").document(run_key)
        result_reference = self._collection("run_results").document(run_key)
        transaction = self.client.transaction()

        @self.firestore.transactional
        def claim(txn):
            snapshot = reference.get(transaction=txn)
            if not snapshot.exists:
                return ClaimResult(status=ClaimStatus.NOT_FOUND)
            manifest = snapshot.to_dict()
            if manifest.get("run_state") in TERMINAL_RUN_STATES:
                result_snapshot = result_reference.get(transaction=txn)
                return ClaimResult(
                    status=ClaimStatus.ALREADY_COMPLETED,
                    manifest=manifest,
                    terminal_result=result_snapshot.to_dict() if result_snapshot.exists else None,
                    state_version=manifest["state_version"],
                    invocation_fence=manifest.get("invocation_fence", 0),
                )
            now = time.time()
            expires_at = float(manifest.get("lease_expires_at", 0) or 0)
            current_owner = manifest.get("lease_owner")
            if expires_at > now and current_owner != worker_id:
                return ClaimResult(
                    status=ClaimStatus.ACTIVE_LEASE_HELD,
                    manifest=manifest,
                    lease_owner=current_owner,
                    lease_expires_at=expires_at,
                    state_version=manifest["state_version"],
                    invocation_fence=manifest.get("invocation_fence", 0),
                )
            new_version = int(manifest.get("state_version", 1)) + 1
            new_fence = int(manifest.get("invocation_fence", 0)) + 1
            new_expiry = now + lease_seconds
            txn.update(
                reference,
                {
                    "run_state": LogicalRunState.CLAIMED.value,
                    "state_version": new_version,
                    "invocation_fence": new_fence,
                    "lease_owner": worker_id,
                    "lease_expires_at": new_expiry,
                },
            )
            manifest.update({
                "run_state": LogicalRunState.CLAIMED.value,
                "state_version": new_version,
                "invocation_fence": new_fence,
                "lease_owner": worker_id,
                "lease_expires_at": new_expiry,
            })
            return ClaimResult(
                status=ClaimStatus.CLAIM_GRANTED,
                manifest=manifest,
                lease_owner=worker_id,
                lease_expires_at=new_expiry,
                state_version=new_version,
                invocation_fence=new_fence,
            )

        return claim(transaction)

    def commit_terminal_result(self, run_key: str, result: RunResult) -> None:
        manifest_ref = self._collection("run_manifests").document(run_key)
        result_ref = self._collection("run_results").document(run_key)
        transaction = self.client.transaction()
        payload = result.model_dump(mode="json")

        @self.firestore.transactional
        def commit(txn):
            manifest_snapshot = manifest_ref.get(transaction=txn)
            if not manifest_snapshot.exists:
                raise KeyError(f"Run manifest not found: {run_key}")
            result_snapshot = result_ref.get(transaction=txn)
            if result_snapshot.exists:
                if result_snapshot.to_dict() != payload:
                    raise IntegrityConflict(f"Conflicting terminal result for {run_key}")
                return
            manifest = manifest_snapshot.to_dict()
            txn.create(result_ref, payload)
            txn.update(
                manifest_ref,
                {
                    "run_state": result.run_state.value,
                    "state_version": int(manifest.get("state_version", 1)) + 1,
                    "terminal_result_key": run_key,
                    "lease_owner": self.firestore.DELETE_FIELD,
                    "lease_expires_at": self.firestore.DELETE_FIELD,
                },
            )

        commit(transaction)

    def cancel_pending_run(self, run_key: str, result: RunResult) -> bool:
        if result.run_state != LogicalRunState.CANCELLED_BEFORE_START:
            raise ValueError("Cancellation result must use CANCELLED_BEFORE_START")
        manifest_ref = self._collection("run_manifests").document(run_key)
        result_ref = self._collection("run_results").document(run_key)
        transaction = self.client.transaction()
        payload = result.model_dump(mode="json")

        @self.firestore.transactional
        def cancel(txn):
            manifest_snapshot = manifest_ref.get(transaction=txn)
            if not manifest_snapshot.exists:
                return False
            manifest = manifest_snapshot.to_dict()
            if manifest.get("run_state") != LogicalRunState.PENDING.value:
                return False
            result_snapshot = result_ref.get(transaction=txn)
            if result_snapshot.exists:
                return result_snapshot.to_dict() == payload
            txn.create(result_ref, payload)
            txn.update(manifest_ref, {
                "run_state": LogicalRunState.CANCELLED_BEFORE_START.value,
                "state_version": int(manifest.get("state_version", 1)) + 1,
                "terminal_result_key": run_key,
            })
            return True

        return bool(cancel(transaction))

    def list_run_results(self, experiment_id: str) -> List[Dict[str, Any]]:
        query = self._collection("run_results").where("experiment_id", "==", experiment_id)
        return [snapshot.to_dict() for snapshot in query.stream()]

    def store_planner_invocation(self, experiment_id: str, record: Dict[str, Any]) -> None:
        self._create_immutable("planner_invocations", experiment_id, record)

    def store_aggregate(self, aggregate: Aggregate) -> None:
        self._create_immutable("aggregates", aggregate.aggregate_id, aggregate.model_dump(mode="json"))

    def get_aggregate(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        snapshot = self._collection("aggregates").document(aggregate_id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def store_canary_result(self, result: CanaryResult) -> None:
        self._create_immutable("canary_results", result.canary_id, result.model_dump(mode="json"))

    def get_canary_result(self, canary_id: str) -> Optional[Dict[str, Any]]:
        snapshot = self._collection("canary_results").document(canary_id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def store_decision_receipt(self, receipt: DecisionReceipt) -> None:
        self._create_immutable("decision_receipts", receipt.receipt_id, receipt.model_dump(mode="json"))

    def publish_decision_receipt(self, receipt: DecisionReceipt, reason: str, actor: str = "publisher") -> None:
        receipt_ref = self._collection("decision_receipts").document(receipt.receipt_id)
        publication_ref = self._collection("published_decisions").document(receipt.experiment_id)
        experiment_ref = self._collection("experiments").document(receipt.experiment_id)
        transaction = self.client.transaction()
        payload = receipt.model_dump(mode="json")

        @self.firestore.transactional
        def publish(txn):
            experiment_snapshot = experiment_ref.get(transaction=txn)
            if not experiment_snapshot.exists:
                raise KeyError(f"Experiment not found: {receipt.experiment_id}")
            publication = publication_ref.get(transaction=txn)
            if publication.exists:
                if publication.get("receipt_id") != receipt.receipt_id:
                    raise IntegrityConflict(
                        f"Experiment {receipt.experiment_id} already has terminal receipt {publication.get('receipt_id')}"
                    )
                return
            experiment = experiment_snapshot.to_dict()
            current_state = ExperimentState(experiment["state"])
            validate_experiment_transition(current_state, ExperimentState.PUBLISHED)
            existing = receipt_ref.get(transaction=txn)
            if existing.exists and existing.to_dict() != payload:
                raise IntegrityConflict(f"Conflicting immutable record for {receipt.receipt_id}")
            if not existing.exists:
                txn.create(receipt_ref, payload)
            sequence = int(experiment.get("state_version", 1))
            timestamp = _utc_now()
            event = {
                "sequence_id": sequence,
                "experiment_id": receipt.experiment_id,
                "correlation_id": receipt.correlation_id,
                "from_state": current_state.value,
                "to_state": ExperimentState.PUBLISHED.value,
                "actor": actor,
                "transition_reason": reason,
                "timestamp": timestamp,
            }
            event["payload_hash"] = _payload_hash(event)
            replay_ref = self._collection("replay_events").document(f"{receipt.experiment_id}:{sequence:06d}")
            txn.create(replay_ref, event)
            txn.update(experiment_ref, {
                "state": ExperimentState.PUBLISHED.value,
                "state_version": sequence + 1,
                "decision_id": receipt.decision_id,
                "receipt_id": receipt.receipt_id,
                "publication_status": "PUBLISHED",
                "updated_at": timestamp,
            })
            txn.create(publication_ref, {
                "experiment_id": receipt.experiment_id,
                "correlation_id": receipt.correlation_id,
                "receipt_id": receipt.receipt_id,
                "decision_id": receipt.decision_id,
                "task_segment_id": receipt.task_segment_id,
                "public_decision": receipt.public_decision.value,
                "publication_status": "PUBLISHED",
                "truth_class": receipt.truth_class.value,
                "created_at": receipt.created_at,
            })

        publish(transaction)

    def get_decision_receipt_for_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        publication = self._collection("published_decisions").document(experiment_id).get()
        if not publication.exists or publication.get("publication_status") != "PUBLISHED":
            return None
        receipt = self._collection("decision_receipts").document(publication.get("receipt_id")).get()
        return receipt.to_dict() if receipt.exists else None

    def list_replay_events(self, experiment_id: str) -> List[Dict[str, Any]]:
        query = self._collection("replay_events").where("experiment_id", "==", experiment_id)
        events = [snapshot.to_dict() for snapshot in query.stream()]
        return sorted(events, key=lambda event: event["sequence_id"])


_ledger_instance: Optional[TransactionalLedger] = None
_ledger_backend: Optional[str] = None
_instance_lock = threading.Lock()


def get_ledger() -> TransactionalLedger:
    global _ledger_instance, _ledger_backend
    backend = settings.repository_backend
    with _instance_lock:
        if _ledger_instance is None or _ledger_backend != backend:
            if backend == "memory" and settings.use_local_mock:
                _ledger_instance = InMemoryTransactionalLedger()
            elif backend == "firestore" and not settings.use_local_mock:
                _ledger_instance = FirestoreTransactionalLedger()
            else:
                raise RuntimeError(
                    f"Repository backend '{backend}' is not allowed in runtime mode '{settings.runtime_mode.value}'"
                )
            _ledger_backend = backend
        return _ledger_instance
