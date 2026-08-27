"""
Client-Side Fine-Tuning Dataset Exporter for benchpress-python.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path


def export_trajectories_to_sft_jsonl(
    trajectories: List[Dict[str, Any]],
    output_filepath: str = "gemini_sft_dataset.jsonl"
) -> int:
    """Export a list of passing trajectories into Vertex AI Gemini SFT JSONL format.

    Returns: count of exported records.
    """
    exported_count = 0
    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for traj in trajectories:
            if not traj.get("pass_at_1", False) and not traj.get("resolved", False):
                continue

            turns = traj.get("turns", [])
            if not turns:
                continue

            contents = [
                {
                    "role": "user",
                    "parts": [{"text": f"Resolve {traj.get('task_id')} in {traj.get('task_suite')}."}]
                }
            ]

            for turn in turns:
                tool = turn.get("tool_call_name")
                if tool:
                    contents.append({
                        "role": "model",
                        "parts": [{"functionCall": {"name": tool, "args": turn.get("tool_call_payload", {})}}]
                    })
                    contents.append({
                        "role": "user",
                        "parts": [{"functionResponse": {"name": tool, "response": {"output": turn.get("sandbox_stdout", "Success")}}}]
                    })
                else:
                    contents.append({
                        "role": "model",
                        "parts": [{"text": turn.get("action", "Step completed")}]
                    })

            record = {
                "system_instruction": {
                    "parts": [{"text": "You are Benchpress Autonomous Agent."}]
                },
                "contents": contents,
            }

            f.write(json.dumps(record) + "\n")
            exported_count += 1

    return exported_count
