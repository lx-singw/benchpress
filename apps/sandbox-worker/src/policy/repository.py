"""
Policy Version Repository.
Manages immutable PolicyVersion records and transactional compare-and-swap active pointer updates.
"""

import threading
from typing import Dict, Any, Optional
from contracts.models import PolicyVersion
from contracts.hashing import utc_now_rfc3339, generate_ulid


class PolicyRepository:
    """Thread-safe transactional repository for active and candidate policy versions."""

    def __init__(self):
        self._lock = threading.Lock()
        self.policies: Dict[str, Dict[str, Any]] = {} # policy_version -> dict
        self.active_pointers: Dict[str, str] = {} # task_segment_id -> policy_version
        self._seed_default_policy()

    def _seed_default_policy(self):
        default_policy = PolicyVersion(
            schema_version="1.0.0",
            policy_version="pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
            task_segment_id="swe_coding_python_interactive",
            configuration_id="cfg_948a3f81e3a1b029",
            is_active=True,
            state_version=1,
            created_at="2026-08-29T10:00:00.000Z",
        )
        self.store_policy_version(default_policy)
        self.active_pointers["swe_coding_python_interactive"] = default_policy.policy_version

    def store_policy_version(self, policy: PolicyVersion) -> None:
        with self._lock:
            self.policies[policy.policy_version] = policy.model_dump(mode="json")

    def get_policy(self, policy_version: str) -> Optional[PolicyVersion]:
        with self._lock:
            data = self.policies.get(policy_version)
            return PolicyVersion.model_validate(data) if data else None

    def get_active_policy(self, task_segment_id: str) -> Optional[PolicyVersion]:
        with self._lock:
            active_version = self.active_pointers.get(task_segment_id)
            if not active_version:
                return None
            data = self.policies.get(active_version)
            return PolicyVersion.model_validate(data) if data else None

    def compare_and_swap_active_policy(
        self,
        task_segment_id: str,
        expected_active_version: str,
        new_candidate_version: str,
        decision_id: str,
    ) -> bool:
        """
        Atomically updates the active policy pointer if and only if current active equals expected.
        """
        with self._lock:
            current_active = self.active_pointers.get(task_segment_id)
            if current_active != expected_active_version:
                return False

            now_iso = utc_now_rfc3339()

            # Mark old as inactive
            if current_active in self.policies:
                self.policies[current_active]["is_active"] = False
                self.policies[current_active]["state_version"] += 1

            # Mark candidate as active
            if new_candidate_version in self.policies:
                self.policies[new_candidate_version]["is_active"] = True
                self.policies[new_candidate_version]["promoted_by_decision_id"] = decision_id
                self.policies[new_candidate_version]["promoted_at"] = now_iso
                self.policies[new_candidate_version]["state_version"] += 1

            self.active_pointers[task_segment_id] = new_candidate_version
            return True


policy_repo_instance = PolicyRepository()

def get_policy_repository() -> PolicyRepository:
    return policy_repo_instance
