"use client";

import React, { useState } from "react";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
  Filter,
  Flame,
  Layers,
  ShieldAlert,
  Sparkles,
  TrendingDown,
  Wrench,
  Zap,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatPercent, formatUsd } from "@/lib/utils";
import type { BenchmarkLeaderboardRow, ParetoDataPoint } from "@/lib/types";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";

const MOCK_LEADERBOARD: BenchmarkLeaderboardRow[] = [
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

const PARETO_POINTS: ParetoDataPoint[] = MOCK_LEADERBOARD.map((item) => ({
  modelId: item.modelId,
  modelName: item.modelName,
  provider: item.provider,
  cprUsd: item.cprUsd,
  passRatePct: item.passRatePct,
  meanLatencySeconds: item.meanLatencySeconds,
  isOnFrontier: item.paretoFrontier,
}));

export default function HubPage() {
  const [selectedSuite, setSelectedSuite] = useState<string>("SWE-bench Verified");
  const [sortBy, setSortBy] = useState<keyof BenchmarkLeaderboardRow>("cprUsd");
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  const sortedLeaderboard = [...MOCK_LEADERBOARD].sort((a, b) => {
    const valA = a[sortBy];
    const valB = b[sortBy];
    if (typeof valA === "number" && typeof valB === "number") {
      return sortAsc ? valA - valB : valB - valA;
    }
    return 0;
  });

  const handleSort = (field: keyof BenchmarkLeaderboardRow) => {
    if (sortBy === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortBy(field);
      setSortAsc(true);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero Header */}
      <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="cyan" dot size="sm">
              LIVE BENCHMARK INTELLIGENCE
            </Badge>
            <span className="text-xs text-gray-500 font-mono">Continuous Cloud Run Gen2 Evals</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            The Economic & Trajectory Intelligence Platform
          </h1>
          <p className="mt-2 text-sm text-gray-400 max-w-2xl">
            Real-time Cost per Resolved Task (CPR), autonomous AST tool-healing metrics, and Pareto-optimal model routing choreography.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="/live"
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#00F0FF] to-[#10B981] px-4 py-2.5 text-sm font-semibold text-[#0A0D14] hover:opacity-95 shadow-glass-cyan transition-all"
          >
            <Activity className="h-4 w-4" />
            Launch Live Runner
          </a>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <GlassCard className="p-5" glow="cyan">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-gray-400">Lowest CPR Frontier</span>
            <DollarSign className="h-5 w-5 text-[#00F0FF]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white">$0.12</span>
            <span className="text-xs text-[#10B981] flex items-center font-medium">
              <TrendingDown className="h-3 w-3 mr-0.5" /> -73% vs Frontier Avg
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-400 font-mono">Gemini 2.5 Flash (SWE-bench)</p>
        </GlassCard>

        <GlassCard className="p-5" glow="emerald">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-gray-400">Max Pass Rate</span>
            <CheckCircle2 className="h-5 w-5 text-[#10B981]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white">70.4%</span>
            <span className="text-xs text-[#00F0FF] font-mono">SWE-bench Verified</span>
          </div>
          <p className="mt-1 text-xs text-gray-400 font-mono">Claude 3.7 Sonnet ($1.15/task)</p>
        </GlassCard>

        <GlassCard className="p-5" glow="none">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-gray-400">AST Tool Auto-Healing</span>
            <Wrench className="h-5 w-5 text-[#F59E0B]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white">92.4%</span>
            <span className="text-xs text-gray-400">Autonomous Patch Success</span>
          </div>
          <p className="mt-1 text-xs text-gray-400 font-mono">312 Tool Signature Mismatches Healed</p>
        </GlassCard>

        <GlassCard className="p-5" glow="none">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-gray-400">FinOps Early-Halt ROI</span>
            <Zap className="h-5 w-5 text-purple-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white">$14,290</span>
            <span className="text-xs text-[#10B981] font-mono">Saved this month</span>
          </div>
          <p className="mt-1 text-xs text-gray-400 font-mono">Turn-5 Markov Sentinel Cutoffs</p>
        </GlassCard>
      </div>

      {/* Main Interactive Section: Pareto Frontier Chart + Leaderboard */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Pareto Frontier Chart (1 Col on Desktop) */}
        <GlassCard className="p-6 lg:col-span-1 flex flex-col justify-between" glow="none">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-[#00F0FF]" />
                <h3 className="font-semibold text-white">Pareto Economic Frontier</h3>
              </div>
              <Badge variant="cyan" size="sm">
                2D Trade-Off
              </Badge>
            </div>
            <p className="text-xs text-gray-400 mb-6">
              Cost per Resolved Task ($) vs. Pass Rate (%). Points highlighted in electric cyan define the Pareto-optimal frontier.
            </p>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A2234" />
                  <XAxis
                    type="number"
                    dataKey="cprUsd"
                    name="CPR (USD)"
                    unit="$"
                    stroke="#6B7280"
                    tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }}
                  />
                  <YAxis
                    type="number"
                    dataKey="passRatePct"
                    name="Pass Rate"
                    unit="%"
                    stroke="#6B7280"
                    tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }}
                  />
                  <Tooltip
                    content={({ payload }) => {
                      if (!payload || payload.length === 0) return null;
                      const data = payload[0].payload as ParetoDataPoint;
                      return (
                        <div className="rounded-lg border border-white/20 bg-[#121722] p-3 text-xs shadow-xl">
                          <div className="font-bold text-white">{data.modelName}</div>
                          <div className="mt-1 text-gray-400 font-mono">
                            CPR: <span className="text-[#00F0FF]">{formatUsd(data.cprUsd)}</span>
                          </div>
                          <div className="text-gray-400 font-mono">
                            Pass Rate: <span className="text-[#10B981]">{formatPercent(data.passRatePct)}</span>
                          </div>
                          <div className="mt-1">
                            {data.isOnFrontier ? (
                              <Badge variant="cyan" size="sm">
                                Optimal Frontier
                              </Badge>
                            ) : (
                              <Badge variant="neutral" size="sm">
                                Dominated
                              </Badge>
                            )}
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Scatter name="Models" data={PARETO_POINTS}>
                    {PARETO_POINTS.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.isOnFrontier ? "#00F0FF" : "#6B7280"}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-[#0A0D14]/60 p-3 text-xs text-gray-400 border border-white/5">
            <span className="text-[#00F0FF] font-semibold">Routing Insight:</span> For coding tasks under $0.50 budget cap, Gemini 2.5 Pro yields 63.8% pass rate with 85% lower CPR than comparable closed-source models.
          </div>
        </GlassCard>

        {/* Leaderboard Table (2 Cols on Desktop) */}
        <GlassCard className="p-6 lg:col-span-2" glow="none">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[#10B981]" />
              <h3 className="font-semibold text-white">Model Economic Leaderboard</h3>
            </div>

            {/* Suite Tabs */}
            <div className="flex items-center gap-1 rounded-lg bg-[#0A0D14] p-1 border border-white/10">
              {["SWE-bench Verified", "HumanEval-XL", "Cybench"].map((suite) => (
                <button
                  key={suite}
                  onClick={() => setSelectedSuite(suite)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                    selectedSuite === suite
                      ? "bg-[#121722] text-[#00F0FF] shadow-sm"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  {suite}
                </button>
              ))}
            </div>
          </div>

          {/* Table Container */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-mono">
                <tr>
                  <th className="pb-3 font-medium">Model</th>
                  <th
                    className="pb-3 font-medium cursor-pointer hover:text-white"
                    onClick={() => handleSort("passRatePct")}
                  >
                    Pass Rate % {sortBy === "passRatePct" && (sortAsc ? "↑" : "↓")}
                  </th>
                  <th
                    className="pb-3 font-medium cursor-pointer hover:text-white"
                    onClick={() => handleSort("cprUsd")}
                  >
                    CPR ($) {sortBy === "cprUsd" && (sortAsc ? "↑" : "↓")}
                  </th>
                  <th className="pb-3 font-medium">Mean Turns</th>
                  <th className="pb-3 font-medium">AST Heals</th>
                  <th className="pb-3 font-medium">Frontier Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {sortedLeaderboard.map((row) => (
                  <tr key={row.modelId} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 pr-4">
                      <div className="font-sans font-medium text-white">{row.modelName}</div>
                      <div className="text-[11px] text-gray-500">{row.provider}</div>
                    </td>
                    <td className="py-3.5 text-[#10B981] font-semibold">
                      {formatPercent(row.passRatePct)}
                    </td>
                    <td className="py-3.5 text-[#00F0FF] font-semibold">
                      {formatUsd(row.cprUsd)}
                    </td>
                    <td className="py-3.5 text-gray-300">{row.meanTurns}</td>
                    <td className="py-3.5 text-gray-300">{row.astHealingCount}</td>
                    <td className="py-3.5">
                      {row.paretoFrontier ? (
                        <Badge variant="cyan" size="sm" dot>
                          Pareto Frontier
                        </Badge>
                      ) : (
                        <Badge variant="neutral" size="sm">
                          Dominated
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
