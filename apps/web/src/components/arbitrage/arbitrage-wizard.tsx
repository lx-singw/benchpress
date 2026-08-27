"use client";

import React, { useState } from "react";
import { TrendingDown, Download, DollarSign, Zap, Sparkles, Check, Copy } from "lucide-react";

export function ArbitrageWizard() {
  const [monthlyAgentRuns, setMonthlyAgentRuns] = useState(25000);
  const [baselineModel, setBaselineModel] = useState("claude-3-7-sonnet");
  const [copiedConfig, setCopiedConfig] = useState<string | null>(null);

  // Pricing constants per resolution ($)
  const baselineCpr: Record<string, number> = {
    "claude-3-7-sonnet": 1.480,
    "gpt-4.5": 8.450,
    "gpt-4o": 1.320,
  };

  const hybridCpr = 0.185; // Benchpress 2-tier Gemini Pro + Flash
  const currentBaselineRate = baselineCpr[baselineModel] || 1.480;

  const baselineMonthlyCost = monthlyAgentRuns * currentBaselineRate;
  const hybridMonthlyCost = monthlyAgentRuns * hybridCpr;
  const monthlySavingsUsd = baselineMonthlyCost - hybridMonthlyCost;
  const annualSavingsUsd = monthlySavingsUsd * 12;
  const savingsPct = Math.round(((currentBaselineRate - hybridCpr) / currentBaselineRate) * 1000) / 10;

  const cursorRulesCode = `# Benchpress Autonomous 2-Tier Model Routing for Cursor
enable_hybrid_routing = true
default_planner_model = "gemini-2.5-pro"
default_coder_model = "gemini-2.5-flash"
max_budget_cap_usd = 0.50
`;

  const liteLlmConfigCode = `model_list:
  - model_name: benchpress-hybrid
    litellm_params:
      model: gemini/gemini-2.5-pro
      api_base: http://localhost:3000/api/v1/proxy
      extra_headers:
        x-benchpress-route: "HYBRID_CHOREOGRAPHY"
`;

  const handleCopy = (key: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedConfig(key);
    setTimeout(() => setCopiedConfig(null), 2000);
  };

  const handleDownload = (filename: string, content: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Interactive Savings Calculator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-xl shadow-2xl space-y-6">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-emerald-400" />
            Live Enterprise Arbitrage Calculator
          </h2>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
                <span>Monthly Agent Task Resolutions:</span>
                <span className="text-indigo-400 font-mono font-bold text-sm">
                  {monthlyAgentRuns.toLocaleString()} runs / mo
                </span>
              </div>
              <input
                type="range"
                min="1000"
                max="250000"
                step="1000"
                value={monthlyAgentRuns}
                onChange={(e) => setMonthlyAgentRuns(Number(e.target.value))}
                className="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-2">
                Baseline Frontier Monolithic Model
              </label>
              <select
                value={baselineModel}
                onChange={(e) => setBaselineModel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              >
                <option value="claude-3-7-sonnet">Claude 3.7 Sonnet ($1.480 CPR)</option>
                <option value="gpt-4.5">GPT-4.5 Frontier ($8.450 CPR)</option>
                <option value="gpt-4o">GPT-4o ($1.320 CPR)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800/80">
            <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Baseline Cost</span>
              <div className="text-lg font-bold text-rose-400 font-mono mt-0.5">
                ${Math.round(baselineMonthlyCost).toLocaleString()} / mo
              </div>
            </div>

            <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Benchpress 2-Tier</span>
              <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                ${Math.round(hybridMonthlyCost).toLocaleString()} / mo
              </div>
            </div>

            <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
              <span className="text-xs text-emerald-400 font-medium">Net FinOps Arbitrage</span>
              <div className="text-xl font-extrabold text-emerald-300 font-mono mt-0.5">
                {savingsPct}% OFF
              </div>
            </div>
          </div>
        </div>

        {/* Projected ROI Banner */}
        <div className="bg-gradient-to-br from-indigo-950/50 via-slate-900/60 to-purple-950/40 border border-indigo-500/30 rounded-xl p-6 backdrop-blur-xl flex flex-col justify-between">
          <div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              <Sparkles className="w-3.5 h-3.5" />
              Annual Enterprise ROI
            </span>
            <div className="text-3xl font-black text-white font-mono mt-3">
              ${Math.round(annualSavingsUsd).toLocaleString()}
            </div>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Redirect saved inference budget into 10x higher trajectory evaluation throughput with zero accuracy degradation.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-indigo-500/20">
            <div className="flex items-center gap-2 text-xs text-indigo-300 font-medium">
              <Zap className="w-4 h-4 text-amber-400" />
              Instant 1-Click Gateway Migration Active
            </div>
          </div>
        </div>
      </div>

      {/* 1-Click Migration Recipes */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
          <h2 className="text-base font-semibold text-white">
            1-Click Drop-In Migration Recipes
          </h2>
          <span className="text-xs text-slate-400">
            Export ready-to-run configurations for your IDE or proxy gateway.
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cursor Rules */}
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white font-mono">.cursorrules</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleCopy("cursor", cursorRulesCode)}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 bg-slate-900 px-2 py-1 rounded border border-slate-800"
                >
                  {copiedConfig === "cursor" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  Copy
                </button>
                <button
                  onClick={() => handleDownload(".cursorrules", cursorRulesCode)}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 bg-slate-900 px-2 py-1 rounded border border-slate-800"
                >
                  <Download className="w-3.5 h-3.5" />
                  Save
                </button>
              </div>
            </div>
            <pre className="text-[11px] font-mono text-indigo-300/90 bg-slate-900/80 p-3 rounded overflow-x-auto border border-slate-800/60">
              {cursorRulesCode}
            </pre>
          </div>

          {/* LiteLLM Gateway */}
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white font-mono">litellm_config.yaml</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleCopy("litellm", liteLlmConfigCode)}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 bg-slate-900 px-2 py-1 rounded border border-slate-800"
                >
                  {copiedConfig === "litellm" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  Copy
                </button>
                <button
                  onClick={() => handleDownload("litellm_config.yaml", liteLlmConfigCode)}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 bg-slate-900 px-2 py-1 rounded border border-slate-800"
                >
                  <Download className="w-3.5 h-3.5" />
                  Save
                </button>
              </div>
            </div>
            <pre className="text-[11px] font-mono text-cyan-300/90 bg-slate-900/80 p-3 rounded overflow-x-auto border border-slate-800/60">
              {liteLlmConfigCode}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
