"""
Firestore Transactional Ledger & CAS Lease Management.
Enforces atomic task claims, idempotency leases, and immutable state transitions.
"""

import time
import threading
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from contracts.models import (
    RunManifest,
    RunResult,
    ExperimentPlan,
    ReplayEvent,
    ChangeEvent,
)
from contracts.states import (
    ExperimentState,
    LogicalRunState,
    validate_experiment_transition,
    validate_run_transition,
)

logger = logging.getLogger("benchpress.ledger.firestore")


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


class InMemoryTransactionalLedger:
    """Thread-safe in-memory transactional ledger for local testing and mock mode."""

    def __init__(self):
        self._lock = threading.Lock()
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.plans: Dict[str, Dict[str, Any]] = {}
        self.manifests: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.replays: Dict[str, List[Dict[str, Any]]] = {}
        self.leases: Dict[str, Dict[str, Any]] = {} # run_key -> {owner, expires_at, version}

    def store_experiment(self, experiment_id: str, initial_data: Dict[str, Any]) -> None:
        with self._lock:
            self.experiments[experiment_id] = {
                "experiment_id": experiment_id,
                "state": initial_data.get("state", ExperimentState.RECEIVED.value),
                "state_version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **initial_data,
            }

    def update_experiment_state(
        self,
        experiment_id: str,
        target_state: ExperimentState,
        reason: str,
        actor: str = "orchestrator",
    ) -> Dict[str, Any]:
        with self._lock:
            exp = self.experiments.get(experiment_id)
            if not exp:
                exp = {"experiment_id": experiment_id, "state": ExperimentState.RECEIVED.value, "state_version": 1}
                self.experiments[experiment_id] = exp

            current_state = ExperimentState(exp["state"])
            validate_experiment_transition(current_state, target_state)

            exp["state"] = target_state.value
            exp["state_version"] += 1
            exp["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Record replay event
            if experiment_id not in self.replays:
                self.replays[experiment_id] = []
            seq_id = len(self.replays[experiment_id]) + 1
            self.replays[experiment_id].append({
                "sequence_id": seq_id,
                "experiment_id": experiment_id,
                "from_state": current_state.value,
                "to_state": target_state.value,
                "actor": actor,
                "transition_reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            return exp

    def store_plan(self, plan: ExperimentPlan) -> None:
        with self._lock:
            self.plans[plan.plan_id] = plan.model_dump(mode="json")

    def store_run_manifests(self, manifests: List[RunManifest]) -> None:
        with self._lock:
            for m in manifests:
                self.manifests[m.logical_run_key] = {
                    **m.model_dump(mode="json"),
                    "run_state": LogicalRunState.PENDING.value,
                    "state_version": 1,
                }

    def claim_logical_run(
        self,
        run_key: str,
        worker_id: str,
        lease_seconds: int = 120,
    ) -> ClaimResult:
        """Atomically claim a logical run task with CAS lease."""
        with self._lock:
            manifest = self.manifests.get(run_key)
            if not manifest:
                return ClaimResult(status=ClaimStatus.NOT_FOUND)

            # Check if already completed
            current_state = manifest.get("run_state")
            if current_state in {
                LogicalRunState.SUCCEEDED.value,
                LogicalRunState.FAILED_MODEL.value,
                LogicalRunState.FAILED_ORACLE.value,
                LogicalRunState.FAILED_INFRA.value,
                LogicalRunState.TIMED_OUT.value,
                LogicalRunState.BUDGET_EXCEEDED.value,
                LogicalRunState.CANCELLED_BEFORE_START.value,
            }:
                return ClaimResult(
                    status=ClaimStatus.ALREADY_COMPLETED,
                    manifest=manifest,
                    terminal_result=self.results.get(run_key),
                )

            # Check active lease
            now = time.time()
            lease = self.leases.get(run_key)
            if lease and lease["expires_at"] > now and lease["owner"] != worker_id:
                return ClaimResult(
                    status=ClaimStatus.ACTIVE_LEASE_HELD,
                    manifest=manifest,
                    lease_owner=lease["owner"],
                    lease_expires_at=lease["expires_at"],
                )

            # Grant lease
            new_expires = now + lease_seconds
            new_version = manifest.get("state_version", 1) + 1
            manifest["run_state"] = LogicalRunState.CLAIMED.value
            manifest["state_version"] = new_version
            manifest["lease_owner"] = worker_id

            self.leases[run_key] = {
                "owner": worker_id,
                "expires_at": new_expires,
                "version": new_version,
            }

            return ClaimResult(
                status=ClaimStatus.CLAIM_GRANTED,
                manifest=manifest,
                lease_owner=worker_id,
                lease_expires_at=new_expires,
                state_version=new_version,
            )

    def commit_terminal_result(self, run_key: str, result: RunResult) -> None:
        with self._lock:
            res_dict = result.model_dump(mode="json")
            self.results[run_key] = res_dict
            if run_key in self.manifests:
                self.manifests[run_key]["run_state"] = result.run_state.value
                self.manifests[run_key]["state_version"] += 1
            # Release lease
            self.leases.pop(run_key, None)


# Singleton instance
ledger_instance = InMemoryTransactionalLedger()

def get_ledger() -> InMemoryTransactionalLedger:
    return ledger_instance
