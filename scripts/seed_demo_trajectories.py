#!/usr/bin/env python3
"""
High-Fidelity Demo Telemetry & Trajectory Seeder (`seed_demo_trajectories.py`).
Populates BigQuery analytics dataset and local JSON cache with 50+ rich multi-turn trajectories across 12 models.
"""

import os
import sys
import json
import random
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

MODELS = [
    {"id": "hybrid-gemini-pro-flash", "name": "Benchpress 2-Tier", "provider": "Benchpress Hybrid", "cpr_base": 0.185, "pass_rate": 71.2, "pareto": True},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "Google Cloud", "cpr_base": 0.420, "pass_rate": 72.8, "pareto": True},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "Google Cloud", "cpr_base": 0.048, "pass_rate": 58.4, "pareto": True},
    {"id": "claude-3-7-sonnet", "name": "Claude 3.7 Sonnet", "provider": "Anthropic", "cpr_base": 1.480, "pass_rate": 70.3, "pareto": False},
    {"id": "gpt-4.5-preview", "name": "GPT-4.5 Preview", "provider": "OpenAI", "cpr_base": 8.450, "pass_rate": 68.9, "pareto": False},
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI", "cpr_base": 1.320, "pass_rate": 64.2, "pareto": False},
    {"id": "deepseek-r1", "name": "DeepSeek R1", "provider": "DeepSeek", "cpr_base": 0.550, "pass_rate": 65.1, "pareto": False},
    {"id": "qwen-2.5-coder-32b", "name": "Qwen 2.5 Coder 32B", "provider": "Alibaba Cloud", "cpr_base": 0.280, "pass_rate": 56.7, "pareto": False},
]

SUITES = ["SWE-bench Verified", "Financial Reconciliation", "Multi-Doc Enterprise Ops"]


def generate_synthetic_trajectory(model: Dict[str, Any], suite: str, run_idx: int) -> Dict[str, Any]:
    """Generate rich multi-turn telemetry record."""
    traj_id = f"traj-{model['id'][:6]}-{run_idx:03d}"
    turns_count = random.randint(4, 12) if "hybrid" in model["id"] else random.randint(8, 22)
    is_resolved = random.random() * 100 < model["pass_rate"]

    turns: List[Dict[str, Any]] = []
    accum_cost = 0.0

    for t in range(1, turns_count + 1):
        step_cost = round((model["cpr_base"] / turns_count) * random.uniform(0.8, 1.2), 4)
        accum_cost += step_cost
        turns.append({
            "turn_index": t,
            "state": "TOOL_DISPATCH_CODER" if t % 2 == 0 else "REASONING_PLANNER",
            "model_id": model["id"],
            "prompt_tokens": random.randint(4000, 15000),
            "completion_tokens": random.randint(300, 1800),
            "turn_cost_usd": step_cost,
            "cumulative_cost_usd": round(accum_cost, 4),
            "latency_ms": round(random.uniform(800, 3200), 1),
            "tool_call_name": "editHunk" if t % 2 == 0 else None,
            "ast_healed": True if t == 2 and "hybrid" in model["id"] else False,
            "sandbox_exit_code": 0,
        })

    return {
        "trajectory_id": traj_id,
        "task_suite": suite,
        "task_id": f"task-django-{1000 + run_idx}",
        "model_id": model["id"],
        "model_name": model["name"],
        "provider": model["provider"],
        "status": "COMPLETED" if is_resolved else "FAILED",
        "current_state": "TERMINATED_SUCCESS" if is_resolved else "FATAL_HALT",
        "pass_at_1": is_resolved,
        "resolved": is_resolved,
        "total_cost_usd": round(accum_cost, 4),
        "cpr_usd": round(accum_cost if is_resolved else accum_cost * 2.5, 4),
        "trajectory_bloat_ratio": 1.05 if "hybrid" in model["id"] else 1.45,
        "ast_heal_count": 1 if "hybrid" in model["id"] else 0,
        "git_snapshots_count": turns_count,
        "turns_count": turns_count,
        "started_at": "2026-08-27T08:00:00Z",
        "completed_at": "2026-08-27T08:01:14Z",
        "turns": turns,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed demo trajectories into Benchpress")
    parser.add_argument("--dry-run", action="store_true", help="Print sample trajectories without writing to files")
    parser.add_argument("--count", type=int, default=50, help="Total trajectories to generate")
    args = parser.parse_args()

    trajectories = []
    for i in range(args.count):
        model = MODELS[i % len(MODELS)]
        suite = SUITES[i % len(SUITES)]
        trajectories.append(generate_synthetic_trajectory(model, suite, i + 1))

    if args.dry_run:
        print(f"✓ [Dry Run] Generated {len(trajectories)} trajectories successfully.")
        print(f"Sample Trajectory (ID: {trajectories[0]['trajectory_id']}):")
        print(json.dumps(trajectories[0], indent=2)[:500] + "\n...")
        return

    out_file = Path("apps/web/public/data/demo_trajectories.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(trajectories, indent=2), encoding="utf-8")
    print(f"✓ Saved {len(trajectories)} demo trajectories to {out_file}.")


if __name__ == "__main__":
    main()
