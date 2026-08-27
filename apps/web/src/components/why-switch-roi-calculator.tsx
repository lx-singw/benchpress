"use client";

import React, { useState, useMemo } from "react";
import { DollarSign, TrendingDown, Users, Zap, ShieldCheck, Download, Sparkles, ArrowRight } from "lucide-react";

export function WhySwitchRoiCalculator() {
  const [teamSize, setTeamSize] = useState<number>(25);
  const [dailyTurnsPerDev, setDailyTurnsPerDev] = useState<number>(50);
  const [workloadType, setWorkloadType] = useState<"SWE_BENCH" | "FULLSTACK" | "FAST_ITERATION">("SWE_BENCH");
  const [showExportToast, setShowExportToast] = useState(false);

  // Economic calculations per turn / task
  const stats = useMemo(() => {
    // Working days per year
    const workingDays = 250;
    const totalDailyTurns = teamSize * dailyTurnsPerDev;
    const annualTotalTurns = totalDailyTurns * workingDays;

    // Cost assumptions per turn ($)
    let frontierCostPerTurn = 0.038; // Claude 3.7 Sonnet baseline avg turn cost
    let benchpressCostPerTurn = 0.0048; // Gemini 2.5 Pro + Flash 2-tier choreography

    if (workloadType === "FULLSTACK") {
      frontierCostPerTurn = 0.045;
      benchpressCostPerTurn = 0.0062;
    } else if (workloadType === "FAST_ITERATION") {
      frontierCostPerTurn = 0.028;
      benchpressCostPerTurn = 0.0028;
    }

    const annualFrontierSpend = Math.round(annualTotalTurns * frontierCostPerTurn);
    const annualBenchpressSpend = Math.round(annualTotalTurns * benchpressCostPerTurn);
    const annualSavings = annualFrontierSpend - annualBenchpressSpend;
    const savingsPercent = Math.round((annualSavings / annualFrontierSpend) * 1000) / 10;
    const hoursSavedPerYear = Math.round((annualTotalTurns * 0.0035) * 10) / 10; // ~12s saved per turn in latency

    return {
      annualTotalTurns,
      annualFrontierSpend,
      annualBenchpressSpend,
      annualSavings,
      savingsPercent,
      hoursSavedPerYear,
    };
  }, [teamSize, dailyTurnsPerDev, workloadType]);

  const handleExportReport = () => {
    const reportData = {
      title: "Benchpress Enterprise ROI & FinOps Assessment",
      generated_at: new Date().toISOString(),
      parameters: {
        team_size_engineers: teamSize,
        daily_turns_per_engineer: dailyTurnsPerDev,
        workload_profile: workloadType,
      },
      projections: {
        annual_agent_turns: stats.annualTotalTurns,
        monolithic_frontier_spend_usd: stats.annualFrontierSpend,
        benchpress_2tier_spend_usd: stats.annualBenchpressSpend,
        net_annual_savings_usd: stats.annualSavings,
        cost_reduction_percent: stats.savingsPercent,
        developer_hours_saved_annually: stats.hoursSavedPerYear,
      },
      recommended_architecture: "Gemini 2.5 Pro (Planner / Supervisor) + Gemini 2.5 Flash (Coder / Tool Executor)",
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchpress-roi-report-${teamSize}devs.json`;
    a.click();
    URL.revokeObjectURL(url);

    setShowExportToast(true);
    setTimeout(() => setShowExportToast(false), 3000);
  };

  return (
    <div className="rounded-xl border border-white/10 bg-obsidian-900/60 p-6 backdrop-blur-xl shadow-2xl relative overflow-hidden">
      {/* Background Neon Glow */}
      <div className="absolute -top-24 -right-24 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-5 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono tracking-widest text-emerald-400 uppercase font-semibold">
              Enterprise FinOps Intelligence
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            Why Switch to Benchpress? <Sparkles className="w-5 h-5 text-amber-400" />
          </h2>
          <p className="text-sm text-zinc-400 mt-0.5">
            Simulate your team&apos;s annual cost savings switching from monolithic frontier models to 2-Tier Choreography.
          </p>
        </div>

        <button
          onClick={handleExportReport}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-mono text-zinc-200 transition"
        >
          <Download className="w-3.5 h-3.5 text-emerald-400" />
          Export ROI Report (JSON)
        </button>
      </div>

      {/* Workload Profile Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        {[
          { id: "SWE_BENCH", label: "SWE-bench Coding Sagas", desc: "Multi-file bug fixes & diff hunks" },
          { id: "FULLSTACK", label: "Full-Stack Web Generation", desc: "High-volume frontend & API tasks" },
          { id: "FAST_ITERATION", label: "Fast Test / Assertion Loops", desc: "Unit tests & quick syntax checks" },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => setWorkloadType(item.id as any)}
            className={`p-3.5 rounded-lg border text-left transition ${
              workloadType === item.id
                ? "border-emerald-500/50 bg-emerald-500/10 text-white shadow-lg shadow-emerald-950/30"
                : "border-white/5 bg-white/[0.02] text-zinc-400 hover:border-white/15"
            }`}
          >
            <div className="text-xs font-semibold text-zinc-200">{item.label}</div>
            <div className="text-[11px] text-zinc-500 mt-0.5">{item.desc}</div>
          </button>
        ))}
      </div>

      {/* Interactive Controls & Output Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Sliders */}
        <div className="lg:col-span-5 space-y-6 bg-white/[0.02] p-5 rounded-xl border border-white/5">
          {/* Team Size Slider */}
          <div>
            <div className="flex justify-between items-center text-xs font-mono mb-2">
              <span className="text-zinc-300 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-cyan-400" />
                Active Engineering Team Size
              </span>
              <span className="text-cyan-400 font-bold text-sm">{teamSize} Engineers</span>
            </div>
            <input
              type="range"
              min={1}
              max={250}
              step={1}
              value={teamSize}
              onChange={(e) => setTeamSize(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-zinc-600 font-mono mt-1">
              <span>1 Dev</span>
              <span>100 Devs</span>
              <span>250 Devs</span>
            </div>
          </div>

          {/* Daily Turns Slider */}
          <div>
            <div className="flex justify-between items-center text-xs font-mono mb-2">
              <span className="text-zinc-300 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Agent Turns / Dev / Day
              </span>
              <span className="text-amber-400 font-bold text-sm">{dailyTurnsPerDev} Turns</span>
            </div>
            <input
              type="range"
              min={10}
              max={200}
              step={5}
              value={dailyTurnsPerDev}
              onChange={(e) => setDailyTurnsPerDev(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
            />
            <div className="flex justify-between text-[10px] text-zinc-600 font-mono mt-1">
              <span>10 Turns</span>
              <span>100 Turns</span>
              <span>200 Turns</span>
            </div>
          </div>

          <div className="pt-2 border-t border-white/5 text-xs text-zinc-500 font-mono flex items-center justify-between">
            <span>Annual Agent Turns:</span>
            <span className="text-zinc-300 font-semibold">{stats.annualTotalTurns.toLocaleString()} turns/yr</span>
          </div>
        </div>

        {/* Right Column: Comparative Financials */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Net Annual Savings Hero Box */}
          <div className="sm:col-span-2 p-5 rounded-xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-obsidian-900 to-emerald-950/20 backdrop-blur-md relative">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-emerald-400 font-semibold">
                Net Annual Projected Savings
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-mono font-bold">
                {stats.savingsPercent}% Cost Reduction
              </span>
            </div>

            <div className="text-4xl font-extrabold text-white tracking-tight mt-2 font-mono flex items-baseline gap-1">
              <span className="text-emerald-400">$</span>
              {stats.annualSavings.toLocaleString()}
              <span className="text-xs font-sans font-normal text-zinc-400">/ year</span>
            </div>

            {/* Visual Spend Progress Bar */}
            <div className="mt-4 space-y-1.5">
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-zinc-400">Benchpress Choreography Spend</span>
                <span className="text-emerald-400 font-bold">${stats.annualBenchpressSpend.toLocaleString()}</span>
              </div>
              <div className="w-full bg-zinc-800 h-2.5 rounded-full overflow-hidden flex">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${100 - stats.savingsPercent}%` }}
                />
                <div
                  className="bg-rose-500/30 h-full transition-all duration-300"
                  style={{ width: `${stats.savingsPercent}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-zinc-500 font-mono">
                <span>2-Tier Orchestration</span>
                <span>Monolithic Frontier Baseline (${stats.annualFrontierSpend.toLocaleString()})</span>
              </div>
            </div>
          </div>

          {/* Metric Box 1: Time Saved */}
          <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="text-xs font-mono text-zinc-400 flex items-center gap-1.5">
              <TrendingDown className="w-3.5 h-3.5 text-cyan-400" />
              Developer Time Reclaimed
            </div>
            <div className="text-2xl font-bold text-white mt-1 font-mono">
              {stats.hoursSavedPerYear.toLocaleString()} <span className="text-xs text-zinc-500">hrs/yr</span>
            </div>
            <p className="text-[11px] text-zinc-500 mt-1">Faster turn latencies eliminate engineer context switching.</p>
          </div>

          {/* Metric Box 2: Enterprise Assurance */}
          <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="text-xs font-mono text-zinc-400 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              Pass@1 Quality Parity
            </div>
            <div className="text-2xl font-bold text-white mt-1 font-mono">
              71.2% <span className="text-xs text-emerald-400 font-normal">SWE-bench</span>
            </div>
            <p className="text-[11px] text-zinc-500 mt-1">Zero regression in accuracy via Gemini 2.5 Pro architectural planning.</p>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      {showExportToast && (
        <div className="absolute bottom-4 right-4 bg-emerald-950 border border-emerald-500/50 text-emerald-200 px-4 py-2 rounded-lg text-xs font-mono shadow-2xl flex items-center gap-2 animate-fade-in">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          ROI Report exported to Downloads!
        </div>
      )}
    </div>
  );
}
