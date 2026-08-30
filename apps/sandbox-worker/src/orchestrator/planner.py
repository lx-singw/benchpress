"""
Gemini Evaluation Planner & Function Calling Loop.
Coordinates the autonomous multi-turn tool-calling loop over sovereign tools.
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple, List
from .prompts import ORCHESTRATOR_SYSTEM_PROMPT, format_planner_user_prompt
from .tools import OrchestratorToolRegistry, GEMINI_TOOL_DECLARATIONS
from .gemini_client import GeminiOrchestratorClient, GeminiUsageMetadata
from contracts.hashing import generate_plan_id
from contracts.hashing import utc_now_rfc3339
from config import settings

logger = logging.getLogger("benchpress.orchestrator.planner")


class GeminiEvaluationPlanner:
    """Multi-turn evaluation orchestrator planner driving Gemini function calling."""

    def __init__(
        self,
        gemini_client: Optional[GeminiOrchestratorClient] = None,
        tool_registry: Optional[OrchestratorToolRegistry] = None,
        max_turns: int = 10,
    ):
        self.client = gemini_client or GeminiOrchestratorClient()
        self.tool_registry = tool_registry or OrchestratorToolRegistry()
        self.max_turns = max_turns
        self.last_invocation_record: Optional[Dict[str, Any]] = None

    def run(
        self,
        event_id: str,
        correlation_id: str,
        segment_id: str = "swe_coding_python_interactive",
    ) -> Tuple[Optional[Dict[str, Any]], GeminiUsageMetadata]:
        """
        Execute the multi-turn agentic planning loop.
        Returns the proposed experiment plan dictionary and aggregate usage metadata.
        """
        user_prompt = format_planner_user_prompt(
            event_id,
            correlation_id,
            segment_id,
            settings.task_fingerprint_id,
        )
        
        # If running in live mode with valid client
        if self.client.is_live():
            return self._run_live_loop(event_id, correlation_id, segment_id, user_prompt)
        
        if settings.use_local_mock:
            return self._run_simulated_loop(event_id, correlation_id, segment_id)
        raise RuntimeError("Eligible Gemini planner client is unavailable outside local_mock mode")

    def _run_simulated_loop(
        self,
        event_id: str,
        correlation_id: str,
        segment_id: str,
    ) -> Tuple[Dict[str, Any], GeminiUsageMetadata]:
        """Authentic multi-turn tool calling simulation for offline tests and local mock mode."""
        # 1. get_change_event
        change_event = self.tool_registry.get_change_event(event_id)
        # 2. get_current_baseline
        baseline_policy = self.tool_registry.get_current_baseline(segment_id)
        # 3. list_supported_configurations
        configs = self.tool_registry.list_supported_configurations("google", "gemini-2.5")
        # 4. get_task_fingerprint
        fingerprint = self.tool_registry.get_task_fingerprint("fp_1a2b3c4d5e6f7a8b")
        # 5. list_candidate_tasks
        tasks = self.tool_registry.list_candidate_tasks("judged_task_cohort.v1")

        # Select candidate configuration
        candidate_ids = [
            c["configuration_id"] for c in configs
            if c["configuration_id"] != baseline_policy["configuration_id"]
        ]
        if not candidate_ids:
            candidate_ids = ["cfg_4f1b82d3e9a0c784"]
        candidate_ids = candidate_ids[:1]

        selected_tasks = [t["task_id"] for t in tasks]

        # Construct deterministic ExperimentPlan
        plan_content = {
            "experiment_id": f"exp_{correlation_id.replace('corr_', '')}",
            "correlation_id": correlation_id,
            "event_id": event_id,
            "fingerprint_id": fingerprint["fingerprint_id"],
            "baseline_configuration_id": baseline_policy["configuration_id"],
            "candidate_configuration_ids": candidate_ids,
            "task_cohort_version": "cohort_swe_judged_v1",
            "selected_task_ids": selected_tasks,
            "repetitions_per_task": 1,
            "max_matrix_spend_usd": "0.500000",
            "reserved_budget_usd": "0.500000",
            "per_run_timeout_seconds": 60,
            "max_turns_per_run": 15,
            "quality_floor_pass_rate": 0.75,
            "early_stop_consecutive_failures": 2,
            "planner_model": settings.planner_model,
            "plan_policy_version": "plan_pol_v1_taskmaster",
            "planning_rationale": "Evaluating candidate configuration with 2048 thinking tokens vs baseline on judged SWE-bench tasks",
        }
        plan_id = generate_plan_id(plan_content)

        proposed_plan = {
            "schema_version": "1.0.0",
            "plan_id": plan_id,
            **plan_content,
            "created_at": utc_now_rfc3339(),
        }

        usage = GeminiUsageMetadata(
            prompt_tokens=1850,
            candidate_tokens=420,
            reasoning_tokens=256,
            total_tokens=2270,
            latency_ms=1200,
            finish_reason="STOP",
            model_id=settings.planner_model,
        )

        self.last_invocation_record = {
            "schema_version": "1.0.0",
            "truth_status": "DEMO_FIXTURE",
            "correlation_id": correlation_id,
            "requested_model": settings.planner_model,
            "request_hash": hashlib.sha256(
                json.dumps({"event_id": event_id, "segment_id": segment_id}, sort_keys=True).encode()
            ).hexdigest(),
            "tool_calls": [
                "get_change_event",
                "get_current_baseline",
                "list_supported_configurations",
                "get_task_fingerprint",
                "list_candidate_tasks",
                "propose_experiment",
            ],
            "usage": usage.__dict__,
            "created_at": utc_now_rfc3339(),
        }

        return proposed_plan, usage

    def _run_live_loop(
        self,
        event_id: str,
        correlation_id: str,
        segment_id: str,
        user_prompt: str,
    ) -> Tuple[Optional[Dict[str, Any]], GeminiUsageMetadata]:
        """Execute real multi-turn function calling conversation with Gemini API."""
        contents: List[Any] = [{"role": "user", "parts": [{"text": user_prompt}]}]
        accumulated_usage = GeminiUsageMetadata()
        proposed_plan: Optional[Dict[str, Any]] = None
        observed_tool_calls: List[Dict[str, Any]] = []
        request_hash = hashlib.sha256(
            json.dumps(
                {
                    "system_instruction": ORCHESTRATOR_SYSTEM_PROMPT,
                    "user_prompt": user_prompt,
                    "tools": GEMINI_TOOL_DECLARATIONS,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

        for turn in range(self.max_turns):
            result = self.client.call_with_tools(
                system_instruction=ORCHESTRATOR_SYSTEM_PROMPT,
                contents=contents,
                tools=GEMINI_TOOL_DECLARATIONS,
            )

            # Accumulate usage
            accumulated_usage.prompt_tokens += result.usage.prompt_tokens
            accumulated_usage.candidate_tokens += result.usage.candidate_tokens
            accumulated_usage.reasoning_tokens += result.usage.reasoning_tokens
            accumulated_usage.total_tokens += result.usage.total_tokens
            accumulated_usage.latency_ms += result.usage.latency_ms
            accumulated_usage.finish_reason = result.usage.finish_reason
            accumulated_usage.model_id = result.usage.model_id
            accumulated_usage.response_model = result.usage.response_model
            accumulated_usage.response_ids.extend(result.usage.response_ids)

            if not result.function_calls:
                # Terminal model response without function calls
                break

            # Gemini 3.7 signs function-call parts. Preserve the exact SDK
            # content object so its opaque thought signatures survive into the
            # next request; reconstructing the calls from name/args is invalid.
            if (
                result.raw_response is None
                or not result.raw_response.candidates
                or result.raw_response.candidates[0].content is None
            ):
                raise RuntimeError("Gemini function-call response omitted signed candidate content")
            contents.append(result.raw_response.candidates[0].content)
            function_response_parts: List[Dict[str, Any]] = []

            # Execute tool calls
            for fc in result.function_calls:
                name = fc["name"]
                args = fc["args"]
                observed_tool_calls.append({"name": name, "arguments_hash": hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()})
                tool_result = self._execute_tool(name, args)

                if name == "propose_experiment":
                    proposed_plan = args.get("plan")
                    self.last_invocation_record = {
                        "schema_version": "1.0.0",
                        "truth_status": "OBSERVED",
                        "correlation_id": correlation_id,
                        "requested_model": settings.planner_model,
                        "response_model": accumulated_usage.response_model,
                        "response_ids": accumulated_usage.response_ids,
                        "request_hash": request_hash,
                        "tool_calls": observed_tool_calls,
                        "usage": accumulated_usage.__dict__,
                        "created_at": utc_now_rfc3339(),
                    }
                    return proposed_plan, accumulated_usage

                function_response_parts.append({
                    "function_response": {
                        "name": name,
                        # FunctionResponse.response is always an object in the
                        # SDK contract, including when a tool returns a list.
                        "response": {"result": tool_result},
                    }
                })

            # Return all parallel tool results in one user turn, matching the
            # google-genai SDK's automatic function-calling conversation shape.
            contents.append({
                "role": "user",
                "parts": function_response_parts,
            })

        self.last_invocation_record = {
            "schema_version": "1.0.0",
            "truth_status": "OBSERVED",
            "correlation_id": correlation_id,
            "requested_model": settings.planner_model,
            "response_model": accumulated_usage.response_model,
            "response_ids": accumulated_usage.response_ids,
            "request_hash": request_hash,
            "tool_calls": observed_tool_calls,
            "usage": accumulated_usage.__dict__,
            "created_at": utc_now_rfc3339(),
        }
        return proposed_plan, accumulated_usage

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Dispatch tool name to OrchestratorToolRegistry method."""
        if name == "get_change_event":
            return self.tool_registry.get_change_event(args.get("event_id", ""))
        elif name == "get_current_baseline":
            return self.tool_registry.get_current_baseline(args.get("segment_id", ""))
        elif name == "list_supported_configurations":
            return self.tool_registry.list_supported_configurations(
                args.get("provider", "google"),
                args.get("model_family", "gemini-2.5")
            )
        elif name == "get_task_fingerprint":
            return self.tool_registry.get_task_fingerprint(args.get("fingerprint_id", ""))
        elif name == "list_candidate_tasks":
            return self.tool_registry.list_candidate_tasks(args.get("cohort_version", "judged_task_cohort.v1"))
        elif name == "propose_experiment":
            return self.tool_registry.propose_experiment(args.get("plan", {}))
        raise ValueError(f"Unknown tool name '{name}'")
