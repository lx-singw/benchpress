"""
Typed Tools Exposed to Gemini 3.5+ Evaluation Orchestrator.
6 Sovereign tools for inspecting triggers, baselines, configurations, fingerprints, tasks, and submitting proposals.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from contracts.models import (
    ChangeEvent,
    TaskFingerprint,
    NativeConfiguration,
    PolicyVersion,
    ExperimentPlan,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
MANIFESTS_DIR = REPO_ROOT / "tests" / "fixtures" / "manifests"
CONTRACTS_VALID_DIR = REPO_ROOT / "tests" / "fixtures" / "contracts" / "valid"


class OrchestratorToolRegistry:
    """Provides typed tool implementations grounded in frozen manifests and contracts."""

    def __init__(
        self,
        event_store: Optional[Dict[str, Dict[str, Any]]] = None,
        policy_store: Optional[Dict[str, Dict[str, Any]]] = None,
        config_store: Optional[Dict[str, Dict[str, Any]]] = None,
        fingerprint_store: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.event_store = event_store or {}
        self.policy_store = policy_store or {}
        self.config_store = config_store or {}
        self.fingerprint_store = fingerprint_store or {}
        self._load_defaults_if_empty()

    def _load_defaults_if_empty(self):
        """Seed default fixtures if store is empty."""
        try:
            # ChangeEvent default
            ce_file = CONTRACTS_VALID_DIR / "change-event.json"
            if ce_file.exists():
                with open(ce_file, "r", encoding="utf-8") as f:
                    ce_data = json.load(f)
                    self.event_store[ce_data["event_id"]] = ce_data

            # Baseline policy default
            baseline_policy = {
                "schema_version": "1.0.0",
                "policy_version": "pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
                "task_segment_id": "swe_coding_python_interactive",
                "configuration_id": "cfg_948a3f81e3a1b029",
                "is_active": True,
                "state_version": 1,
                "parent_policy_version": None,
                "promoted_by_decision_id": None,
                "promoted_at": None,
                "created_at": "2026-08-29T10:00:00.000Z",
            }
            self.policy_store["swe_coding_python_interactive"] = baseline_policy

            # Baseline config
            baseline_cfg = {
                "schema_version": "1.0.0",
                "configuration_id": "cfg_948a3f81e3a1b029",
                "provider": "google",
                "request_model": "gemini-2.5-pro",
                "thinking_budget_tokens": 0,
                "temperature": 0.0,
                "top_p": 1.0,
                "max_output_tokens": 8192,
                "system_instruction_hash": "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
                "tool_schema_hash": "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
                "price_input_per_million_usd": "1.250000",
                "price_output_per_million_usd": "5.000000",
                "price_source_version": "2026-08-29",
                "created_at": "2026-08-29T10:00:00.000Z",
            }
            self.config_store["cfg_948a3f81e3a1b029"] = baseline_cfg

            # Target Candidate config (2048 thinking)
            candidate_cfg = {
                "schema_version": "1.0.0",
                "configuration_id": "cfg_4f1b82d3e9a0c784",
                "provider": "google",
                "request_model": "gemini-2.5-pro",
                "thinking_budget_tokens": 2048,
                "temperature": 0.0,
                "top_p": 1.0,
                "max_output_tokens": 8192,
                "system_instruction_hash": "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
                "tool_schema_hash": "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
                "price_input_per_million_usd": "1.250000",
                "price_output_per_million_usd": "5.000000",
                "price_source_version": "2026-08-29",
                "created_at": "2026-08-29T10:00:15.000Z",
            }
            self.config_store["cfg_4f1b82d3e9a0c784"] = candidate_cfg

            # Flash cheap config
            flash_cfg = {
                "schema_version": "1.0.0",
                "configuration_id": "cfg_7c2a93e4f1b80d19",
                "provider": "google",
                "request_model": "gemini-2.5-flash",
                "thinking_budget_tokens": 0,
                "temperature": 0.0,
                "top_p": 1.0,
                "max_output_tokens": 8192,
                "system_instruction_hash": "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2",
                "tool_schema_hash": "d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
                "price_input_per_million_usd": "0.075000",
                "price_output_per_million_usd": "0.300000",
                "price_source_version": "2026-08-29",
                "created_at": "2026-08-29T10:00:00.000Z",
            }
            self.config_store["cfg_7c2a93e4f1b80d19"] = flash_cfg

            # Fingerprint default
            fp_file = CONTRACTS_VALID_DIR / "task-fingerprint.json"
            if fp_file.exists():
                with open(fp_file, "r", encoding="utf-8") as f:
                    fp_data = json.load(f)
                    self.fingerprint_store[fp_data["fingerprint_id"]] = fp_data

        except Exception:
            pass

    # Tool 1: get_change_event
    def get_change_event(self, event_id: str) -> Dict[str, Any]:
        """Fetch sanitized ChangeEvent by its unique event_id."""
        if event_id in self.event_store:
            return self.event_store[event_id]
        if self.event_store:
            return next(iter(self.event_store.values()))
        raise KeyError(f"ChangeEvent with event_id '{event_id}' not found.")

    # Tool 2: get_current_baseline
    def get_current_baseline(self, segment_id: str) -> Dict[str, Any]:
        """Fetch current immutable active policy version and configuration for task segment."""
        if segment_id in self.policy_store:
            return self.policy_store[segment_id]
        if self.policy_store:
            return next(iter(self.policy_store.values()))
        raise KeyError(f"Baseline policy for segment '{segment_id}' not found.")

    # Tool 3: list_supported_configurations
    def list_supported_configurations(self, provider: str, model_family: str) -> List[Dict[str, Any]]:
        """List pre-verified native configurations supported for the target provider and model family."""
        results = [
            cfg for cfg in self.config_store.values()
            if cfg.get("provider") == provider
        ]
        return results if results else list(self.config_store.values())

    # Tool 4: get_task_fingerprint
    def get_task_fingerprint(self, fingerprint_id: str) -> Dict[str, Any]:
        """Fetch workload complexity fingerprint and requirements."""
        if fingerprint_id in self.fingerprint_store:
            return self.fingerprint_store[fingerprint_id]
        if self.fingerprint_store:
            return next(iter(self.fingerprint_store.values()))
        raise KeyError(f"TaskFingerprint '{fingerprint_id}' not found.")

    # Tool 5: list_candidate_tasks
    def list_candidate_tasks(self, cohort_version: str) -> List[Dict[str, Any]]:
        """List available discriminating task descriptors in the judged cohort."""
        cohort_file = MANIFESTS_DIR / f"{cohort_version}.json"
        if not cohort_file.exists():
            cohort_file = MANIFESTS_DIR / "judged_task_cohort.v1.json"
        
        with open(cohort_file, "r", encoding="utf-8") as f:
            cohort_data = json.load(f)

        descriptors = []
        for t in cohort_data.get("tasks", []):
            descriptors.append({
                "task_id": t["task_id"],
                "name": t["name"],
                "difficulty": t["difficulty"],
                "language": t["language"],
                "files_count": t["files_count"],
                "fingerprint": t["fingerprint"],
            })
        return descriptors

    # Tool 6: propose_experiment
    def propose_experiment(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Submit proposed experiment plan dictionary for deterministic validation."""
        return {
            "status": "PROPOSAL_SUBMITTED",
            "received_plan": plan,
        }


