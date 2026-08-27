import { NextRequest, NextResponse } from "next/server";
import { ParetoRouter, RoutingTaskRequest } from "@/lib/pareto-router";

export const runtime = "nodejs";

/**
 * POST /api/v1/routing-recommendation
 * Returns real-time Pareto-optimal 2-tier model choreography recommendation with cost-saving analytics.
 */
export async function POST(req: NextRequest) {
  try {
    const body: RoutingTaskRequest = await req.json().catch(() => ({ task_type: "code_bug_fix" }));

    const decision = ParetoRouter.calculateRoute(body);

    return NextResponse.json({
      success: true,
      data: decision,
      evaluated_at: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message || "Failed to calculate routing recommendation" },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  // Support GET with query parameter defaults
  const searchParams = req.nextUrl.searchParams;
  const taskType = (searchParams.get("task_type") as any) || "code_bug_fix";
  const costWeight = searchParams.get("cost_weight") ? parseFloat(searchParams.get("cost_weight")!) : 0.5;
  const maxLatency = searchParams.get("max_latency") ? parseFloat(searchParams.get("max_latency")!) : 30;

  const decision = ParetoRouter.calculateRoute({
    task_type: taskType,
    cost_weight: costWeight,
    max_latency_sec: maxLatency,
  });

  return NextResponse.json({
    success: true,
    data: decision,
    evaluated_at: new Date().toISOString(),
  });
}
