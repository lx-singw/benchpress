"use client";

import React, { useState } from "react";
import {
  Sparkles,
  TrendingDown,
  DollarSign,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Wrench,
  Zap,
  Activity,
  Filter,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatPercent, formatUsd } from "@/lib/utils";
import type { BenchmarkLeaderboardRow } from "@/lib/types";

const ALL_BENCHMARKS: BenchmarkLeaderboardRow[] = [
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
    modelId: "hybrid-gemini-pro-flash",
    modelName: "Hybrid: Gemini 2.5 Pro + Flash",
    provider: "Google",
    taskSuite: "SWE-bench Verified",
    passRatePct: 62.4,
    cprUsd: 0.28,
    meanTurns: 10.4,
    meanLatencySeconds: 14.2,
    astHealingCount: 22,
    tokenVelocityKps: 6.1,
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

interface CprLeaderboardTableProps {
  selectedModelId?: string;
  onSelectModel?: (modelId: string) => void;
}

export function CprLeaderboardTable({ selectedModelId, onSelectModel }: CprLeaderboardTableProps) {
  const [selectedSuite, setSelectedSuite] = useState<string>("SWE-bench Verified");
  const [selectedProvider, setSelectedProvider] = useState<string>("ALL");
  const [expandedModelId, setExpandedModelId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<keyof BenchmarkLeaderboardRow>("cprUsd");
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  const filtered = ALL_BENCHMARKS.filter((item) => {
    const matchSuite = item.taskSuite.toLowerCase() === selectedSuite.toLowerCase();
    const matchProvider = selectedProvider === "ALL" || item.provider.toLowerCase() === selectedProvider.toLowerCase();
    return matchSuite && matchProvider;
  });

  const sorted = [...filtered].sort((a, b) => {
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

  const toggleExpand = (id: string) => {
    setExpandedModelId(expandedModelId === id ? null : id);
  };

  return (
    <GlassCard className="p-6" glow="none">
      {/* Header Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#10B981]/10 text-[#10B981]">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-sm">Model Economic Index & Leaderboard</h3>
            <p className="text-[11px] text-gray-400">Continuous Evaluation & Cost per Resolved Task</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
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

          {/* Provider Filter */}
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="rounded-lg border border-white/10 bg-[#0A0D14] px-2.5 py-1.5 text-xs font-mono text-gray-300 focus:border-[#00F0FF] focus:outline-none"
          >
            <option value="ALL">All Providers</option>
            <option value="Google">Google Vertex</option>
            <option value="Anthropic">Anthropic</option>
            <option value="OpenAI">OpenAI</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-mono">
            <tr>
              <th className="pb-3 font-medium">Model / Strategy</th>
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
              <th className="pb-3 font-medium text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono">
            {sorted.map((row) => {
              const isSelected = selectedModelId === row.modelId;
              const isExpanded = expandedModelId === row.modelId;

              return (
                <React.Fragment key={row.modelId}>
                  <tr
                    onClick={() => onSelectModel?.(row.modelId)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-[#00F0FF]/10 border-l-2 border-[#00F0FF]"
                        : "hover:bg-white/[0.02]"
                    }`}
                  >
                    <td className="py-3.5 pr-4">
                      <div className="font-sans font-medium text-white flex items-center gap-1.5">
                        <span>{row.modelName}</span>
                      </div>
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
                    <td className="py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpand(row.modelId);
                        }}
                        className="rounded p-1 text-gray-400 hover:bg-white/10 hover:text-white"
                      >
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </button>
                    </td>
                  </tr>

                  {/* Expandable Model Economics Drawer */}
                  {isExpanded && (
                    <tr className="bg-[#0A0D14]/80">
                      <td colSpan={7} className="p-4">
                        <div className="rounded-lg border border-white/10 bg-[#121722] p-4 text-xs font-sans">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2 font-mono font-bold text-white">
                              <Cpu className="h-4 w-4 text-[#00F0FF]" />
                              <span>Deep Economic Profile: {row.modelName}</span>
                            </div>
                            <Badge variant="emerald" size="sm">
                              {row.taskSuite}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[11px] mb-3">
                            <div className="rounded bg-[#0A0D14] p-2.5 border border-white/5">
                              <div className="text-gray-500 uppercase text-[9px]">Token Velocity</div>
                              <div className="text-white font-bold mt-0.5">{row.tokenVelocityKps} kps</div>
                            </div>
                            <div className="rounded bg-[#0A0D14] p-2.5 border border-white/5">
                              <div className="text-gray-500 uppercase text-[9px]">AST Self-Healing Rate</div>
                              <div className="text-[#F59E0B] font-bold mt-0.5">{row.astHealingCount} recoveries</div>
                            </div>
                            <div className="rounded bg-[#0A0D14] p-2.5 border border-white/5">
                              <div className="text-gray-500 uppercase text-[9px]">Enterprise Savings vs Claude 3.7</div>
                              <div className="text-[#10B981] font-bold mt-0.5">
                                {formatPercent(((1.15 - row.cprUsd) / 1.15) * 100)} Savings
                              </div>
                            </div>
                          </div>

                          <p className="text-gray-300 text-[11px]">
                            <strong>Choreography Rationale:</strong> When evaluated across 500 SWE-bench Verified tasks, this configuration demonstrated high tool call reliability with an average execution duration of {row.meanLatencySeconds}s per turn.
                          </p>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
}
