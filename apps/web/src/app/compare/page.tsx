"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getAllModels, getModelById, ModelProfileData } from "@/lib/models-data";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeftRight,
  DollarSign,
  TrendingUp,
  Activity,
  Layers,
  Shield,
  Zap,
  Sparkles,
  Check,
  Calculator,
  ArrowRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Tooltip,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

function CompareContent() {
  const searchParams = useSearchParams();
  const allModels = getAllModels();

  const initialModelA = searchParams.get("a") || "claude-3-7-sonnet";
  const initialModelB = searchParams.get("b") || "benchpress-hybrid";

  const [modelAId, setModelAId] = useState<string>(initialModelA);
  const [modelBId, setModelBId] = useState<string>(initialModelB);
  const [monthlyTaskVolume, setMonthlyTaskVolume] = useState<number>(10000);

  useEffect(() => {
    const a = searchParams.get("a");
    const b = searchParams.get("b");
    if (a && getModelById(a)) setModelAId(a);
    if (b && getModelById(b)) setModelBId(b);
  }, [searchParams]);

  const modelA = getModelById(modelAId) || allModels[3]; // Claude 3.7 Sonnet default
  const modelB = getModelById(modelBId) || allModels[2]; // Benchpress Hybrid default

  // Radar Data calculation (normalized 0 to 100)
  const radarData = [
    {
      subject: "Accuracy (Pass@1)",
      [modelA.name]: Math.min(100, (modelA.metrics.passAt1 / 70) * 100),
      [modelB.name]: Math.min(100, (modelB.metrics.passAt1 / 70) * 100),
    },
    {
      subject: "Cost Efficiency (1/CPR)",
      [modelA.name]: Math.min(100, (0.24 / modelA.metrics.cprUsd) * 100),
      [modelB.name]: Math.min(100, (0.24 / modelB.metrics.cprUsd) * 100),
    },
    {
      subject: "Velocity (Speed)",
      [modelA.name]: Math.min(100, (30 / modelA.metrics.avgExecutionTimeSeconds) * 100),
      [modelB.name]: Math.min(100, (30 / modelB.metrics.avgExecutionTimeSeconds) * 100),
    },
    {
      subject: "Resilience (Self-Heal)",
      [modelA.name]: modelA.metrics.syntaxSelfHealingRate,
      [modelB.name]: modelB.metrics.syntaxSelfHealingRate,
    },
    {
      subject: "Context Retention",
      [modelA.name]: modelA.metrics.turn20ContextRetention,
      [modelB.name]: modelB.metrics.turn20ContextRetention,
    },
    {
      subject: "Low Bloat (100-TBR)",
      [modelA.name]: 100 - modelA.metrics.tbrBloatRatio,
      [modelB.name]: 100 - modelB.metrics.tbrBloatRatio,
    },
  ];

  // Combined Degradation Curve for Dual Line Chart
  const combinedDegradationData = modelA.degradationCurve.map((pointA) => {
    const pointB = modelB.degradationCurve.find((p) => p.turn === pointA.turn);
    return {
      turn: pointA.turn,
      [modelA.name]: pointA.accuracyRetention,
      [modelB.name]: pointB ? pointB.accuracyRetention : 0,
    };
  });

  // Financial Calculations
  const monthlyCostA = monthlyTaskVolume * modelA.metrics.cprUsd;
  const monthlyCostB = monthlyTaskVolume * modelB.metrics.cprUsd;
  const monthlySavings = Math.max(0, monthlyCostA - monthlyCostB);
  const savingsPct = monthlyCostA > 0 ? ((monthlyCostA - monthlyCostB) / monthlyCostA) * 100 : 0;

  const presets = [
    { label: "Claude 3.7 vs. ★ Hybrid", a: "claude-3-7-sonnet", b: "benchpress-hybrid" },
    { label: "GPT-4o vs. Gemini 2.5 Pro", a: "gpt-4o", b: "gemini-2-5-pro" },
    { label: "DeepSeek-R1 vs. Gemini 3.5 Flash", a: "deepseek-r1", b: "gemini-3-5-flash" },
    { label: "Llama 3.3 vs. Gemini 2.5 Pro", a: "llama-3-3-70b", b: "gemini-2-5-pro" },
  ];

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="text-center sm:text-left">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="cyan" size="sm">
              Head-to-Head Benchmark Matrix
            </Badge>
            <span className="text-xs font-mono text-gray-400">Deterministic Multi-Turn Profiling</span>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
              DEMO FIXTURE
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Side-by-Side Agentic Model Comparison
          </h1>
          <p className="mt-2 text-sm text-gray-400 max-w-3xl">
            Compare multi-turn Cost Per Resolution (CPR), context degradation curves, and token bloat across any two foundation models.
          </p>
          <div className="mt-4 p-3 rounded-lg bg-purple-500/[0.08] border border-purple-500/30 text-xs font-mono text-purple-200 flex items-center justify-between flex-wrap gap-2">
            <span>ℹ️ Historical comparative matrix is tagged as DEMO FIXTURE. For live, ground-truth verified decision receipts, visit the Taskmaster Governance pages.</span>
            <Link href="/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20" className="text-cyan-400 underline font-semibold">View Live Judged Decision ➔</Link>
          </div>
        </div>

        {/* Comparison Presets */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-gray-400">Quick Presets:</span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setModelAId(p.a);
                setModelBId(p.b);
              }}
              className="rounded-lg border border-white/10 bg-[#121722]/80 px-3 py-1.5 text-xs font-medium text-gray-300 hover:border-[#00F0FF]/40 hover:text-white transition-all"
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Model Selectors Bar */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
          <div>
            <label className="block text-xs font-mono text-gray-400 mb-2 uppercase tracking-wider">
              Model A (Baseline Target)
            </label>
            <select
              value={modelAId}
              onChange={(e) => setModelAId(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/60 px-4 py-2.5 text-sm font-bold text-white focus:border-[#00F0FF]/50 focus:outline-none"
            >
              {allModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.provider}) — ${m.metrics.cprUsd.toFixed(2)} CPR
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono text-gray-400 mb-2 uppercase tracking-wider">
              Model B (Challenger / Routing Target)
            </label>
            <select
              value={modelBId}
              onChange={(e) => setModelBId(e.target.value)}
              className="w-full rounded-xl border border-[#00F0FF]/40 bg-black/60 px-4 py-2.5 text-sm font-bold text-[#00F0FF] focus:border-[#00F0FF]/50 focus:outline-none"
            >
              {allModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.provider}) — ${m.metrics.cprUsd.toFixed(2)} CPR
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Side-by-Side Metric Comparison Table */}
        <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
          <h3 className="text-base font-bold text-white mb-4">Multi-Turn Economic & Architectural Matrix</h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="border-b border-white/10 uppercase tracking-wider text-[10px] text-gray-400">
                <tr>
                  <th className="pb-3">Dimension / Metric</th>
                  <th className="pb-3 text-gray-200">{modelA.name}</th>
                  <th className="pb-3 text-[#00F0FF]">{modelB.name}</th>
                  <th className="pb-3 text-right">Economic Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {/* CPR */}
                <tr className="hover:bg-white/5">
                  <td className="py-3 font-bold text-gray-300">Cost Per Resolution (CPR)</td>
                  <td className="py-3 font-bold text-white">${modelA.metrics.cprUsd.toFixed(2)}</td>
                  <td className="py-3 font-bold text-[#00F0FF]">${modelB.metrics.cprUsd.toFixed(2)}</td>
                  <td className="py-3 text-right font-bold">
                    {modelB.metrics.cprUsd < modelA.metrics.cprUsd ? (
                      <span className="text-emerald-400">
                        -{(((modelA.metrics.cprUsd - modelB.metrics.cprUsd) / modelA.metrics.cprUsd) * 100).toFixed(1)}% Cheaper
                      </span>
                    ) : (
                      <span className="text-rose-400">
                        +{(((modelB.metrics.cprUsd - modelA.metrics.cprUsd) / modelA.metrics.cprUsd) * 100).toFixed(1)}% Cost
                      </span>
                    )}
                  </td>
                </tr>

                {/* Pass@1 */}
                <tr className="hover:bg-white/5">
                  <td className="py-3 font-bold text-gray-300">Verified Pass@1 (SWE-bench)</td>
                  <td className="py-3 text-white">{modelA.metrics.passAt1}%</td>
                  <td className="py-3 text-[#00F0FF]">{modelB.metrics.passAt1}%</td>
                  <td className="py-3 text-right">
                    {modelB.metrics.passAt1 >= modelA.metrics.passAt1 ? (
                      <span className="text-emerald-400">+{(modelB.metrics.passAt1 - modelA.metrics.passAt1).toFixed(1)}% Higher</span>
                    ) : (
                      <span className="text-rose-400">{(modelB.metrics.passAt1 - modelA.metrics.passAt1).toFixed(1)}%</span>
                    )}
                  </td>
                </tr>

                {/* Trajectory Bloat */}
                <tr className="hover:bg-white/5">
                  <td className="py-3 font-bold text-gray-300">Trajectory Bloat Ratio (TBR)</td>
                  <td className="py-3 text-white">{modelA.metrics.tbrBloatRatio}%</td>
                  <td className="py-3 text-[#00F0FF]">{modelB.metrics.tbrBloatRatio}%</td>
                  <td className="py-3 text-right">
                    {modelB.metrics.tbrBloatRatio < modelA.metrics.tbrBloatRatio ? (
                      <span className="text-emerald-400">
                        -{(((modelA.metrics.tbrBloatRatio - modelB.metrics.tbrBloatRatio) / modelA.metrics.tbrBloatRatio) * 100).toFixed(1)}% Less Waste
                      </span>
                    ) : (
                      <span className="text-rose-400">Higher Bloat</span>
                    )}
                  </td>
                </tr>

                {/* Mean Turns */}
                <tr className="hover:bg-white/5">
                  <td className="py-3 font-bold text-gray-300">Mean Turns to Resolve</td>
                  <td className="py-3 text-white">{modelA.metrics.meanTurnsToResolve} turns</td>
                  <td className="py-3 text-[#00F0FF]">{modelB.metrics.meanTurnsToResolve} turns</td>
                  <td className="py-3 text-right">
                    {modelB.metrics.meanTurnsToResolve < modelA.metrics.meanTurnsToResolve ? (
                      <span className="text-emerald-400">Faster Resolution</span>
                    ) : (
                      <span className="text-gray-400">Standard</span>
                    )}
                  </td>
                </tr>

                {/* Context Retention */}
                <tr className="hover:bg-white/5">
                  <td className="py-3 font-bold text-gray-300">Turn-20 Context Focus</td>
                  <td className="py-3 text-white">{modelA.metrics.turn20ContextRetention}%</td>
                  <td className="py-3 text-[#00F0FF]">{modelB.metrics.turn20ContextRetention}%</td>
                  <td className="py-3 text-right">
                    {modelB.metrics.turn20ContextRetention >= modelA.metrics.turn20ContextRetention ? (
                      <span className="text-emerald-400">Superior Context Focus</span>
                    ) : (
                      <span className="text-gray-400">Standard</span>
                    )}
                  </td>
                </tr>

                {/* AST Self-Healing */}
                <tr className="hover:bg-white/5">
                  <td className="py-3 font-bold text-gray-300">AST Self-Healing Rate</td>
                  <td className="py-3 text-white">{modelA.metrics.syntaxSelfHealingRate}%</td>
                  <td className="py-3 text-[#00F0FF]">{modelB.metrics.syntaxSelfHealingRate}%</td>
                  <td className="py-3 text-right">
                    {modelB.metrics.syntaxSelfHealingRate >= modelA.metrics.syntaxSelfHealingRate ? (
                      <span className="text-emerald-400">Higher Autonomy</span>
                    ) : (
                      <span className="text-gray-400">Lower Recovery</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Visual Charts Grid: Radar Capability + Degradation Comparison */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Multi-Axis Capability Radar */}
          <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
            <h3 className="text-base font-bold text-white mb-1">Multi-Axis Capability Radar</h3>
            <p className="text-xs text-gray-400 mb-4">
              Normalized capability scores across 6 key agentic dimensions.
            </p>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#ffffff15" />
                  <PolarAngleAxis dataKey="subject" stroke="#9ca3af" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} stroke="#ffffff10" tick={false} />
                  <Radar name={modelA.name} dataKey={modelA.name} stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.25} />
                  <Radar name={modelB.name} dataKey={modelB.name} stroke="#00F0FF" fill="#00F0FF" fillOpacity={0.4} />
                  <Legend />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0A0D14", borderColor: "#ffffff20", borderRadius: "8px" }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Dual Context Degradation Curves */}
          <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
            <h3 className="text-base font-bold text-white mb-1">Context Degradation Over Time</h3>
            <p className="text-xs text-gray-400 mb-4">
              Comparing reasoning accuracy retention across 1 to 30 sequential turns.
            </p>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={combinedDegradationData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="turn" stroke="#6b7280" tickFormatter={(t) => `T${t}`} />
                  <YAxis domain={[0, 100]} stroke="#6b7280" tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0A0D14", borderColor: "#ffffff20", borderRadius: "8px" }}
                    formatter={(val: any) => [`${val}%`]}
                  />
                  <Legend />
                  <Line type="monotone" dataKey={modelA.name} stroke="#F59E0B" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey={modelB.name} stroke="#00F0FF" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Interactive Financial ROI & Cost Arbitrage Estimator */}
        <div className="rounded-2xl border border-[#00F0FF]/30 bg-gradient-to-r from-[#121722] via-[#0A0D14] to-[#00F0FF]/10 p-6 sm:p-8 backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-4">
            <Calculator className="h-5 w-5 text-[#00F0FF]" />
            <h3 className="text-lg font-bold text-white">Monthly Enterprise Financial ROI Calculator</h3>
          </div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3 items-center">
            {/* Slider Column */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-400">Monthly Multi-Turn Tasks Executed:</span>
                <span className="font-bold text-[#00F0FF] text-base">{monthlyTaskVolume.toLocaleString()} tasks / mo</span>
              </div>

              <input
                type="range"
                min={1000}
                max={50000}
                step={1000}
                value={monthlyTaskVolume}
                onChange={(e) => setMonthlyTaskVolume(Number(e.target.value))}
                className="w-full accent-[#00F0FF] h-2 bg-black/60 rounded-lg cursor-pointer"
              />

              <div className="flex justify-between text-[10px] font-mono text-gray-500">
                <span>1,000 (Small Team)</span>
                <span>10,000 (Mid-Market)</span>
                <span>50,000 (Enterprise)</span>
              </div>
            </div>

            {/* Result Box */}
            <div className="rounded-xl border border-white/10 bg-black/60 p-6 text-center lg:text-right">
              <div className="text-[10px] uppercase font-mono tracking-wider text-gray-400">
                Estimated Net Savings with {modelB.name}
              </div>
              <div className="text-3xl font-extrabold font-mono text-[#10B981] mt-1">
                ${Math.round(monthlySavings).toLocaleString()} / mo
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {savingsPct > 0 ? `${savingsPct.toFixed(1)}% reduction in AI spend` : "Comparable spend"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0A0D14] flex items-center justify-center text-gray-400">Loading comparison...</div>}>
      <CompareContent />
    </Suspense>
  );
}
