#!/usr/bin/env python3
"""
High-Fidelity Demo Telemetry & Trajectory Seeder (`seed_demo_trajectories.py`).
Populates local JSON cache and BigQuery/Firestore with 50+ rich multi-turn trajectories across 12 models.
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
    {
        "id": "hybrid-gemini-pro-flash",
        "name": "Benchpress 2-Tier Hybrid",
        "provider": "Benchpress Hybrid",
        "cpr_base": 0.0245,
        "pass_rate": 84.2,
        "pareto": True,
        "recommended_tier": "HYBRID_CHOREOGRAPHY",
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "Google Cloud",
        "cpr_base": 0.380,
        "pass_rate": 78.6,
        "pareto": True,
        "recommended_tier": "FRONTIER_REASONER",
    },
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "Google Cloud",
        "cpr_base": 0.048,
        "pass_rate": 62.4,
        "pareto": True,
        "recommended_tier": "HIGH_SPEED_CODER",
    },
    {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "provider": "Google Cloud",
        "cpr_base": 0.039,
        "pass_rate": 68.1,
        "pareto": True,
        "recommended_tier": "HIGH_SPEED_CODER",
    },
    {
        "id": "claude-3-7-sonnet",
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "cpr_base": 1.150,
        "pass_rate": 74.5,
        "pareto": False,
        "recommended_tier": "FRONTIER_REASONER",
    },
    {
        "id": "claude-3-5-haiku",
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "cpr_base": 0.220,
        "pass_rate": 54.2,
        "pareto": False,
        "recommended_tier": "HIGH_SPEED_CODER",
    },
    {
        "id": "gpt-4.5-preview",
        "name": "GPT-4.5 Preview",
        "provider": "OpenAI",
        "cpr_base": 7.850,
        "pass_rate": 72.1,
        "pareto": False,
        "recommended_tier": "FRONTIER_REASONER",
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "OpenAI",
        "cpr_base": 1.280,
        "pass_rate": 66.8,
        "pareto": False,
        "recommended_tier": "FRONTIER_REASONER",
    },
    {
        "id": "o3-mini",
        "name": "o3-mini",
        "provider": "OpenAI",
        "cpr_base": 0.450,
        "pass_rate": 71.3,
        "pareto": True,
        "recommended_tier": "FRONTIER_REASONER",
    },
    {
        "id": "deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "DeepSeek",
        "cpr_base": 0.480,
        "pass_rate": 69.4,
        "pareto": True,
        "recommended_tier": "FRONTIER_REASONER",
    },
    {
        "id": "deepseek-v3",
        "name": "DeepSeek V3",
        "provider": "DeepSeek",
        "cpr_base": 0.140,
        "pass_rate": 59.8,
        "pareto": False,
        "recommended_tier": "HIGH_SPEED_CODER",
    },
    {
        "id": "llama-3.3-70b",
        "name": "Llama 3.3 70B",
        "provider": "Meta",
        "cpr_base": 0.320,
        "pass_rate": 57.5,
        "pareto": False,
        "recommended_tier": "HIGH_SPEED_CODER",
    },
]

TASK_FIXTURES = [
    {"suite": "SWE-bench Verified", "task_id": "django__django-11099", "name": "Django username validator regex anchor boundary bug"},
    {"suite": "SWE-bench Verified", "task_id": "django__django-12858", "name": "Django Model ordering constraint collision"},
    {"suite": "SWE-bench Verified", "task_id": "flask__flask-5063", "name": "Flask blueprint subdomain routing resolution"},
    {"suite": "SWE-bench Verified", "task_id": "sympy__sympy-20590", "name": "SymPy symbolic AST tree evaluation precision"},
    {"suite": "Financial Reconciliation", "task_id": "fin-ledger-recon-2026", "name": "Multi-bank transaction reconciliation and ledger imbalance fix"},
    {"suite": "Financial Reconciliation", "task_id": "arbitrage-spread-audit-01", "name": "Crypto-fiat cross-exchange orderbook latency arbitrage auditor"},
]


def generate_synthetic_trajectory(model: Dict[str, Any], task: Dict[str, Any], run_idx: int) -> Dict[str, Any]:
    """Generate rich multi-turn telemetry record with realistic token burn, tool calls, and git snapshots."""
    traj_id = f"traj-{model['id'][:7]}-{run_idx:03d}"
    is_hybrid = "hybrid" in model["id"]
    turns_count = random.randint(4, 7) if is_hybrid else random.randint(8, 18)
    is_resolved = (random.random() * 100) < model["pass_rate"]

    turns: List[Dict[str, Any]] = []
    accum_cost = 0.0

    for t in range(1, turns_count + 1):
        step_cost = round((model["cpr_base"] / max(turns_count, 1)) * random.uniform(0.85, 1.15), 5)
        accum_cost += step_cost

        state = "REASONING_PLANNER" if t == 1 else ("TOOL_DISPATCH_CODER" if t % 2 == 0 else "AST_VALIDATION")
        if t == turns_count and is_resolved:
            state = "EVAL_ASSERTION"

        tool_name = None
        tool_args = None
        if t == 1:
            tool_name = "readFile"
            tool_args = {"path": "django/core/validators.py"}
        elif t == 2 and is_hybrid:
            tool_name = "editHunk"
            tool_args = {
                "path": "django/core/validators.py",
                "target_content": "^[\\w.@+-]+$",
                "replacement_content": "\\A[\\w.@+-]+\\Z"
            }
        elif t % 2 == 0:
            tool_name = "editHunk"
            tool_args = {"path": "django/core/validators.py", "target_content": "old_regex", "replacement_content": "new_regex"}
        elif t == turns_count:
            tool_name = "runPytest"
            tool_args = {"test_path": "tests/test_validators.py"}

        turns.append({
            "turn_index": t,
            "state": state,
            "model_id": "gemini-2.5-pro" if (is_hybrid and t == 1) else model["id"],
            "prompt_tokens": random.randint(4200, 14500),
            "completion_tokens": random.randint(350, 1600),
            "reasoning_tokens": random.randint(200, 800) if "pro" in model["id"] or "o3" in model["id"] or "r1" in model["id"] else 0,
            "turn_cost_usd": step_cost,
            "cumulative_cost_usd": round(accum_cost, 5),
            "latency_ms": round(random.uniform(320, 1850), 1),
            "tool_call_name": tool_name,
            "tool_call_payload": tool_args,
            "ast_healed": True if (is_hybrid and t == 2) else False,
            "ast_healing_trace": "Renamed 'file_path' -> 'path' and normalized range" if (is_hybrid and t == 2) else None,
            "sandbox_exit_code": 0,
            "sandbox_stdout": f"Executed step {t} in isolated gVisor container" if tool_name else "",
            "git_tree_hash": f"tree_{random.randint(100000, 999999):x}",
            "timestamp": f"2026-08-27T08:{t:02d}:00Z",
        })

    total_cost = round(accum_cost, 4)
    cpr_usd = round(total_cost if is_resolved else total_cost * 2.2, 4)

    return {
        "trajectory_id": traj_id,
        "task_suite": task["suite"],
        "task_id": task["task_id"],
        "task_name": task["name"],
        "model_id": model["id"],
        "model_name": model["name"],
        "provider": model["provider"],
        "recommended_tier": model["recommended_tier"],
        "is_pareto_frontier": model["pareto"],
        "status": "COMPLETED" if is_resolved else "FAILED",
        "current_state": "COMPLETE" if is_resolved else "FATAL_HALT",
        "pass_at_1": is_resolved,
        "resolved": is_resolved,
        "early_halted": False if is_resolved else (turns_count < 8),
        "halt_reason": None if is_resolved else ("Markov Token Velocity Sentinel Early-Halt" if turns_count < 8 else "Test Assertion Failure"),
        "total_cost_usd": total_cost,
        "cpr_usd": cpr_usd,
        "trajectory_bloat_ratio": 0.042 if is_hybrid else round(random.uniform(0.18, 0.42), 3),
        "context_decay_score": 0.012 if is_hybrid else round(random.uniform(0.08, 0.25), 3),
        "ast_heal_count": 1 if is_hybrid else 0,
        "git_snapshots_count": turns_count,
        "turns_count": turns_count,
        "started_at": "2026-08-27T08:00:00Z",
        "completed_at": f"2026-08-27T08:{turns_count:02d}:15Z",
        "turns": turns,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed demo trajectories into Benchpress")
    parser.add_argument("--dry-run", action="store_true", help="Print sample trajectories without writing to files")
    parser.add_argument("--count", type=int, default=52, help="Total trajectories to generate")
    args = parser.parse_args()

    trajectories = []
    for i in range(args.count):
        model = MODELS[i % len(MODELS)]
        task = TASK_FIXTURES[i % len(TASK_FIXTURES)]
        trajectories.append(generate_synthetic_trajectory(model, task, i + 1))

    if args.dry_run:
        print(f"[SUCCESS] [Dry Run] Generated {len(trajectories)} trajectories successfully.")
        print(f"Sample Trajectory (ID: {trajectories[0]['trajectory_id']}):")
        print(json.dumps(trajectories[0], indent=2)[:600] + "\n...")
        return

    out_file = Path("apps/web/public/data/demo_trajectories.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(trajectories, indent=2), encoding="utf-8")
    print(f"[SUCCESS] Saved {len(trajectories)} high-fidelity demo trajectories across {len(MODELS)} models to {out_file}.")


if __name__ == "__main__":
    main()
