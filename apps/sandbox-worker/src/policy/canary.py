"""Contained, duplicate-safe baseline/candidate canary execution."""

from __future__ import annotations

from typing import Optional

from contracts.hashing import generate_deterministic_ulid, generate_logical_run_key, utc_now_rfc3339
from contracts.models import CanaryResult, RunManifest, RunResult
from execution.run_service import RunExecutionService
from idempotency.service import IdempotencyService
from ledger.firestore import get_ledger


class CanaryExecutor:
    def __init__(self, run_service: Optional[RunExecutionService] = None, ledger=None):
        self.ledger = ledger or get_ledger()
        self.run_service = run_service or RunExecutionService(ledger=self.ledger)
        self.idempotency = IdempotencyService(ledger=self.ledger)

    def _manifest(self, experiment_id: str, correlation_id: str, configuration_id: str, task_id: str, role: str, created_at: str) -> RunManifest:
        run_key = generate_logical_run_key({
            "experiment_id": experiment_id,
            "configuration_id": configuration_id,
            "task_id": task_id,
            "role": role,
            "harness_version": "pytest-8.3.0",
            "oracle_version": "oracle_v1_deterministic",
        })
        return RunManifest(
            logical_run_key=run_key,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            configuration_id=configuration_id,
            task_id=task_id,
            task_version_hash="647325057dca762d6a46813726e2764d12a98741ea7aed388acd9f3c32c814de",
            repetition_index=0,
            harness_version="pytest-8.3.0",
            oracle_version="oracle_v1_deterministic",
            tool_allowlist=["view_file", "edit_hunk"],
            path_allowlist=[],
            max_turns=10,
            timeout_seconds=30,
            max_spend_usd="0.050000",
            created_at=created_at,
        )

    async def execute_canary(
        self,
        experiment_id: str,
        correlation_id: str,
        baseline_policy_version: str,
        candidate_policy_version: str,
        baseline_config_id: str,
        candidate_config_id: str,
        canary_task_id: str = "TASK-001",
    ) -> CanaryResult:
        canary_id = f"cnry_{generate_deterministic_ulid({'experiment_id': experiment_id, 'candidate_policy_version': candidate_policy_version, 'canary_task_id': canary_task_id})}"
        existing = self.ledger.get_canary_result(canary_id)
        if existing:
            return CanaryResult.model_validate(existing)
        created_at = utc_now_rfc3339()
        baseline_manifest = self._manifest(
            experiment_id, correlation_id, baseline_config_id, canary_task_id, "baseline_canary", created_at
        )
        candidate_manifest = self._manifest(
            experiment_id, correlation_id, candidate_config_id, canary_task_id, "candidate_canary", created_at
        )
        if baseline_manifest.logical_run_key == candidate_manifest.logical_run_key:
            raise RuntimeError("Baseline and candidate canary run keys must be distinct")
        self.ledger.store_run_manifests([baseline_manifest, candidate_manifest])

        async def execute(manifest: RunManifest, worker: str) -> RunResult:
            outcome = await self.idempotency.execute_idempotent_run(
                manifest.logical_run_key,
                worker,
                lambda: self.run_service.execute_run(manifest=manifest, worker_id=worker),
            )
            if outcome["status"] not in {"EXECUTED", "CACHED_TERMINAL"}:
                raise RuntimeError(f"Canary run did not reach terminal state: {outcome['status']}")
            return RunResult.model_validate(outcome["result"])

        baseline_result = await execute(baseline_manifest, f"canary-baseline-{canary_id[5:15]}")
        candidate_result = await execute(candidate_manifest, f"canary-candidate-{canary_id[5:15]}")

        guardrails_evaluated = [
            "QUALITY_ASSERTION_ALL_PASS",
            "NO_BASELINE_QUALITY_REGRESSION",
            "LATENCY_UNDER_10S",
            "SPEND_UNDER_CEILING",
            "NO_SECURITY_BREACH",
        ]
        guardrails_breached = []
        if not candidate_result.resolved:
            guardrails_breached.append("QUALITY_ASSERTION_ALL_PASS")
        if baseline_result.resolved and not candidate_result.resolved:
            guardrails_breached.append("NO_BASELINE_QUALITY_REGRESSION")
        if candidate_result.latency_ms > 10_000:
            guardrails_breached.append("LATENCY_UNDER_10S")
        if float(candidate_result.observed_cost_usd) > float(candidate_manifest.max_spend_usd):
            guardrails_breached.append("SPEND_UNDER_CEILING")
        if "Security Violation" in (candidate_result.failure_details or ""):
            guardrails_breached.append("NO_SECURITY_BREACH")

        candidate_passed = not guardrails_breached
        evaluated_at = utc_now_rfc3339()
        result = CanaryResult(
            canary_id=canary_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            baseline_policy_version=baseline_policy_version,
            candidate_policy_version=candidate_policy_version,
            canary_task_ids=[canary_task_id],
            baseline_run_keys=[baseline_manifest.logical_run_key],
            candidate_run_keys=[candidate_manifest.logical_run_key],
            candidate_passed=candidate_passed,
            guardrails_evaluated=guardrails_evaluated,
            guardrails_breached=guardrails_breached,
            promotion_approved=candidate_passed,
            rollback_triggered=not candidate_passed,
            rollback_reason=(f"Canary failed guardrails: {', '.join(guardrails_breached)}" if guardrails_breached else None),
            evaluated_at=evaluated_at,
            created_at=evaluated_at,
        )
        self.ledger.store_canary_result(result)
        return result
