"use client";

import React, { use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getModelById, getAllModels } from "@/lib/models-data";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  DollarSign,
  TrendingUp,
  Activity,
  Layers,
  Zap,
  Shield,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sparkles,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";

interface PageProps {
  params: Promise<{ modelId: string }>;
}

export default function ModelDetailPage({ params }: PageProps) {
  const { modelId } = use(params);
  const model = getModelById(modelId);

  if (!model) {
    notFound();
  }

  const isHybrid = model.id === "benchpress-hybrid";

  // Data for Tool Failure Pie Chart
  const toolFailureData = [
    { name: "Wrong Line Offset", value: model.toolFailures.wrongLineOffsetPct, color: "#EF4444" },
    { name: "Malformed JSON Schema", value: model.toolFailures.malformedJsonPct, color: "#F59E0B" },
    { name: "Hallucinated Tool", value: model.toolFailures.hallucinatedToolPct, color: "#8B5CF6" },
    { name: "Bash Timeout (>30s)", value: model.toolFailures.bashTimeoutPct, color: "#3B82F6" },
    { name: "Syntax Regression", value: model.toolFailures.syntaxRegressionPct, color: "#EC4899" },
  ].filter((item) => item.value > 0);

  // Data for Token Burn Waterfall Bar Chart
  const tokenWaterfallData = [
    {
      category: "Token Composition",
      "Input Context": model.tokenWaterfall.inputTokensPct,
      "Useful Output": model.tokenWaterfall.outputTokensPct,
      "Reasoning Overhead": model.tokenWaterfall.reasoningTokensPct,
      "Wasted Bloat": model.tokenWaterfall.wastedBloatTokensPct,
    },
  ];

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/models"
            className="flex items-center gap-2 text-xs font-mono text-gray-400 hover:text-[#00F0FF] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Model Catalog
          </Link>

          <Link
            href={`/compare?a=${model.id}&b=benchpress-hybrid`}
            className="flex items-center gap-2 rounded-lg border border-[#00F0FF]/30 bg-[#00F0FF]/10 px-3 py-1.5 text-xs font-mono text-[#00F0FF] hover:bg-[#00F0FF]/20 hover:shadow-glass-cyan transition-all"
          >
            Compare with Hybrid Route ⚖️
          </Link>
        </div>

        {/* Hero Header Card */}
        <div
          className={`relative overflow-hidden rounded-2xl border p-6 sm:p-8 backdrop-blur-xl ${
            isHybrid
              ? "border-[#00F0FF]/50 bg-gradient-to-br from-[#121722]/95 via-[#0A0D14] to-[#00F0FF]/10 shadow-[0_0_40px_rgba(0,240,255,0.2)]"
              : "border-white/10 bg-[#121722]/80"
          }`}
        >
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono tracking-wider text-gray-400 uppercase">
                  {model.provider}
                </span>
                <Badge
                  variant={
                    isHybrid
                      ? "cyan"
                      : model.provider === "Google"
                      ? "emerald"
                      : model.provider === "Anthropic"
                      ? "amber"
                      : "purple"
                  }
                  size="sm"
                >
                  {model.tier}
                </Badge>
                <span className="text-xs font-mono text-gray-400">
                  {model.contextWindow.toLocaleString()} Token Context Window
                </span>
              </div>

              <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
                {model.name}
              </h1>

              <p className="text-sm text-gray-300 max-w-3xl">
                {model.strengths[0]}
              </p>
            </div>

            {/* Nominal Pricing Pill */}
            <div className="rounded-xl border border-white/10 bg-black/40 p-4 text-right">
              <div className="text-[10px] uppercase font-mono tracking-wider text-gray-400">
                Nominal API Rate Card
              </div>
              <div className="text-base font-mono font-bold text-white mt-1">
                ${model.pricing.inputPerMillion.toFixed(2)} in / ${model.pricing.outputPerMillion.toFixed(2)} out
              </div>
              <div className="text-[11px] font-mono text-gray-400">per 1M tokens</div>
            </div>
          </div>

          {/* Optimal Hybrid Partner Banner */}
          <div className="mt-6 flex items-center gap-3 rounded-xl border border-[#00F0FF]/20 bg-[#00F0FF]/5 p-3 text-xs text-gray-300">
            <Sparkles className="h-4 w-4 shrink-0 text-[#00F0FF]" />
            <div>
              <span className="font-bold text-[#00F0FF]">Economic Recommendation: </span>
              {model.recommendedHybridPartner}
            </div>
          </div>
        </div>

        {/* Primary Agentic Metrics Row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-400 mb-1">
              <DollarSign className="h-3.5 w-3.5 text-[#10B981]" />
              Cost Per Resolution
            </div>
            <div className="text-2xl font-mono font-bold text-white">
              ${model.metrics.cprUsd.toFixed(2)}
            </div>
            <div className="text-[10px] text-gray-500 mt-1">True dollar cost / verified fix</div>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-400 mb-1">
              <TrendingUp className="h-3.5 w-3.5 text-[#00F0FF]" />
              Verified Pass@1
            </div>
            <div className="text-2xl font-mono font-bold text-white">
              {model.metrics.passAt1}%
            </div>
            <div className="text-[10px] text-gray-500 mt-1">SWE-bench Verified (Pytest)</div>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-400 mb-1">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
              Trajectory Bloat
            </div>
            <div className="text-2xl font-mono font-bold text-white">
              {model.metrics.tbrBloatRatio}%
            </div>
            <div className="text-[10px] text-gray-500 mt-1">Wasted tokens on retries</div>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-400 mb-1">
              <Activity className="h-3.5 w-3.5 text-purple-400" />
              Mean Turns
            </div>
            <div className="text-2xl font-mono font-bold text-white">
              {model.metrics.meanTurnsToResolve}
            </div>
            <div className="text-[10px] text-gray-500 mt-1">Avg agent turns per task</div>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-400 mb-1">
              <Shield className="h-3.5 w-3.5 text-emerald-400" />
              AST Self-Healing
            </div>
            <div className="text-2xl font-mono font-bold text-white">
              {model.metrics.syntaxSelfHealingRate}%
            </div>
            <div className="text-[10px] text-gray-500 mt-1">Autonomous syntax recovery</div>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-400 mb-1">
              <Layers className="h-3.5 w-3.5 text-cyan-400" />
              Turn-20 Retention
            </div>
            <div className="text-2xl font-mono font-bold text-white">
              {model.metrics.turn20ContextRetention}%
            </div>
            <div className="text-[10px] text-gray-500 mt-1">Context focus at depth</div>
          </div>
        </div>

        {/* Deep Analysis Charts Grid */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Chart 1: Context Degradation Curve */}
          <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-[#00F0FF]" />
                  Context Degradation Curve (Δdecay)
                </h3>
                <p className="text-xs text-gray-400">
                  Reasoning, symbol recall, and focus retention over 1 to 30 sequential turns.
                </p>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={model.degradationCurve} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="turn" stroke="#6b7280" tickFormatter={(t) => `T${t}`} />
                  <YAxis domain={[0, 100]} stroke="#6b7280" tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0A0D14", borderColor: "#ffffff20", borderRadius: "8px" }}
                    formatter={(value: any) => [`${value}%`]}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="accuracyRetention" name="Accuracy Retention" stroke="#00F0FF" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="symbolRecall" name="Symbol Recall" stroke="#10B981" strokeWidth={1.5} strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="reasoningFocus" name="Reasoning Focus" stroke="#8B5CF6" strokeWidth={1.5} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Tool Failure Taxonomy Breakdown */}
          <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Tool Failure Taxonomy Breakdown
                </h3>
                <p className="text-xs text-gray-400">
                  Distribution of failed tool execution steps in gVisor sandboxes.
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between h-64">
              <div className="h-full w-full sm:w-1/2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={toolFailureData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {toolFailureData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0A0D14", borderColor: "#ffffff20", borderRadius: "8px" }}
                      formatter={(val: any) => [`${val}%`]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="flex flex-col gap-2 w-full sm:w-1/2 text-xs">
                {toolFailureData.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-gray-300">{item.name}</span>
                    </div>
                    <span className="font-mono font-bold text-white">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Token Waterfall Composition Bar */}
        <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
          <div className="mb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="h-4 w-4 text-purple-400" />
              Turn-by-Turn Token Composition & Waste Waterfall
            </h3>
            <p className="text-xs text-gray-400">
              Breakdown of total tokens incurred across 100 canonical multi-turn SWE-bench evaluation runs.
            </p>
          </div>

          <div className="h-24 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={tokenWaterfallData} margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} stroke="#6b7280" />
                <YAxis type="category" dataKey="category" hide />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0A0D14", borderColor: "#ffffff20", borderRadius: "8px" }}
                  formatter={(val: any) => [`${val}%`]}
                />
                <Legend />
                <Bar dataKey="Input Context" stackId="a" fill="#00F0FF" />
                <Bar dataKey="Useful Output" stackId="a" fill="#10B981" />
                <Bar dataKey="Reasoning Overhead" stackId="a" fill="#8B5CF6" />
                <Bar dataKey="Wasted Bloat" stackId="a" fill="#EF4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Strengths & Weaknesses Comparison Cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-6 backdrop-blur-xl">
            <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2 mb-3">
              <CheckCircle2 className="h-4 w-4" />
              Architectural Strengths
            </h3>
            <ul className="space-y-2 text-xs text-gray-300">
              {model.strengths.map((str, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border border-rose-500/20 bg-rose-950/10 p-6 backdrop-blur-xl">
            <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2 mb-3">
              <XCircle className="h-4 w-4" />
              Agentic Limitations & Failure Modes
            </h3>
            <ul className="space-y-2 text-xs text-gray-300">
              {model.weaknesses.map((weak, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-rose-400 font-bold">•</span>
                  <span>{weak}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Recent Evaluation Trajectories Table */}
        <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Recent Verified Trajectory Traces</h3>
              <p className="text-xs text-gray-400">
                Inspect line-by-line tool executions and unit test assertions in gVisor sandboxes.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="border-b border-white/10 font-mono uppercase tracking-wider text-[10px] text-gray-400">
                <tr>
                  <th className="pb-3">Task ID</th>
                  <th className="pb-3">Suite</th>
                  <th className="pb-3">Turns</th>
                  <th className="pb-3">Cost ($)</th>
                  <th className="pb-3">Self-Healed</th>
                  <th className="pb-3">Outcome</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {model.recentTrajectories.map((traj) => (
                  <tr key={traj.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 font-bold text-white">{traj.taskId}</td>
                    <td className="py-3 text-gray-400">{traj.taskSuite}</td>
                    <td className="py-3">{traj.turns} turns</td>
                    <td className="py-3 font-bold text-[#10B981]">${traj.cprUsd.toFixed(2)}</td>
                    <td className="py-3">
                      {traj.healedErrorsCount > 0 ? (
                        <span className="text-emerald-400">{traj.healedErrorsCount} AST fixes</span>
                      ) : (
                        <span className="text-gray-500">None</span>
                      )}
                    </td>
                    <td className="py-3">
                      <Badge variant={traj.status === "PASS" ? "emerald" : "crimson"} size="sm">
                        {traj.status}
                      </Badge>
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        href={`/trajectories/${traj.id}`}
                        className="inline-flex items-center gap-1 text-[#00F0FF] hover:underline"
                      >
                        Inspect Trace
                        <ChevronRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
