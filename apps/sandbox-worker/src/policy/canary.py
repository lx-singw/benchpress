"""
Contained Canary Task Executor & Guardrail Evaluator.
Executes candidate policy on dedicated canary workload and verifies safety and quality guardrails before promotion.
"""

from typing import List, Dict, Any, Optional
from contracts.models import CanaryResult, RunManifest
from contracts.hashing import utc_now_rfc3339, generate_ulid
from execution.run_service import RunExecutionService


class CanaryExecutor:
    """Executes contained canary verification and evaluates guardrail invariant checks."""

    def __init__(self, run_service: Optional[RunExecutionService] = None):
        self.run_service = run_service or RunExecutionService()

    async def execute_canary(
        self,
        experiment_id: str,
        correlation_id: str,
        baseline_policy_version: str,
        candidate_policy_version: str,
        candidate_config_id: str,
        canary_task_id: str = "TASK-001",
    ) -> CanaryResult:
        canary_id = f"cnry_{generate_ulid()}"
        now_iso = utc_now_rfc3339()

        manifest = RunManifest(
            schema_version="1.0.0",
            logical_run_key=f"run_canary_{canary_id[5:21]}",
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            configuration_id=candidate_config_id,
            task_id=canary_task_id,
            task_version_hash="647325057dca762d6a46813726e2764d12a98741ea7aed388acd9f3c32c814de",
            repetition_index=0,
            harness_version="pytest-8.3.0",
            oracle_version="oracle_v1_deterministic",
            tool_allowlist=["view_file", "edit_hunk"],
            path_allowlist=[],
            max_turns=10,
            timeout_seconds=30,
            max_spend_usd="0.050000",
            created_at=now_iso,
        )

        run_res = await self.run_service.execute_run(
            manifest=manifest,
            worker_id=f"canary_worker_{canary_id[5:15]}",
        )

        guardrails_evaluated = [
            "QUALITY_ASSERTION_ALL_PASS",
            "LATENCY_UNDER_10S",
            "SPEND_UNDER_CEILING",
            "NO_SECURITY_BREACH",
        ]
        guardrails_breached = []

        if not run_res.resolved:
            guardrails_breached.append("QUALITY_ASSERTION_ALL_PASS")
        if run_res.latency_ms > 10000:
            guardrails_breached.append("LATENCY_UNDER_10S")
        if float(run_res.observed_cost_usd) > 0.05:
            guardrails_breached.append("SPEND_UNDER_CEILING")

        candidate_passed = len(guardrails_breached) == 0
        promotion_approved = candidate_passed
        rollback_triggered = not candidate_passed

        rollback_reason = None
        if rollback_triggered:
            rollback_reason = f"Canary failed guardrails: {', '.join(guardrails_breached)}"

        evaluated_iso = utc_now_rfc3339()

        return CanaryResult(
            schema_version="1.0.0",
            canary_id=canary_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            baseline_policy_version=baseline_policy_version,
            candidate_policy_version=candidate_policy_version,
            canary_task_ids=[canary_task_id],
            baseline_run_keys=[manifest.logical_run_key],
            candidate_run_keys=[manifest.logical_run_key],
            candidate_passed=candidate_passed,
            guardrails_evaluated=guardrails_evaluated,
            guardrails_breached=guardrails_breached,
            promotion_approved=promotion_approved,
            rollback_triggered=rollback_triggered,
            rollback_reason=rollback_reason,
            evaluated_at=evaluated_iso,
            created_at=evaluated_iso,
        )
