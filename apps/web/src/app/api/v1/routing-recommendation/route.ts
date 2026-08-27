import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { ParetoRouter } from "@/lib/pareto-router";

// Strict Zod validation schema for incoming model routing queries
const RoutingRecommendationSchema = z.object({
  task_type: z.enum(["code_bug_fix", "architectural_refactor", "financial_extraction", "quick_edit"]),
  codebase_language: z.enum(["python", "typescript", "rust", "go", "java"]),
  current_model: z.string().default("claude-3-7-sonnet"),
  max_budget_per_task_usd: z.number().positive().optional().default(0.50),
  pareto_weights: z
    .object({
      accuracy: z.number().min(0).max(1).default(0.5),
      cost: z.number().min(0).max(1).default(0.5),
      latency: z.number().min(0).max(1).default(0.2),
    })
    .optional(),
  estimated_prompt_tokens: z.number().optional().default(15000),
  estimated_completion_tokens: z.number().optional().default(2500),
});

export async function POST(request: NextRequest) {
  const startTime = performance.now();

  try {
    const rawBody = await request.json();
    const validated = RoutingRecommendationSchema.parse(rawBody);

    // Compute optimal 2-tier choreography & cost arbitrage
    const recommendation = ParetoRouter.computeOptimalRoute(
      validated.task_type,
      validated.codebase_language,
      validated.current_model,
      validated.max_budget_per_task_usd,
      validated.estimated_prompt_tokens,
      validated.estimated_completion_tokens
    );

    const executionLatencyMs = Math.round((performance.now() - startTime) * 100) / 100;

    return NextResponse.json({
      status: "success",
      latency_ms: executionLatencyMs,
      timestamp: new Date().toISOString(),
      recommendation: {
        ...recommendation,
        query: {
          task_type: validated.task_type,
          codebase_language: validated.codebase_language,
          current_model: validated.current_model,
        },
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          status: "error",
          code: "VALIDATION_ERROR",
          errors: error.errors,
        },
        { status: 400 }
      );
    }

    return NextResponse.json(
      {
        status: "error",
        code: "INTERNAL_ROUTING_ERROR",
        message: error instanceof Error ? error.message : "Failed to compute routing recommendation",
      },
      { status: 500 }
    );
  }
}
