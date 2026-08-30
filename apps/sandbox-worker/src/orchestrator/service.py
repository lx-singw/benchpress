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
from contracts.hashing import compute_canonical_hash, generate_logical_run_key, utc_now_rfc3339
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

        # 1. Initialize once, then resume safely from durable checkpoints on retry.
        experiment = self.ledger.get_experiment(experiment_id)
        if experiment is None:
            self.ledger.store_experiment(experiment_id, {
                "event_id": event_id,
                "correlation_id": correlation_id,
                "state": ExperimentState.RECEIVED.value,
            })
            experiment = self.ledger.get_experiment(experiment_id)
        elif (
            experiment.get("event_id") != event_id
            or experiment.get("correlation_id") != correlation_id
        ):
            raise ValueError(
                f"Experiment identity mismatch for {experiment_id}: "
                "event_id and correlation_id must be immutable"
            )

        current_state = ExperimentState(experiment["state"])
        if current_state == ExperimentState.RECEIVED:
            experiment = self.ledger.update_experiment_state(
                experiment_id=experiment_id,
                target_state=ExperimentState.PLANNING,
                reason="ChangeEvent validated; invoking Gemini 3.7 Evaluation Planner",
                actor="orchestrator_service",
            )
            current_state = ExperimentState(experiment["state"])

        if current_state not in {
            ExperimentState.PLANNING,
            ExperimentState.PLAN_APPROVED,
            ExperimentState.DISPATCHING,
        }:
            return {
                "status": "ALREADY_PROGRESSED",
                "experiment_id": experiment_id,
                "state": current_state.value,
            }

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

        usage = None
        approved_plan: Optional[ExperimentPlan] = None
        plan_hash: Optional[str] = None
        if current_state == ExperimentState.PLANNING:
            # 4. Run Gemini Evaluation Planner
            proposed_plan_dict, usage = self.planner.run(
                event_id=event_id,
                correlation_id=correlation_id,
                segment_id=segment_id,
            )
            if self.planner.last_invocation_record:
                self.ledger.store_planner_invocation(experiment_id, self.planner.last_invocation_record)

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

            approved_plan = approval.plan
            plan_hash = approval.plan_hash
            self.ledger.store_plan(approved_plan)

            # 6. Transition state: PLANNING -> PLAN_APPROVED
            self.ledger.update_experiment_state(
                experiment_id=experiment_id,
                target_state=ExperimentState.PLAN_APPROVED,
                reason=f"Plan '{approved_plan.plan_id}' approved. Hash: {plan_hash}",
            )
            current_state = ExperimentState.PLAN_APPROVED
        else:
            stored_plan = self.ledger.get_plan_for_experiment(experiment_id)
            if stored_plan is None:
                raise RuntimeError(
                    f"Experiment {experiment_id} is {current_state.value} without a durable plan checkpoint"
                )
            approved_plan = ExperimentPlan.model_validate(stored_plan)
            plan_hash = compute_canonical_hash(approved_plan.model_dump(mode="json"))

        # 7. Generate Immutable Run Manifests for each matrix cell
        stored_manifests = self.ledger.list_run_manifests(experiment_id)
        if stored_manifests:
            manifests = [
                RunManifest.model_validate({
                    field_name: manifest[field_name]
                    for field_name in RunManifest.model_fields
                    if field_name in manifest
                })
                for manifest in stored_manifests
            ]
        else:
            manifests = self._generate_run_manifests(approved_plan)
            self.ledger.store_run_manifests(manifests)
        logger.info(f"[Orchestrator] Generated {len(manifests)} immutable run manifests for '{experiment_id}'")

        # 8. Transition state: PLAN_APPROVED -> DISPATCHING
        if current_state == ExperimentState.PLAN_APPROVED:
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
            "plan_hash": plan_hash,
            "runs_count": len(manifests),
            "dispatched_task_names": dispatched_task_names,
            "usage": usage.__dict__ if usage else None,
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
                        tool_allowlist=["view_file", "edit_hunk", "run_bash"],
                        path_allowlist=[],
                        max_turns=plan.max_turns_per_run,
                        timeout_seconds=plan.per_run_timeout_seconds,
                        max_spend_usd="0.050000",
                        created_at=utc_now_rfc3339(),
                    )
                    manifests.append(manifest)

        return manifests
