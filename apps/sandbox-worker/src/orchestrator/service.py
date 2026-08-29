"""
Orchestration Workflow Coordinator Service.
Coordinates ChangeEvent ingestion, Gemini planning, PlanPolicy gate, RunManifest generation, and Cloud Tasks dispatch.
"""

import logging
from typing import Dict, Any, List, Optional

from .planner import GeminiEvaluationPlanner
from .plan_policy import PlanPolicyValidator, PlanApprovalResult
from .tools import OrchestratorToolRegistry
from contracts.models import ChangeEvent, ExperimentPlan, RunManifest
from contracts.states import ExperimentState
from contracts.hashing import generate_logical_run_key, utc_now_rfc3339
from ledger.firestore import get_ledger
from task_queue.cloud_tasks import CloudTasksDispatcher

logger = logging.getLogger("benchpress.orchestrator.service")


class OrchestratorService:
    """Manages the lifecycle of an evaluation planning and dispatch session."""

    def __init__(
        self,
        planner: Optional[GeminiEvaluationPlanner] = None,
        validator: Optional[PlanPolicyValidator] = None,
        ledger = None,
        dispatcher: Optional[CloudTasksDispatcher] = None,
        tool_registry: Optional[OrchestratorToolRegistry] = None,
    ):
        self.tool_registry = tool_registry or OrchestratorToolRegistry()
        self.planner = planner or GeminiEvaluationPlanner(tool_registry=self.tool_registry)
        self.validator = validator or PlanPolicyValidator()
        self.ledger = ledger or get_ledger()
        self.dispatcher = dispatcher or CloudTasksDispatcher()

    async def orchestrate(
        self,
        event_id: str,
        correlation_id: str,
        segment_id: str = "swe_coding_python_interactive",
    ) -> Dict[str, Any]:
        """
        Main execution endpoint for POST /orchestrate.
        Transitions experiment from RECEIVED -> PLANNING -> PLAN_APPROVED -> DISPATCHING.
        """
        experiment_id = f"exp_{correlation_id.replace('corr_', '')}"
        logger.info(f"[Orchestrator] Starting orchestration for experiment '{experiment_id}' (event: {event_id})")

        # 1. Ensure experiment record is initialized in RECEIVED
        self.ledger.store_experiment(experiment_id, {
            "event_id": event_id,
            "correlation_id": correlation_id,
            "state": ExperimentState.RECEIVED.value,
        })

        # 2. Transition state: RECEIVED -> PLANNING
        self.ledger.update_experiment_state(
            experiment_id=experiment_id,
            target_state=ExperimentState.PLANNING,
            reason="ChangeEvent validated; invoking Gemini 3.5+ Evaluation Planner",
            actor="orchestrator_service",
        )

        # 3. Fetch triggering ChangeEvent
        try:
            change_event_dict = self.tool_registry.get_change_event(event_id)
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to fetch change event {event_id}: {e}")
            self.ledger.update_experiment_state(
                experiment_id=experiment_id,
                target_state=ExperimentState.FAILED_TERMINAL,
                reason=f"Failed to fetch change event: {str(e)}",
            )
            return {"status": "FAILED", "error": f"ChangeEvent not found: {str(e)}"}

        # 4. Run Gemini Evaluation Planner
        proposed_plan_dict, usage = self.planner.run(
            event_id=event_id,
            correlation_id=correlation_id,
            segment_id=segment_id,
        )

        if not proposed_plan_dict:
            rejection_reason = "Planner failed to propose a structured experiment plan."
            self.ledger.update_experiment_state(
                experiment_id=experiment_id,
                target_state=ExperimentState.PLAN_REJECTED,
                reason=rejection_reason,
            )
            return {
                "status": "PLAN_REJECTED",
                "experiment_id": experiment_id,
                "reasons": [rejection_reason],
                "usage": usage.__dict__,
            }

        # 5. Evaluate deterministic Plan Policy
        approval: PlanApprovalResult = self.validator.evaluate_plan(
            raw_plan=proposed_plan_dict,
            trigger_event=change_event_dict,
        )

        if not approval.approved:
            logger.warning(f"[Orchestrator] Plan rejected for experiment '{experiment_id}': {approval.reasons}")
            self.ledger.update_experiment_state(
                experiment_id=experiment_id,
                target_state=ExperimentState.PLAN_REJECTED,
                reason="; ".join(approval.reasons),
            )
            return {
                "status": "PLAN_REJECTED",
                "experiment_id": experiment_id,
                "reasons": approval.reasons,
                "usage": usage.__dict__,
            }

        approved_plan: ExperimentPlan = approval.plan
        self.ledger.store_plan(approved_plan)

        # 6. Transition state: PLANNING -> PLAN_APPROVED
        self.ledger.update_experiment_state(
            experiment_id=experiment_id,
            target_state=ExperimentState.PLAN_APPROVED,
            reason=f"Plan '{approved_plan.plan_id}' approved. Hash: {approval.plan_hash}",
        )

        # 7. Generate Immutable Run Manifests for each matrix cell
        manifests = self._generate_run_manifests(approved_plan)
        self.ledger.store_run_manifests(manifests)
        logger.info(f"[Orchestrator] Generated {len(manifests)} immutable run manifests for '{experiment_id}'")

        # 8. Transition state: PLAN_APPROVED -> DISPATCHING
        self.ledger.update_experiment_state(
            experiment_id=experiment_id,
            target_state=ExperimentState.DISPATCHING,
            reason=f"Dispatching {len(manifests)} runs to Cloud Tasks",
        )

        # 9. Dispatch Run Tasks via Cloud Tasks
        dispatched_task_names = self.dispatcher.dispatch_run_tasks(manifests)

        return {
            "status": "DISPATCHED",
            "experiment_id": experiment_id,
            "plan_id": approved_plan.plan_id,
            "plan_hash": approval.plan_hash,
            "runs_count": len(manifests),
            "dispatched_task_names": dispatched_task_names,
            "usage": usage.__dict__,
        }

    def _generate_run_manifests(self, plan: ExperimentPlan) -> List[RunManifest]:
        """Generate immutable matrix of RunManifests across configurations, tasks, and repetitions."""
        manifests: List[RunManifest] = []
        all_configs = [plan.baseline_configuration_id] + plan.candidate_configuration_ids

        for cfg_id in all_configs:
            for task_id in plan.selected_task_ids:
                for rep in range(plan.repetitions_per_task):
                    task_version_hash = "647325057dca762d6a46813726e2764d12a98741ea7aed388acd9f3c32c814de"
                    harness_version = "pytest-8.3.0"
                    oracle_version = "oracle_v1_deterministic"

                    run_key = generate_logical_run_key({
                        "experiment_id": plan.experiment_id,
                        "task_id": task_id,
                        "task_version_hash": task_version_hash,
                        "configuration_id": cfg_id,
                        "repetition_index": rep,
                        "harness_version": harness_version,
                        "oracle_version": oracle_version,
                    })

                    manifest = RunManifest(
                        schema_version="1.0.0",
                        logical_run_key=run_key,
                        experiment_id=plan.experiment_id,
                        correlation_id=plan.correlation_id,
                        configuration_id=cfg_id,
                        task_id=task_id,
                        task_version_hash=task_version_hash,
                        repetition_index=rep,
                        harness_version=harness_version,
                        oracle_version=oracle_version,
                        tool_allowlist=["read_file", "replace_file_content", "run_pytest"],
                        path_allowlist=[],
                        max_turns=plan.max_turns_per_run,
                        timeout_seconds=plan.per_run_timeout_seconds,
                        max_spend_usd="0.050000",
                        created_at=utc_now_rfc3339(),
                    )
                    manifests.append(manifest)

        return manifests
