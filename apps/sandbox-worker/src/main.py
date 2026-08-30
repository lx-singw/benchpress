"""
Benchpress Sandbox Worker: FastAPI Cloud Tasks Target, Evaluation Orchestrator & Live Stream.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field

from config import settings
from fsm.states import TrajectoryContext, TrajectoryStatus
from fsm.engine import AsyncFSMRunner
from security.task_auth import verify_task_request
from orchestrator.service import OrchestratorService
from idempotency.service import IdempotencyService
from execution.run_service import RunExecutionService
from aggregation.aggregator import ConfigurationAggregator
from aggregation.sufficiency import SufficiencyEvaluator
from aggregation.early_stopping import EarlyStoppingEvaluator, StopAction
from policy.canary import CanaryExecutor
from policy.promotion import PolicyPromotionService
from policy.rollback import PolicyRollbackService
from policy.publication import mint_test_more_receipt
from policy.repository import get_policy_repository
from ledger.firestore import get_ledger
from contracts.models import RunManifest, RunResult, Aggregate, CanaryResult, DecisionReceipt, PolicyVersion
from contracts.states import ExperimentState, InternalOutcome, PublicDecision
from contracts.hashing import generate_deterministic_ulid, utc_now_rfc3339
from contracts.states import FailureReason, LogicalRunState
from task_queue.cloud_tasks import CloudTasksDispatcher
from telemetry.events import workflow_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchpress.worker")

app = FastAPI(
    title="Benchpress Sandbox Worker & Policy Governor",
    version="1.0.0",
    description="Cloud Run Gen2 Evaluation Orchestrator, Sandboxed Execution & Policy Promotion Engine",
)

orchestrator_service = OrchestratorService()
idempotency_service = IdempotencyService()
run_execution_service = RunExecutionService()
aggregator = ConfigurationAggregator()
sufficiency_evaluator = SufficiencyEvaluator()
early_stopping_evaluator = EarlyStoppingEvaluator()
canary_executor = CanaryExecutor()
promotion_service = PolicyPromotionService()
rollback_service = PolicyRollbackService()
policy_repo = get_policy_repository()
ledger = get_ledger()
task_dispatcher = CloudTasksDispatcher()


class OrchestrateRequest(BaseModel):
    event_id: str
    correlation_id: str
    segment_id: str = "swe_coding_python_interactive"


class AggregateRequest(BaseModel):
    experiment_id: str
    correlation_id: str
    baseline_configuration_id: str
    candidate_configuration_id: str
    task_segment_id: str = "swe_coding_python_interactive"


class CanaryRequest(BaseModel):
    experiment_id: str
    correlation_id: str
    task_segment_id: str = "swe_coding_python_interactive"
    baseline_policy_version: str
    candidate_policy_version: str
    baseline_configuration_id: str
    candidate_configuration_id: str
    baseline_aggregate_id: str
    candidate_aggregate_id: str
    canary_task_id: str = "TASK-001"


class TrajectoryTaskPayload(BaseModel):
    trajectory_id: str
    task_suite: str = Field(default="SWE_BENCH_VERIFIED")
    task_id: str = Field(default="django__django-11099")
    model_id: str = Field(default="gemini-2.5-pro")
    budget_limit_usd: float = Field(default=2.00, ge=0.01)
    max_turns: int = Field(default=20, ge=1, le=50)
    metadata: Optional[Dict[str, Any]] = None


active_connections: Dict[str, List[WebSocket]] = {}


def _resume_or_return_published(experiment_id: str) -> Optional[Dict[str, Any]]:
    """Complete a crash-interrupted publication and return its immutable receipt."""
    stored = ledger.get_decision_receipt_for_experiment(experiment_id)
    if not stored:
        return None
    experiment = ledger.get_experiment(experiment_id)
    if experiment and experiment.get("state") != ExperimentState.PUBLISHED.value:
        decision = PublicDecision(stored["public_decision"])
        if decision == PublicDecision.SWITCH:
            terminal_state = ExperimentState.RECOMMENDED
        elif decision == PublicDecision.TEST_MORE:
            terminal_state = ExperimentState.ABSTAINED
        else:
            terminal_state = (
                ExperimentState.ROLLED_BACK
                if stored.get("canary_id")
                else ExperimentState.REJECTED
            )
        if experiment.get("state") != terminal_state.value:
            ledger.update_experiment_state(
                experiment_id,
                terminal_state,
                reason=f"Resuming publication of receipt {stored['receipt_id']}.",
                actor="publisher_recovery",
            )
        ledger.update_experiment_state(
            experiment_id,
            ExperimentState.PUBLISHED,
            reason=f"Receipt {stored['receipt_id']} stored.",
            actor="publisher_recovery",
        )
    return stored


def _cancel_future_candidate_runs(manifest: RunManifest, plan: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the frozen early-stop policy only to queue tasks still unclaimed."""
    results = [RunResult.model_validate(item) for item in ledger.list_run_results(manifest.experiment_id)]
    baseline_id = plan["baseline_configuration_id"]
    candidate_id = manifest.configuration_id
    if candidate_id == baseline_id:
        return {"action": StopAction.CONTINUE.value, "cancelled": []}
    candidate_results = sorted(
        [item for item in results if item.configuration_id == candidate_id and item.eligible_for_aggregation],
        key=lambda item: (item.finished_at, item.logical_run_key),
    )
    baseline_results = sorted(
        [item for item in results if item.configuration_id == baseline_id and item.eligible_for_aggregation],
        key=lambda item: (item.finished_at, item.logical_run_key),
    )
    total_planned = len(plan["selected_task_ids"]) * int(plan["repetitions_per_task"])
    evaluation = early_stopping_evaluator.evaluate(
        candidate_results,
        baseline_results=baseline_results,
        total_planned_runs=total_planned,
        quality_floor=float(plan["quality_floor_pass_rate"]),
        consecutive_failure_limit=int(plan["early_stop_consecutive_failures"]),
    )
    cancelled = []
    if evaluation.cancel_undispatched:
        for pending in ledger.list_run_manifests(manifest.experiment_id):
            if pending.get("configuration_id") != candidate_id or pending.get("run_state") != LogicalRunState.PENDING.value:
                continue
            run_key = pending["logical_run_key"]
            timestamp = utc_now_rfc3339()
            cancellation = RunResult(
                logical_run_key=run_key,
                attempt_id=f"att_{generate_deterministic_ulid({'run_key': run_key, 'outcome': 'cancelled'})}",
                experiment_id=pending["experiment_id"],
                correlation_id=pending["correlation_id"],
                configuration_id=pending["configuration_id"],
                task_id=pending["task_id"],
                repetition_index=pending["repetition_index"],
                run_state=LogicalRunState.CANCELLED_BEFORE_START,
                resolved=False,
                failure_reason=FailureReason.CANCELLED,
                failure_details=evaluation.reason,
                turns_executed=0,
                prompt_tokens=0,
                completion_tokens=0,
                cached_tokens=0,
                reasoning_tokens=0,
                total_tokens=0,
                requested_model=None,
                response_model=None,
                provider_response_ids=[],
                observed_cost_usd="0.000000",
                price_version="NOT_INCURRED_EARLY_STOP",
                latency_ms=0,
                exit_code=0,
                assertions_passed=0,
                assertions_failed=0,
                eligible_for_aggregation=False,
                ineligibility_reason=evaluation.action.value,
                lease_owner="early_stopping_policy",
                started_at=timestamp,
                finished_at=timestamp,
                created_at=timestamp,
            )
            if ledger.cancel_pending_run(run_key, cancellation):
                task_dispatcher.cancel_run_task(run_key)
                cancelled.append(run_key)
    return {"action": evaluation.action.value, "reason": evaluation.reason, "cancelled": cancelled}


