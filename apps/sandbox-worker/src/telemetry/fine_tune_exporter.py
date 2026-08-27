"""
Continuous Model Fine-Tuning Dataset Generator (`FineTuneExporter`).
Converts verified golden agent execution traces into Vertex AI Gemini Supervised Fine-Tuning (SFT)
and Direct Preference Optimization (DPO) JSONL datasets.
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger("benchpress.telemetry.fine_tune_exporter")


@dataclass
class GeminiSftTurn:
    role: str  # "user" or "model"
    parts: List[Dict[str, Any]]


@dataclass
class GeminiSftRecord:
    system_instruction: Dict[str, Any]
    contents: List[GeminiSftTurn]


@dataclass
class DpoPreferencePair:
    prompt: str
    chosen: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    task_id: str
    cost_savings_pct: float
    metadata: Dict[str, Any]


class FineTuneExporter:
    """Exports verified trajectory runs into Gemini SFT and DPO alignment datasets."""

    SYSTEM_PROMPT = (
        "You are Benchpress Autonomous Agent, an elite autonomous SWE engineer operating inside "
        "a gVisor sandboxed Linux environment with deterministic AST tool-calling and Git Sagas."
    )

    @classmethod
    def export_to_gemini_sft(cls, trajectory: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single verified passing trajectory into Gemini SFT multi-turn format."""
        if not trajectory.get("pass_at_1", False) and not trajectory.get("resolved", False):
            logger.info(f"[FineTuneExporter] Skipping non-passing trajectory {trajectory.get('trajectory_id')}")
            return None

        turns_data = trajectory.get("turns", [])
        if not turns_data:
            return None

        contents: List[Dict[str, Any]] = []

        # Turn 1 User prompt
        task_id = trajectory.get("task_id", "unknown_task")
        task_suite = trajectory.get("task_suite", "SWE_BENCH_VERIFIED")
        initial_prompt = f"Resolve issue {task_id} in {task_suite}. Verify with pytest."

        contents.append({
            "role": "user",
            "parts": [{"text": initial_prompt}],
        })

        # Multi-turn model interactions
        for turn in turns_data:
            model_parts = []
            if turn.get("tool_call_name"):
                model_parts.append({
                    "functionCall": {
                        "name": turn.get("tool_call_name"),
                        "args": turn.get("tool_call_payload", {}),
                    }
                })
            else:
                model_parts.append({"text": turn.get("action", f"Completed turn in state {turn.get('state')}")})

            contents.append({
                "role": "model",
                "parts": model_parts,
            })

            # Synthetic tool response turn if a tool was called
            if turn.get("tool_call_name"):
                tool_output = turn.get("sandbox_stdout") or f"Exit code {turn.get('sandbox_exit_code', 0)}"
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": turn.get("tool_call_name"),
                            "response": {"output": tool_output},
                        }
                    }],
                })

        return {
            "system_instruction": {
                "parts": [{"text": cls.SYSTEM_PROMPT}]
            },
            "contents": contents,
        }

    @classmethod
    def export_to_dpo_pair(
        cls,
        winning_trajectory: Dict[str, Any],
        failed_trajectory: Dict[str, Any]
    ) -> DpoPreferencePair:
        """Create contrastive DPO pair: winning 2-tier trace (chosen) vs failed monolithic trace (rejected)."""
        prompt = f"Resolve {winning_trajectory.get('task_id', 'task')} in {winning_trajectory.get('task_suite')}."

        # Chosen trace
        chosen_steps = [
            {
                "turn": t.get("turn_index", i + 1),
                "state": t.get("state"),
                "tool": t.get("tool_call_name"),
                "cost_usd": t.get("turn_cost_usd", 0.0),
            }
            for i, t in enumerate(winning_trajectory.get("turns", []))
        ]

        # Rejected trace
        rejected_steps = [
            {
                "turn": t.get("turn_index", i + 1),
                "state": t.get("state"),
                "tool": t.get("tool_call_name"),
                "cost_usd": t.get("turn_cost_usd", 0.0),
            }
            for i, t in enumerate(failed_trajectory.get("turns", []))
        ]

        win_cost = winning_trajectory.get("total_cost_usd", 0.185)
        fail_cost = max(failed_trajectory.get("total_cost_usd", 1.48), 0.01)
        savings_pct = max(0.0, Math_round((fail_cost - win_cost) / fail_cost * 100))

        return DpoPreferencePair(
            prompt=prompt,
            chosen=chosen_steps,
            rejected=rejected_steps,
            task_id=winning_trajectory.get("task_id", "unknown"),
            cost_savings_pct=savings_pct,
            metadata={
                "winning_model": winning_trajectory.get("model_id"),
                "failed_model": failed_trajectory.get("model_id"),
                "winning_turns": len(chosen_steps),
                "failed_turns": len(rejected_steps),
            },
        )


def Math_round(val: float) -> float:
    return round(val * 10) / 10
