"""
Gemini Evaluation Planner & Orchestration Workflow Tests (IMP-02).
"""

import os
from types import SimpleNamespace
import pytest
from orchestrator.tools import OrchestratorToolRegistry
from orchestrator.planner import GeminiEvaluationPlanner
from orchestrator.plan_policy import PlanPolicyValidator
from orchestrator.service import OrchestratorService
from orchestrator.gemini_client import (
    GeminiCallResult,
    GeminiOrchestratorClient,
    GeminiUsageMetadata,
)
from orchestrator.tools import GEMINI_TOOL_DECLARATIONS
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


def test_gemini_tool_declarations_are_wrapped_for_sdk():
    """Raw repository declarations must become one SDK Tool container."""
    pytest.importorskip("google.genai")
    config = GeminiOrchestratorClient._build_generation_config(
        GEMINI_TOOL_DECLARATIONS,
        "gemini-3.7-flash",
    )

    assert len(config.tools) == 1
    assert len(config.tools[0].function_declarations) == len(GEMINI_TOOL_DECLARATIONS)
    assert config.tools[0].function_declarations[0].name == "get_change_event"
    assert str(config.thinking_config.thinking_level).endswith("MEDIUM")


def test_live_planner_replays_signed_model_content_verbatim():
    """Gemini 3.7 thought signatures must survive multi-turn tool calls."""
    signed_content = object()

    class RecordingClient:
        def __init__(self):
            self.calls = []

        def is_live(self):
            return True

        def call_with_tools(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return GeminiCallResult(
                    function_calls=[{
                        "name": "list_candidate_tasks",
                        "args": {"cohort_version": "judged_task_cohort.v1"},
                    }],
                    usage=GeminiUsageMetadata(model_id="gemini-3.7-flash"),
                    raw_response=SimpleNamespace(
                        candidates=[SimpleNamespace(content=signed_content)]
                    ),
                )
            return GeminiCallResult(
                text="done",
                usage=GeminiUsageMetadata(model_id="gemini-3.7-flash"),
                raw_response=SimpleNamespace(candidates=[]),
            )

    client = RecordingClient()
    planner = GeminiEvaluationPlanner(gemini_client=client)
    plan, _ = planner.run(
        event_id="evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
    )

    assert plan is None
    second_turn_contents = client.calls[1]["contents"]
    assert second_turn_contents[1] is signed_content
    assert second_turn_contents[2]["role"] == "user"
    function_response = second_turn_contents[2]["parts"][0]["function_response"]
    assert function_response["name"] == "list_candidate_tasks"
    assert len(function_response["response"]["result"]) == 4


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

    retry_result = await service.orchestrate(
        event_id="evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
    )
    assert retry_result["status"] == "DISPATCHED"
    assert retry_result["usage"] is None
    assert retry_result["plan_hash"] == result["plan_hash"]


@pytest.mark.asyncio
async def test_orchestrator_resumes_from_planning_checkpoint():
    """A Cloud Tasks retry must resume after the RECEIVED -> PLANNING commit."""
    ledger = InMemoryTransactionalLedger()
    correlation_id = "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02"
    experiment_id = "exp_01J6G7R8Q9ABCDEFGHJKMNPQ02"
    event_id = "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01"
    ledger.store_experiment(experiment_id, {
        "event_id": event_id,
        "correlation_id": correlation_id,
        "state": ExperimentState.RECEIVED.value,
    })
    ledger.update_experiment_state(
        experiment_id,
        ExperimentState.PLANNING,
        reason="simulate a retry after the durable planning transition",
    )
    service = OrchestratorService(
        ledger=ledger,
        dispatcher=CloudTasksDispatcher(),
    )

    result = await service.orchestrate(
        event_id=event_id,
        correlation_id=correlation_id,
    )

    assert result["status"] == "DISPATCHED"
    assert ledger.get_experiment(experiment_id)["state"] == ExperimentState.DISPATCHING.value
