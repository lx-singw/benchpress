"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
  Flame,
  Layers,
  Sparkles,
  TrendingDown,
  Wrench,
  Zap,
  Radio,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { ParetoFrontierChart } from "@/components/pareto-frontier-chart";
import { CprLeaderboardTable } from "@/components/cpr-leaderboard-table";
import { VisionErrorDropzone } from "@/components/vision-error-dropzone";
import { WhySwitchRoiCalculator } from "@/components/why-switch-roi-calculator";

export default function HubPage() {
  const [selectedModelId, setSelectedModelId] = useState<string>("hybrid-gemini-pro-flash");
  const [domSyncNotice, setDomSyncNotice] = useState<string | null>(null);

  // Listen to Spoken Voice Copilot DOM sync notifications
  useEffect(() => {
    const handleDomSync = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail?.message) {
        setDomSyncNotice(customEvent.detail.message);
        setTimeout(() => setDomSyncNotice(null), 4000);
      }
    };

    window.addEventListener("benchpress:dom-sync", handleDomSync);
    return () => window.removeEventListener("benchpress:dom-sync", handleDomSync);
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Voice Copilot Live Synchronization Toast */}
      {domSyncNotice && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-xl border border-[#00F0FF]/40 bg-[#121722]/95 p-3.5 text-xs font-mono text-white shadow-glass-cyan backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4">
          <Radio className="h-4 w-4 animate-pulse text-[#00F0FF]" />
          <span>{domSyncNotice}</span>
        </div>
      )}

      {/* Hero Header */}
      <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="cyan" dot size="sm">
              TRI-MODAL INTELLIGENCE PLATFORM
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

      {/* Grid: Interactive Pareto Frontier (Modality 3) & Computer Vision Dropzone (Modality 2) */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3 mb-8">
        <div className="lg:col-span-2">
          <ParetoFrontierChart onSelectModel={(id) => setSelectedModelId(id)} />
        </div>
        <div className="lg:col-span-1">
          <VisionErrorDropzone />
        </div>
      </div>

      {/* Enterprise Leaderboard Table */}
      <div className="mb-8">
        <CprLeaderboardTable
          selectedModelId={selectedModelId}
          onSelectModel={(id) => setSelectedModelId(id)}
        />
      </div>

      {/* Enterprise 'Why Switch?' ROI Calculator */}
      <div className="mb-8">
        <WhySwitchRoiCalculator />
      </div>
    </div>
  );
}