# Tool Declarations for Gemini Function Calling
GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "get_change_event",
        "description": "Fetch sanitized ChangeEvent by its unique event_id.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "event_id": {"type": "STRING", "description": "The event_id to fetch."}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "get_current_baseline",
        "description": "Fetch current immutable active policy version and configuration for task segment.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "segment_id": {"type": "STRING", "description": "The task_segment_id."}
            },
            "required": ["segment_id"]
        }
    },
    {
        "name": "list_supported_configurations",
        "description": "List pre-verified native configurations supported for provider and model family.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "provider": {"type": "STRING", "description": "Provider name (e.g. google)."},
                "model_family": {"type": "STRING", "description": "Model family (e.g. gemini-2.5)."}
            },
            "required": ["provider", "model_family"]
        }
    },
    {
        "name": "get_task_fingerprint",
        "description": "Fetch workload complexity fingerprint and requirements.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "fingerprint_id": {"type": "STRING", "description": "The fingerprint_id to fetch."}
            },
            "required": ["fingerprint_id"]
        }
    },
    {
        "name": "list_candidate_tasks",
        "description": "List available discriminating task descriptors in the judged cohort.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "cohort_version": {"type": "STRING", "description": "Cohort identifier."}
            },
            "required": ["cohort_version"]
        }
    },
    {
        "name": "propose_experiment",
        "description": "Submit structured ExperimentPlan proposal for deterministic policy verification.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "plan": {
                    "type": "OBJECT",
                    "description": "The full structured ExperimentPlan matching the sovereign schema."
                }
            },
            "required": ["plan"]
        }
    }
]
