"use client";

import React from "react";
import { FsmState } from "@/lib/types";

interface FsmStateBadgeProps {
  state: FsmState | string;
  className?: string;
}

export function FsmStateBadge({ state, className = "" }: FsmStateBadgeProps) {
  let style = "border-white/10 bg-white/5 text-zinc-300";

  switch (state) {
    case FsmState.INITIALIZING:
    case "INIT_ENVIRONMENT":
      style = "border-cyan-500/40 bg-cyan-500/15 text-cyan-300";
      break;
    case FsmState.REASONING_PLANNER:
    case "PROMPT_PLANNER":
      style = "border-purple-500/40 bg-purple-500/15 text-purple-300";
      break;
    case FsmState.AST_VALIDATION:
    case "VALIDATE_AST":
    case FsmState.SUPERVISOR_AST_HEAL:
      style = "border-amber-500/40 bg-amber-500/15 text-amber-300 animate-pulse";
      break;
    case FsmState.SANDBOX_EXECUTION:
    case "EXECUTE_SANDBOX":
      style = "border-blue-500/40 bg-blue-500/15 text-blue-300";
      break;
    case FsmState.PREDICTIVE_SENTINEL_EVAL:
    case "FINOPS_SENTINEL":
      style = "border-emerald-500/40 bg-emerald-500/15 text-emerald-300";
      break;
    case FsmState.SAGA_COMPENSATING_ROLLBACK:
    case FsmState.FATAL_HALT:
      style = "border-rose-500/40 bg-rose-500/15 text-rose-300";
      break;
    case FsmState.COMPLETE:
    case "HALT_TERMINAL":
      style = "border-emerald-500/40 bg-emerald-500/20 text-emerald-300 font-bold";
      break;
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${style} ${className}`}
    >
      {state}
    </span>
  );
}