@app.get("/healthz")
async def health_check():
    """Liveness probe."""
    return {
        "status": "healthy",
        "service": "benchpress-sandbox-worker",
        "version": "1.0.0",
        "runtime": "python-3.12",
        "active_trajectories": len(active_connections),
    }


@app.get("/readyz")
async def readiness_check():
    """Sanitized startup-configuration readiness; live dependencies use release preflight."""
    return {
        "status": "ready",
        "service": "benchpress-sandbox-worker",
        **settings.readiness_summary(),
    }


@app.post("/orchestrate")
async def orchestrate_evaluation(
    payload: OrchestrateRequest,
    authenticated: bool = Depends(verify_task_request),
):
    """
    Cloud Tasks Target for Sovereign Evaluation Planning.
    """
    logger.info(f"[Worker] Received /orchestrate for event '{payload.event_id}' (corr: {payload.correlation_id})")
    result = await orchestrator_service.orchestrate(
        event_id=payload.event_id,
        correlation_id=payload.correlation_id,
        segment_id=payload.segment_id,
    )
    workflow_events.emit(
        correlation_id=payload.correlation_id,
        object_id=result.get("experiment_id", payload.event_id),
        event_type="ORCHESTRATION_COMPLETED",
        service="sandbox-worker",
        details={"status": result.get("status"), "plan_id": result.get("plan_id")},
    )
    return result


