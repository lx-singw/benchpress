import { NextRequest, NextResponse } from "next/server";
import { FsmState } from "@/lib/types";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // Mock trajectory details lookup (returns telemetry, turns, and FSM lifecycle status)
  const trajectoryData = {
    trajectory_id: id,
    task_suite: "SWE_BENCH_VERIFIED",
    task_id: "django__django-11099",
    model_id: "hybrid-gemini-pro-flash",
    status: "COMPLETED",
    current_state: FsmState.COMPLETE,
    pass_at_1: true,
    resolved: true,
    total_cost_usd: 0.185,
    cpr_usd: 0.185,
    trajectory_bloat_ratio: 1.12,
    ast_heal_count: 1,
    git_snapshots_count: 4,
    turns_count: 5,
    started_at: new Date(Date.now() - 45000).toISOString(),
    completed_at: new Date().toISOString(),
    turns: [
      {
        turn_index: 1,
        state: FsmState.INITIALIZING,
        model_id: "gemini-2.5-pro",
        prompt_tokens: 1200,
        completion_tokens: 180,
        turn_cost_usd: 0.005,
        cumulative_cost_usd: 0.005,
        latency_ms: 340,
        tool_call_name: "readFile",
        ast_healed: false,
        sandbox_exit_code: 0,
      },
      {
        turn_index: 2,
        state: FsmState.REASONING_PLANNER,
        model_id: "gemini-2.5-pro",
        prompt_tokens: 4500,
        completion_tokens: 650,
        turn_cost_usd: 0.038,
        cumulative_cost_usd: 0.043,
        latency_ms: 1820,
        ast_healed: false,
        sandbox_exit_code: 0,
      },
      {
        turn_index: 3,
        state: FsmState.SUPERVISOR_AST_HEAL,
        model_id: "gemini-2.5-flash",
        prompt_tokens: 6200,
        completion_tokens: 420,
        turn_cost_usd: 0.012,
        cumulative_cost_usd: 0.055,
        latency_ms: 650,
        tool_call_name: "editHunk",
        ast_healed: true,
        ast_healing_trace: "Auto-repaired file_path -> path parameter schema",
        sandbox_exit_code: 0,
      },
      {
        turn_index: 4,
        state: FsmState.SANDBOX_EXECUTION,
        model_id: "gemini-2.5-flash",
        prompt_tokens: 7800,
        completion_tokens: 890,
        turn_cost_usd: 0.018,
        cumulative_cost_usd: 0.073,
        latency_ms: 2400,
        tool_call_name: "runPytest",
        ast_healed: false,
        sandbox_exit_code: 0,
      },
      {
        turn_index: 5,
        state: FsmState.COMPLETE,
        model_id: "gemini-2.5-flash",
        prompt_tokens: 8200,
        completion_tokens: 310,
        turn_cost_usd: 0.010,
        cumulative_cost_usd: 0.185,
        latency_ms: 480,
        ast_healed: false,
        sandbox_exit_code: 0,
      },
    ],
  };

  return NextResponse.json({
    status: "success",
    data: trajectoryData,
  });
}
