"""
Gemini Evaluation Planner & Orchestration Workflow Tests (IMP-02).
"""

import os
import pytest
from orchestrator.tools import OrchestratorToolRegistry
from orchestrator.planner import GeminiEvaluationPlanner
from orchestrator.plan_policy import PlanPolicyValidator
from orchestrator.service import OrchestratorService
from contracts.models import ExperimentPlan
from contracts.states import ExperimentState
from ledger.firestore import InMemoryTransactionalLedger
from task_queue.cloud_tasks import CloudTasksDispatcher


def test_tool_registry_methods():
    """Verify all 6 typed tools return valid data structures."""
    registry = OrchestratorToolRegistry()

    # Tool 1: get_change_event
    ce = registry.get_change_event("evt_01J6G7R8Q9ABCDEFGHJKMNPQ01")
    assert ce["event_id"] == "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01"

    # Tool 2: get_current_baseline
    baseline = registry.get_current_baseline("swe_coding_python_interactive")
    assert baseline["configuration_id"].startswith("cfg_")

    # Tool 3: list_supported_configurations
    configs = registry.list_supported_configurations("google", "gemini-2.5")
    assert len(configs) >= 2

    # Tool 4: get_task_fingerprint
    fp = registry.get_task_fingerprint("fp_1a2b3c4d5e6f7a8b")
    assert fp["fingerprint_id"] == "fp_1a2b3c4d5e6f7a8b"

    # Tool 5: list_candidate_tasks
    tasks = registry.list_candidate_tasks("judged_task_cohort.v1")
    assert len(tasks) == 4

    # Tool 6: propose_experiment
    prop = registry.propose_experiment({"test": "plan"})
    assert prop["status"] == "PROPOSAL_SUBMITTED"


def test_planner_multi_turn_simulation():
    """Verify GeminiEvaluationPlanner produces a structured, validated ExperimentPlan."""
    planner = GeminiEvaluationPlanner()
    plan_dict, usage = planner.run(
        event_id="evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
    )

    assert plan_dict is not None
    assert "plan_id" in plan_dict
    assert plan_dict["baseline_configuration_id"] == "cfg_948a3f81e3a1b029"
    assert len(plan_dict["selected_task_ids"]) == 4

    # Verify Pydantic validation passes
    validated_plan = ExperimentPlan.model_validate(plan_dict)
    assert validated_plan.schema_version == "1.0.0"
    assert usage.total_tokens > 0


@pytest.mark.asyncio
async def test_orchestrator_service_lifecycle():
    """Verify full end-to-end orchestration workflow from RECEIVED to DISPATCHED."""
    ledger = InMemoryTransactionalLedger()
    dispatcher = CloudTasksDispatcher()
    service = OrchestratorService(ledger=ledger, dispatcher=dispatcher)

    result = await service.orchestrate(
        event_id="evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
    )

    assert result["status"] == "DISPATCHED"
    assert result["runs_count"] >= 4
    assert len(result["dispatched_task_names"]) == result["runs_count"]

    # Verify state in ledger
    exp_id = result["experiment_id"]
    exp = ledger.experiments.get(exp_id)
    assert exp is not None
    assert exp["state"] == ExperimentState.DISPATCHING.value
    assert exp["state_version"] >= 4 # RECEIVED -> PLANNING -> PLAN_APPROVED -> DISPATCHING