@app.post("/execute-run")
async def execute_run(
    manifest: RunManifest,
    authenticated: bool = Depends(verify_task_request),
    x_worker_id: Optional[str] = Header(None),
):
    """
    Cloud Tasks Target for Sandboxed Run Execution with CAS Idempotency.
    """
    worker_id = x_worker_id or f"worker_instance_{os.getpid()}"
    logger.info(f"[Worker] Received /execute-run for run_key '{manifest.logical_run_key}' (worker: {worker_id})")

    async def _execute_sandboxed():
        return await run_execution_service.execute_run(
            manifest=manifest,
            worker_id=worker_id,
        )

    outcome = await idempotency_service.execute_idempotent_run(
        run_key=manifest.logical_run_key,
        worker_id=worker_id,
        execution_coro=_execute_sandboxed,
    )

    if outcome.get("status") == "LEASE_HELD":
        raise HTTPException(status_code=429, detail="Active lease held by another worker. Retry later.")
    if outcome.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Run manifest not found.")

    experiment = ledger.get_experiment(manifest.experiment_id)
    if experiment and experiment.get("state") == ExperimentState.DISPATCHING.value:
        ledger.update_experiment_state(
            manifest.experiment_id,
            ExperimentState.RUNNING,
            reason=f"Terminal run stored: {manifest.logical_run_key}",
            actor="run_handler",
        )
        experiment = ledger.get_experiment(manifest.experiment_id)
    plan = ledger.get_plan_for_experiment(manifest.experiment_id)
    stopping = _cancel_future_candidate_runs(manifest, plan) if plan else {"action": StopAction.CONTINUE.value, "cancelled": []}
    if experiment and experiment.get("state") == ExperimentState.RUNNING.value and plan and plan.get("candidate_configuration_ids"):
        task_dispatcher.dispatch_aggregate_task(
            manifest.experiment_id,
            manifest.correlation_id,
            {
                "experiment_id": manifest.experiment_id,
                "correlation_id": manifest.correlation_id,
                "baseline_configuration_id": plan["baseline_configuration_id"],
                "candidate_configuration_id": plan["candidate_configuration_ids"][0],
                "task_segment_id": "swe_coding_python_interactive",
            },
        )

    workflow_events.emit(
        correlation_id=manifest.correlation_id,
        causation_id=manifest.logical_run_key,
        object_id=manifest.logical_run_key,
        event_type="RUN_TERMINAL_STORED",
        service="sandbox-worker",
        details={"status": outcome.get("status"), "deduplicated": outcome.get("deduplicated", False)},
    )

    outcome["early_stopping"] = stopping

    return outcome


