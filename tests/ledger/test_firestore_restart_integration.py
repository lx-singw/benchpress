from __future__ import annotations

import os
import uuid

import pytest

from contracts.models import PolicyVersion, RunManifest, RunResult
from contracts.states import LogicalRunState
from ledger.firestore import ClaimStatus, FirestoreTransactionalLedger
from policy.repository import FirestorePolicyRepository


pytestmark = pytest.mark.skipif(
    not os.getenv("FIRESTORE_EMULATOR_HOST"),
    reason="requires FIRESTORE_EMULATOR_HOST",
)


def _manifest() -> RunManifest:
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


def _result(manifest: RunManifest) -> RunResult:
    return RunResult(
        logical_run_key=manifest.logical_run_key,
        attempt_id="att_01J6G7R8Q9ABCDEFGHJKMNPQ30",
        experiment_id=manifest.experiment_id,
        correlation_id=manifest.correlation_id,
        configuration_id=manifest.configuration_id,
        task_id=manifest.task_id,
        repetition_index=0,
        run_state=LogicalRunState.SUCCEEDED,
        resolved=True,
        failure_reason="NONE",
        turns_executed=1,
        prompt_tokens=10,
        completion_tokens=2,
        cached_tokens=0,
        total_tokens=12,
        observed_cost_usd="0.000001",
        price_version="test",
        latency_ms=10,
        exit_code=0,
        assertions_passed=1,
        assertions_failed=0,
        eligible_for_aggregation=True,
        lease_owner="worker-1",
        started_at="2026-08-29T10:00:00.000Z",
        finished_at="2026-08-29T10:00:01.000Z",
        created_at="2026-08-29T10:00:01.000Z",
    )


def test_terminal_result_survives_repository_restart():
    from google.cloud import firestore

    client = firestore.Client(project="benchpress-emulator")
    prefix = f"test_{uuid.uuid4().hex}"
    first = FirestoreTransactionalLedger(client=client, collection_prefix=prefix)
    manifest = _manifest()
    first.store_run_manifests([manifest])
    assert first.claim_logical_run(manifest.logical_run_key, "worker-1").status is ClaimStatus.CLAIM_GRANTED
    first.commit_terminal_result(manifest.logical_run_key, _result(manifest))

    restarted = FirestoreTransactionalLedger(client=client, collection_prefix=prefix)
    replay = restarted.claim_logical_run(manifest.logical_run_key, "worker-2")
    assert replay.status is ClaimStatus.ALREADY_COMPLETED
    assert replay.terminal_result["attempt_id"] == "att_01J6G7R8Q9ABCDEFGHJKMNPQ30"


def test_policy_pointer_cas_survives_repository_restart():
    from google.cloud import firestore

    client = firestore.Client(project="benchpress-emulator")
    prefix = f"test_{uuid.uuid4().hex}"
    first = FirestorePolicyRepository(client=client, collection_prefix=prefix)
    baseline = PolicyVersion(
        policy_version="pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
        task_segment_id="segment-test",
        configuration_id="cfg_948a3f81e3a1b029",
        is_active=True,
        state_version=1,
        created_at="2026-08-29T10:00:00.000Z",
    )
    candidate = PolicyVersion(
        policy_version="pol_01J6G7R8Q9ABCDEFGHJKMNPQ11",
        task_segment_id="segment-test",
        configuration_id="cfg_4f1b82d3e9a0c784",
        is_active=False,
        state_version=1,
        parent_policy_version=baseline.policy_version,
        created_at="2026-08-29T10:00:00.000Z",
    )
    first.initialize_active_policy(baseline)
    first.store_policy_version(candidate)
    assert first.compare_and_swap_active_policy(
        "segment-test",
        baseline.policy_version,
        candidate.policy_version,
        "dec_01J6G7R8Q9ABCDEFGHJKMNPQ50",
    )

    restarted = FirestorePolicyRepository(client=client, collection_prefix=prefix)
    active = restarted.get_active_policy("segment-test")
    assert active is not None
    assert active.policy_version == candidate.policy_version
    assert not restarted.compare_and_swap_active_policy(
        "segment-test",
        baseline.policy_version,
        candidate.policy_version,
        "dec_01J6G7R8Q9ABCDEFGHJKMNPQ51",
    )
