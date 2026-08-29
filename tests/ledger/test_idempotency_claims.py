"""
Transactional CAS Claims & Idempotency Tests (IMP-03).
"""

import time
import pytest
from ledger.firestore import InMemoryTransactionalLedger, ClaimStatus, ClaimResult
from idempotency.service import IdempotencyService
from contracts.models import RunManifest, RunResult
from contracts.states import LogicalRunState


@pytest.fixture
def sample_manifest():
    return RunManifest(
        schema_version="1.0.0",
        logical_run_key="run_01a2b3c4d5e6f789",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id="cfg_4f1b82d3e9a0c784",
        task_id="TASK-001",
        task_version_hash="647325057dca762d6a46813726e2764d12a98741ea7aed388acd9f3c32c814de",
        repetition_index=0,
        harness_version="pytest-8.3.0",
        oracle_version="oracle_v1_deterministic",
        tool_allowlist=["read_file"],
        path_allowlist=[],
        max_turns=15,
        timeout_seconds=60,
        max_spend_usd="0.050000",
        created_at="2026-08-29T10:00:25.000Z",
    )


def test_concurrent_claim_and_active_lease(sample_manifest):
    ledger = InMemoryTransactionalLedger()
    ledger.store_run_manifests([sample_manifest])

    run_key = sample_manifest.logical_run_key

    # Worker 1 claims lease
    claim1: ClaimResult = ledger.claim_logical_run(run_key, worker_id="worker_instance_1", lease_seconds=120)
    assert claim1.status == ClaimStatus.CLAIM_GRANTED
    assert claim1.lease_owner == "worker_instance_1"

    # Worker 2 tries to claim while lease is active
    claim2: ClaimResult = ledger.claim_logical_run(run_key, worker_id="worker_instance_2", lease_seconds=120)
    assert claim2.status == ClaimStatus.ACTIVE_LEASE_HELD
    assert claim2.lease_owner == "worker_instance_1"


@pytest.mark.asyncio
async def test_idempotent_cached_result_replay(sample_manifest):
    ledger = InMemoryTransactionalLedger()
    ledger.store_run_manifests([sample_manifest])
    service = IdempotencyService(ledger=ledger)

    run_key = sample_manifest.logical_run_key
    execution_count = 0

    async def sample_work():
        nonlocal execution_count
        execution_count += 1
        return RunResult(
            schema_version="1.0.0",
            logical_run_key=run_key,
            attempt_id="att_01J6G7R8Q9ABCDEFGHJKMNPQ30",
            experiment_id=sample_manifest.experiment_id,
            correlation_id=sample_manifest.correlation_id,
            configuration_id=sample_manifest.configuration_id,
            task_id=sample_manifest.task_id,
            repetition_index=0,
            run_state=LogicalRunState.SUCCEEDED,
            resolved=True,
            failure_reason="NONE",
            turns_executed=3,
            prompt_tokens=1250,
            completion_tokens=420,
            cached_tokens=0,
            total_tokens=1670,
            observed_cost_usd="0.003662",
            price_version="2026-08-29",
            latency_ms=2450,
            exit_code=0,
            assertions_passed=3,
            assertions_failed=0,
            eligible_for_aggregation=True,
            lease_owner="worker_instance_1",
            started_at="2026-08-29T10:00:26.000Z",
            finished_at="2026-08-29T10:00:29.000Z",
            created_at="2026-08-29T10:00:29.000Z",
        )

    # First delivery: executes work
    outcome1 = await service.execute_idempotent_run(run_key, "worker_instance_1", sample_work)
    assert outcome1["status"] == "EXECUTED"
    assert outcome1["deduplicated"] is False
    assert execution_count == 1

    # Second delivery (retry/duplicate): returns cached result without executing sample_work
    outcome2 = await service.execute_idempotent_run(run_key, "worker_instance_2", sample_work)
    assert outcome2["status"] == "CACHED_TERMINAL"
    assert outcome2["deduplicated"] is True
    assert execution_count == 1 # Work was NOT re-executed!
