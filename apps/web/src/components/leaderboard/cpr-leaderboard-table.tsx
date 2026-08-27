"use client";

import React, { useState, useMemo } from "react";
import {
  TrendingDown,
  Sparkles,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Search,
  Zap,
} from "lucide-react";
import { BENCHMARK_MODELS } from "@/lib/mock-data";
import { ModelBadge } from "./model-badge";

interface CprLeaderboardTableProps {
  selectedModelId?: string;
  onSelectModel?: (modelId: string) => void;
}

export function CprLeaderboardTable({ selectedModelId, onSelectModel }: CprLeaderboardTableProps) {
  const [activeTab, setActiveTab] = useState<string>("SWE_BENCH_VERIFIED");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<"cpr_usd" | "pass_at_1" | "trajectory_bloat_ratio">("cpr_usd");
  const [sortAsc, setSortAsc] = useState(true);
  const [expandedModelId, setExpandedModelId] = useState<string | null>(null);

  const filteredModels = useMemo(() => {
    return BENCHMARK_MODELS.filter((m) => {
      const matchesTab = m.task_suite === activeTab;
      const matchesSearch =
        m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.provider.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesTab && matchesSearch;
    }).sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      return sortAsc ? valA - valB : valB - valA;
    });
  }, [activeTab, searchQuery, sortField, sortAsc]);

  const handleSort = (field: "cpr_usd" | "pass_at_1" | "trajectory_bloat_ratio") => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === "cpr_usd" || field === "trajectory_bloat_ratio");
    }
  };

  return (
    <div className="rounded-xl border border-white/10 bg-obsidian-900/80 p-6 shadow-2xl backdrop-blur-xl space-y-5">
      {/* Header & Suite Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Continuous Economic Leaderboard <Sparkles className="w-5 h-5 text-[#00F0FF]" />
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Ranked by Cost Per Resolution (CPR) and Verified Task Resolution Rate (Pass@1).
          </p>
        </div>

        {/* Suite Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-white/5 rounded-lg border border-white/5">
          {[
            { id: "SWE_BENCH_VERIFIED", label: "SWE-bench Verified" },
            { id: "HUMANEVAL_XL", label: "HumanEval-XL" },
            { id: "CYBENCH", label: "Cybench" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition ${
                activeTab === tab.id
                  ? "bg-[#00F0FF] text-[#0A0D14] font-bold shadow-glass-cyan"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 max-w-sm">
        <Search className="w-4 h-4 text-zinc-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter model name or provider..."
          className="w-full bg-transparent text-xs font-mono text-white placeholder-zinc-500 focus:outline-none"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-white/10 text-zinc-400">
              <th className="pb-3 pl-2 font-medium">Rank & Model</th>
              <th className="pb-3 font-medium">Provider</th>
              <th
                className="pb-3 font-medium cursor-pointer hover:text-white transition"
                onClick={() => handleSort("cpr_usd")}
              >
                <div className="flex items-center gap-1">
                  <span>CPR (USD)</span>
                  {sortField === "cpr_usd" && (sortAsc ? <ChevronUp className="w-3 h-3 text-[#00F0FF]" /> : <ChevronDown className="w-3 h-3 text-[#00F0FF]" />)}
                </div>
              </th>
              <th
                className="pb-3 font-medium cursor-pointer hover:text-white transition"
                onClick={() => handleSort("pass_at_1")}
              >
                <div className="flex items-center gap-1">
                  <span>Pass@1 Rate</span>
                  {sortField === "pass_at_1" && (sortAsc ? <ChevronUp className="w-3 h-3 text-[#00F0FF]" /> : <ChevronDown className="w-3 h-3 text-[#00F0FF]" />)}
                </div>
              </th>
              <th
                className="pb-3 font-medium cursor-pointer hover:text-white transition"
                onClick={() => handleSort("trajectory_bloat_ratio")}
              >
                <div className="flex items-center gap-1">
                  <span>Bloat Ratio (TBR)</span>
                  {sortField === "trajectory_bloat_ratio" && (sortAsc ? <ChevronUp className="w-3 h-3 text-[#00F0FF]" /> : <ChevronDown className="w-3 h-3 text-[#00F0FF]" />)}
                </div>
              </th>
              <th className="pb-3 font-medium">AST Auto-Heal</th>
              <th className="pb-3 pr-2 text-right font-medium">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filteredModels.map((model, idx) => {
              const isSelected = selectedModelId === model.model_id;
              const isExpanded = expandedModelId === model.model_id;

              return (
                <React.Fragment key={model.model_id}>
                  <tr
                    className={`transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-[#00F0FF]/10 text-white"
                        : "hover:bg-white/[0.03] text-zinc-300"
                    }`}
                    onClick={() => {
                      if (onSelectModel) onSelectModel(model.model_id);
                      setExpandedModelId(isExpanded ? null : model.model_id);
                    }}
                  >
                    <td className="py-3 pl-2 flex items-center gap-2.5 font-bold text-white">
                      <span className="text-zinc-500 w-4">#{idx + 1}</span>
                      <span>{model.name}</span>
                      {model.is_pareto_frontier && (
                        <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          Pareto
                        </span>
                      )}
                    </td>
                    <td className="py-3">
                      <ModelBadge provider={model.provider} />
                    </td>
                    <td className="py-3 font-bold text-emerald-400">${model.cpr_usd.toFixed(3)}</td>
                    <td className="py-3 text-[#00F0FF]">{(model.pass_at_1 * 100).toFixed(1)}%</td>
                    <td className="py-3 text-zinc-300">{model.trajectory_bloat_ratio.toFixed(2)}x</td>
                    <td className="py-3 text-amber-300">
                      {(model.ast_healing_success_rate * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 pr-2 text-right">
                      <button className="text-zinc-500 hover:text-white transition">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </td>
                  </tr>

                  {/* Expandable Profile */}
                  {isExpanded && (
                    <tr className="bg-black/40">
                      <td colSpan={7} className="p-4 border-t border-b border-white/10">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
                          <div>
                            <span className="text-zinc-500 uppercase text-[10px]">Context Window</span>
                            <div className="text-white font-bold">{model.context_window_tokens.toLocaleString()} tokens</div>
                          </div>
                          <div>
                            <span className="text-zinc-500 uppercase text-[10px]">Price per 1M In/Out</span>
                            <div className="text-zinc-300 font-bold">${model.price_per_1m_input} / ${model.price_per_1m_output}</div>
                          </div>
                          <div>
                            <span className="text-zinc-500 uppercase text-[10px]">Mean Turn Latency</span>
                            <div className="text-[#00F0FF] font-bold">{model.mean_latency_sec}s / turn</div>
                          </div>
                          <div>
                            <span className="text-zinc-500 uppercase text-[10px]">Execution Sagas</span>
                            <div className="text-emerald-400 font-bold">gVisor Isolated</div>
                          </div>
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
    </div>
  );
}
