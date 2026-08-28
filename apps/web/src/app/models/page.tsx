"use client";

import React, { useState } from "react";
import Link from "next/link";
import { getAllModels, ModelProfileData } from "@/lib/models-data";
import { Badge } from "@/components/ui/badge";
import { Cpu, Search, ArrowRight, TrendingUp, DollarSign, Activity, Zap, Shield, Layers } from "lucide-react";

export default function ModelsCatalogPage() {
  const allModels = getAllModels();
  const [selectedProvider, setSelectedProvider] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"cpr" | "pass" | "speed" | "context">("cpr");

  const providers = ["ALL", "Google", "Anthropic", "OpenAI", "DeepSeek", "Meta", "Benchpress"];

  const filteredModels = allModels
    .filter((model) => {
      const matchesProvider = selectedProvider === "ALL" || model.provider === selectedProvider;
      const matchesSearch =
        model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.tier.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.bestFitTaskTypes.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesProvider && matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === "cpr") return a.metrics.cprUsd - b.metrics.cprUsd;
      if (sortBy === "pass") return b.metrics.passAt1 - a.metrics.passAt1;
      if (sortBy === "speed") return a.metrics.avgExecutionTimeSeconds - b.metrics.avgExecutionTimeSeconds;
      if (sortBy === "context") return b.contextWindow - a.contextWindow;
      return 0;
    });

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Page Header */}
        <div className="mb-10 text-center sm:text-left">
          <div className="flex items-center gap-2 mb-3">
            <Badge variant="cyan" size="sm">
              Global Model Directory
            </Badge>
            <span className="text-xs font-mono text-gray-400">15 Evaluated Models • Multi-Turn Agentic Profiles</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            AI Model Economic & Architectural Catalog
          </h1>
          <p className="mt-2 text-base text-gray-400 max-w-3xl">
            Explore empirical multi-turn agent profiles. Compare real Cost Per Resolution (CPR), context degradation curves, tool failure rates, and token waterfalls across every major foundation model.
          </p>
        </div>

        {/* Filters & Search Toolbar */}
        <div className="mb-8 flex flex-col gap-4 rounded-xl border border-white/10 bg-[#121722]/80 p-4 backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between">
          {/* Provider Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            {providers.map((provider) => (
              <button
                key={provider}
                onClick={() => setSelectedProvider(provider)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  selectedProvider === provider
                    ? "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/40 shadow-glass-cyan"
                    : "text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent"
                }`}
              >
                {provider === "Benchpress" ? "★ Benchpress Hybrid" : provider}
              </button>
            ))}
          </div>

          {/* Search & Sort Controls */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 sm:w-64">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search models, tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-black/40 py-1.5 pl-9 pr-3 text-xs text-white placeholder-gray-500 focus:border-[#00F0FF]/50 focus:outline-none focus:ring-1 focus:ring-[#00F0FF]/50"
              />
            </div>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="rounded-lg border border-white/10 bg-black/40 px-3 py-1.5 text-xs text-gray-300 focus:border-[#00F0FF]/50 focus:outline-none"
            >
              <option value="cpr">Sort by: Lowest CPR ($)</option>
              <option value="pass">Sort by: Highest Pass@1 (%)</option>
              <option value="speed">Sort by: Fastest Resolution</option>
              <option value="context">Sort by: Context Window</option>
            </select>
          </div>
        </div>

        {/* Model Cards Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredModels.map((model) => {
            const isHybrid = model.id === "benchpress-hybrid";
            return (
              <div
                key={model.id}
                className={`group relative flex flex-col justify-between rounded-xl border p-6 backdrop-blur-xl transition-all hover:translate-y-[-2px] ${
                  isHybrid
                    ? "border-[#00F0FF]/50 bg-gradient-to-b from-[#121722]/95 to-[#00F0FF]/5 shadow-[0_0_30px_rgba(0,240,255,0.15)]"
                    : "border-white/10 bg-[#121722]/70 hover:border-white/20 hover:bg-[#121722]/90"
                }`}
              >
                <div>
                  {/* Top Bar: Provider & Tier */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-mono text-gray-400">{model.provider}</span>
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
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-white group-hover:text-[#00F0FF] transition-colors mb-2">
                    {model.name}
                  </h3>

                  <p className="text-xs text-gray-400 line-clamp-2 mb-6">
                    {model.strengths[0]}
                  </p>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-6">
                    <div className="rounded-lg bg-black/40 border border-white/5 p-3">
                      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                        <DollarSign className="h-3 w-3 text-[#10B981]" />
                        Cost Per Resolution
                      </div>
                      <div className="text-lg font-mono font-bold text-white">
                        ${model.metrics.cprUsd.toFixed(2)}
                      </div>
                    </div>

                    <div className="rounded-lg bg-black/40 border border-white/5 p-3">
                      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                        <TrendingUp className="h-3 w-3 text-[#00F0FF]" />
                        Verified Pass@1
                      </div>
                      <div className="text-lg font-mono font-bold text-white">
                        {model.metrics.passAt1}%
                      </div>
                    </div>

                    <div className="rounded-lg bg-black/40 border border-white/5 p-3">
                      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                        <Activity className="h-3 w-3 text-amber-400" />
                        Mean Turns
                      </div>
                      <div className="text-sm font-mono text-gray-200">
                        {model.metrics.meanTurnsToResolve} turns
                      </div>
                    </div>

                    <div className="rounded-lg bg-black/40 border border-white/5 p-3">
                      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                        <Layers className="h-3 w-3 text-purple-400" />
                        Context Retention
                      </div>
                      <div className="text-sm font-mono text-gray-200">
                        {model.metrics.turn20ContextRetention}% @ T20
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="border-t border-white/10 pt-4 flex items-center justify-between">
                  <Link
                    href={`/compare?a=${model.id}&b=benchpress-hybrid`}
                    className="text-xs font-mono text-gray-400 hover:text-white transition-colors"
                  >
                    Compare ⚖️
                  </Link>

                  <Link
                    href={`/models/${model.id}`}
                    className="flex items-center gap-1.5 text-xs font-mono font-bold text-[#00F0FF] group-hover:translate-x-0.5 transition-transform"
                  >
                    Deep Profile
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
