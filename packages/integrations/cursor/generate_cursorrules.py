#!/usr/bin/env python3
"""
Automated .cursorrules Generator for Benchpress Model Routing & FinOps Arbitrage.
"""

import sys
import os
from pathlib import Path


CURSORRULES_TEMPLATE = """# Benchpress Autonomous Model Routing Rules for Cursor AI
# Generated automatically by Benchpress Developer CLI

[routing_policy]
enable_hybrid_routing = true
default_planner_model = "gemini-2.5-pro"
default_coder_model = "gemini-2.5-flash"
benchmark_verification_target = "SWE-bench Verified"
budget_cap_usd_per_task = 0.50

[prompt_choreography]
# 1. Architectural & Multi-file Planning -> Gemini 2.5 Pro (Deep reasoning, L1 symbol cache)
planner_trigger_patterns = ["refactor", "architect", "multi-file", "bug fix in core/"]

# 2. Syntax Repair, Hunk Replacement & AST Formatting -> Gemini 2.5 Flash (Sub-8s execution)
coder_trigger_patterns = ["edit hunk", "replace", "fix typing", "add test", "quick edit"]

[error_healing]
auto_ast_wrapper_healing = true
git_saga_compensating_rollback = true
"""


def generate_cursorrules(target_dir: str = "."):
    target_path = Path(target_dir) / ".cursorrules"
    target_path.write_text(CURSORRULES_TEMPLATE.strip() + "\n", encoding="utf-8")
    print(f"✓ Generated {target_path} successfully (Benchpress 2-Tier Routing active).")


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_cursorrules(out_dir)
