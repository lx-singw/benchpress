import { NextRequest, NextResponse } from "next/server";
import { BenchmarkLeaderboardRow } from "@/lib/types";

const BENCHMARK_CATALOG: BenchmarkLeaderboardRow[] = [
  {
    modelId: "gemini-2.5-pro",
    modelName: "Gemini 2.5 Pro",
    provider: "Google",
    taskSuite: "SWE-bench Verified",
    passRatePct: 63.8,
    cprUsd: 0.42,
    meanTurns: 11.2,
    meanLatencySeconds: 18.4,
    astHealingCount: 14,
    tokenVelocityKps: 4.8,
    paretoFrontier: true,
  },
  {
    modelId: "claude-3-7-sonnet",
    modelName: "Claude 3.7 Sonnet (Thinking)",
    provider: "Anthropic",
    taskSuite: "SWE-bench Verified",
    passRatePct: 70.4,
    cprUsd: 1.15,
    meanTurns: 14.6,
    meanLatencySeconds: 32.1,
    astHealingCount: 8,
    tokenVelocityKps: 3.2,
    paretoFrontier: true,
  },
  {
    modelId: "gemini-2.5-flash",
    modelName: "Gemini 2.5 Flash",
    provider: "Google",
    taskSuite: "SWE-bench Verified",
    passRatePct: 41.5,
    cprUsd: 0.12,
    meanTurns: 8.5,
    meanLatencySeconds: 6.8,
    astHealingCount: 19,
    tokenVelocityKps: 7.2,
    paretoFrontier: true,
  },
  {
    modelId: "gpt-4o",
    modelName: "GPT-4o",
    provider: "OpenAI",
    taskSuite: "SWE-bench Verified",
    passRatePct: 48.2,
    cprUsd: 0.88,
    meanTurns: 16.1,
    meanLatencySeconds: 22.0,
    astHealingCount: 29,
    tokenVelocityKps: 3.9,
    paretoFrontier: false,
  },
  {
    modelId: "o3-mini",
    modelName: "o3-mini (High)",
    provider: "OpenAI",
    taskSuite: "SWE-bench Verified",
    passRatePct: 58.7,
    cprUsd: 0.76,
    meanTurns: 12.8,
    meanLatencySeconds: 28.5,
    astHealingCount: 11,
    tokenVelocityKps: 4.1,
    paretoFrontier: false,
  },
];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const suite = searchParams.get("suite");

    let results = BENCHMARK_CATALOG;
    if (suite) {
      results = results.filter((b) => b.taskSuite.toLowerCase() === suite.toLowerCase());
    }

    return NextResponse.json({
      status: "success",
      benchmarks: results,
      totalCount: results.length,
      generatedAt: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: "Failed to fetch benchmarks", message: error.message },
      { status: 500 }
    );
  }
}