@app.post("/aggregate")
async def aggregate_experiment_results(
    payload: AggregateRequest,
    authenticated: bool = Depends(verify_task_request),
):
    """
    Cloud Tasks Target for Aggregation, Stopping Evaluation and Sufficiency Decision.
    """
    logger.info(f"[Worker] Received /aggregate for experiment '{payload.experiment_id}'")

    published = _resume_or_return_published(payload.experiment_id)
    if published:
        return {
            "status": "PUBLISHED",
            "experiment_id": payload.experiment_id,
            "decision_receipt": published,
            "deduplicated": True,
        }

    experiment = ledger.get_experiment(payload.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.get("state") == ExperimentState.CANARY_PENDING.value:
        return {"status": "CANARY_PENDING", "experiment_id": payload.experiment_id, "deduplicated": True}

    # Select only the exact immutable run matrix. Foreign/late records cannot
    # influence a frozen experiment.
    manifests = ledger.list_run_manifests(payload.experiment_id)
    baseline_keys = {
        item["logical_run_key"]
        for item in manifests
        if item.get("configuration_id") == payload.baseline_configuration_id
    }
    candidate_keys = {
        item["logical_run_key"]
        for item in manifests
        if item.get("configuration_id") == payload.candidate_configuration_id
    }
    all_results = [
        RunResult.model_validate(res)
        for res in ledger.list_run_results(payload.experiment_id)
    ]

    base_results = [r for r in all_results if r.logical_run_key in baseline_keys]
    cand_results = [r for r in all_results if r.logical_run_key in candidate_keys]

    if (
        not baseline_keys
        or not candidate_keys
        or len(base_results) != len(baseline_keys)
        or len(cand_results) != len(candidate_keys)
    ):
        raise HTTPException(
            status_code=503,
            detail={
                "status": "AWAITING_RUNS",
                "experiment_id": payload.experiment_id,
                "baseline_runs_count": len(base_results),
                "baseline_runs_expected": len(baseline_keys),
                "candidate_runs_count": len(cand_results),
                "candidate_runs_expected": len(candidate_keys),
            },
        )

    base_agg = aggregator.aggregate_runs(
        experiment_id=payload.experiment_id,
        correlation_id=payload.correlation_id,
        configuration_id=payload.baseline_configuration_id,
        results=base_results,
    )

    cand_agg = aggregator.aggregate_runs(
        experiment_id=payload.experiment_id,
        correlation_id=payload.correlation_id,
        configuration_id=payload.candidate_configuration_id,
        results=cand_results,
    )

    ledger.store_aggregate(base_agg)
    ledger.store_aggregate(cand_agg)

    outcome = sufficiency_evaluator.evaluate_outcome(base_agg, cand_agg)
    workflow_events.emit(
        correlation_id=payload.correlation_id,
        object_id=cand_agg.aggregate_id,
        event_type="AGGREGATION_COMPLETED",
        service="sandbox-worker",
        details={
            "baseline_aggregate_id": base_agg.aggregate_id,
            "candidate_aggregate_id": cand_agg.aggregate_id,
            "internal_outcome": outcome.value,
        },
    )

    if experiment.get("state") == ExperimentState.RUNNING.value:
        ledger.update_experiment_state(
            experiment_id=payload.experiment_id,
            target_state=ExperimentState.AGGREGATING,
            reason=f"Complete frozen cohort aggregated. Outcome: {outcome.value}",
        )
    elif experiment.get("state") not in {
        ExperimentState.AGGREGATING.value,
        ExperimentState.REJECTED.value,
        ExperimentState.ABSTAINED.value,
    }:
        raise HTTPException(status_code=409, detail=f"Experiment cannot aggregate from state {experiment.get('state')}")

    active_policy = policy_repo.get_active_policy(payload.task_segment_id)
    if active_policy is None:
        raise HTTPException(status_code=409, detail="No immutable active baseline policy")
    approved_plan = ledger.get_plan_for_experiment(payload.experiment_id) or {}

    if outcome == InternalOutcome.SWITCH_RECOMMENDED:
        candidate_policy = PolicyVersion(
            policy_version=f"pol_{generate_deterministic_ulid({'experiment_id': payload.experiment_id, 'candidate_aggregate_id': cand_agg.aggregate_id})}",
            task_segment_id=payload.task_segment_id,
            configuration_id=payload.candidate_configuration_id,
            is_active=False,
            state_version=1,
            parent_policy_version=active_policy.policy_version,
            created_at=max(base_agg.created_at, cand_agg.created_at),
        )
        policy_repo.store_policy_version(candidate_policy)
        ledger.update_experiment_state(
            payload.experiment_id,
            ExperimentState.CANARY_PENDING,
            reason="Sufficient candidate evidence; contained canary scheduled.",
            actor="sufficiency_policy",
        )
        canary_task_name = task_dispatcher.dispatch_canary_task(
            candidate_policy.policy_version,
            payload.correlation_id,
            {
                "experiment_id": payload.experiment_id,
                "correlation_id": payload.correlation_id,
                "task_segment_id": payload.task_segment_id,
                "baseline_policy_version": active_policy.policy_version,
                "candidate_policy_version": candidate_policy.policy_version,
                "baseline_configuration_id": payload.baseline_configuration_id,
                "candidate_configuration_id": payload.candidate_configuration_id,
                "baseline_aggregate_id": base_agg.aggregate_id,
                "candidate_aggregate_id": cand_agg.aggregate_id,
                "canary_task_id": "TASK-001",
            },
        )
        workflow_events.emit(
            correlation_id=payload.correlation_id,
            causation_id=cand_agg.aggregate_id,
            object_id=candidate_policy.policy_version,
            event_type="CANARY_DISPATCHED",
            service="sandbox-worker",
            details={"cloud_task_name": canary_task_name},
        )
        return {
            "status": "CANARY_DISPATCHED",
            "experiment_id": payload.experiment_id,
            "internal_outcome": outcome.value,
            "canary_task_name": canary_task_name,
            "baseline_aggregate": base_agg.model_dump(mode="json"),
            "candidate_aggregate": cand_agg.model_dump(mode="json"),
        }

    if outcome == InternalOutcome.ABSTAIN_INSUFFICIENT_EVIDENCE:
        receipt = mint_test_more_receipt(
            experiment_id=payload.experiment_id,
            correlation_id=payload.correlation_id,
            task_segment_id=payload.task_segment_id,
            baseline_config_id=payload.baseline_configuration_id,
            candidate_config_id=payload.candidate_configuration_id,
            baseline_agg=base_agg,
            candidate_agg=cand_agg,
            reason="Frozen evidence-sufficiency policy did not support promotion or rejection.",
            trigger_event_id=experiment.get("event_id"),
            fingerprint_id=approved_plan.get("fingerprint_id"),
            plan_id=approved_plan.get("plan_id"),
            baseline_policy_version=active_policy.policy_version,
            selected_task_ids=approved_plan.get("selected_task_ids", []),
        )
        terminal_state = ExperimentState.ABSTAINED
    else:
        receipt = rollback_service.execute_rollback(
            experiment_id=payload.experiment_id,
            correlation_id=payload.correlation_id,
            task_segment_id=payload.task_segment_id,
            baseline_policy_version=active_policy.policy_version,
            candidate_policy_version=None,
            baseline_config_id=payload.baseline_configuration_id,
            candidate_config_id=payload.candidate_configuration_id,
            baseline_agg=base_agg,
            candidate_agg=cand_agg,
            rollback_reason=f"Deterministic aggregate outcome: {outcome.value}",
            trigger_event_id=experiment.get("event_id"),
            fingerprint_id=approved_plan.get("fingerprint_id"),
            plan_id=approved_plan.get("plan_id"),
            selected_task_ids=approved_plan.get("selected_task_ids", []),
        )
        terminal_state = ExperimentState.REJECTED
    ledger.update_experiment_state(payload.experiment_id, terminal_state, reason=receipt.why_decision, actor="decision_policy")
    ledger.publish_decision_receipt(
        receipt,
        reason=f"Receipt {receipt.receipt_id} stored and published.",
        actor="publisher",
    )
    workflow_events.emit(
        correlation_id=payload.correlation_id,
        object_id=receipt.receipt_id,
        event_type="DECISION_PUBLISHED",
        service="sandbox-worker",
        details={"public_decision": receipt.public_decision.value, "internal_outcome": receipt.internal_outcome.value},
    )

    return {
        "status": "PUBLISHED",
        "experiment_id": payload.experiment_id,
        "internal_outcome": outcome.value,
        "baseline_aggregate": base_agg.model_dump(mode="json"),
        "candidate_aggregate": cand_agg.model_dump(mode="json"),
        "decision_receipt": receipt.model_dump(mode="json"),
    }


@app.post("/canary")
async def execute_canary_evaluation(
    payload: CanaryRequest,
    authenticated: bool = Depends(verify_task_request),
):
    """
    Cloud Tasks Target for Contained Canary Verification and Atomic Policy Promotion.
    """
    logger.info(f"[Worker] Received /canary for candidate '{payload.candidate_policy_version}'")

    published = _resume_or_return_published(payload.experiment_id)
    if published:
        return {
            "status": "CANARY_COMPLETED",
            "experiment_id": payload.experiment_id,
            "decision_receipt": published,
            "deduplicated": True,
        }

    experiment = ledger.get_experiment(payload.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    approved_plan = ledger.get_plan_for_experiment(payload.experiment_id) or {}
    if experiment.get("state") == ExperimentState.CANARY_PENDING.value:
        ledger.update_experiment_state(
            payload.experiment_id,
            ExperimentState.CANARY_RUNNING,
            reason="Contained baseline/candidate canary execution started.",
            actor="canary_handler",
        )
    elif experiment.get("state") not in {
        ExperimentState.CANARY_RUNNING.value,
        ExperimentState.RECOMMENDED.value,
        ExperimentState.ROLLED_BACK.value,
    }:
        raise HTTPException(status_code=409, detail=f"Experiment cannot canary from state {experiment.get('state')}")

    canary_result = await canary_executor.execute_canary(
        experiment_id=payload.experiment_id,
        correlation_id=payload.correlation_id,
        baseline_policy_version=payload.baseline_policy_version,
        candidate_policy_version=payload.candidate_policy_version,
        baseline_config_id=payload.baseline_configuration_id,
        candidate_config_id=payload.candidate_configuration_id,
        canary_task_id=payload.canary_task_id,
    )

    baseline_agg_data = ledger.get_aggregate(payload.baseline_aggregate_id)
    candidate_agg_data = ledger.get_aggregate(payload.candidate_aggregate_id)
    if not baseline_agg_data or not candidate_agg_data:
        raise HTTPException(status_code=409, detail="Canary aggregate evidence is missing")
    baseline_agg = Aggregate.model_validate(baseline_agg_data)
    candidate_agg = Aggregate.model_validate(candidate_agg_data)

    if canary_result.promotion_approved:
        receipt = promotion_service.promote_candidate(
            experiment_id=payload.experiment_id,
            correlation_id=payload.correlation_id,
            task_segment_id=payload.task_segment_id,
            baseline_policy_version=payload.baseline_policy_version,
            candidate_policy_version=payload.candidate_policy_version,
            baseline_config_id=payload.baseline_configuration_id,
            candidate_config_id=payload.candidate_configuration_id,
            baseline_agg=baseline_agg,
            candidate_agg=candidate_agg,
            canary_res=canary_result,
            trigger_event_id=experiment.get("event_id"),
            fingerprint_id=approved_plan.get("fingerprint_id"),
            plan_id=approved_plan.get("plan_id"),
            selected_task_ids=approved_plan.get("selected_task_ids", []),
        )
        ledger.update_experiment_state(
            experiment_id=payload.experiment_id,
            target_state=ExperimentState.RECOMMENDED,
            reason="Canary passed all guardrails. Policy promoted.",
        )
    else:
        receipt = rollback_service.execute_rollback(
            experiment_id=payload.experiment_id,
            correlation_id=payload.correlation_id,
            task_segment_id=payload.task_segment_id,
            baseline_policy_version=payload.baseline_policy_version,
            candidate_policy_version=payload.candidate_policy_version,
            baseline_config_id=payload.baseline_configuration_id,
            candidate_config_id=payload.candidate_configuration_id,
            baseline_agg=baseline_agg,
            candidate_agg=candidate_agg,
            canary_res=canary_result,
            rollback_reason=canary_result.rollback_reason or "Contained canary failed.",
            trigger_event_id=experiment.get("event_id"),
            fingerprint_id=approved_plan.get("fingerprint_id"),
            plan_id=approved_plan.get("plan_id"),
            selected_task_ids=approved_plan.get("selected_task_ids", []),
        )
        ledger.update_experiment_state(
            experiment_id=payload.experiment_id,
            target_state=ExperimentState.ROLLED_BACK,
            reason=f"Canary failed: {canary_result.rollback_reason}",
        )

    ledger.publish_decision_receipt(
        receipt,
        reason=f"Decision receipt {receipt.receipt_id} stored and published.",
        actor="publisher",
    )
    workflow_events.emit(
        correlation_id=payload.correlation_id,
        causation_id=canary_result.canary_id,
        object_id=receipt.receipt_id,
        event_type="DECISION_PUBLISHED",
        service="sandbox-worker",
        details={
            "public_decision": receipt.public_decision.value,
            "canary_passed": canary_result.candidate_passed,
            "rollback_triggered": canary_result.rollback_triggered,
        },
    )

    return {
        "status": "CANARY_COMPLETED",
        "experiment_id": payload.experiment_id,
        "canary_result": canary_result.model_dump(mode="json"),
        "decision_receipt": receipt.model_dump(mode="json"),
    }


# Legacy endpoints
@app.post("/execute-task")
async def execute_trajectory_task(
    payload: TrajectoryTaskPayload,
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(verify_task_request),
    x_cloudtasks_queuename: Optional[str] = Header(None),
    x_benchpress_hmac: Optional[str] = Header(None),
):
    if not settings.use_local_mock:
        raise HTTPException(status_code=404, detail="Legacy endpoint disabled")

    background_tasks.add_task(_run_trajectory_job, payload)
    return {
        "status": "PROCESSING",
        "trajectory_id": payload.trajectory_id,
        "model_id": payload.model_id,
        "task_id": payload.task_id,
        "enqueued_at": ctx_now(),
    }


async def _run_trajectory_job(payload: TrajectoryTaskPayload):
    ctx = TrajectoryContext(
        trajectory_id=payload.trajectory_id,
        task_suite=payload.task_suite,
        task_id=payload.task_id,
        model_id=payload.model_id,
        budget_limit_usd=payload.budget_limit_usd,
        max_turns=payload.max_turns,
        metadata=payload.metadata or {},
    )
    runner = AsyncFSMRunner(context=ctx)
    result_ctx = await runner.run()
    await broadcast_trajectory_event(payload.trajectory_id, {
        "type": "TRAJECTORY_FINISHED",
        "status": result_ctx.status.value,
        "pass_at_1": result_ctx.pass_at_1,
        "turns_count": result_ctx.current_turn,
        "total_cost_usd": result_ctx.accumulated_cost_usd,
    })


async def broadcast_trajectory_event(trajectory_id: str, event_data: Dict[str, Any]):
    if trajectory_id in active_connections:
        for ws in active_connections[trajectory_id]:
            try:
                await ws.send_json(event_data)
            except Exception:
                pass


@app.websocket("/ws/trajectories/{trajectory_id}")
async def websocket_trajectory_stream(websocket: WebSocket, trajectory_id: str):
    if not settings.use_local_mock:
        await websocket.close(code=1008, reason="Legacy stream disabled outside local_mock")
        return
    await websocket.accept()
    if trajectory_id not in active_connections:
        active_connections[trajectory_id] = []
    active_connections[trajectory_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[trajectory_id].remove(websocket)
        if not active_connections[trajectory_id]:
            del active_connections[trajectory_id]


def ctx_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, log_level="info")
