#!/usr/bin/env python3
"""
Automated .windsurfrules Generator for Benchpress Model Routing & FinOps Arbitrage.
"""

import sys
import os
from pathlib import Path


WINDSURFRULES_TEMPLATE = """# Benchpress Autonomous Model Routing Rules for Windsurf IDE Cascade
# Generated automatically by Benchpress Developer CLI

# 1. Cascade Reasoning & Execution Directives
cascade_model_routing:
  planner:
    model: "gemini-2.5-pro"
    purpose: "Formulate step-by-step diff plans and maintain L1 AST scratchpad"
  coder:
    model: "gemini-2.5-flash"
    purpose: "Fast execution of localized diff hunks and pytest commands"

# 2. FinOps Guardrails
finops:
  max_cpr_ceiling_usd: 0.50
  markov_velocity_sentinel: true
  auto_downgrade_on_token_burst: true

# 3. Trajectory Telemetry
telemetry:
  stream_to_benchpress: true
  endpoint: "http://localhost:3000/api/v1/proxy/chat/completions"
"""


def generate_windsurfrules(target_dir: str = "."):
    target_path = Path(target_dir) / ".windsurfrules"
    target_path.write_text(WINDSURFRULES_TEMPLATE.strip() + "\n", encoding="utf-8")
    print(f"✓ Generated {target_path} successfully (Benchpress Windsurf Cascade active).")


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_windsurfrules(out_dir)
