import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { firestoreRepo } from "@/lib/server/firestore-repo";
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

    // Look up live active policy from Firestore for the segment
    const mode = process.env.RUNTIME_MODE || "local_mock";
    const activePolicy = await firestoreRepo.getActivePolicy("swe_coding_python_interactive");
    const decisionExperimentId = mode === "local_mock"
      ? "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20"
      : process.env.ROUTING_DECISION_EXPERIMENT_ID;
    const decision = decisionExperimentId ? await firestoreRepo.getDecision(decisionExperimentId) : null;

    if (mode !== "local_mock") {
      if (!activePolicy || !decision || decision.truth_class !== "BENCHPRESS_MEASURED") {
        return NextResponse.json(
          {
            status: "unavailable",
            code: "NO_PUBLISHED_MEASURED_POLICY",
            message: "A verified published measured decision is required before serving recommendations.",
          },
          { status: 503, headers: { "Cache-Control": "no-store" } }
        );
      }
      return NextResponse.json({
        status: "success",
        timestamp: new Date().toISOString(),
        truth_class: "BENCHPRESS_MEASURED",
        active_policy: {
          policy_version: activePolicy.policy_version,
          configuration_id: activePolicy.configuration_id,
          is_active: activePolicy.is_active,
        },
        decision_receipt_id: decision.receipt_id,
        recommendation: {
          configuration_id: activePolicy.configuration_id,
          task_segment_id: activePolicy.task_segment_id,
          rationale: decision.why_decision,
        },
      }, { headers: { "Cache-Control": "no-store" } });
    }

    // Local-only illustrative router. It never participates in measured policy.
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
      active_policy: activePolicy
        ? {
            policy_version: activePolicy.policy_version,
            configuration_id: activePolicy.configuration_id,
            is_active: activePolicy.is_active,
          }
        : null,
      decision_receipt_id: decision?.receipt_id || null,
      recommendation: {
        ...recommendation,
        truth_class: "DEMO_FIXTURE",
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
