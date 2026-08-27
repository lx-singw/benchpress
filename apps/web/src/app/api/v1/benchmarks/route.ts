import { NextRequest, NextResponse } from "next/server";
import { BenchmarkLeaderboardRow } from "@/lib/types";

const BENCHMARK_CATALOG: BenchmarkLeaderboardRow[] = [
  {
    modelId: "hybrid-gemini-pro-flash",
    modelName: "Benchpress 2-Tier (Gemini 2.5 Pro + Flash)",
    provider: "Benchpress Hybrid",
    taskSuite: "SWE-bench Verified",
    passRatePct: 71.2,
    cprUsd: 0.185,
    meanTurns: 9.4,
    meanLatencySeconds: 14.6,
    astHealingCount: 28,
    tokenVelocityKps: 5.4,
    paretoFrontier: true,
  },
  {
    modelId: "gemini-2.5-pro",
    modelName: "Gemini 2.5 Pro",
    provider: "Google",
    taskSuite: "SWE-bench Verified",
    passRatePct: 73.8,
    cprUsd: 0.58,
    meanTurns: 11.2,
    meanLatencySeconds: 22.4,
    astHealingCount: 14,
    tokenVelocityKps: 4.8,
    paretoFrontier: true,
  },
  {
    modelId: "gemini-2.5-flash",
    modelName: "Gemini 2.5 Flash",
    provider: "Google",
    taskSuite: "SWE-bench Verified",
    passRatePct: 58.4,
    cprUsd: 0.048,
    meanTurns: 8.5,
    meanLatencySeconds: 8.2,
    astHealingCount: 19,
    tokenVelocityKps: 8.2,
    paretoFrontier: true,
  },
  {
    modelId: "claude-3-7-sonnet",
    modelName: "Claude 3.7 Sonnet (Thinking)",
    provider: "Anthropic",
    taskSuite: "SWE-bench Verified",
    passRatePct: 74.2,
    cprUsd: 1.48,
    meanTurns: 14.6,
    meanLatencySeconds: 32.8,
    astHealingCount: 8,
    tokenVelocityKps: 3.2,
    paretoFrontier: false,
  },
  {
    modelId: "claude-3-5-haiku",
    modelName: "Claude 3.5 Haiku",
    provider: "Anthropic",
    taskSuite: "SWE-bench Verified",
    passRatePct: 52.1,
    cprUsd: 0.38,
    meanTurns: 12.0,
    meanLatencySeconds: 11.5,
    astHealingCount: 11,
    tokenVelocityKps: 6.5,
    paretoFrontier: false,
  },
  {
    modelId: "o3-mini",
    modelName: "o3-mini (High Reasoning)",
    provider: "OpenAI",
    taskSuite: "SWE-bench Verified",
    passRatePct: 69.5,
    cprUsd: 0.89,
    meanTurns: 16.2,
    meanLatencySeconds: 28.5,
    astHealingCount: 12,
    tokenVelocityKps: 3.8,
    paretoFrontier: false,
  },
  {
    modelId: "gpt-4o",
    modelName: "GPT-4o (Omni)",
    provider: "OpenAI",
    taskSuite: "SWE-bench Verified",
    passRatePct: 64.8,
    cprUsd: 1.32,
    meanTurns: 15.4,
    meanLatencySeconds: 21.0,
    astHealingCount: 9,
    tokenVelocityKps: 4.1,
    paretoFrontier: false,
  },
  {
    modelId: "gpt-4.5-preview",
    modelName: "GPT-4.5 Preview",
    provider: "OpenAI",
    taskSuite: "SWE-bench Verified",
    passRatePct: 75.1,
    cprUsd: 8.45,
    meanTurns: 18.0,
    meanLatencySeconds: 38.0,
    astHealingCount: 7,
    tokenVelocityKps: 2.1,
    paretoFrontier: false,
  },
  {
    modelId: "deepseek-v3",
    modelName: "DeepSeek V3",
    provider: "DeepSeek",
    taskSuite: "SWE-bench Verified",
    passRatePct: 59.8,
    cprUsd: 0.16,
    meanTurns: 13.8,
    meanLatencySeconds: 18.2,
    astHealingCount: 15,
    tokenVelocityKps: 5.9,
    paretoFrontier: true,
  },
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const suiteParam = searchParams.get("suite");
  const providerParam = searchParams.get("provider");
  const paretoOnly = searchParams.get("paretoOnly") === "true";
  const maxCpr = searchParams.get("maxCpr") ? parseFloat(searchParams.get("maxCpr")!) : null;

  let filtered = [...BENCHMARK_CATALOG];

  if (suiteParam) {
    filtered = filtered.filter((r) => r.taskSuite.toLowerCase().includes(suiteParam.toLowerCase()));
  }

  if (providerParam) {
    filtered = filtered.filter((r) => r.provider.toLowerCase() === providerParam.toLowerCase());
  }

  if (paretoOnly) {
    filtered = filtered.filter((r) => r.paretoFrontier);
  }

  if (maxCpr !== null && !isNaN(maxCpr)) {
    filtered = filtered.filter((r) => r.cprUsd <= maxCpr);
  }

  return NextResponse.json({
    status: "success",
    count: filtered.length,
    timestamp: new Date().toISOString(),
    data: filtered,
  });
}
